import base64
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import CurrentUser, SessionDep, WorkspaceContext, require
from app.api.v1.errors import CONFLICT, FORBIDDEN, NOT_FOUND, domain_errors
from app.application.workspaces import (
    MemberService,
    WorkspaceService,
    activity,
    create_team_workspace,
    memberships_of,
)
from app.core.permissions import MATRIX, Permission, Role
from app.infrastructure.models import AuditLog, Workspace

router = APIRouter(tags=["workspaces"])

Reader = Annotated[WorkspaceContext, Depends(require(Permission.WORKSPACE_READ))]
Updater = Annotated[WorkspaceContext, Depends(require(Permission.WORKSPACE_UPDATE))]
Owner = Annotated[WorkspaceContext, Depends(require(Permission.WORKSPACE_DELETE))]
Manager = Annotated[WorkspaceContext, Depends(require(Permission.MEMBERS_MANAGE))]


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_personal: bool
    role: Role
    permissions: list[Permission]


class WorkspaceName(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class MemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    display_name: str | None
    role: Role
    is_you: bool


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    created_at: datetime


class MembersResponse(BaseModel):
    members: list[MemberResponse]
    invitations: list[InvitationResponse]


class InvitationCreate(BaseModel):
    email: EmailStr = Field(max_length=320)
    role: Role


class RoleChange(BaseModel):
    role: Role


class Actor(BaseModel):
    email: str
    display_name: str | None


class ActivityItem(BaseModel):
    id: uuid.UUID
    created_at: datetime
    actor: Actor | None
    action: str
    summary: str
    outcome: str


class ActivityPage(BaseModel):
    items: list[ActivityItem]
    next_cursor: str | None = Field(description="Pásalo como `cursor` para la página siguiente")


def _workspace(workspace: Workspace, role: str) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        is_personal=workspace.is_personal,
        role=Role(role),
        permissions=sorted(MATRIX[Role(role)]),
    )


# --- Workspaces ---------------------------------------------------------------


@router.get(
    "/workspaces", response_model=list[WorkspaceResponse], summary="Mis workspaces y mi rol"
)
async def list_workspaces(user: CurrentUser, session: SessionDep):
    return [_workspace(m.workspace, m.role) for m in await memberships_of(session, user.id)]


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear workspace de equipo (quien lo crea es dueño)",
)
async def create_workspace(body: WorkspaceName, user: CurrentUser, session: SessionDep):
    workspace = await create_team_workspace(session, user.id, body.name)
    return _workspace(workspace, Role.OWNER)


@router.get(
    "/workspaces/current",
    response_model=WorkspaceResponse,
    summary="Workspace actual (cabecera X-Workspace-Id)",
    responses=NOT_FOUND,
)
async def current_workspace(ctx: Reader):
    return _workspace(ctx.workspace, ctx.role)


@router.patch(
    "/workspaces/current",
    response_model=WorkspaceResponse,
    summary="Renombrar el workspace actual",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def rename_workspace(body: WorkspaceName, ctx: Updater, session: SessionDep):
    workspace = await WorkspaceService(session, ctx.scope).rename(ctx.workspace, body.name)
    return _workspace(workspace, ctx.role)


@router.delete(
    "/workspaces/current",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar el workspace actual (no el personal)",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def delete_workspace(ctx: Owner, session: SessionDep) -> None:
    with domain_errors():
        await WorkspaceService(session, ctx.scope).delete(ctx.workspace)


# --- Miembros -----------------------------------------------------------------


@router.get(
    "/members",
    response_model=MembersResponse,
    summary="Miembros e invitaciones pendientes del workspace actual",
    responses=NOT_FOUND,
)
async def list_members(ctx: Reader, session: SessionDep):
    service = MemberService(session, ctx.scope)
    return MembersResponse(
        members=[
            MemberResponse(
                id=m.id,
                user_id=m.user_id,
                email=m.user.email,
                display_name=m.user.display_name,
                role=Role(m.role),
                is_you=m.user_id == ctx.user.id,
            )
            for m in await service.members()
        ],
        invitations=[
            InvitationResponse(id=i.id, email=i.email, role=Role(i.role), created_at=i.created_at)
            for i in await service.invitations()
        ],
    )


@router.post(
    "/members/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invitar por email (queda pendiente; el envío de correo llega en O5)",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def invite_member(body: InvitationCreate, ctx: Manager, session: SessionDep):
    with domain_errors():
        invitation = await MemberService(session, ctx.scope).invite(body.email, body.role)
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        role=Role(invitation.role),
        created_at=invitation.created_at,
    )


@router.delete(
    "/members/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar invitación pendiente",
    responses={**NOT_FOUND, **FORBIDDEN},
)
async def revoke_invitation(invitation_id: uuid.UUID, ctx: Manager, session: SessionDep) -> None:
    with domain_errors("Invitación no encontrada"):
        await MemberService(session, ctx.scope).revoke_invitation(invitation_id)


@router.patch(
    "/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar el rol de un miembro",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def change_role(
    membership_id: uuid.UUID, body: RoleChange, ctx: Manager, session: SessionDep
) -> None:
    with domain_errors("Miembro no encontrado"):
        await MemberService(session, ctx.scope).change_role(membership_id, body.role)


@router.delete(
    "/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar a un miembro del workspace",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def remove_member(membership_id: uuid.UUID, ctx: Manager, session: SessionDep) -> None:
    with domain_errors("Miembro no encontrado"):
        await MemberService(session, ctx.scope).remove(membership_id)


# --- Actividad ----------------------------------------------------------------


def _encode(entry: AuditLog) -> str:
    raw = f"{entry.created_at.isoformat()}|{entry.id}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        created_at, entry_id = base64.urlsafe_b64decode(cursor).decode().split("|")
        return datetime.fromisoformat(created_at), uuid.UUID(entry_id)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Cursor inválido") from None


@router.get(
    "/activity",
    response_model=ActivityPage,
    summary="Registro de actividad del workspace actual (más reciente primero)",
    responses=NOT_FOUND,
)
async def list_activity(
    ctx: Reader,
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
):
    before = _decode(cursor) if cursor else None
    entries = await activity(session, ctx.workspace.id, limit=limit + 1, before=before)
    page = entries[:limit]
    return ActivityPage(
        items=[
            ActivityItem(
                id=e.id,
                created_at=e.created_at,
                actor=Actor(email=e.actor.email, display_name=e.actor.display_name)
                if e.actor
                else None,
                action=e.action,
                summary=e.summary,
                outcome=e.outcome,
            )
            for e in page
        ],
        next_cursor=_encode(page[-1]) if len(entries) > limit else None,
    )
