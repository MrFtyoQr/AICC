"""Casos de uso de tareas (O1): crear, listar, consultar historial y aplicar comandos.

Toda transición pasa por `domain.tasks.state_machine` y escribe un `event` y un `audit_log` en la
misma transacción que el cambio de estado (HU-16).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.application.audit import audit, sanitize
from app.application.workspaces import Conflict, NotFound, Scope
from app.domain.tasks.state_machine import Command, TaskStatus, next_status
from app.infrastructure.models import Environment, Event, Project, Task

TITLE_MAX = 80


class StaleVersion(Exception):
    """Otra persona (u otro proceso) modificó la tarea desde que la leíste."""


def title_from(text: str) -> str:
    first_line = text.strip().splitlines()[0].strip()
    return first_line if len(first_line) <= TITLE_MAX else first_line[: TITLE_MAX - 1] + "…"


class TaskService:
    def __init__(self, session: AsyncSession, scope: Scope) -> None:
        self.session = session
        self.scope = scope

    # --- Lectura ---

    async def get(self, task_id: uuid.UUID) -> Task:
        task = await self.session.scalar(
            select(Task).where(Task.id == task_id, Task.workspace_id == self.scope.workspace_id)
        )
        if task is None:
            raise NotFound
        return task

    async def search(
        self,
        *,
        statuses: list[TaskStatus],
        project_id: uuid.UUID | None,
        limit: int,
        before: tuple[datetime, uuid.UUID] | None,
    ) -> list[Task]:
        query = select(Task).where(Task.workspace_id == self.scope.workspace_id)
        if statuses:
            query = query.where(Task.status.in_(statuses))
        if project_id is not None:
            query = query.where(Task.project_id == project_id)
        if before is not None:
            query = query.where(tuple_(Task.created_at, Task.id) < before)
        result = await self.session.scalars(
            query.order_by(Task.created_at.desc(), Task.id.desc()).limit(limit)
        )
        return list(result)

    async def events(self, task_id: uuid.UUID) -> list[Event]:
        task = await self.get(task_id)
        result = await self.session.scalars(
            select(Event).where(Event.task_id == task.id).order_by(Event.id)
        )
        return list(result)

    # --- Escritura ---

    async def create(
        self, text: str, project_id: uuid.UUID | None, environment_id: uuid.UUID | None
    ) -> Task:
        project, environment = await self._target(project_id, environment_id)
        task = Task(
            id=uuid.uuid4(),
            workspace_id=self.scope.workspace_id,
            project=project,
            environment=environment,
            title=title_from(text),
            description=text.strip(),
            status=TaskStatus.DRAFT,
            created_by=self.scope.user_id,
        )
        self.session.add(task)
        # Sin relación ORM con Event, el flush garantiza que la tarea se inserte primero.
        await self.session.flush()
        self._event(task, "task.created", status=TaskStatus.DRAFT)
        self._audit(task, "task.create", f"Creó la tarea «{task.title}»")
        await self.session.commit()
        return task

    async def apply(
        self,
        task_id: uuid.UUID,
        command: Command,
        expected_version: int,
        *,
        reason: str | None = None,
        **payload: Any,
    ) -> Task:
        """Aplica un comando si la versión coincide; lanza InvalidTransition o StaleVersion.

        `reason` explica el nuevo estado al usuario (p. ej. por qué falló el plan) y queda también
        en el evento. Lo añadido a la sesión antes de llamar se confirma en la misma transacción.
        """
        task = await self.get(task_id)
        if task.version != expected_version:
            raise StaleVersion
        source = TaskStatus(task.status)
        target = next_status(source, command)
        task.status = target
        task.status_reason = reason
        if reason is not None:
            payload["reason"] = reason
        self._event(
            task, "task.state_changed", command=command, **{"from": source, "to": target}, **payload
        )
        self._audit(task, f"task.{command}", _SUMMARIES[command].format(title=task.title))
        try:
            await self.session.commit()
        except StaleDataError as exc:
            # Dos peticiones leyeron la misma versión: la segunda en confirmar pierde.
            await self.session.rollback()
            raise StaleVersion from exc
        return task

    async def edit(self, task_id: uuid.UUID, expected_version: int, text: str | None) -> Task:
        """Vuelve a Borrador tras un plan fallido o rechazado, opcionalmente con texto nuevo."""
        if text is not None:
            task = await self.get(task_id)
            if task.version == expected_version:
                task.title = title_from(text)
                task.description = text.strip()
        # Sin autoflush: el texto y el cambio de estado salen en un solo UPDATE (una versión).
        with self.session.no_autoflush:
            return await self.apply(task_id, Command.EDIT, expected_version)

    # --- Internos ---

    async def _target(
        self, project_id: uuid.UUID | None, environment_id: uuid.UUID | None
    ) -> tuple[Project, Environment]:
        """Proyecto y ambiente del workspace; sin ids, el primer proyecto y su primer ambiente."""
        query = select(Project).where(Project.workspace_id == self.scope.workspace_id)
        if project_id is not None:
            query = query.where(Project.id == project_id)
        project = await self.session.scalar(query.order_by(Project.created_at).limit(1))
        if project is None:
            raise NotFound
        if environment_id is None:
            environment = project.environments[0] if project.environments else None
        else:
            environment = next((e for e in project.environments if e.id == environment_id), None)
        if environment is None:
            raise Conflict("Ese ambiente no pertenece al proyecto elegido")
        return project, environment

    def _event(self, task: Task, type_: str, **payload: Any) -> None:
        self.session.add(
            Event(
                workspace_id=task.workspace_id,
                task_id=task.id,
                type=type_,
                payload=sanitize(payload),
                actor_id=self.scope.user_id,
            )
        )

    def _audit(self, task: Task, action: str, summary: str) -> None:
        audit(
            self.session,
            workspace_id=task.workspace_id,
            actor_id=self.scope.user_id,
            action=action,
            resource_type="task",
            resource_id=task.id,
            summary=summary,
        )


_SUMMARIES = {
    Command.PLAN: "Pidió un plan para «{title}»",
    Command.PLAN_READY: "Se preparó el plan de «{title}»",
    Command.PLAN_FAILED: "No se pudo armar el plan de «{title}»",
    Command.POLICY_REJECT: "Las reglas no permiten «{title}»",
    Command.APPROVE: "Aprobó «{title}»",
    Command.REJECT: "Rechazó «{title}»",
    Command.REQUEST_CHANGES: "Pidió cambios en «{title}»",
    Command.EDIT: "Editó «{title}»",
    Command.ENQUEUE: "Puso en marcha «{title}»",
    Command.PAUSE: "Se pausó «{title}»",
    Command.RESUME: "Se reanudó «{title}»",
    Command.SUCCEED: "Terminó «{title}»",
    Command.FAIL: "Falló «{title}»",
    Command.CANCEL: "Canceló «{title}»",
}
