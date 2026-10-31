import re
import uuid

import pytest
from sqlalchemy import select

from app.core.config import REPO_ROOT
from app.core.permissions import MATRIX, Permission, Role, can
from app.infrastructure.models import Membership
from tests.tenancy import Account

PERMISSIONS_DOC = REPO_ROOT / "docs" / "architecture" / "permisos.md"


def add_member(db, workspace_id: str, user_id: uuid.UUID, role: str) -> None:
    async def go(session):
        session.add(Membership(workspace_id=uuid.UUID(workspace_id), user_id=user_id, role=role))
        await session.commit()

    db(go)


# --- HU-09: workspace listo al registrarse ----------------------------------


@pytest.mark.integration
def test_register_creates_personal_workspace_project_and_environment(client):
    ana = Account(client, "ana@example.com")

    workspaces = ana.get("/api/v1/workspaces").json()
    projects = ana.request("GET", "/api/v1/projects").json()

    assert len(workspaces) == 1
    assert workspaces[0]["is_personal"] is True
    assert workspaces[0]["role"] == "owner"
    assert workspaces[0]["name"] == "Espacio de ana"
    assert [p["name"] for p in projects] == ["General"]
    assert [(e["name"], e["kind"]) for e in projects[0]["environments"]] == [
        ("development", "development")
    ]


@pytest.mark.integration
def test_missing_header_uses_personal_workspace(client):
    ana = Account(client, "ana@example.com")

    response = client.get("/api/v1/projects", headers=ana.auth)

    assert response.status_code == 200
    assert response.json()[0]["name"] == "General"


@pytest.mark.integration
def test_malformed_workspace_header_is_rejected(client):
    ana = Account(client, "ana@example.com")

    response = client.get("/api/v1/projects", headers={**ana.auth, "X-Workspace-Id": "abc"})

    assert response.status_code == 422


@pytest.mark.integration
def test_project_crud_in_own_workspace(client):
    ana = Account(client, "ana@example.com")

    created = ana.request("POST", "/api/v1/projects", json={"name": "Tienda"})
    project_id = created.json()["id"]
    renamed = ana.request("PATCH", f"/api/v1/projects/{project_id}", json={"name": "Tienda web"})
    duplicate = ana.request("POST", "/api/v1/projects", json={"name": "General"})
    deleted = ana.request("DELETE", f"/api/v1/projects/{project_id}")

    assert created.status_code == 201
    assert created.json()["environments"][0]["kind"] == "development"
    assert renamed.json()["name"] == "Tienda web"
    assert duplicate.status_code == 409
    assert deleted.status_code == 204
    assert ana.request("GET", f"/api/v1/projects/{project_id}").status_code == 404


# --- HU-11: roles y matriz de permisos --------------------------------------


def documented_matrix() -> dict[Role, set[Permission]]:
    text = PERMISSIONS_DOC.read_text(encoding="utf-8")
    table = text.split("<!-- matriz:inicio -->")[1].split("<!-- matriz:fin -->")[0]
    rows = [line for line in table.strip().splitlines() if line.startswith("|")]
    roles = [Role(cell.strip()) for cell in rows[0].strip("|").split("|")[1:]]
    matrix: dict[Role, set[Permission]] = {role: set() for role in roles}
    for row in rows[2:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        for role, mark in zip(roles, cells[1:], strict=True):
            if mark == "✅":
                matrix[role].add(Permission(cells[0]))
    return matrix


def test_matrix_matches_documentation():
    assert documented_matrix() == {role: set(perms) for role, perms in MATRIX.items()}


def test_every_permission_is_documented():
    documented = re.findall(r"^\| ([a-z]+\.[a-z]+) \|", PERMISSIONS_DOC.read_text("utf-8"), re.M)
    assert sorted(documented) == sorted(p.value for p in Permission)


def test_unknown_role_has_no_permissions():
    assert not can("superuser", Permission.WORKSPACE_READ)


WRITE_ACTIONS = [
    ("POST", "/api/v1/projects", {"name": "Nuevo"}),
    ("PATCH", "/api/v1/projects/{id}", {"name": "Otro"}),
    ("DELETE", "/api/v1/projects/{id}", None),
]


@pytest.mark.integration
@pytest.mark.parametrize("role", list(Role))
@pytest.mark.parametrize(("method", "path", "body"), WRITE_ACTIONS)
def test_write_actions_follow_the_matrix(client, db, role, method, path, body):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    add_member(db, ana.workspace_id, bea.user_id, role)
    project_id = ana.first_project()["id"]
    needed = Permission.PROJECT_DELETE if method == "DELETE" else Permission.PROJECT_WRITE

    response = bea.request(
        method, path.format(id=project_id), workspace_id=ana.workspace_id, json=body
    )

    assert (response.status_code < 400) is can(role, needed), response.text
    if not can(role, needed):
        assert response.status_code == 403


@pytest.mark.integration
def test_viewer_can_read_but_sees_its_role(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")
    add_member(db, ana.workspace_id, bea.user_id, Role.VIEWER)

    current = bea.get("/api/v1/workspaces/current", workspace_id=ana.workspace_id).json()
    projects = bea.request("GET", "/api/v1/projects", workspace_id=ana.workspace_id)

    assert current["role"] == "viewer"
    assert current["permissions"] == ["workspace.read"]
    assert projects.status_code == 200
    assert len(bea.get("/api/v1/workspaces").json()) == 2


@pytest.mark.integration
def test_membership_role_is_constrained_in_database(client, db):
    ana = Account(client, "ana@example.com")
    bea = Account(client, "bea@example.com")

    with pytest.raises(Exception, match="ck_memberships_role"):
        add_member(db, ana.workspace_id, bea.user_id, "superuser")
    assert db(lambda s: s.scalar(select(Membership).where(Membership.user_id == bea.user_id)))
