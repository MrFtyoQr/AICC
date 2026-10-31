# ADR-012: El motor determinista valida; el LLM solo propone y explica

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
Un LLM puede equivocarse o ser manipulado por el texto que recibe (*prompt injection*). AICC actúa sobre la
infraestructura y los datos de clientes, así que ninguna decisión con consecuencias puede depender solo del modelo.

## Decisión
- El LLM **interpreta** el pedido y **elige** una receta con sus parámetros (ADR-007). Todo lo demás es determinista:
  validación de esquemas, dependencias, riesgo (de la capacidad), política (del riesgo y del Policy Engine en O3),
  costo y aprobación.
- El pedido del usuario se envía **delimitado** (`<pedido>…</pedido>`), con los signos `<` y `>` neutralizados para que
  no pueda cerrar el bloque, y el prompt de sistema declara que su contenido son datos, no instrucciones.
- La salida del modelo siempre se valida con un esquema (salida estructurada + Pydantic); lo que no valida se rechaza.
- `AgentRuntime` es la única puerta a proveedores de IA. `FakeRuntime` (determinista, sin red) se usa en pruebas y en
  desarrollo sin clave; `AnthropicRuntime` usa el SDK oficial con la clave **solo en el backend** (`SecretStr`, nunca en
  respuestas, logs ni en la app). Proveedor y modelo se eligen por configuración (`AI_PROVIDER`, `AI_MODEL`).

## Consecuencias
- La suite de pruebas nunca llama a un proveedor real (una prueba lo verifica bloqueando la red).
- HU-21 (S6) amplía esta defensa: 20 pedidos de prueba, casos maliciosos documentados y la puerta de O2.
- Cambiar de proveedor o de modelo no cambia el contrato del plan.
