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
    ("GET", "/api/v1/projects", None),
    ("POST", "/api/v1/projects", {"name": "Intruso"}),
]

PROJECT_ROUTES = [
    ("GET", "/api/v1/projects/{id}", None),
    ("PATCH", "/api/v1/projects/{id}", {"name": "Hackeado"}),
    ("DELETE", "/api/v1/projects/{id}", None),
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
    project_id = ana.first_project()["id"]
    workspace = eve.workspace_id if via == "own-workspace" else ana.workspace_id

    response = eve.request(method, path.format(id=project_id), workspace_id=workspace, json=body)

    assert response.status_code == 404


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
