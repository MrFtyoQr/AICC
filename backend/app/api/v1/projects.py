import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentWorkspace, SessionDep, WorkspaceContext, require
from app.api.v1.errors import CONFLICT, FORBIDDEN, NOT_FOUND, domain_errors
from app.application.workspaces import ProjectService
from app.core.permissions import Permission
from app.infrastructure.models import Environment, Project

router = APIRouter(tags=["projects"])

Writer = Annotated[WorkspaceContext, Depends(require(Permission.PROJECT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Permission.PROJECT_DELETE))]


class EnvironmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    kind: str

    @classmethod
    def of(cls, environment: Environment) -> "EnvironmentResponse":
        return cls(id=environment.id, name=environment.name, kind=environment.kind)


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
            environments=[EnvironmentResponse.of(e) for e in project.environments],
        )


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    kind: Literal["development", "staging", "production"]


class EnvironmentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=40)


def _service(ctx: WorkspaceContext, session) -> ProjectService:
    return ProjectService(session, ctx.scope)


_PROJECT = "Proyecto no encontrado"
_ENVIRONMENT = "Ambiente no encontrado"


@router.get(
    "/projects",
    response_model=list[ProjectResponse],
    summary="Proyectos del workspace actual",
    responses=NOT_FOUND,
)
async def list_projects(ctx: CurrentWorkspace, session: SessionDep):
    return [ProjectResponse.of(p) for p in await _service(ctx, session).list()]


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto (incluye ambiente development)",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def create_project(body: ProjectCreate, ctx: Writer, session: SessionDep):
    with domain_errors(_PROJECT):
        project = await _service(ctx, session).create(body.name, body.description)
    return ProjectResponse.of(project)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Detalle de proyecto",
    responses=NOT_FOUND,
)
async def get_project(project_id: uuid.UUID, ctx: CurrentWorkspace, session: SessionDep):
    with domain_errors(_PROJECT):
        return ProjectResponse.of(await _service(ctx, session).get(project_id))


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Editar proyecto",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def update_project(
    project_id: uuid.UUID, body: ProjectUpdate, ctx: Writer, session: SessionDep
):
    with domain_errors(_PROJECT):
        project = await _service(ctx, session).update(
            project_id, name=body.name, description=body.description
        )
    return ProjectResponse.of(project)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar proyecto y sus ambientes",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def delete_project(project_id: uuid.UUID, ctx: Deleter, session: SessionDep) -> None:
    with domain_errors(_PROJECT):
        await _service(ctx, session).delete(project_id)


@router.post(
    "/projects/{project_id}/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir ambiente a un proyecto",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def create_environment(
    project_id: uuid.UUID, body: EnvironmentCreate, ctx: Writer, session: SessionDep
):
    with domain_errors(_PROJECT):
        environment = await _service(ctx, session).add_environment(project_id, body.name, body.kind)
    return EnvironmentResponse.of(environment)


@router.patch(
    "/projects/{project_id}/environments/{environment_id}",
    response_model=EnvironmentResponse,
    summary="Renombrar ambiente",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def update_environment(
    project_id: uuid.UUID,
    environment_id: uuid.UUID,
    body: EnvironmentUpdate,
    ctx: Writer,
    session: SessionDep,
):
    with domain_errors(_ENVIRONMENT):
        environment = await _service(ctx, session).rename_environment(
            project_id, environment_id, body.name
        )
    return EnvironmentResponse.of(environment)


@router.delete(
    "/projects/{project_id}/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar ambiente (un proyecto conserva al menos uno)",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def delete_environment(
    project_id: uuid.UUID, environment_id: uuid.UUID, ctx: Deleter, session: SessionDep
) -> None:
    with domain_errors(_ENVIRONMENT):
        await _service(ctx, session).delete_environment(project_id, environment_id)
