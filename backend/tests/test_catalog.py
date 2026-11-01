"""HU-18: catálogo de capacidades y recetas (sin base de datos salvo la prueba de la API)."""

import pytest
from pydantic import BaseModel

from app.domain.catalog import capabilities, recipes
from app.domain.catalog.capabilities import (
    CAPABILITIES,
    Capability,
    CatalogError,
    DefaultPolicy,
    RiskLevel,
)
from app.domain.catalog.recipes import RECIPES, Recipe, StepTemplate
from tests.tenancy import Account


def make_capability(**overrides) -> Capability:
    values = {
        "id": "test.cap",
        "version": "1.0.0",
        "title": "Prueba",
        "input_schema": capabilities.NotifyInAppInput,
        "risk_level": RiskLevel.READ,
        "cost_model": "none",
        "timeout_s": 1,
        "max_retries": 0,
        "idempotent": True,
    } | overrides
    return Capability(**values)


def test_initial_capabilities_are_registered():
    assert set(CAPABILITIES) == {"llm.generate", "http.get_allowlisted", "notify.in_app"}


@pytest.mark.parametrize("schema", [None, dict, "esquema"])
def test_capability_without_schema_fails_at_registration(schema):
    with pytest.raises(CatalogError, match="no declara un esquema"):
        capabilities.register(make_capability(input_schema=schema))


def test_duplicate_capability_is_rejected():
    with pytest.raises(CatalogError, match="ya está registrada"):
        capabilities.register(make_capability(id="llm.generate"))


@pytest.mark.parametrize(
    ("risk", "policy"),
    [
        (RiskLevel.READ, DefaultPolicy.ALLOW),
        (RiskLevel.WRITE_INTERNAL, DefaultPolicy.ALLOW),
        (RiskLevel.WRITE_EXTERNAL, DefaultPolicy.REQUIRE_APPROVAL),
        (RiskLevel.SPEND, DefaultPolicy.REQUIRE_APPROVAL),
        (RiskLevel.DESTRUCTIVE, DefaultPolicy.DENY),
    ],
)
def test_default_policy_follows_risk(risk, policy):
    assert make_capability(risk_level=risk).default_policy == policy


class _P(BaseModel):
    tema: str


def make_recipe(*steps: StepTemplate) -> Recipe:
    return Recipe(key="prueba", version="1", title="t", description="d", params=_P, steps=steps)


@pytest.mark.parametrize(
    ("steps", "message"),
    [
        ((), "entre 1 y"),
        ((StepTemplate("a", "A", "no.existe", {}),), "inexistente"),
        (
            (StepTemplate("a", "A", "llm.generate", {"instruction": "{{params.otro}}"}),),
            "desconocidos",
        ),
        (
            (StepTemplate("a", "A", "llm.generate", {"instruction": "{{steps.b.output}}"}),),
            "no declarados",
        ),
        (
            (
                StepTemplate("a", "A", "llm.generate", {"instruction": "x"}, depends_on=("b",)),
                StepTemplate("b", "B", "llm.generate", {"instruction": "y"}),
            ),
            "posteriores",
        ),
    ],
)
def test_broken_recipes_fail_at_registration(steps, message):
    with pytest.raises(CatalogError, match=message):
        recipes.register(make_recipe(*steps))


def test_every_registered_recipe_only_uses_known_capabilities():
    for recipe in RECIPES.values():
        assert {s.capability for s in recipe.steps} <= set(CAPABILITIES)


@pytest.mark.integration
def test_capabilities_endpoint_shows_schema_and_risk(client):
    ana = Account(client, "ana@example.com")

    body = {c["id"]: c for c in ana.get("/api/v1/capabilities").json()}

    assert body["notify.in_app"]["risk_level"] == "write_internal"
    assert body["notify.in_app"]["risk_label"] == "Cambia algo dentro de AICC"
    assert body["llm.generate"]["default_policy"] == "allow"
    assert "instruction" in body["llm.generate"]["input_schema"]["properties"]


@pytest.mark.integration
def test_catalog_requires_authentication(client):
    assert client.get("/api/v1/capabilities").status_code == 401
    assert client.get("/api/v1/recipes").status_code == 401


@pytest.mark.integration
def test_recipes_endpoint_lists_fixed_steps(client):
    ana = Account(client, "ana@example.com")

    body = {r["key"]: r for r in ana.get("/api/v1/recipes").json()}

    assert [s["key"] for s in body["consulta_web"]["steps"]] == ["leer", "responder", "avisar"]
