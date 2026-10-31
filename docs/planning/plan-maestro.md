# Plan maestro AICC

> Documento rector. Si algo no está aquí, no se construye todavía.
> Fecha de esta versión: 2026‑10‑31 · Responsable: Joseph Quintana · Revisión: al cerrar cada fase.

## 0. Cómo leer este plan

- El trabajo avanza en **fases secuenciales**. Una fase solo empieza cuando la anterior pasa su **puerta de salida** (*gate*).
- Cada fase se reparte en **6 frentes** que avanzan juntos, para que backend, app y UX nunca se desincronicen:

| Frente | Código | Qué cubre |
|---|---|---|
| Backend / Orquestación | `BE` | API, dominio, worker, conectores |
| App móvil | `APP` | Flutter, por incrementos (ver [app-movil-incremental.md](app-movil-incremental.md)) |
| UX / UI | `UX` | Flujos, pantallas, componentes, copy (ver [../ux/principios-ux.md](../ux/principios-ux.md)) |
| Infraestructura / DevOps | `OPS` | Docker, CI, entornos, medición local (ver [../environment/entorno-local.md](../environment/entorno-local.md)) |
| Seguridad | `SEC` | Auth, aislamiento, secretos, políticas, auditoría |
| Documentación | `DOC` | ADRs, contratos OpenAPI, guías, changelog |

- Todo se rastrea en Jira (proyecto `AICC`). Cada fase = **Epic**, cada fila de tarea = **Story/Task** con su código (ej. `O2-BE-03`). Ver [jira/README.md](jira/README.md).

## 1. Estrategia: primero orquestación

AICC tiene dos etapas. **No se toca la Etapa B hasta cerrar la Etapa A.**

```
ETAPA A · Plataforma de orquestación (el "cerebro" y el "centro de mando")
  F0 Fundamentos ─▶ F1 Identidad y Workspace ─▶ O1 Tareas ─▶ O2 Planner ─▶ O3 Políticas y Aprobaciones
                                                                  ─▶ O4 Ejecución en vivo ─▶ O5 Conectores ─▶ O6 Consumo y Presupuesto
                                                                                                            ║
                                                                                                  H2: Orquestador MVP
ETAPA B · Soluciones y negocio (se planifica en detalle al cerrar H2)
  S1 Catálogo y Cotizador ─▶ S2 Provisionamiento ─▶ S3 Lead Capture Starter ─▶ S4 Mensajería ─▶ S5 Media Studio ─▶ S6 Operación comercial
```

Por qué este orden: cotizar, desplegar o vender plantillas sin un orquestador confiable (estados, políticas,
aprobaciones, auditoría, costos) obligaría a rehacerlo todo. El orquestador es el producto base; las
soluciones son "programas" que corren sobre él.

### Hitos

| Hito | Al cerrar | Qué demuestra |
|---|---|---|
| **H1 Base técnica** | F0 | Repo reproducible, circuito app → API → BD/Redis, CI verde, login |
| **H1.5 Multi‑workspace seguro** | F1 | Aislamiento probado entre usuarios |
| **H2 Orquestador MVP** | O6 | Describir → planificar → aprobar → ejecutar → ver en vivo → ver costo, con conectores reales |
| **H3 MVP comercial** | S3 | Lead Capture Starter vendible |
| **H4 Expansión** | S6 | Canales, media y operación con márgenes medidos |

## 2. Reglas de trabajo

1. **Definición de listo (DoR)** de una tarea: objetivo claro, criterio de aceptación verificable, dependencias resueltas, diseño UX aprobado si toca pantalla.
2. **Definición de terminado (DoD)** de una tarea: código + pruebas + lint verde en CI, documentación actualizada, contrato OpenAPI regenerado si cambió, revisado en PR, ticket Jira cerrado.
3. **Una rama por ticket:** `AICC-123-descripcion-corta`. Commits con convención (`feat:`, `fix:`…) e incluyen la clave Jira.
4. **Nada de dependencias "por si acaso".** Cada paquete entra con el ticket que lo necesita.
5. **Medición local en cada gate:** se ejecuta el protocolo de [entorno-local.md](../environment/entorno-local.md) y se agrega una fila a la tabla de resultados para comparar fases.
6. **Decisión importante = ADR** antes del código.

---

## F0 · Fundamentos

**Objetivo:** repositorio reproducible y circuito mínimo funcionando. Detalle ampliado en [fase-0-fundamentos.md](fase-0-fundamentos.md).

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| F0-OPS-01 | OPS | Monorepo, `.gitignore`, `.env.example`, `.gitattributes`, README | Clonar no expone secretos ✅ (hecho) |
| F0-OPS-02 | OPS | Publicar en GitHub (privado) + protección de `main` | PR obligatorio para `main` |
| F0-OPS-03 | OPS | `docker-compose.yml`: PostgreSQL 16 + Redis 7 en `127.0.0.1` con healthchecks | Ambos *healthy* ✅ (hecho) |
| F0-OPS-04 | OPS | Medición base del entorno (línea 0) con `scripts/medir-entorno.sh` | Fila "F0‑base" en entorno-local.md ✅ (hecho) |
| F0-OPS-06 | OPS | Decidir ubicación del repo (fuera de OneDrive o exclusiones) y cambiar Flutter a stable | Documentado en entorno-local.md ✅ (hecho) |
| F0-BE-01 | BE | Proyecto `backend/` con `uv`, Python 3.12, FastAPI, `/health` | 200 + `/docs` ✅ (hecho) |
| F0-BE-02 | BE | `core/config.py` (pydantic‑settings) con falla explícita | Test: sin `DATABASE_URL` → error claro ✅ (hecho) |
| F0-BE-03 | BE | SQLAlchemy 2 async (asyncpg) + Alembic; migración inicial vacía | `alembic upgrade head` OK ✅ (hecho) |
| F0-BE-04 | BE | `/health/ready` comprueba BD y Redis | Test con servicios arriba/abajo ✅ (hecho) |
| F0-BE-05 | BE | Logging estructurado JSON con `request_id` | Cada respuesta lleva `X-Request-ID` ✅ (hecho) |
| F0-BE-06 | BE | Exportar OpenAPI a `shared/contracts/openapi.json` | Script + verificación en CI ✅ (hecho) |
| F0-APP-01 | APP | Flutter stable, `apps/mobile` con `com.treetech.aicc` | Corre en emulador Android ✅ (hecho) |
| F0-APP-02 | APP | Esqueleto `lib/` (app, core, features) + `AICC_API_BASE_URL` | Ver incremento M0 ✅ (hecho) |
| F0-APP-03 | APP | Pantalla de estado de conexión (M0) | OK / timeout / caída sin bloquear |
| F0-UX-01 | UX | Principios UX, arquitectura de información y mapa de pantallas | Documento aprobado ✅ (hecho) |
| F0-UX-02 | UX | Tokens de diseño (color, tipografía, espaciado, estados) + tema claro/oscuro | `app/theme/` refleja tokens |
| F0-SEC-01 | SEC | Auth propia: `users`, hash Argon2, access JWT 15 min + refresh rotatorio | Tests de expiración/rotación/reuso |
| F0-SEC-02 | SEC | CORS restringido, límite de body, rate limit básico | Tests |
| F0-APP-04 | APP | Login + `flutter_secure_storage` + Riverpod + GoRouter (M1) | Login → Home |
| F0-OPS-05 | OPS | CI GitHub Actions: backend (ruff, pytest con servicios) y mobile (analyze, test) | CI verde |
| F0-DOC-01 | DOC | ADR‑001..006 aceptados (004: uv/Python 3.12, 005: cola, 006: auth propia) | Revisados ✅ (hecho) |

**Gate F0 (H1):** DoD de la sección 15 de la guía + CI verde + login desde Android + medición F0 registrada. Tag `v0.1.0`.

---

## F1 · Identidad y Workspace

**Objetivo:** cada usuario trabaja dentro de un workspace aislado con roles, proyectos y ambientes.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| F1-BE-01 | BE | Modelos `workspaces`, `memberships(role)`, `projects`, `environments` + migraciones | Migración reversible |
| F1-BE-02 | BE | Al registrarse se crea workspace personal + proyecto "General" + env `development` | Test |
| F1-SEC-01 | SEC | Dependencia `current_workspace` que resuelve por membresía (header `X-Workspace-Id` validado) | Test: ID ajeno → 404 |
| F1-SEC-02 | SEC | Roles `owner`, `admin`, `operator`, `viewer` con matriz de permisos en código | Tabla de permisos documentada + tests |
| F1-SEC-03 | SEC | Suite de pruebas de aislamiento multi‑tenant (fixture con 2 usuarios/2 workspaces) | Se ejecuta en CI siempre |
| F1-BE-03 | BE | `audit_logs` + helper `audit()` usado en cada comando | Cada endpoint de escritura audita |
| F1-BE-04 | BE | CRUD: workspaces, projects, environments, members (invitar por email: solo registro, sin envío aún) | OpenAPI actualizado |
| F1-APP-01 | APP | Selector de workspace / proyecto / ambiente siempre visible (M2) | Cambio de contexto en 1 toque |
| F1-APP-02 | APP | Pantalla Actividad (lista de audit log) | Paginada |
| F1-UX-01 | UX | Patrón "contexto actual" (chip superior) y "cambiar contexto" (bottom sheet) | Prototipo aprobado |
| F1-DOC-01 | DOC | ADR‑010 Workspace lógico ≠ infraestructura | Aceptado |

**Gate F1 (H1.5):** suite de aislamiento 100 % verde; un usuario no puede leer, listar ni modificar nada de otro workspace.

---

## O1 · Tareas (sin IA todavía)

**Objetivo:** el ciclo de vida de una Task existe, es estricto y se ve en la app. Aún no hay planner.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O1-BE-01 | BE | Modelo `tasks` (title, description, status, project_id, environment_id, created_by, version) | Migración |
| O1-BE-02 | BE | `domain/tasks/state_machine.py` con tabla de transiciones explícita | Test por cada transición válida e inválida |
| O1-BE-03 | BE | Tabla `events` append‑only; cada transición escribe event + audit en la misma transacción | Test transaccional |
| O1-BE-04 | BE | Endpoints `POST/GET /tasks`, `GET /tasks/{id}`, `POST /tasks/{id}/cancel` | Contrato OpenAPI |
| O1-BE-05 | BE | Bloqueo optimista (`version`) → 409 en conflicto | Test de concurrencia |
| O1-APP-01 | APP | Command Center v1: campo "¿Qué necesitas?" que crea Task en DRAFT (M3) | Crear en < 3 toques |
| O1-APP-02 | APP | Lista de tareas con filtro por estado y tarjeta de estado | Estados con color + icono + texto |
| O1-UX-01 | UX | Diseño del Command Center y de la "tarjeta de tarea" (componente central) | Prototipo interactivo aprobado |
| O1-UX-02 | UX | Diccionario de estados en lenguaje de negocio ("Borrador", "Esperando tu aprobación"…) | Documento de copy |

**Gate O1:** se crea, lista, cancela una tarea desde la app; ninguna transición ilegal es posible.

---

## O2 · Planner y catálogo de capabilities

**Objetivo:** una Task en DRAFT recibe un **plan estructurado y validado**; nada se ejecuta.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O2-BE-01 | BE | Catálogo de capabilities en código (registro + JSON Schema + risk_level) con 3 iniciales: `llm.generate`, `http.get_allowlisted`, `notify.in_app` | `GET /capabilities` |
| O2-BE-02 | BE | `AgentRuntime` + `FakeRuntime` determinista para pruebas | Tests sin red |
| O2-BE-03 | BE | Primer proveedor LLM real detrás de `AgentRuntime` (clave solo en backend) | Smoke test manual |
| O2-BE-04 | BE | Planner: prompt versionado + salida estructurada (Pydantic) | Plan válido con FakeRuntime |
| O2-BE-05 | BE | Validador determinista del plan (capability existe, schema, DAG acíclico, límites) | Tests de planes maliciosos/rotos |
| O2-BE-06 | BE | `plans` y `plan_steps` versionados; `POST /tasks/{id}/plan`, `GET /plans/{id}` | Contrato |
| O2-BE-07 | BE | Estimador de costo por step (tokens estimados × tarifa fechada) | Costo visible en plan |
| O2-SEC-01 | SEC | Defensa ante *prompt injection*: el texto del usuario nunca se interpola en instrucciones del sistema sin delimitar; salida siempre validada | Casos de prueba documentados |
| O2-APP-01 | APP | Vista "Propuesta de plan": pasos en lenguaje natural, costo estimado, supuestos (M4) | Entendible sin conocimientos técnicos |
| O2-UX-01 | UX | Patrón "plan como lista de pasos" con detalle técnico plegable | Prototipo aprobado |
| O2-DOC-01 | DOC | ADR‑007 contrato del plan; ADR‑012 el LLM solo propone | Aceptados |

**Gate O2:** 20 descripciones de prueba → 100 % de planes válidos o rechazados con razón; ningún plan contiene una capability inexistente.

---

## O3 · Políticas y aprobaciones

**Objetivo:** cada plan se evalúa con reglas deterministas y las acciones sensibles exigen aprobación humana.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O3-BE-01 | BE | Policy Engine (`allow/deny/require_approval` + reason + policy_id) | Tabla de decisiones probada |
| O3-BE-02 | BE | Tabla `policies` por workspace (sobrescribe valores por defecto, nunca relaja `destructive`) | Tests |
| O3-BE-03 | BE | `approvals` + endpoints approve / reject / request‑changes | Auditado |
| O3-BE-04 | BE | `request-changes` genera Plan v2 conservando historial | Diff entre versiones |
| O3-SEC-01 | SEC | Solo `owner/admin/operator` aprueban; nadie aprueba su propio plan si la política exige 2 personas (opcional por workspace) | Tests |
| O3-APP-01 | APP | Bandeja de Aprobaciones con badge y acciones aprobar / rechazar / pedir cambios (M5) | 1 toque + confirmación |
| O3-APP-02 | APP | Confirmación reforzada para acciones `spend`/`write_external` (deslizar para aprobar) | Prueba de usabilidad |
| O3-UX-01 | UX | Patrón de aprobación: qué pasará, cuánto cuesta, qué se puede deshacer | Prototipo aprobado |
| O3-DOC-01 | DOC | ADR‑008 Policy Engine propio (sin OPA en MVP); ADR‑014 aprobación antes de gastar | Aceptados |

**Gate O3:** ningún plan con step `write_external`/`spend` llega a APPROVED sin approval registrada.

---

## O4 · Ejecución en vivo

**Objetivo:** un plan aprobado se ejecuta fuera de HTTP y el usuario lo sigue en tiempo real.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O4-BE-01 | BE | Cola Redis + worker (ADR‑005, preferencia arq) como servicio en Compose | Worker *healthy* |
| O4-BE-02 | BE | `runs` y `step_runs` con idempotency key, reintentos, timeouts | Tests de fallo y reintento |
| O4-BE-03 | BE | Ejecutor de DAG: resolución de `{{steps.x.output}}`, re‑evaluación de política por step | Tests |
| O4-BE-04 | BE | Pausas: `AWAITING_STEP_APPROVAL`, `WAITING_INPUT`; reanudar | Tests |
| O4-BE-05 | BE | Cancelación cooperativa + reaper de runs huérfanos | Test matando el worker |
| O4-BE-06 | BE | SSE `GET /tasks/{id}/events` con `Last-Event-ID` | Reconexión sin perder eventos |
| O4-BE-07 | BE | `artifacts` (texto/JSON en BD; archivos en almacenamiento local por ahora) | Descargables |
| O4-APP-01 | APP | Vista de ejecución en vivo: línea de tiempo de pasos con progreso (M6) | Actualiza sin refrescar |
| O4-APP-02 | APP | Visor de artefactos + notificación in‑app al terminar | — |
| O4-UX-01 | UX | Patrón "línea de tiempo viva" y estados de error recuperables | Prototipo aprobado |
| O4-OPS-01 | OPS | Medición: latencia de encolado, tiempo por step, RAM del worker | Fila O4 en entorno-local.md |

**Gate O4:** 50 ejecuciones con FakeRuntime + conectores falsos, incluidos fallos inyectados → 0 estados inconsistentes.

---

## O5 · Conectores reales

**Objetivo:** el orquestador actúa sobre el mundo exterior de forma controlada.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O5-BE-01 | BE | Interfaz `Connector` común (auth, timeout, reintentos, telemetría, errores normalizados) | Documentada |
| O5-BE-02 | BE | `provider_connections` con `secret_ref`; secretos cifrados (clave maestra en env en dev; KMS/Vault en prod) | Ningún secreto en tablas de negocio |
| O5-BE-03 | BE | `http.request` con allowlist de dominios por workspace | Test SSRF (IPs privadas bloqueadas) |
| O5-BE-04 | BE | `email.send` (proveedor transaccional en modo sandbox) | Envío real a cuenta de prueba |
| O5-BE-05 | BE | `n8n.trigger_workflow` contra n8n local en Docker | Workflow de ejemplo ejecutado |
| O5-BE-06 | BE | Cliente MCP: exponer herramientas de un servidor MCP como capabilities (allowlist) | 1 servidor MCP de prueba |
| O5-APP-01 | APP | Pantalla Conectores: estado, probar conexión, desconectar (M7) | — |
| O5-UX-01 | UX | Patrón "conectar servicio" en 3 pasos | Prototipo aprobado |
| O5-OPS-01 | OPS | n8n en Compose (perfil `connectors`) | Arranca con `docker compose --profile connectors up` |
| O5-DOC-01 | DOC | ADR‑017 licencia n8n (uso interno validado) | Aceptado |

**Gate O5:** la tarea demo "Resume los leads de prueba y mándame un email" se ejecuta de punta a punta con aprobación.

---

## O6 · Consumo, presupuesto y observabilidad

**Objetivo:** cada ejecución tiene costo medido, límites y métricas; el usuario ve todo en lenguaje de negocio.

| Código | Frente | Paso | Criterio de aceptación |
|---|---|---|---|
| O6-BE-01 | BE | `usage_events` desde AgentRuntime y conectores | Costo por run |
| O6-BE-02 | BE | `budgets` por workspace/proyecto/run con umbrales 70/90/100 % | Pausa automática al 100 % |
| O6-BE-03 | BE | `GET /usage/summary`, `GET /budgets` | Contrato |
| O6-BE-04 | BE | Comparación estimado vs. real por run | Reporte |
| O6-OPS-01 | OPS | Métricas Prometheus (`/metrics`) + Grafana local opcional (perfil `observability`) | Dashboard básico |
| O6-APP-01 | APP | Home / Dashboard: tareas activas, aprobaciones pendientes, gasto del mes (M8) | Todo de un vistazo |
| O6-APP-02 | APP | Pantalla Consumo con barra de presupuesto | — |
| O6-UX-01 | UX | Revisión completa de usabilidad con 3–5 personas | Hallazgos corregidos |
| O6-DOC-01 | DOC | ADR‑015 medición estimado/real; manual de usuario v1 | Publicado |

**Gate O6 (H2 · Orquestador MVP):** demo completa grabada; medición O6 comparada con F0; revisión de seguridad interna (checklist OWASP ASVS nivel 1).

---

## Etapa B · Soluciones (planificación de alto nivel)

Se detallará al cerrar H2 con los aprendizajes reales. Resumen tomado de la guía (secciones 19–36):

| Fase | Entregable | Puerta |
|---|---|---|
| S1 Catálogo y Cotizador | Solution Templates versionadas, perfiles de carga, `quotes` + `quote_items`, comparador determinista | Costos y supuestos visibles antes de desplegar |
| S2 Provisionamiento | `InfrastructureProvider` (Docker/VPS primero), `provisioning_jobs`, ciclo de vida, BYOC | Idempotente, health check, rollback |
| S3 Lead Capture Starter | Webhook → n8n → BD → dedupe → notificación | Pruebas end‑to‑end; vendible (H3) |
| S4 Mensajería | Email en producción; WhatsApp: piloto controlado → Cloud API oficial | Consentimiento, escalamiento humano |
| S5 Media Studio | Pipeline de video por etapas con cotización por trabajo | Costo por etapa y límite de regeneración |
| S6 Operación comercial | Planes Starter/Managed/Business, facturación, soporte | Margen medido en pilotos (H4) |

## 3. Registro de ADRs planificados

| ADR | Tema | Fase |
|---|---|---|
| 001–003 | Monolito modular · Flutter · PostgreSQL | F0 |
| 004 | uv + Python 3.12 | F0 |
| 005 | Biblioteca de cola (arq / Dramatiq / Celery) | F0 (decisión) / O4 (uso) |
| 006 | Autenticación propia con JWT | F0 |
| 007 | Contrato del plan | O2 |
| 008 | Policy Engine propio | O3 |
| 009 | SSE para tiempo real (vs. WebSocket) | O4 |
| 010–017 | Ver [decisions/README.md](../decisions/README.md) | F1–S4 |

## 4. Riesgos transversales

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Alcance crece antes de H2 | Alta | Alto | Este plan es la frontera; todo lo nuevo va a Jira como "Etapa B" |
| LLM produce planes inválidos | Media | Medio | Validador determinista + FakeRuntime + métricas de rechazo |
| Prompt injection vía datos externos | Media | Alto | Datos externos nunca como instrucciones; capabilities con allowlist; aprobación humana |
| Fuga de secretos | Baja | Crítico | Secret refs, escaneo de secretos en CI (gitleaks), nada en Flutter |
| Solo Windows (sin iOS) | Cierta | Medio | Android primero; iOS cuando haya macOS o CI con runner macOS |
| Flutter en canal `main` | Cierta | Medio | Cambiar a stable en F0 |
| Trabajo en carpeta OneDrive | Media | Medio | Excluir `.venv`, `build`, `.dart_tool` de la sincronización o mover el repo fuera de OneDrive |
