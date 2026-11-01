"""Capacidades: acciones atómicas que AICC sabe ejecutar (orquestacion.md §5, HU-18).

Cada capacidad declara su esquema de entrada (un modelo Pydantic), su riesgo y su modelo de costo.
Registrar una capacidad sin esquema hace fallar el arranque: el planner nunca puede referirse a algo
que el backend no sabe validar.
"""

from dataclasses import dataclass
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    READ = "read"
    WRITE_INTERNAL = "write_internal"
    WRITE_EXTERNAL = "write_external"
    SPEND = "spend"
    DESTRUCTIVE = "destructive"


class DefaultPolicy(StrEnum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


POLICY_BY_RISK = {
    RiskLevel.READ: DefaultPolicy.ALLOW,
    RiskLevel.WRITE_INTERNAL: DefaultPolicy.ALLOW,
    RiskLevel.WRITE_EXTERNAL: DefaultPolicy.REQUIRE_APPROVAL,
    RiskLevel.SPEND: DefaultPolicy.REQUIRE_APPROVAL,
    RiskLevel.DESTRUCTIVE: DefaultPolicy.DENY,
}

RISK_LABELS = {
    RiskLevel.READ: "Solo consulta",
    RiskLevel.WRITE_INTERNAL: "Cambia algo dentro de AICC",
    RiskLevel.WRITE_EXTERNAL: "Actúa fuera de AICC",
    RiskLevel.SPEND: "Genera un gasto",
    RiskLevel.DESTRUCTIVE: "Borra o destruye",
}


class CatalogError(Exception):
    """Definición inválida del catálogo; se lanza al importar, así el arranque falla."""


@dataclass(frozen=True)
class Capability:
    id: str
    version: str
    title: str
    input_schema: type[BaseModel]
    risk_level: RiskLevel
    cost_model: str
    timeout_s: int
    max_retries: int
    idempotent: bool

    @property
    def default_policy(self) -> DefaultPolicy:
        return POLICY_BY_RISK[self.risk_level]


class _Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LlmGenerateInput(_Inputs):
    instruction: str = Field(min_length=1, max_length=4000)
    context: str | None = Field(default=None, max_length=20000)


class HttpGetInput(_Inputs):
    url: AnyHttpUrl


class NotifyInAppInput(_Inputs):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=4000)


CAPABILITIES: dict[str, Capability] = {}


def register(capability: Capability) -> Capability:
    schema = capability.input_schema
    if not (isinstance(schema, type) and issubclass(schema, BaseModel)):
        raise CatalogError(f"La capacidad {capability.id} no declara un esquema de entrada")
    if capability.id in CAPABILITIES:
        raise CatalogError(f"La capacidad {capability.id} ya está registrada")
    CAPABILITIES[capability.id] = capability
    return capability


register(
    Capability(
        id="llm.generate",
        version="1.0.0",
        title="Redactar con IA",
        input_schema=LlmGenerateInput,
        risk_level=RiskLevel.READ,
        cost_model="per_token",
        timeout_s=60,
        max_retries=2,
        idempotent=True,
    )
)
register(
    Capability(
        id="http.get_allowlisted",
        version="1.0.0",
        title="Leer una página web permitida",
        input_schema=HttpGetInput,
        risk_level=RiskLevel.READ,
        cost_model="none",
        timeout_s=15,
        max_retries=2,
        idempotent=True,
    )
)
register(
    Capability(
        id="notify.in_app",
        version="1.0.0",
        title="Avisarte en la app",
        input_schema=NotifyInAppInput,
        risk_level=RiskLevel.WRITE_INTERNAL,
        cost_model="none",
        timeout_s=5,
        max_retries=3,
        idempotent=False,
    )
)
