from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.domain.catalog.capabilities import CAPABILITIES, RISK_LABELS, DefaultPolicy, RiskLevel
from app.domain.catalog.recipes import RECIPES

router = APIRouter(tags=["catalog"])


class CapabilityResponse(BaseModel):
    id: str
    version: str
    title: str
    risk_level: RiskLevel
    risk_label: str
    default_policy: DefaultPolicy
    cost_model: str
    input_schema: dict


class RecipeStepResponse(BaseModel):
    key: str
    title: str
    capability: str


class RecipeResponse(BaseModel):
    key: str
    version: str
    title: str
    description: str
    params_schema: dict
    steps: list[RecipeStepResponse]


@router.get(
    "/capabilities",
    response_model=list[CapabilityResponse],
    summary="Acciones que AICC sabe ejecutar, con su esquema y nivel de riesgo",
)
async def list_capabilities(_: CurrentUser):
    return [
        CapabilityResponse(
            id=c.id,
            version=c.version,
            title=c.title,
            risk_level=c.risk_level,
            risk_label=RISK_LABELS[c.risk_level],
            default_policy=c.default_policy,
            cost_model=c.cost_model,
            input_schema=c.input_schema.model_json_schema(),
        )
        for c in CAPABILITIES.values()
    ]


@router.get(
    "/recipes",
    response_model=list[RecipeResponse],
    summary="Soluciones que AICC ofrece (recetas con pasos fijos)",
)
async def list_recipes(_: CurrentUser):
    return [
        RecipeResponse(
            key=r.key,
            version=r.version,
            title=r.title,
            description=r.description,
            params_schema=r.params.model_json_schema(),
            steps=[
                RecipeStepResponse(key=s.key, title=s.title, capability=s.capability)
                for s in r.steps
            ],
        )
        for r in RECIPES.values()
    ]
