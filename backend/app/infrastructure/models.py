"""Modelos SQLAlchemy. Todo modelo nuevo se define (o importa) aquí para que Alembic lo vea."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.permissions import Role
from app.domain.catalog.capabilities import RiskLevel
from app.domain.tasks.state_machine import TaskStatus
from app.infrastructure.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Se guarda normalizado en minúsculas; la unicidad es exacta sobre ese valor.
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class RefreshToken(Base):
    """Refresh token rotatorio. Todos los tokens de una sesión comparten `family_id`."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# --- Tenencia (F1) ----------------------------------------------------------
# Toda tabla que pertenece a un cliente lleva `workspace_id`, aunque pueda deducirse por otra
# relación: así cada consulta filtra por tenant de forma directa y verificable (ADR-010).

ROLES = tuple(role.value for role in Role)
ENVIRONMENT_KINDS = ("development", "staging", "production")


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_personal: Mapped[bool] = mapped_column(default=False, nullable=False)


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id"),
        CheckConstraint(f"role IN {ROLES}", name="role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)

    workspace: Mapped[Workspace] = relationship(lazy="joined")
    user: Mapped[User] = relationship(lazy="joined")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("workspace_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    environments: Mapped[list["Environment"]] = relationship(
        lazy="selectin", order_by="Environment.created_at", cascade="all, delete-orphan"
    )


class Environment(TimestampMixin, Base):
    __tablename__ = "environments"
    __table_args__ = (
        UniqueConstraint("project_id", "name"),
        CheckConstraint(f"kind IN {ENVIRONMENT_KINDS}", name="kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)


INVITATION_STATUSES = ("pending", "accepted", "revoked")


class Invitation(TimestampMixin, Base):
    """Invitación por email a un workspace. En F1 solo se registra; el envío llega con O5."""

    __tablename__ = "invitations"
    __table_args__ = (
        CheckConstraint(f"role IN {ROLES}", name="role"),
        CheckConstraint(f"status IN {INVITATION_STATUSES}", name="status"),
        Index(
            "uq_invitations_pending_email",
            "workspace_id",
            "email",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AuditLog(Base):
    """Registro inmutable de quién hizo qué (HU-13). Sin secretos: ver app.application.audit."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint("outcome IN ('success', 'denied')", name="outcome"),
        Index("ix_audit_logs_workspace_created", "workspace_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[uuid.UUID | None]
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    summary: Mapped[str] = mapped_column(String(300), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    actor: Mapped[User | None] = relationship(lazy="joined")


# --- Orquestación (O1) --------------------------------------------------------

TASK_STATUSES = tuple(status.value for status in TaskStatus)
RISK_LEVELS = tuple(level.value for level in RiskLevel)


class Task(TimestampMixin, Base):
    """Lo que el usuario pidió, con su ciclo de vida (orquestacion.md §3)."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(f"status IN {TASK_STATUSES}", name="status"),
        Index("ix_tasks_workspace_status_created", "workspace_id", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("environments.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    # Por qué está en su estado actual, en lenguaje claro (p. ej. por qué no se pudo planificar).
    status_reason: Mapped[str | None] = mapped_column(String(300))
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    # Bloqueo optimista: SQLAlchemy incrementa `version` en cada UPDATE y falla si cambió.
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012 - API declarativa de SQLAlchemy

    project: Mapped[Project] = relationship(lazy="joined")
    environment: Mapped[Environment] = relationship(lazy="joined")


class Event(Base):
    """Hecho inmutable del sistema (append-only: un trigger impide modificarlo)."""

    __tablename__ = "events"
    __table_args__ = (Index("ix_events_task_id_id", "task_id", "id"),)

    # Secuencial: ordena y permite reanudar el flujo SSE con Last-Event-ID (O4).
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Plan(Base):
    """Receta del catálogo instanciada para una tarea (ADR-007). Inmutable: cambio = versión."""

    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("task_id", "version"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(nullable=False)
    recipe_key: Mapped[str] = mapped_column(String(64), nullable=False)
    recipe_version: Mapped[str] = mapped_column(String(16), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSONB, nullable=False)
    # Trazabilidad del motor: qué prompt y qué modelo lo propusieron, y cuántos tokens costó.
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    input_tokens: Mapped[int] = mapped_column(nullable=False)
    output_tokens: Mapped[int] = mapped_column(nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    steps: Mapped[list["PlanStep"]] = relationship(
        lazy="selectin", order_by="PlanStep.position", cascade="all, delete-orphan"
    )


class PlanStep(Base):
    __tablename__ = "plan_steps"
    __table_args__ = (
        UniqueConstraint("plan_id", "key"),
        CheckConstraint(f"risk_level IN {RISK_LEVELS}", name="risk_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    capability_version: Mapped[str] = mapped_column(String(16), nullable=False)
    inputs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    depends_on: Mapped[list] = mapped_column(JSONB, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
