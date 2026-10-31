import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, CurrentWorkspace, SessionDep, WorkspaceContext, require
from app.application.workspaces import NameTaken, NotFound, ProjectService, memberships_of
from app.core.permissions import MATRIX, Permission, Role
from app.infrastructure.models import Project

router = APIRouter(tags=["workspaces"])

_NOT_FOUND = {404: {"description": "No existe o pertenece a otro workspace"}}
_FORBIDDEN = {403: {"description": "Tu rol no permite esta acción"}}


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_personal: bool
    role: Role
    permissions: list[Permission]


class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    kind: str


class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    environments: list[EnvironmentResponse]

    @classmethod
    def of(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            environments=[
                EnvironmentResponse(id=e.id, name=e.name, kind=e.kind) for e in project.environments
            ],
        )


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


def _workspace(workspace, role: str) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        is_personal=workspace.is_personal,
        role=Role(role),
        permissions=sorted(MATRIX[Role(role)]),
    )


def _service(ctx: WorkspaceContext, session) -> ProjectService:
    return ProjectService(session, ctx.workspace.id)


_NAME_TAKEN = HTTPException(status.HTTP_409_CONFLICT, "Ya existe un proyecto con ese nombre")


@router.get(
    "/workspaces", response_model=list[WorkspaceResponse], summary="Mis workspaces y mi rol"
)
async def list_workspaces(user: CurrentUser, session: SessionDep):
    return [_workspace(m.workspace, m.role) for m in await memberships_of(session, user.id)]


@router.get(
    "/workspaces/current",
    response_model=WorkspaceResponse,
    summary="Workspace actual (cabecera X-Workspace-Id)",
    responses=_NOT_FOUND,
)
async def current_workspace(ctx: CurrentWorkspace):
    return _workspace(ctx.workspace, ctx.role)


@router.get(
    "/projects",
    response_model=list[ProjectResponse],
    summary="Proyectos del workspace actual",
    responses=_NOT_FOUND,
)
async def list_projects(ctx: CurrentWorkspace, session: SessionDep):
    return [ProjectResponse.of(p) for p in await _service(ctx, session).list()]


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto (incluye ambiente development)",
    responses={**_NOT_FOUND, **_FORBIDDEN, 409: {"description": "Nombre repetido"}},
)
async def create_project(
    body: ProjectCreate,
    ctx: Annotated[WorkspaceContext, Depends(require(Permission.PROJECT_WRITE))],
    session: SessionDep,
):
    try:
        project = await _service(ctx, session).create(body.name, body.description)
    except NameTaken:
        raise _NAME_TAKEN from None
    return ProjectResponse.of(project)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Detalle de proyecto",
    responses=_NOT_FOUND,
)
async def get_project(project_id: uuid.UUID, ctx: CurrentWorkspace, session: SessionDep):
    try:
        return ProjectResponse.of(await _service(ctx, session).get(project_id))
    except NotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Editar proyecto",
    responses={**_NOT_FOUND, **_FORBIDDEN, 409: {"description": "Nombre repetido"}},
)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    ctx: Annotated[WorkspaceContext, Depends(require(Permission.PROJECT_WRITE))],
    session: SessionDep,
):
    try:
        project = await _service(ctx, session).update(
            project_id, name=body.name, description=body.description
        )
    except NotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
    except NameTaken:
        raise _NAME_TAKEN from None
    return ProjectResponse.of(project)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar proyecto y sus ambientes",
    responses={**_NOT_FOUND, **_FORBIDDEN},
)
async def delete_project(
    project_id: uuid.UUID,
    ctx: Annotated[WorkspaceContext, Depends(require(Permission.PROJECT_DELETE))],
    session: SessionDep,
) -> None:
    try:
        await _service(ctx, session).delete(project_id)
    except NotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Proyecto no encontrado") from None
