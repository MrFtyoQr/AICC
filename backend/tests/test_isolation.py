"""Suite de aislamiento multi-tenant (HU-10, gate F1).

Dos usuarios, cada uno con su workspace. Ninguno puede listar, leer, modificar ni borrar
recursos del otro, ni enviando el id del workspace ajeno ni el id del recurso ajeno desde su
propio workspace.
Toda ruta nueva que exponga datos de cliente debe añadirse aquí.
"""

import uuid

import pytest
from sqlalchemy import select

from app.infrastructure.models import Project
from tests.tenancy import Account

pytestmark = [pytest.mark.integration, pytest.mark.isolation]


@pytest.fixture
def ana(client) -> Account:
    return Account(client, "ana@example.com")


@pytest.fixture
def eve(client) -> Account:
    """La usuaria que intenta acceder a lo de Ana."""
    return Account(client, "eve@example.com")


WORKSPACE_ROUTES = [
    ("GET", "/api/v1/workspaces/current", None),
    ("PATCH", "/api/v1/workspaces/current", {"name": "Hackeado"}),
    ("DELETE", "/api/v1/workspaces/current", None),
    ("GET", "/api/v1/projects", None),
    ("POST", "/api/v1/projects", {"name": "Intruso"}),
    ("GET", "/api/v1/members", None),
    ("POST", "/api/v1/members/invitations", {"email": "eve2@example.com", "role": "owner"}),
    ("GET", "/api/v1/activity", None),
    ("GET", "/api/v1/tasks", None),
    ("POST", "/api/v1/tasks", {"text": "Tarea intrusa"}),
]

TASK_ROUTES = [
    ("GET", "/api/v1/tasks/{task}", None),
    ("GET", "/api/v1/tasks/{task}/events", None),
    ("POST", "/api/v1/tasks/{task}/cancel", {"version": 1}),
]

PROJECT_ROUTES = [
    ("GET", "/api/v1/projects/{id}", None),
    ("PATCH", "/api/v1/projects/{id}", {"name": "Hackeado"}),
    ("DELETE", "/api/v1/projects/{id}", None),
    ("POST", "/api/v1/projects/{id}/environments", {"name": "x", "kind": "production"}),
    ("PATCH", "/api/v1/projects/{id}/environments/{env}", {"name": "Hackeado"}),
    ("DELETE", "/api/v1/projects/{id}/environments/{env}", None),
]

MEMBER_ROUTES = [
    ("PATCH", "/api/v1/members/{member}", {"role": "viewer"}),
    ("DELETE", "/api/v1/members/{member}", None),
    ("DELETE", "/api/v1/members/invitations/{invitation}", None),
]


@pytest.mark.parametrize(("method", "path", "body"), WORKSPACE_ROUTES)
def test_foreign_workspace_header_is_404(ana, eve, method, path, body):
    response = eve.request(method, path, workspace_id=ana.workspace_id, json=body)

    assert response.status_code == 404


@pytest.mark.parametrize(("method", "path", "body"), WORKSPACE_ROUTES)
def test_unknown_workspace_is_indistinguishable_from_foreign(eve, method, path, body):
    response = eve.request(method, path, workspace_id=str(uuid.uuid4()), json=body)

    assert response.status_code == 404


@pytest.mark.parametrize("via", ["own-workspace", "foreign-workspace"])
@pytest.mark.parametrize(("method", "path", "body"), PROJECT_ROUTES)
def test_foreign_project_is_404(ana, eve, via, method, path, body):
    project = ana.first_project()
    workspace = eve.workspace_id if via == "own-workspace" else ana.workspace_id
    url = path.format(id=project["id"], env=project["environments"][0]["id"])

    response = eve.request(method, url, workspace_id=workspace, json=body)

    assert response.status_code == 404


@pytest.mark.parametrize("via", ["own-workspace", "foreign-workspace"])
@pytest.mark.parametrize(("method", "path", "body"), MEMBER_ROUTES)
def test_foreign_members_and_invitations_are_404(ana, eve, via, method, path, body):
    invitation = ana.request(
        "POST", "/api/v1/members/invitations", json={"email": "bea@example.com", "role": "viewer"}
    ).json()
    member = ana.request("GET", "/api/v1/members").json()["members"][0]
    workspace = eve.workspace_id if via == "own-workspace" else ana.workspace_id
    url = path.format(member=member["id"], invitation=invitation["id"])

    response = eve.request(method, url, workspace_id=workspace, json=body)

    assert response.status_code == 404


def test_activity_never_shows_foreign_entries(ana, eve):
    ana.request("POST", "/api/v1/projects", json={"name": "Secreto de Ana"})

    summaries = [i["summary"] for i in eve.request("GET", "/api/v1/activity").json()["items"]]

    assert summaries == ["Creó su cuenta y su espacio personal"]


def test_listings_never_include_foreign_data(ana, eve):
    ana.request("POST", "/api/v1/projects", json={"name": "Secreto de Ana"})

    eve_workspaces = {w["id"] for w in eve.get("/api/v1/workspaces").json()}
    eve_projects = [p["name"] for p in eve.request("GET", "/api/v1/projects").json()]

    assert ana.workspace_id not in eve_workspaces
    assert eve_projects == ["General"]


def test_attacks_leave_foreign_data_untouched(ana, eve, db):
    project_id = ana.first_project()["id"]
    for workspace in (eve.workspace_id, ana.workspace_id):
        eve.request("PATCH", f"/api/v1/projects/{project_id}", workspace, json={"name": "Hackeado"})
        eve.request("DELETE", f"/api/v1/projects/{project_id}", workspace)

    stored = db(lambda s: s.scalar(select(Project).where(Project.id == uuid.UUID(project_id))))
    assert stored is not None
    assert stored.name == "General"
    assert str(stored.workspace_id) == ana.workspace_id


@pytest.mark.parametrize("via", ["own-workspace", "foreign-workspace"])
@pytest.mark.parametrize(("method", "path", "body"), TASK_ROUTES)
def test_foreign_task_is_404(ana, eve, via, method, path, body):
    task = ana.request("POST", "/api/v1/tasks", json={"text": "Tarea de Ana"}).json()
    workspace = eve.workspace_id if via == "own-workspace" else ana.workspace_id

    response = eve.request(method, path.format(task=task["id"]), workspace_id=workspace, json=body)

    assert response.status_code == 404
    assert ana.request("GET", f"/api/v1/tasks/{task['id']}").json()["status"] == "DRAFT"


def test_foreign_project_cannot_host_my_task(ana, eve):
    project = ana.first_project()

    response = eve.request(
        "POST", "/api/v1/tasks", json={"text": "Intruso", "project_id": project["id"]}
    )

    assert response.status_code == 404
