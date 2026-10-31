"""Del pedido a un plan: expandir la receta elegida y validarla de forma determinista (ADR-012).

Nada de aquí llama a la IA. Recibe la receta y los parámetros que propuso y decide si el plan es
válido; si no lo es, explica por qué en lenguaje claro.
"""

import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.domain.catalog.capabilities import CAPABILITIES, RiskLevel
from app.domain.catalog.recipes import MAX_STEPS, RECIPES, Recipe

_PARAM_REF = re.compile(r"\{\{params\.([a-z_]+)\}\}")
_STEP_REF = re.compile(r"\{\{steps\.([a-z_]+)\.output\}\}")


class PlanningError(Exception):
    """El pedido no se puede convertir en un plan válido. `reason` se muestra al usuario."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class StepDraft:
    position: int
    key: str
    title: str
    capability: str
    capability_version: str
    inputs: dict[str, str]
    depends_on: tuple[str, ...]
    risk_level: RiskLevel


@dataclass(frozen=True)
class PlanDraft:
    recipe: Recipe
    params: dict[str, Any]
    assumptions: tuple[str, ...]
    steps: tuple[StepDraft, ...]


def build_plan(recipe_key: str, raw_params: dict[str, str], assumptions: list[str]) -> PlanDraft:
    recipe = RECIPES.get(recipe_key)
    if recipe is None:
        raise PlanningError("Todavía no tengo una solución para ese pedido.")
    try:
        params = recipe.params.model_validate(raw_params).model_dump(mode="json")
    except ValidationError as exc:
        fields = sorted({str(error["loc"][0]) for error in exc.errors() if error["loc"]})
        raise PlanningError(
            f"Para «{recipe.title}» faltan o no son válidos estos datos: {', '.join(fields)}."
        ) from None

    def render(value: str) -> str:
        return _PARAM_REF.sub(lambda m: str(params[m.group(1)]), value)

    steps = tuple(
        StepDraft(
            position=index,
            key=step.key,
            title=step.title,
            capability=step.capability,
            capability_version=CAPABILITIES[step.capability].version,
            inputs={name: render(value) for name, value in step.inputs.items()},
            depends_on=step.depends_on,
            risk_level=CAPABILITIES[step.capability].risk_level,
        )
        for index, step in enumerate(recipe.steps)
    )
    # Supuestos de la receta primero (fijos) y luego los que propuso la IA, acotados.
    extra = tuple(a.strip()[:200] for a in assumptions[:3] if a.strip())
    draft = PlanDraft(recipe, params, recipe.assumptions + extra, steps)
    validate(draft)
    return draft


def validate(draft: PlanDraft) -> None:
    """Revalida el plan completo: capacidades, esquemas, dependencias y límites."""
    if not 0 < len(draft.steps) <= MAX_STEPS:
        raise PlanningError(f"Un plan tiene entre 1 y {MAX_STEPS} pasos.")
    earlier: set[str] = set()
    for step in draft.steps:
        capability = CAPABILITIES.get(step.capability)
        if capability is None:
            raise PlanningError(f"El paso «{step.title}» usa una acción que AICC no conoce.")
        if step.key in earlier:
            raise PlanningError(f"El paso «{step.key}» está repetido.")
        if missing := set(step.depends_on) - earlier:
            raise PlanningError(
                f"El paso «{step.title}» depende de pasos que no van antes: {missing}."
            )
        referenced = {ref for value in step.inputs.values() for ref in _STEP_REF.findall(value)}
        if referenced - set(step.depends_on):
            raise PlanningError(f"El paso «{step.title}» usa resultados que no declaró.")
        # Los resultados de pasos previos aún no existen: se validan con un valor de muestra.
        sample = {k: _STEP_REF.sub("(resultado previo)", v) for k, v in step.inputs.items()}
        try:
            capability.input_schema.model_validate(sample)
        except ValidationError:
            raise PlanningError(f"Los datos del paso «{step.title}» no son válidos.") from None
        earlier.add(step.key)
