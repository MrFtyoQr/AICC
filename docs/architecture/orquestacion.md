# Núcleo de orquestación

Este documento define **cómo AICC convierte una intención en trabajo ejecutado y auditado**.
Es la referencia para las fases O1–O6 del [plan maestro](../planning/plan-maestro.md). Todo lo demás
(cotizador, provisionamiento, Lead Capture, media) se construye encima de este núcleo.

## 1. Vocabulario

| Término | Definición | Tabla |
|---|---|---|
| **Workspace** | Límite de aislamiento: identidad, permisos, presupuesto, auditoría | `workspaces` |
| **Project** | Agrupa una solución de negocio dentro del workspace | `projects` |
| **Environment** | `development` · `staging` · `production` de un proyecto | `environments` |
| **Task** | Lo que el usuario pidió, en sus palabras, con su ciclo de vida | `tasks` |
| **Plan** | Propuesta estructurada y versionada para resolver una Task | `plans` |
| **Step** | Unidad atómica de un plan: una capacidad con entradas y salidas | `plan_steps` |
| **Capability** | Algo que AICC sabe hacer (ej. `llm.generate`, `http.request`, `n8n.trigger_workflow`) con su esquema y riesgo | `capabilities` (catálogo) |
| **Connector** | Implementación concreta de una o más capabilities contra un proveedor | código + `provider_connections` |
| **Policy** | Regla determinista que permite, deniega o exige aprobación | `policies` |
| **Approval** | Decisión humana registrada sobre un plan o un step | `approvals` |
| **Run** | Una ejecución de un plan aprobado | `runs` |
| **Step Run** | Ejecución de un step dentro de un run (con intentos) | `step_runs` |
| **Event** | Hecho inmutable emitido por el sistema (se transmite por SSE) | `events` |
| **Artifact** | Resultado persistente producido por un step (texto, archivo, enlace) | `artifacts` |
| **Usage Event** | Consumo medido (tokens, segundos, mensajes) con costo | `usage_events` |

## 2. Flujo completo

```
Usuario (Flutter)
  │ 1. Describe el objetivo
  ▼
POST /api/v1/tasks                         → Task(DRAFT)
  │ 2. Pide plan
  ▼
POST /api/v1/tasks/{id}/plan               → Task(PLANNING)
  │   Planner (LLM vía AgentRuntime) propone JSON estructurado
  │   Validador de esquema: steps solo con capabilities del catálogo
  │   Policy Engine evalúa cada step (allow / deny / require_approval)
  │   Estimador calcula costo esperado y lo compara con el presupuesto
  ▼
Plan v1 (PROPOSED)                         → Task(AWAITING_APPROVAL)  o  Task(REJECTED_BY_POLICY)
  │ 3. Usuario revisa (puede pedir cambios → Plan v2)
  ▼
POST /api/v1/plans/{id}/approve            → Approval registrada, Task(APPROVED)
  │ 4. Encolar
  ▼
Run(QUEUED) → Redis → Worker               → Task(RUNNING)
  │   Por cada step: re-evaluar política → ejecutar connector → registrar usage/artifacts/events
  │   Step sensible → pausa en AWAITING_STEP_APPROVAL
  │   Presupuesto al 100 % → PAUSED_BUDGET
  ▼
Run(SUCCEEDED | FAILED | CANCELLED)        → Task(DONE | FAILED | CANCELLED)
  │
  └─ Eventos SSE en cada transición → la app se actualiza en vivo
```

## 3. Máquina de estados de Task

```
DRAFT ──plan──▶ PLANNING ──ok──▶ AWAITING_APPROVAL ──approve──▶ APPROVED ──enqueue──▶ RUNNING
  ▲                │                    │   │                                         │  │  │
  │                │fail                │   └─request_changes──▶ PLANNING             │  │  └─▶ DONE
  │                ▼                    │reject                                       │  └────▶ FAILED
  └──edit── PLANNING_FAILED             ▼                                             ▼
                                   REJECTED                               PAUSED (input / aprobación / presupuesto)
REJECTED_BY_POLICY (terminal; el usuario puede editar y volver a DRAFT)     CANCELLED (desde cualquier estado no terminal)
```

Reglas:

1. Las transiciones se implementan en **un único módulo de dominio** (`domain/tasks/state_machine.py`) con una tabla explícita; cualquier transición no listada lanza error.
2. Cada transición escribe un `event` y un `audit_log` en la **misma transacción**.
3. El cliente nunca fija estados: solo invoca comandos (`plan`, `approve`, `cancel`…).
4. Concurrencia: columna `version` (bloqueo optimista) en `tasks`, `plans` y `runs`. Cada comando envía la
   `version` que leyó; si no coincide, o si otra petición confirma antes, responde **409**.
5. La tabla vive en `backend/app/domain/tasks/state_machine.py`; `test_state_machine.py` la compara con este
   diagrama y prueba **todas** las combinaciones estado × comando (válidas e inválidas). El texto de cada estado
   (`LABELS`) se compara con el diccionario de `principios-ux.md` §6. `events` es append-only (un trigger impide
   `UPDATE`).

## 4. Contrato del plan (lo que el LLM puede devolver)

> **Regla (ADR-011, [modelo-operacion.md](modelo-operacion.md)):** AICC no inventa soluciones. Un plan es una
> **receta del catálogo instanciada**: el LLM elige la receta (`recipe`) y rellena sus parámetros; los `steps` los
> genera el backend a partir de la versión de la receta. Mientras no exista el catálogo (O2), el validador acepta solo
> steps que formen parte de una receta registrada. El ejemplo de abajo muestra el plan **ya expandido**.

```json
{
  "plan_version": 1,
  "recipe": {"key": "lead_daily_summary", "version": "1.0.0"},
  "goal": "Resumir los 10 leads de hoy y enviarme un email",
  "assumptions": ["Los leads están en la tabla leads del proyecto"],
  "steps": [
    {
      "key": "fetch_leads",
      "capability": "db.query_leads",
      "inputs": {"since": "today"},
      "depends_on": []
    },
    {
      "key": "summarize",
      "capability": "llm.generate",
      "inputs": {"prompt_template": "lead_summary_v1", "data": "{{steps.fetch_leads.output}}"},
      "depends_on": ["fetch_leads"]
    },
    {
      "key": "notify",
      "capability": "email.send",
      "inputs": {"to": "{{workspace.owner_email}}", "body": "{{steps.summarize.output}}"},
      "depends_on": ["summarize"]
    }
  ]
}
```

Validación determinista antes de mostrarlo al usuario:

- `recipe` debe existir en el catálogo; los `steps` deben coincidir con los de esa versión de la receta.
- `capability` debe existir en el catálogo y estar habilitada para el workspace.
- `inputs` validados contra el JSON Schema de la capability.
- Grafo `depends_on` acíclico; referencias `{{...}}` solo a steps previos o variables permitidas.
- Límite de steps por plan (inicial: 10) y de profundidad.
- El LLM **no** puede fijar riesgo, costo, aprobación ni destinatarios fuera de los permitidos: eso lo calcula el backend.

## 5. Capabilities y riesgo

Cada capability declara:

| Campo | Ejemplo |
|---|---|
| `id` | `email.send` |
| `version` | `1.0.0` |
| `input_schema` / `output_schema` | JSON Schema |
| `risk_level` | `read` · `write_internal` · `write_external` · `spend` · `destructive` |
| `default_policy` | `allow` · `require_approval` · `deny` |
| `cost_model` | `none` · `per_token` · `per_call` · `per_second` |
| `timeout_s`, `max_retries`, `idempotent` | `30`, `3`, `false` |

Política por defecto según riesgo:

| Riesgo | Por defecto |
|---|---|
| `read` | allow |
| `write_internal` | allow (auditado) |
| `write_external` (enviar, publicar) | require_approval |
| `spend` (genera costo > umbral) | require_approval |
| `destructive` | deny en MVP |

## 6. Policy Engine

- Entrada: `(actor, workspace, environment, capability, inputs, costo_estimado, presupuesto)`.
- Salida: `allow | deny | require_approval` + `reason` legible + `policy_id` aplicada.
- Implementación inicial: reglas en código Python + tabla `policies` para ajustes por workspace. Sin motores externos (OPA) hasta que haga falta.
- Se evalúa **dos veces**: al proponer el plan y justo antes de ejecutar cada step (el contexto pudo cambiar).
- Un LLM nunca evalúa políticas ni puede modificarlas.

## 7. AgentRuntime (abstracción de proveedores LLM)

```python
class AgentRuntime(Protocol):
    async def generate(self, request: GenerateRequest) -> GenerateResult: ...
    async def generate_structured(self, request: GenerateRequest, schema: type[BaseModel]) -> StructuredResult: ...
    async def estimate(self, request: GenerateRequest) -> CostEstimate: ...
```

- Un solo proveedor en el MVP de orquestación; el segundo solo cuando haya caso validado.
- Cada llamada registra `usage_event` (tokens in/out, modelo, costo, latencia).
- Las claves viven en el backend (secret manager / variable de entorno), nunca en Flutter.
- Un `FakeRuntime` determinista para pruebas: todas las pruebas de orquestación corren sin red.

## 8. Ejecución (Worker)

- Cola en Redis; biblioteca a decidir en ADR‑005 (candidatas: **arq** async nativo, Dramatiq, Celery). Preferencia: arq por ser asíncrono y simple.
- El worker carga el run desde PostgreSQL (Redis solo transporta el `run_id`).
- `step_runs` con `idempotency_key = run_id:step_key:attempt`; reintentos con backoff exponencial solo si la capability es idempotente o el error es transitorio.
- Timeouts por step; heartbeat del worker; un *reaper* marca runs huérfanos.
- Cancelación cooperativa: el worker revisa la bandera de cancelación entre steps.

## 9. Eventos en tiempo real

- Tabla `events` (append‑only) + canal Redis pub/sub por workspace.
- `GET /api/v1/tasks/{id}/events` con **SSE**; reanudación con `Last-Event-ID`.
- Tipos: `task.state_changed`, `plan.proposed`, `approval.requested`, `step.started`, `step.succeeded`, `step.failed`, `usage.recorded`, `budget.threshold_reached`.
- La app nunca hace *polling* agresivo; si se pierde SSE, reconecta y pide eventos desde el último id.

## 10. Auditoría y medición

- `audit_logs`: actor, acción, recurso, política aplicada, resultado, IP/dispositivo, timestamp. Sin secretos ni payloads completos.
- `usage_events` por cada llamada con costo; `budgets` con umbrales 70 % alerta, 90 % confirmación, 100 % pausa.

## 11. API de orquestación (v1)

| Método | Ruta | Fase |
|---|---|---|
| POST | `/api/v1/tasks` | O1 |
| GET | `/api/v1/tasks` · `/api/v1/tasks/{id}` | O1 |
| POST | `/api/v1/tasks/{id}/plan` | O2 |
| GET | `/api/v1/plans/{id}` | O2 |
| POST | `/api/v1/plans/{id}/approve` · `/reject` · `/request-changes` | O3 |
| GET | `/api/v1/approvals?status=pending` | O3 |
| POST | `/api/v1/tasks/{id}/cancel` (envía `version`) | O1 |
| GET | `/api/v1/runs/{id}` · `/api/v1/runs/{id}/steps` | O4 |
| GET | `/api/v1/tasks/{id}/events` (JSON en O1; SSE en O4) | O1 / O4 |
| GET | `/api/v1/capabilities` | O2 |
| GET | `/api/v1/usage/summary` · `/api/v1/budgets` | O6 |

Todas las rutas bajo `/api/v1` exigen autenticación y resuelven el workspace desde la membresía del usuario, no desde el body.
