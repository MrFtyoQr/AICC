"""AgentRuntime: interfaz única para proveedores de IA (orquestacion.md §7, HU-19).

- `FakeRuntime`: determinista, sin red ni costo. Es el motor de las pruebas y del desarrollo local.
- `AnthropicRuntime`: Claude vía el SDK oficial. La clave solo vive en el backend (variables de
  entorno / gestor de secretos) y nunca se envía a la app.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import anthropic
from pydantic import BaseModel

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerateRequest:
    system: str
    user: str
    max_tokens: int = 2000


@dataclass(frozen=True)
class StructuredResult[T: BaseModel]:
    output: T
    model: str
    input_tokens: int
    output_tokens: int


class RuntimeUnavailable(Exception):
    """El proveedor no respondió o rechazó la petición; el planner lo trata como fallo legible."""


class AgentRuntime(Protocol):
    name: str

    async def generate_structured[T: BaseModel](
        self, request: GenerateRequest, schema: type[T]
    ) -> StructuredResult[T]: ...


class FakeRuntime:
    """Responde con `responder(request, schema)`; por defecto, la heurística del planner."""

    name = "fake"

    def __init__(self, responder: Callable[[GenerateRequest, type], BaseModel]) -> None:
        self._responder = responder
        self.requests: list[GenerateRequest] = []

    async def generate_structured[T: BaseModel](
        self, request: GenerateRequest, schema: type[T]
    ) -> StructuredResult[T]:
        self.requests.append(request)
        output = self._responder(request, schema)
        if not isinstance(output, schema):
            output = schema.model_validate(output.model_dump())
        return StructuredResult(output, "fake", len(request.user) // 4, 50)


class AnthropicRuntime:
    name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        key = settings.anthropic_api_key
        if key is None or not key.get_secret_value():
            raise ValueError("ANTHROPIC_API_KEY es obligatoria con AI_PROVIDER=anthropic")
        self._model = settings.ai_model
        self._client = anthropic.AsyncAnthropic(
            api_key=key.get_secret_value(),
            timeout=settings.ai_timeout_s,
            max_retries=2,
        )

    async def generate_structured[T: BaseModel](
        self, request: GenerateRequest, schema: type[T]
    ) -> StructuredResult[T]:
        try:
            response = await self._client.messages.parse(
                model=self._model,
                max_tokens=request.max_tokens,
                system=request.system,
                messages=[{"role": "user", "content": request.user}],
                output_format=schema,
            )
        except anthropic.RateLimitError as exc:
            raise RuntimeUnavailable("El motor de IA está saturado; intenta en un momento") from exc
        except anthropic.APIStatusError as exc:
            logger.warning("anthropic error", extra={"check": str(exc.status_code)})
            raise RuntimeUnavailable("El motor de IA no pudo responder") from exc
        except anthropic.APIConnectionError as exc:
            raise RuntimeUnavailable("No hay conexión con el motor de IA") from exc
        if response.stop_reason == "refusal" or response.parsed_output is None:
            raise RuntimeUnavailable("El motor de IA no aceptó este pedido")
        return StructuredResult(
            response.parsed_output,
            response.model,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )


def build_runtime(settings: Settings) -> AgentRuntime:
    if settings.ai_provider == "anthropic":
        return AnthropicRuntime(settings)
    from app.application.planner import heuristic_choice

    return FakeRuntime(heuristic_choice)
