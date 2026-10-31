"""HU-15 (pedir algo con mis palabras), HU-16 (estados confiables) y HU-17 (filtrar)."""

import asyncio
import uuid

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from app.application.tasks import StaleVersion, TaskService, title_from
from app.application.workspaces import Scope
from app.domain.tasks.state_machine import Command, TaskStatus
from app.infrastructure.models import AuditLog, Event, Membership, Task
from tests.tenancy import Account

pytestmark = pytest.mark.integration


def create(account: Account, text_: str = "Responde a los leads de hoy", **extra):
    return account.request("POST", "/api/v1/tasks", json={"text": text_, **extra})


def force_status(db, task_id: str, status: TaskStatus) -> None:
    """Coloca una tarea en un estado que aún no tiene comando público (O2–O4)."""

    async def go(session):
        await session.execute(
            update(Task).where(Task.id == uuid.UUID(task_id)).values(status=status)
        )
        await session.commit()

    db(go)


# --- HU-15 · Crear ------------------------------------------------------------


def test_create_task_in_draft_with_default_context(client):
    ana = Account(client, "ana@example.com")
    project = ana.first_project()

    response = create(ana, "Quiero capturar leads de mi formulario\ny avisarme por correo")

    body = response.json()
    assert response.status_code == 201
    assert body["status"] == "DRAFT"
    assert body["status_label"] == "Borrador"
    assert body["title"] == "Quiero capturar leads de mi formulario"
    assert body["description"].endswith("avisarme por correo")
    assert body["project"] == {"id": project["id"], "name": "General"}
    assert body["environment"]["kind"] == "development"
    assert body["version"] == 1
    assert "cancel" in body["allowed_commands"]


def test_create_task_in_chosen_project_and_environment(client):
    ana = Account(client, "ana@example.com")
    project = ana.request("POST", "/api/v1/projects", json={"name": "Tienda"}).json()
    prod = ana.request(
        "POST",
        f"/api/v1/projects/{project['id']}/environments",
        json={"name": "prod", "kind": "production"},
    ).json()

    body = create(ana, project_id=project["id"], environment_id=prod["id"]).json()

    assert body["project"]["name"] == "Tienda"
    assert body["environment"] == {"id": prod["id"], "name": "prod", "kind": "production"}


def test_environment_from_another_project_is_rejected(client):
    ana = Account(client, "ana@example.com")
    general = ana.first_project()
    other = ana.request("POST", "/api/v1/projects", json={"name": "Otro"}).json()

    response = create(ana, project_id=general["id"], environment_id=other["environments"][0]["id"])

    assert response.status_code == 409


@pytest.mark.parametrize("text_", ["", "  ", "x" * 4001])
def test_task_text_is_validated(client, text_):
    ana = Account(client, "ana@example.com")

    assert create(ana, text_).status_code == 422


def test_long_first_line_is_truncated_for_the_title():
    assert title_from("a" * 200) == "a" * 79 + "…"


def test_viewer_cannot_create_tasks(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")

    async def add(session):
        session.add(
            Membership(workspace_id=uuid.UUID(ana.workspace_id), user_id=bea.user_id, role="viewer")
        )
        await session.commit()

    db(add)

    response = bea.request("POST", "/api/v1/tasks", ana.workspace_id, json={"text": "Hola hola"})

    assert response.status_code == 403
    assert bea.request("GET", "/api/v1/tasks", ana.workspace_id).status_code == 200


# --- HU-15 · Ver y cancelar ---------------------------------------------------


def test_cancel_task_records_history(client):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()

    cancelled = ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 1})
    detail = ana.request("GET", f"/api/v1/tasks/{task['id']}").json()
    events = ana.request("GET", f"/api/v1/tasks/{task['id']}/events").json()

    assert cancelled.status_code == 200
    assert detail["status"] == "CANCELLED"
    assert detail["status_label"] == "Cancelada"
    assert detail["version"] == 2
    assert detail["allowed_commands"] == []
    assert [e["type"] for e in events] == ["task.created", "task.state_changed"]
    assert events[1]["payload"] == {"command": "cancel", "from": "DRAFT", "to": "CANCELLED"}
    assert [e["summary"] for e in events] == ["Se creó la tarea", "Borrador → Cancelada"]


# --- HU-16 · Transiciones, evento + auditoría, concurrencia -------------------


def test_illegal_transition_is_rejected(client):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()
    ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 1})

    again = ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 2})

    assert again.status_code == 409
    assert "CANCELLED" in again.json()["detail"]


@pytest.mark.parametrize("terminal", [TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.REJECTED])
def test_terminal_tasks_cannot_be_cancelled(client, db, terminal):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()
    force_status(db, task["id"], terminal)

    response = ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 1})

    assert response.status_code == 409


def test_transition_writes_event_and_audit_in_the_same_transaction(client, db):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()

    ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 1})

    async def rows(session):
        events = await session.scalars(select(Event).where(Event.type == "task.state_changed"))
        audits = await session.scalars(select(AuditLog).where(AuditLog.action == "task.cancel"))
        return list(events), list(audits)

    events, audits = db(rows)
    assert len(events) == 1
    assert len(audits) == 1
    assert audits[0].summary == "Canceló «Responde a los leads de hoy»"
    # Mismo commit = misma transacción = mismo now() de PostgreSQL.
    assert events[0].created_at == audits[0].created_at


def test_failed_transition_leaves_no_trace(client, db):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()
    force_status(db, task["id"], TaskStatus.DONE)

    ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 1})

    count = db(
        lambda s: s.scalar(text("SELECT count(*) FROM events WHERE type = 'task.state_changed'"))
    )
    assert count == 0


def test_stale_version_gets_409(client):
    ana = Account(client, "ana@example.com")
    task = create(ana).json()

    response = ana.request("POST", f"/api/v1/tasks/{task['id']}/cancel", json={"version": 7})

    assert response.status_code == 409
    assert response.json()["detail"] == "La tarea cambió mientras tanto; recárgala"


def test_two_simultaneous_modifications_second_gets_conflict(client, db, migrated_db):
    """Dos sesiones leen la versión 1; solo la primera en confirmar gana."""
    ana = Account(client, "ana@example.com")
    task_id = uuid.UUID(create(ana).json()["id"])
    scope = Scope(user_id=ana.user_id, workspace_id=uuid.UUID(ana.workspace_id), role="owner")

    async def race():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.pool import NullPool

        engine = create_async_engine(migrated_db, poolclass=NullPool)
        try:
            async with (
                AsyncSession(engine, expire_on_commit=False) as first,
                AsyncSession(engine, expire_on_commit=False) as second,
            ):
                a, b = TaskService(first, scope), TaskService(second, scope)
                await a.get(task_id)
                await b.get(task_id)
                await a.apply(task_id, Command.CANCEL, 1)
                with pytest.raises(StaleVersion):
                    await b.apply(task_id, Command.CANCEL, 1)
        finally:
            await engine.dispose()

    asyncio.run(race())
    assert db(lambda s: s.scalar(select(Task.version).where(Task.id == task_id))) == 2


def test_events_are_append_only(client, db):
    ana = Account(client, "ana@example.com")
    create(ana)

    async def tamper(session):
        await session.execute(text("UPDATE events SET type = 'hackeado'"))

    with pytest.raises(DBAPIError, match="append-only"):
        db(tamper)


# --- HU-17 · Listar y filtrar -------------------------------------------------


def test_list_filters_by_status_newest_first(client, db):
    ana = Account(client, "ana@example.com")
    first = create(ana, "Primera tarea").json()
    create(ana, "Segunda tarea")
    third = create(ana, "Tercera tarea").json()
    ana.request("POST", f"/api/v1/tasks/{first['id']}/cancel", json={"version": 1})
    force_status(db, third["id"], TaskStatus.RUNNING)

    everything = ana.request("GET", "/api/v1/tasks").json()["items"]
    drafts = ana.request("GET", "/api/v1/tasks?status=DRAFT").json()["items"]
    attention = ana.request("GET", "/api/v1/tasks?status=RUNNING&status=CANCELLED").json()

    assert [t["title"] for t in everything] == ["Tercera tarea", "Segunda tarea", "Primera tarea"]
    assert [t["title"] for t in drafts] == ["Segunda tarea"]
    assert {t["status"] for t in attention["items"]} == {"RUNNING", "CANCELLED"}


def test_list_is_paginated(client):
    ana = Account(client, "ana@example.com")
    for i in range(3):
        create(ana, f"Tarea {i}")

    first = ana.request("GET", "/api/v1/tasks?limit=2").json()
    second = ana.request("GET", f"/api/v1/tasks?limit=2&cursor={first['next_cursor']}").json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert second["next_cursor"] is None


def test_unknown_status_filter_is_rejected(client):
    ana = Account(client, "ana@example.com")

    assert ana.request("GET", "/api/v1/tasks?status=ALGO").status_code == 422
