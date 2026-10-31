import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import audit
from app.application.workspaces import Scope, membership
from app.core.config import Settings
from app.core.permissions import Permission, can
from app.core.security import InvalidTokenError, decode_access_token
from app.infrastructure.database import get_session
from app.infrastructure.models import User, Workspace

_bearer = HTTPBearer(auto_error=False)

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_settings_dep(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


async def get_current_user(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        user_id = decode_access_token(
            credentials.credentials, secret=settings.jwt_secret, issuer=settings.jwt_issuer
        )
    except InvalidTokenError:
        raise unauthorized from None
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass(frozen=True)
class WorkspaceContext:
    user: User
    workspace: Workspace
    role: str

    @property
    def scope(self) -> Scope:
        return Scope(user_id=self.user.id, workspace_id=self.workspace.id, role=self.role)


async def get_current_workspace(
    user: CurrentUser,
    session: SessionDep,
    workspace_id: Annotated[
        uuid.UUID | None,
        Header(
            alias="X-Workspace-Id",
            description="Workspace sobre el que se actúa; si falta, el workspace personal.",
        ),
    ] = None,
) -> WorkspaceContext:
    """Resuelve el workspace por membresía. Uno ajeno responde 404, igual que uno inexistente."""
    found = await membership(session, user.id, workspace_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace no encontrado")
    return WorkspaceContext(user=user, workspace=found.workspace, role=found.role)


CurrentWorkspace = Annotated[WorkspaceContext, Depends(get_current_workspace)]


def require(permission: Permission) -> Callable[..., WorkspaceContext]:
    """Dependencia que exige un permiso de la matriz en el workspace actual (403 si falta).

    Las denegaciones también quedan en el registro de actividad (HU-13).
    """

    async def check(
        ctx: CurrentWorkspace, session: SessionDep, request: Request
    ) -> WorkspaceContext:
        if not can(ctx.role, permission):
            audit(
                session,
                workspace_id=ctx.workspace.id,
                actor_id=ctx.user.id,
                action=permission.value,
                resource_type=permission.value.split(".", 1)[0],
                resource_id=None,
                outcome="denied",
                summary=f"Intento sin permiso: {request.method} {request.url.path}",
            )
            await session.commit()
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Tu rol no permite esta acción")
        return ctx

    return check
