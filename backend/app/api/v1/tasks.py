import base64
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import RuntimeDep, SessionDep, WorkspaceContext, require
from app.api.v1.errors import CONFLICT, FORBIDDEN, NOT_FOUND, domain_errors
from app.application.planner import PlannerService
from app.application.tasks import StaleVersion, TaskService
from app.core.permissions import Permission
from app.domain.catalog.capabilities import RISK_LABELS, RiskLevel
from app.domain.catalog.recipes import RECIPES
from app.domain.tasks.state_machine import (
    LABELS,
    Command,
    InvalidTransition,
    TaskStatus,
    allowed_commands,
)
from app.infrastructure.models import Event, Plan, Task

router = APIRouter(tags=["tasks"])

Reader = Annotated[WorkspaceContext, Depends(require(Permission.WORKSPACE_READ))]
Runner = Annotated[WorkspaceContext, Depends(require(Permission.TASK_RUN))]

_TASK = "Tarea no encontrada"


class Ref(BaseModel):
    id: uuid.UUID
    name: str


class EnvironmentRef(Ref):
    kind: str


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: TaskStatus
    status_label: str = Field(description="Texto del diccionario de estados (principios-ux §6)")
    status_reason: str | None = Field(description="Por qué está en este estado, si aplica")
    project: Ref
    environment: EnvironmentRef
    version: int = Field(description="Envíala en cada comando (bloqueo optimista)")
    allowed_commands: list[Command]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, task: Task) -> "TaskResponse":
        state = TaskStatus(task.status)
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=state,
            status_label=LABELS[state],
            status_reason=task.status_reason,
            project=Ref(id=task.project.id, name=task.project.name),
            environment=EnvironmentRef(
                id=task.environment.id, name=task.environment.name, kind=task.environment.kind
            ),
            version=task.version,
            allowed_commands=allowed_commands(state),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


class TaskPage(BaseModel):
    items: list[TaskResponse]
    next_cursor: str | None


class TaskEdit(BaseModel):
    version: int = Field(ge=1)
    text: str | None = Field(default=None, min_length=3, max_length=4000)


class PlanStepResponse(BaseModel):
    position: int
    key: str
    title: str
    capability: str
    risk_level: RiskLevel
    risk_label: str
    depends_on: list[str]
    inputs: dict


class PlanResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    version: int
    recipe_key: str
    recipe_title: str
    recipe_version: str
    params: dict
    assumptions: list[str]
    steps: list[PlanStepResponse]
    model: str
    prompt_version: str
    created_at: datetime

    @classmethod
    def of(cls, plan: Plan) -> "PlanResponse":
        recipe = RECIPES.get(plan.recipe_key)
        return cls(
            id=plan.id,
            task_id=plan.task_id,
            version=plan.version,
            recipe_key=plan.recipe_key,
            recipe_title=recipe.title if recipe else plan.recipe_key,
            recipe_version=plan.recipe_version,
            params=plan.params,
            assumptions=plan.assumptions,
            steps=[
                PlanStepResponse(
                    position=s.position,
                    key=s.key,
                    title=s.title,
                    capability=s.capability,
                    risk_level=RiskLevel(s.risk_level),
                    risk_label=RISK_LABELS[RiskLevel(s.risk_level)],
                    depends_on=s.depends_on,
                    inputs=s.inputs,
                )
                for s in plan.steps
            ],
            model=plan.model,
            prompt_version=plan.prompt_version,
            created_at=plan.created_at,
        )


class TaskCreate(BaseModel):
    text: str = Field(
        min_length=3, max_length=4000, description="Lo que necesitas, en tus palabras"
    )
    project_id: uuid.UUID | None = None
    environment_id: uuid.UUID | None = None


class VersionedCommand(BaseModel):
    version: int = Field(ge=1)


class EventResponse(BaseModel):
    id: int
    type: str
    summary: str = Field(description="Qué pasó, en el lenguaje del diccionario de estados")
    payload: dict
    created_at: datetime

    @classmethod
    def of(cls, event: Event) -> "EventResponse":
        return cls(
            id=event.id,
            type=event.type,
            summary=_describe(event),
            payload=event.payload,
            created_at=event.created_at,
        )


def _describe(event: Event) -> str:
    if event.type == "task.created":
        return "Se creó la tarea"
    if event.type == "task.state_changed":
        source = LABELS[TaskStatus(event.payload["from"])]
        target = LABELS[TaskStatus(event.payload["to"])]
        return f"{source} → {target}"
    return event.type


def _service(ctx: WorkspaceContext, session) -> TaskService:
    return TaskService(session, ctx.scope)


def _encode(task: Task) -> str:
    return base64.urlsafe_b64encode(f"{task.created_at.isoformat()}|{task.id}".encode()).decode()


def _decode(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        created_at, task_id = base64.urlsafe_b64decode(cursor).decode().split("|")
        return datetime.fromisoformat(created_at), uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Cursor inválido") from None


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea en Borrador a partir de lo que pidió el usuario",
    responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT},
)
async def create_task(body: TaskCreate, ctx: Runner, session: SessionDep):
    with domain_errors("Proyecto no encontrado"):
        task = await _service(ctx, session).create(body.text, body.project_id, body.environment_id)
    return TaskResponse.of(task)


@router.get(
    "/tasks",
    response_model=TaskPage,
    summary="Tareas del workspace actual, más recientes primero",
    responses=NOT_FOUND,
)
async def list_tasks(
    ctx: Reader,
    session: SessionDep,
    status_filter: Annotated[list[TaskStatus] | None, Query(alias="status")] = None,
    project_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
):
    tasks = await _service(ctx, session).search(
        statuses=status_filter or [],
        project_id=project_id,
        limit=limit + 1,
        before=_decode(cursor) if cursor else None,
    )
    page = tasks[:limit]
    return TaskPage(
        items=[TaskResponse.of(t) for t in page],
        next_cursor=_encode(page[-1]) if len(tasks) > limit else None,
    )


@router.get(
    "/tasks/{task_id}", response_model=TaskResponse, summary="Detalle de tarea", responses=NOT_FOUND
)
async def get_task(task_id: uuid.UUID, ctx: Reader, session: SessionDep):
    with domain_errors(_TASK):
        return TaskResponse.of(await _service(ctx, session).get(task_id))


@router.get(
    "/tasks/{task_id}/events",
    response_model=list[EventResponse],
    summary="Historial de la tarea (en O4 se sirve también por SSE)",
    responses=NOT_FOUND,
)
async def task_events(task_id: uuid.UUID, ctx: Reader, session: SessionDep):
    with domain_errors(_TASK):
        return [EventResponse.of(e) for e in await _service(ctx, session).events(task_id)]


_COMMAND_CONFLICT = {
    409: {"description": "El estado actual no lo permite o la versión está desactualizada"}
}


@contextmanager
def command_errors() -> Iterator[None]:
    """Errores comunes de los comandos sobre una tarea (404, 409 por estado o por versión)."""
    with domain_errors(_TASK):
        try:
            yield
        except InvalidTransition as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
        except StaleVersion:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "La tarea cambió mientras tanto; recárgala"
            ) from None


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    summary="Cancelar una tarea (desde cualquier estado no terminal)",
    responses={**NOT_FOUND, **FORBIDDEN, **_COMMAND_CONFLICT},
)
async def cancel_task(task_id: uuid.UUID, body: VersionedCommand, ctx: Runner, session: SessionDep):
    with command_errors():
        task = await _service(ctx, session).apply(task_id, Command.CANCEL, body.version)
    return TaskResponse.of(task)


@router.post(
    "/tasks/{task_id}/edit",
    response_model=TaskResponse,
    summary="Volver a Borrador (tras un plan fallido o rechazado), opcionalmente con texto nuevo",
    responses={**NOT_FOUND, **FORBIDDEN, **_COMMAND_CONFLICT},
)
async def edit_task(task_id: uuid.UUID, body: TaskEdit, ctx: Runner, session: SessionDep):
    with command_errors():
        task = await _service(ctx, session).edit(task_id, body.version, body.text)
    return TaskResponse.of(task)


@router.post(
    "/tasks/{task_id}/plan",
    response_model=TaskResponse,
    summary="Pedir un plan: la IA elige una receta del catálogo y AICC la valida. No ejecuta nada.",
    responses={**NOT_FOUND, **FORBIDDEN, **_COMMAND_CONFLICT},
)
async def plan_task(
    task_id: uuid.UUID,
    body: VersionedCommand,
    ctx: Runner,
    session: SessionDep,
    runtime: RuntimeDep,
):
    with command_errors():
        task = await PlannerService(session, ctx.scope, runtime).plan(task_id, body.version)
    return TaskResponse.of(task)


@router.get(
    "/tasks/{task_id}/plan",
    response_model=PlanResponse,
    summary="Último plan propuesto para la tarea",
    responses=NOT_FOUND,
)
async def latest_plan(task_id: uuid.UUID, ctx: Reader, session: SessionDep, runtime: RuntimeDep):
    with domain_errors(_TASK):
        plan = await PlannerService(session, ctx.scope, runtime).latest(task_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La tarea todavía no tiene plan")
    return PlanResponse.of(plan)


@router.get(
    "/plans/{plan_id}",
    response_model=PlanResponse,
    summary="Detalle de un plan",
    responses=NOT_FOUND,
)
async def get_plan(plan_id: uuid.UUID, ctx: Reader, session: SessionDep, runtime: RuntimeDep):
    plan = await PlannerService(session, ctx.scope, runtime).get(plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan no encontrado")
    return PlanResponse.of(plan)
