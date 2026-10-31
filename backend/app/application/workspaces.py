"""Casos de uso de tenencia: workspace personal, membresías, proyectos y ambientes.

Regla de aislamiento (ADR-010): toda consulta de un recurso de cliente recibe el `workspace_id`
ya resuelto por membresía y filtra por él. Un recurso de otro workspace es indistinguible de uno
que no existe.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Role
from app.infrastructure.models import Environment, Membership, Project, User, Workspace

DEFAULT_PROJECT = "General"
DEFAULT_ENVIRONMENT = "development"


class NotFound(Exception):
    pass


class NameTaken(Exception):
    pass


def new_project(workspace_id: uuid.UUID, name: str, description: str | None = None) -> Project:
    """Proyecto con su ambiente `development`, listo para añadirse a la sesión."""
    project = Project(workspace_id=workspace_id, name=name, description=description)
    project.environments.append(
        Environment(workspace_id=workspace_id, name=DEFAULT_ENVIRONMENT, kind="development")
    )
    return project


async def add_personal_workspace(session: AsyncSession, user: User) -> Workspace:
    """Crea (sin confirmar) el workspace personal del usuario con su proyecto inicial."""
    owner_name = user.display_name or user.email.split("@", 1)[0]
    workspace = Workspace(name=f"Espacio de {owner_name}", is_personal=True)
    session.add(workspace)
    # Sin relaciones ORM entre estas tablas, el flush fija el orden de los INSERT.
    await session.flush()
    session.add(Membership(workspace_id=workspace.id, user_id=user.id, role=Role.OWNER))
    session.add(new_project(workspace.id, DEFAULT_PROJECT))
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


class ProjectService:
    def __init__(self, session: AsyncSession, workspace_id: uuid.UUID) -> None:
        self.session = session
        self.workspace_id = workspace_id

    async def list(self) -> list[Project]:
        result = await self.session.scalars(
            select(Project).where(Project.workspace_id == self.workspace_id).order_by(Project.name)
        )
        return list(result)

    async def get(self, project_id: uuid.UUID) -> Project:
        project = await self.session.scalar(
            select(Project).where(
                Project.id == project_id, Project.workspace_id == self.workspace_id
            )
        )
        if project is None:
            raise NotFound
        return project

    async def create(self, name: str, description: str | None) -> Project:
        project = new_project(self.workspace_id, name, description)
        self.session.add(project)
        await self._commit()
        return project

    async def update(
        self, project_id: uuid.UUID, *, name: str | None, description: str | None
    ) -> Project:
        project = await self.get(project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        await self._commit()
        return project

    async def delete(self, project_id: uuid.UUID) -> None:
        await self.session.delete(await self.get(project_id))
        await self.session.commit()

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise NameTaken from exc
