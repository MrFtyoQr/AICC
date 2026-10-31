"""HU-12 (gestionar workspaces, proyectos, ambientes y miembros) y HU-13 (registro de actividad)."""

import json
import uuid

import pytest
from sqlalchemy import select

from app.application.audit import REDACTED, sanitize
from app.infrastructure.models import AuditLog, Invitation, Membership
from tests.tenancy import Account

pytestmark = pytest.mark.integration


def add_member(db, workspace_id: str, user_id: uuid.UUID, role: str) -> str:
    async def go(session):
        member = Membership(workspace_id=uuid.UUID(workspace_id), user_id=user_id, role=role)
        session.add(member)
        await session.commit()
        return str(member.id)

    return db(go)


def members(account: Account, workspace_id: str | None = None) -> dict:
    return account.request("GET", "/api/v1/members", workspace_id).json()


def my_membership(account: Account, owner: Account) -> str:
    return next(m["id"] for m in members(owner)["members"] if m["email"] == account.email)


# --- HU-12 · Workspaces -------------------------------------------------------


def test_create_team_workspace_makes_me_owner_with_general_project(client):
    ana = Account(client, "ana@example.com")

    created = client.post("/api/v1/workspaces", json={"name": "Tienda"}, headers=ana.auth)
    team = created.json()["id"]

    assert created.status_code == 201
    assert created.json() | {"permissions": None} == {
        "id": team,
        "name": "Tienda",
        "is_personal": False,
        "role": "owner",
        "permissions": None,
    }
    assert [p["name"] for p in ana.request("GET", "/api/v1/projects", team).json()] == ["General"]
    assert len(ana.get("/api/v1/workspaces").json()) == 2


def test_rename_and_delete_team_workspace(client):
    ana = Account(client, "ana@example.com")
    team = client.post("/api/v1/workspaces", json={"name": "Tienda"}, headers=ana.auth).json()

    renamed = ana.request("PATCH", "/api/v1/workspaces/current", team["id"], json={"name": "Shop"})
    deleted = ana.request("DELETE", "/api/v1/workspaces/current", team["id"])

    assert renamed.json()["name"] == "Shop"
    assert deleted.status_code == 204
    assert ana.request("GET", "/api/v1/workspaces/current", team["id"]).status_code == 404


def test_personal_workspace_cannot_be_deleted(client):
    ana = Account(client, "ana@example.com")

    response = ana.request("DELETE", "/api/v1/workspaces/current")

    assert response.status_code == 409
    assert response.json()["detail"] == "El workspace personal no se puede borrar"


# --- HU-12 · Ambientes --------------------------------------------------------


def test_environments_lifecycle(client):
    ana = Account(client, "ana@example.com")
    project = ana.first_project()
    base = f"/api/v1/projects/{project['id']}/environments"
    development = project["environments"][0]["id"]

    created = ana.request("POST", base, json={"name": "producción", "kind": "production"})
    renamed = ana.request("PATCH", f"{base}/{created.json()['id']}", json={"name": "prod"})
    duplicate = ana.request("POST", base, json={"name": "prod", "kind": "staging"})
    removed = ana.request("DELETE", f"{base}/{development}")
    last = ana.request("DELETE", f"{base}/{created.json()['id']}")

    assert created.status_code == 201
    assert renamed.json() == {"id": created.json()["id"], "name": "prod", "kind": "production"}
    assert duplicate.status_code == 409
    assert removed.status_code == 204
    assert last.status_code == 409
    assert last.json()["detail"] == "Un proyecto necesita al menos un ambiente"


def test_unknown_environment_kind_is_rejected(client):
    ana = Account(client, "ana@example.com")
    project_id = ana.first_project()["id"]

    response = ana.request(
        "POST", f"/api/v1/projects/{project_id}/environments", json={"name": "x", "kind": "qa"}
    )

    assert response.status_code == 422


# --- HU-12 · Miembros e invitaciones -----------------------------------------


def test_invitation_stays_pending_with_role(client, db):
    ana = Account(client, "ana@example.com")

    created = ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "Bea@Example.com", "role": "operator"}
    )
    again = ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "bea@example.com", "role": "viewer"}
    )

    assert created.status_code == 201
    assert again.status_code == 409
    assert [(i["email"], i["role"]) for i in members(ana)["invitations"]] == [
        ("bea@example.com", "operator")
    ]
    stored = db(lambda s: s.scalar(select(Invitation)))
    assert stored.status == "pending"


def test_revoked_invitation_disappears_and_can_be_reissued(client):
    ana = Account(client, "ana@example.com")
    body = {"email": "bea@example.com", "role": "viewer"}
    invitation = ana.request("POST", "/api/v1/members/invitations", json=body).json()

    revoked = ana.request("DELETE", f"/api/v1/members/invitations/{invitation['id']}")

    assert revoked.status_code == 204
    assert members(ana)["invitations"] == []
    assert ana.request("POST", "/api/v1/members/invitations", json=body).status_code == 201


def test_cannot_invite_existing_member(client):
    ana = Account(client, "ana@example.com")

    response = ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "ana@example.com", "role": "admin"}
    )

    assert response.status_code == 409


def test_members_list_marks_me(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    add_member(db, ana.workspace_id, bea.user_id, "viewer")

    listed = members(ana)["members"]

    assert [(m["email"], m["role"], m["is_you"]) for m in listed] == [
        ("ana@example.com", "owner", True),
        ("bea@example.com", "viewer", False),
    ]


def test_admin_cannot_grant_owner(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    add_member(db, ana.workspace_id, bea.user_id, "admin")

    invite = bea.request(
        "POST",
        "/api/v1/members/invitations",
        ana.workspace_id,
        json={"email": "eve@example.com", "role": "owner"},
    )
    promote = bea.request(
        "PATCH",
        f"/api/v1/members/{my_membership(bea, ana)}",
        ana.workspace_id,
        json={"role": "owner"},
    )

    assert invite.status_code == 403
    assert promote.status_code == 403


def test_last_owner_cannot_be_demoted_or_removed(client):
    ana = Account(client, "ana@example.com")
    me = my_membership(ana, ana)

    demote = ana.request("PATCH", f"/api/v1/members/{me}", json={"role": "admin"})
    remove = ana.request("DELETE", f"/api/v1/members/{me}")

    assert demote.status_code == 409
    assert remove.status_code == 409
    assert demote.json()["detail"] == "El workspace necesita al menos un dueño"


def test_owner_changes_role_and_removes_member(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    membership = add_member(db, ana.workspace_id, bea.user_id, "viewer")

    promoted = ana.request("PATCH", f"/api/v1/members/{membership}", json={"role": "operator"})
    role = bea.get("/api/v1/workspaces/current", workspace_id=ana.workspace_id).json()["role"]
    removed = ana.request("DELETE", f"/api/v1/members/{membership}")

    assert promoted.status_code == 204
    assert role == "operator"
    assert removed.status_code == 204
    assert bea.get("/api/v1/workspaces/current", workspace_id=ana.workspace_id).status_code == 404


# --- HU-13 · Registro de actividad -------------------------------------------


def test_every_write_leaves_an_audit_entry(client, db):
    ana = Account(client, "ana@example.com")
    project = ana.request("POST", "/api/v1/projects", json={"name": "Tienda"}).json()
    ana.request("PATCH", f"/api/v1/projects/{project['id']}", json={"name": "Tienda web"})
    ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "bea@example.com", "role": "viewer"}
    )
    ana.request("DELETE", f"/api/v1/projects/{project['id']}")

    entries = db(
        lambda s: s.scalars(select(AuditLog).order_by(AuditLog.created_at, AuditLog.action))
    )
    actions = sorted(e.action for e in entries)

    assert actions == sorted(
        [
            "workspace.create",
            "project.create",
            "project.update",
            "member.invite",
            "project.delete",
        ]
    )
    assert all(e.actor_id == ana.user_id and e.outcome == "success" for e in entries)


def test_denied_attempts_are_recorded(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    add_member(db, ana.workspace_id, bea.user_id, "viewer")

    bea.request("POST", "/api/v1/projects", ana.workspace_id, json={"name": "Intruso"})

    denied = db(lambda s: s.scalar(select(AuditLog).where(AuditLog.outcome == "denied")))
    assert denied.actor_id == bea.user_id
    assert denied.action == "project.write"
    assert str(denied.workspace_id) == ana.workspace_id


def test_activity_is_paginated_in_plain_language(client):
    ana = Account(client, "ana@example.com")
    for name in ("Uno", "Dos", "Tres"):
        ana.request("POST", "/api/v1/projects", json={"name": name})

    first = ana.request("GET", "/api/v1/activity?limit=2").json()
    second = ana.request("GET", f"/api/v1/activity?limit=2&cursor={first['next_cursor']}").json()

    summaries = [i["summary"] for i in first["items"] + second["items"]]
    assert len(first["items"]) == 2
    assert second["next_cursor"] is None
    assert sorted(summaries) == sorted(
        [
            "Creó el proyecto «Uno»",
            "Creó el proyecto «Dos»",
            "Creó el proyecto «Tres»",
            "Creó su cuenta y su espacio personal",
        ]
    )
    assert first["items"][0]["actor"] == {"email": "ana@example.com", "display_name": None}


def test_invalid_cursor_is_rejected(client):
    ana = Account(client, "ana@example.com")

    assert ana.request("GET", "/api/v1/activity?cursor=basura").status_code == 422


def test_audit_never_stores_secrets(client, db):
    ana = Account(client, "ana@example.com")
    ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "bea@example.com", "role": "viewer"}
    )

    stored = json.dumps([e.details for e in db(lambda s: s.scalars(select(AuditLog)))])

    assert "una-clave-larga-segura" not in stored
    assert "Bearer" not in stored


def test_sanitize_redacts_sensitive_keys_recursively():
    details = {
        "name": "ok",
        "api_key": "sk-123",
        "nested": {"password": "x", "items": [{"refresh_token": "y", "kind": "z"}]},
        "Authorization": "Bearer abc",
    }

    assert sanitize(details) == {
        "name": "ok",
        "api_key": REDACTED,
        "nested": {"password": REDACTED, "items": [{"refresh_token": REDACTED, "kind": "z"}]},
        "Authorization": REDACTED,
    }
