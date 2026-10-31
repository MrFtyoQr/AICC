"""Máquina de estados de Task (orquestacion.md §3, HU-16).

Única fuente de verdad de las transiciones. El cliente nunca fija un estado: invoca un comando y
este módulo decide el estado siguiente o lanza `InvalidTransition`.
"""

from enum import StrEnum


class TaskStatus(StrEnum):
    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    PLANNING_FAILED = "PLANNING_FAILED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    REJECTED_BY_POLICY = "REJECTED_BY_POLICY"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Command(StrEnum):
    PLAN = "plan"
    PLAN_READY = "plan_ready"
    PLAN_FAILED = "plan_failed"
    POLICY_REJECT = "policy_reject"
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    EDIT = "edit"
    ENQUEUE = "enqueue"
    PAUSE = "pause"
    RESUME = "resume"
    SUCCEED = "succeed"
    FAIL = "fail"
    CANCEL = "cancel"


S, C = TaskStatus, Command

TERMINAL = frozenset({S.DONE, S.FAILED, S.CANCELLED, S.REJECTED})

TRANSITIONS: dict[tuple[TaskStatus, Command], TaskStatus] = {
    (S.DRAFT, C.PLAN): S.PLANNING,
    (S.PLANNING, C.PLAN_READY): S.AWAITING_APPROVAL,
    (S.PLANNING, C.PLAN_FAILED): S.PLANNING_FAILED,
    (S.PLANNING, C.POLICY_REJECT): S.REJECTED_BY_POLICY,
    (S.PLANNING_FAILED, C.EDIT): S.DRAFT,
    (S.REJECTED_BY_POLICY, C.EDIT): S.DRAFT,
    (S.AWAITING_APPROVAL, C.APPROVE): S.APPROVED,
    (S.AWAITING_APPROVAL, C.REJECT): S.REJECTED,
    (S.AWAITING_APPROVAL, C.REQUEST_CHANGES): S.PLANNING,
    (S.APPROVED, C.ENQUEUE): S.RUNNING,
    (S.RUNNING, C.PAUSE): S.PAUSED,
    (S.PAUSED, C.RESUME): S.RUNNING,
    (S.RUNNING, C.SUCCEED): S.DONE,
    (S.RUNNING, C.FAIL): S.FAILED,
    # Cancelar es posible desde cualquier estado no terminal.
    **{(status, C.CANCEL): S.CANCELLED for status in S if status not in TERMINAL},
}

# Texto al usuario: docs/ux/principios-ux.md §6. Una prueba verifica que coinciden.
LABELS: dict[TaskStatus, str] = {
    S.DRAFT: "Borrador",
    S.PLANNING: "Preparando un plan…",
    S.PLANNING_FAILED: "No pude armar un plan",
    S.AWAITING_APPROVAL: "Esperando tu aprobación",
    S.REJECTED_BY_POLICY: "No permitido por tus reglas",
    S.REJECTED: "Rechazada",
    S.APPROVED: "Aprobada, en cola",
    S.RUNNING: "En marcha",
    S.PAUSED: "En pausa: necesita algo de ti",
    S.DONE: "Lista",
    S.FAILED: "Falló",
    S.CANCELLED: "Cancelada",
}


class InvalidTransition(Exception):
    def __init__(self, status: TaskStatus, command: Command) -> None:
        super().__init__(f"No se puede '{command}' una tarea en estado {status}")
        self.status = status
        self.command = command


def next_status(status: TaskStatus, command: Command) -> TaskStatus:
    try:
        return TRANSITIONS[(status, command)]
    except KeyError:
        raise InvalidTransition(status, command) from None


def allowed_commands(status: TaskStatus) -> list[Command]:
    """Comandos válidos desde un estado; la app los usa para mostrar solo lo posible."""
    return [command for (source, command) in TRANSITIONS if source == status]
