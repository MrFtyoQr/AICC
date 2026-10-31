"""Casos de uso de tenencia: workspaces, membresías, invitaciones, proyectos y ambientes.

Regla de aislamiento (ADR-010): toda consulta de un recurso de cliente recibe el `workspace_id`
ya resuelto por membresía y filtra por él. Un recurso de otro workspace es indistinguible de uno
que no existe.

Regla de auditoría (HU-13): cada comando de escritura llama a `audit()` antes de confirmar, de modo
que el cambio y su registro se guardan juntos.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.audit import audit
from app.core.permissions import Role
from app.infrastructure.models import (
    AuditLog,
    Environment,
    Invitation,
    Membership,
    Project,
    User,
    Workspace,
)

DEFAULT_PROJECT = "General"
DEFAULT_ENVIRONMENT = "development"

KIND_LABELS = {"development": "desarrollo", "staging": "pruebas", "production": "producción"}

ROLE_LABELS = {
    Role.OWNER: "dueño",
    Role.ADMIN: "administrador",
    Role.OPERATOR: "operador",
    Role.VIEWER: "solo lectura",
}


class NotFound(Exception):
    pass


class NameTaken(Exception):
    pass


class Conflict(Exception):
    """La acción rompería una regla del dominio; el mensaje se muestra tal cual al usuario."""


class NotAllowed(Exception):
    """El rol permite la acción en general, pero no en este caso (p. ej. otorgar `owner`)."""


@dataclass(frozen=True)
class Scope:
    """Quién actúa y sobre qué workspace, ya validado por membresía."""

    user_id: uuid.UUID
    workspace_id: uuid.UUID
    role: str


def new_project(workspace_id: uuid.UUID, name: str, description: str | None = None) -> Project:
    """Proyecto con su ambiente `development`, listo para añadirse a la sesión."""
    project = Project(
        id=uuid.uuid4(), workspace_id=workspace_id, name=name, description=description
    )
    project.environments.append(
        Environment(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            name=DEFAULT_ENVIRONMENT,
            kind="development",
        )
    )
    return project


async def _add_workspace(
    session: AsyncSession, user_id: uuid.UUID, name: str, *, personal: bool
) -> Workspace:
    workspace = Workspace(name=name, is_personal=personal)
    session.add(workspace)
    # Sin relaciones ORM entre estas tablas, el flush fija el orden de los INSERT.
    await session.flush()
    session.add(Membership(workspace_id=workspace.id, user_id=user_id, role=Role.OWNER))
    session.add(new_project(workspace.id, DEFAULT_PROJECT))
    return workspace


async def add_personal_workspace(session: AsyncSession, user: User) -> Workspace:
    """Crea (sin confirmar) el workspace personal del usuario con su proyecto inicial."""
    owner_name = user.display_name or user.email.split("@", 1)[0]
    workspace = await _add_workspace(session, user.id, f"Espacio de {owner_name}", personal=True)
    audit(
        session,
        workspace_id=workspace.id,
        actor_id=user.id,
        action="workspace.create",
        resource_type="workspace",
        resource_id=workspace.id,
        summary="Creó su cuenta y su espacio personal",
    )
    return workspace


async def memberships_of(session: AsyncSession, user_id: uuid.UUID) -> list[Membership]:
    result = await session.scalars(
        select(Membership)
        .join(Workspace)
        .where(Membership.user_id == user_id)
        .order_by(Workspace.is_personal.desc(), Workspace.created_at)
    )
    return list(result)


async def membership(
    session: AsyncSession, user_id: uuid.UUID, workspace_id: uuid.UUID | None
) -> Membership | None:
    """Membresía del usuario en ese workspace; sin id, su workspace personal."""
    query = select(Membership).join(Workspace).where(Membership.user_id == user_id)
    if workspace_id is None:
        query = query.where(Workspace.is_personal.is_(True))
    else:
        query = query.where(Membership.workspace_id == workspace_id)
    return await session.scalar(query)


class _Service:
    def __init__(self, session: AsyncSession, scope: Scope) -> None:
        self.session = session
        self.scope = scope

    def _audit(
        self,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None,
        summary: str,
        **details,
    ) -> None:
        audit(
            self.session,
            workspace_id=self.scope.workspace_id,
            actor_id=self.scope.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            summary=summary,
            details=details,
        )

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise NameTaken from exc


# --- Workspaces ---------------------------------------------------------------


async def create_team_workspace(session: AsyncSession, user_id: uuid.UUID, name: str) -> Workspace:
    """Workspace de equipo; quien lo crea es su dueño."""
    workspace = await _add_workspace(session, user_id, name, personal=False)
    audit(
        session,
        workspace_id=workspace.id,
        actor_id=user_id,
        action="workspace.create",
        resource_type="workspace",
        resource_id=workspace.id,
        summary=f"Creó el workspace «{name}»",
    )
    await session.commit()
    return workspace


class WorkspaceService(_Service):
    async def rename(self, workspace: Workspace, name: str) -> Workspace:
        old = workspace.name
        workspace.name = name
        self._audit(
            "workspace.update",
            "workspace",
            workspace.id,
            f"Renombró el workspace «{old}» a «{name}»",
        )
        await self.session.commit()
        return workspace

    async def delete(self, workspace: Workspace) -> None:
        if workspace.is_personal:
            raise Conflict("El workspace personal no se puede borrar")
        await self.session.delete(workspace)
        await self.session.commit()


# --- Proyectos ----------------------------------------------------------------


class ProjectService(_Service):
    async def list(self) -> list[Project]:
        result = await self.session.scalars(
            select(Project)
            .where(Project.workspace_id == self.scope.workspace_id)
            .order_by(Project.name)
        )
        return list(result)

    async def get(self, project_id: uuid.UUID) -> Project:
        project = await self.session.scalar(
            select(Project).where(
                Project.id == project_id, Project.workspace_id == self.scope.workspace_id
            )
        )
        if project is None:
            raise NotFound
        return project

    async def create(self, name: str, description: str | None) -> Project:
        project = new_project(self.scope.workspace_id, name, description)
        self.session.add(project)
        self._audit("project.create", "project", project.id, f"Creó el proyecto «{name}»")
        await self._commit()
        return project

    async def update(
        self, project_id: uuid.UUID, *, name: str | None, description: str | None
    ) -> Project:
        project = await self.get(project_id)
        changes = {}
        if name is not None and name != project.name:
            changes["name"] = name
            project.name = name
        if description is not None:
            changes["description"] = description
            project.description = description
        self._audit(
            "project.update",
            "project",
            project.id,
            f"Editó el proyecto «{project.name}»",
            **changes,
        )
        await self._commit()
        return project

    async def delete(self, project_id: uuid.UUID) -> None:
        project = await self.get(project_id)
        self._audit("project.delete", "project", project.id, f"Borró el proyecto «{project.name}»")
        await self.session.delete(project)
        await self.session.commit()

    # --- Ambientes (siempre dentro de un proyecto del workspace) ---

    async def add_environment(self, project_id: uuid.UUID, name: str, kind: str) -> Environment:
        project = await self.get(project_id)
        environment = Environment(
            id=uuid.uuid4(),
            workspace_id=self.scope.workspace_id,
            project_id=project.id,
            name=name,
            kind=kind,
        )
        self.session.add(environment)
        self._audit(
            "environment.create",
            "environment",
            environment.id,
            f"Creó el ambiente «{name}» ({KIND_LABELS[kind]}) en «{project.name}»",
        )
        await self._commit()
        return environment

    async def _environment(self, project_id: uuid.UUID, environment_id: uuid.UUID):
        project = await self.get(project_id)
        environment = next((e for e in project.environments if e.id == environment_id), None)
        if environment is None:
            raise NotFound
        return project, environment

    async def rename_environment(
        self, project_id: uuid.UUID, environment_id: uuid.UUID, name: str
    ) -> Environment:
        project, environment = await self._environment(project_id, environment_id)
        old = environment.name
        environment.name = name
        self._audit(
            "environment.update",
            "environment",
            environment.id,
            f"Renombró el ambiente «{old}» a «{name}» en «{project.name}»",
        )
        await self._commit()
        return environment

    async def delete_environment(self, project_id: uuid.UUID, environment_id: uuid.UUID) -> None:
        project, environment = await self._environment(project_id, environment_id)
        if len(project.environments) == 1:
            raise Conflict("Un proyecto necesita al menos un ambiente")
        self._audit(
            "environment.delete",
            "environment",
            environment.id,
            f"Borró el ambiente «{environment.name}» de «{project.name}»",
        )
        project.environments.remove(environment)
        await self.session.commit()


# --- Miembros e invitaciones --------------------------------------------------


class MemberService(_Service):
    async def members(self) -> list[Membership]:
        result = await self.session.scalars(
            select(Membership)
            .join(User)
            .where(Membership.workspace_id == self.scope.workspace_id)
            .order_by(Membership.created_at)
        )
        return list(result)

    async def invitations(self) -> list[Invitation]:
        result = await self.session.scalars(
            select(Invitation)
            .where(
                Invitation.workspace_id == self.scope.workspace_id,
                Invitation.status == "pending",
            )
            .order_by(Invitation.created_at)
        )
        return list(result)

    def _check_can_grant(self, role: str) -> None:
        # Solo un dueño crea otros dueños; un admin gestiona admin, operator y viewer.
        if role == Role.OWNER and self.scope.role != Role.OWNER:
            raise NotAllowed("Solo un dueño puede otorgar el rol de dueño")

    async def invite(self, email: str, role: str) -> Invitation:
        self._check_can_grant(role)
        email = email.strip().lower()
        already = await self.session.scalar(
            select(Membership)
            .join(User)
            .where(Membership.workspace_id == self.scope.workspace_id, User.email == email)
        )
        if already is not None:
            raise Conflict("Esa persona ya es miembro del workspace")
        invitation = Invitation(
            id=uuid.uuid4(),
            workspace_id=self.scope.workspace_id,
            email=email,
            role=role,
            invited_by=self.scope.user_id,
        )
        self.session.add(invitation)
        self._audit(
            "member.invite",
            "invitation",
            invitation.id,
            f"Invitó a {email} como {ROLE_LABELS[Role(role)]}",
            role=role,
        )
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise Conflict("Ya hay una invitación pendiente para ese email") from exc
        return invitation

    async def revoke_invitation(self, invitation_id: uuid.UUID) -> None:
        invitation = await self.session.scalar(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.workspace_id == self.scope.workspace_id,
                Invitation.status == "pending",
            )
        )
        if invitation is None:
            raise NotFound
        invitation.status = "revoked"
        self._audit(
            "member.invite_revoke",
            "invitation",
            invitation.id,
            f"Canceló la invitación de {invitation.email}",
        )
        await self.session.commit()

    async def _member(self, membership_id: uuid.UUID) -> Membership:
        member = await self.session.scalar(
            select(Membership).where(
                Membership.id == membership_id,
                Membership.workspace_id == self.scope.workspace_id,
            )
        )
        if member is None:
            raise NotFound
        return member

    async def _owners(self) -> int:
        return await self.session.scalar(
            select(func.count()).where(
                Membership.workspace_id == self.scope.workspace_id,
                Membership.role == Role.OWNER,
            )
        )

    async def change_role(self, membership_id: uuid.UUID, role: str) -> Membership:
        member = await self._member(membership_id)
        self._check_can_grant(role)
        if member.role == Role.OWNER and self.scope.role != Role.OWNER:
            raise NotAllowed("Solo un dueño puede cambiar el rol de otro dueño")
        if member.role == Role.OWNER and role != Role.OWNER and await self._owners() == 1:
            raise Conflict("El workspace necesita al menos un dueño")
        old = member.role
        member.role = role
        email = await self._email(member.user_id)
        self._audit(
            "member.role_change",
            "membership",
            member.id,
            f"Cambió el rol de {email} de {ROLE_LABELS[Role(old)]} a {ROLE_LABELS[Role(role)]}",
            role=role,
        )
        await self.session.commit()
        return member

    async def remove(self, membership_id: uuid.UUID) -> None:
        member = await self._member(membership_id)
        if member.role == Role.OWNER and self.scope.role != Role.OWNER:
            raise NotAllowed("Solo un dueño puede quitar a otro dueño")
        if member.role == Role.OWNER and await self._owners() == 1:
            raise Conflict("El workspace necesita al menos un dueño")
        email = await self._email(member.user_id)
        self._audit("member.remove", "membership", member.id, f"Quitó a {email} del workspace")
        await self.session.delete(member)
        await self.session.commit()

    async def _email(self, user_id: uuid.UUID) -> str:
        return await self.session.scalar(select(User.email).where(User.id == user_id))


# --- Actividad ----------------------------------------------------------------


async def activity(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    *,
    limit: int,
    before: tuple[datetime, uuid.UUID] | None,
) -> list[AuditLog]:
    """Entradas más recientes primero, paginadas por cursor (created_at, id)."""
    query = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
    if before is not None:
        query = query.where(tuple_(AuditLog.created_at, AuditLog.id) < before)
    result = await session.scalars(
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    )
    return list(result)
