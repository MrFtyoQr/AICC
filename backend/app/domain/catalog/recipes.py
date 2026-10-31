"""Recetas: soluciones probadas con pasos fijos (ADR-007, modelo-operacion.md §4).

La IA solo elige una receta y propone sus parámetros. Los pasos salen siempre de la plantilla de la
receta, nunca del modelo: así AICC entrega soluciones conocidas en lugar de improvisar planes.
"""

import re
from dataclasses import dataclass, field

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from app.domain.catalog.capabilities import CAPABILITIES, CatalogError

MAX_STEPS = 10
_PARAM_REF = re.compile(r"\{\{params\.([a-z_]+)\}\}")
_STEP_REF = re.compile(r"\{\{steps\.([a-z_]+)\.output\}\}")


@dataclass(frozen=True)
class StepTemplate:
    key: str
    title: str
    capability: str
    inputs: dict[str, str]
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Recipe:
    key: str
    version: str
    title: str
    description: str
    params: type[BaseModel]
    steps: tuple[StepTemplate, ...]
    assumptions: tuple[str, ...] = field(default=())


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SummaryParams(_Params):
    tema: str = Field(min_length=3, max_length=500, description="Qué hay que resumir o explicar")


class WebParams(_Params):
    url: AnyHttpUrl = Field(description="Dirección https de la página a consultar")
    pregunta: str = Field(min_length=3, max_length=500, description="Qué quiere saber de la página")

    @field_validator("url")
    @classmethod
    def https_only(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("Solo se consultan páginas https")
        return value


class DraftParams(_Params):
    destinatario: str = Field(min_length=2, max_length=200, description="A quién va el mensaje")
    objetivo: str = Field(min_length=3, max_length=500, description="Qué debe lograr el mensaje")


RECIPES: dict[str, Recipe] = {}


def register(recipe: Recipe) -> Recipe:
    """Valida la plantilla al importar: capacidades existentes, referencias y orden correctos."""
    seen: set[str] = set()
    param_names = set(recipe.params.model_fields)
    if not 0 < len(recipe.steps) <= MAX_STEPS:
        raise CatalogError(f"La receta {recipe.key} debe tener entre 1 y {MAX_STEPS} pasos")
    for step in recipe.steps:
        if step.capability not in CAPABILITIES:
            raise CatalogError(f"{recipe.key}.{step.key}: capacidad {step.capability} inexistente")
        for value in step.inputs.values():
            if missing := set(_PARAM_REF.findall(value)) - param_names:
                raise CatalogError(f"{recipe.key}.{step.key}: parámetros desconocidos {missing}")
            if bad := set(_STEP_REF.findall(value)) - set(step.depends_on):
                raise CatalogError(f"{recipe.key}.{step.key}: usa pasos no declarados {bad}")
        if unknown := set(step.depends_on) - seen:
            raise CatalogError(f"{recipe.key}.{step.key}: depende de pasos posteriores {unknown}")
        seen.add(step.key)
    if recipe.key in RECIPES:
        raise CatalogError(f"La receta {recipe.key} ya está registrada")
    RECIPES[recipe.key] = recipe
    return recipe


register(
    Recipe(
        key="resumen_aviso",
        version="1.0.0",
        title="Resumir un tema y avisarte",
        description="Redacta un resumen claro sobre un tema que el usuario indica y se lo deja "
        "como aviso en la app.",
        params=SummaryParams,
        steps=(
            StepTemplate(
                key="redactar",
                title="Redactar el resumen",
                capability="llm.generate",
                inputs={"instruction": "Resume de forma clara y breve: {{params.tema}}"},
            ),
            StepTemplate(
                key="avisar",
                title="Avisarte en la app con el resumen",
                capability="notify.in_app",
                inputs={"title": "Tu resumen está listo", "body": "{{steps.redactar.output}}"},
                depends_on=("redactar",),
            ),
        ),
        assumptions=("El resumen se basa en conocimiento general, no en tus archivos.",),
    )
)
register(
    Recipe(
        key="consulta_web",
        version="1.0.0",
        title="Consultar una página web y resumirla",
        description="Lee una página https pública que el usuario indica, responde su pregunta "
        "sobre ella y se lo deja como aviso en la app.",
        params=WebParams,
        steps=(
            StepTemplate(
                key="leer",
                title="Leer la página",
                capability="http.get_allowlisted",
                inputs={"url": "{{params.url}}"},
            ),
            StepTemplate(
                key="responder",
                title="Responder tu pregunta con lo que dice la página",
                capability="llm.generate",
                inputs={
                    "instruction": "Responde usando solo la página: {{params.pregunta}}",
                    "context": "{{steps.leer.output}}",
                },
                depends_on=("leer",),
            ),
            StepTemplate(
                key="avisar",
                title="Avisarte en la app con la respuesta",
                capability="notify.in_app",
                inputs={"title": "Respuesta lista", "body": "{{steps.responder.output}}"},
                depends_on=("responder",),
            ),
        ),
        assumptions=(
            "La página es pública y su dominio debe estar en la lista permitida del workspace.",
        ),
    )
)
register(
    Recipe(
        key="borrador_mensaje",
        version="1.0.0",
        title="Redactar un mensaje para revisar",
        description="Redacta un borrador de mensaje (correo, WhatsApp, respuesta a un cliente o "
        "lead) y te lo deja para revisar. No envía nada.",
        params=DraftParams,
        steps=(
            StepTemplate(
                key="redactar",
                title="Redactar el borrador",
                capability="llm.generate",
                inputs={
                    "instruction": "Redacta un mensaje cordial para {{params.destinatario}} "
                    "con este objetivo: {{params.objetivo}}"
                },
            ),
            StepTemplate(
                key="avisar",
                title="Dejarte el borrador para revisar",
                capability="notify.in_app",
                inputs={
                    "title": "Borrador listo para revisar",
                    "body": "{{steps.redactar.output}}",
                },
                depends_on=("redactar",),
            ),
        ),
        assumptions=(
            "El mensaje no se envía: enviarlo llegará en una fase posterior y con tu aprobación.",
        ),
    )
)
