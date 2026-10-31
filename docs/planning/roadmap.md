# Roadmap AICC (vista resumida)

El detalle paso a paso, con tareas y criterios por frente, está en el **[plan maestro](plan-maestro.md)**.
Esta página es la vista de una sola pantalla.

## Principios

1. **Primero orquestación.** La Etapa B (cotizar, desplegar, vender soluciones) no empieza hasta cerrar H2.
2. **El LLM propone, el código decide.** Autorización, presupuestos y selección de proveedor son deterministas.
3. **Cotizar/estimar → aprobar → gastar.**
4. **Aislamiento por workspace** verificado en servidor.
5. **Secretos fuera del cliente y del repo.**
6. **Incremental:** backend, app (M0–M8) y UX avanzan juntos por fase.

## Etapa A · Plataforma de orquestación

| Fase | Entregable | Gate | App |
|---|---|---|---|
| **F0** Fundamentos | Monorepo, FastAPI, Postgres/Redis, CI, auth base | H1: entorno reproducible, CI verde, login | M0–M1 |
| **F1** Identidad y Workspace | Workspaces, roles, proyectos, ambientes, auditoría | H1.5: aislamiento probado | M2 |
| **O1** Tareas | Task + máquina de estados + eventos | Ninguna transición ilegal posible | M3 |
| **O2** Planner | Capabilities, AgentRuntime, plan validado, estimación | 100 % planes válidos o rechazados con razón | M4 |
| **O3** Políticas y aprobaciones | Policy Engine, approvals, versiones de plan | Nada sensible sin aprobación | M5 |
| **O4** Ejecución en vivo | Cola, worker, runs, SSE, artefactos | 0 estados inconsistentes en 50 runs con fallos | M6 |
| **O5** Conectores | HTTP allowlist, email, n8n, MCP, secretos cifrados | Demo de punta a punta | M7 |
| **O6** Consumo y presupuesto | Usage, budgets, métricas, dashboard | **H2: Orquestador MVP** | M8 |

## Etapa B · Soluciones (se detalla al cerrar H2)

S1 Catálogo y cotizador → S2 Provisionamiento → S3 Lead Capture Starter (**H3**) → S4 Mensajería → S5 Media Studio → S6 Operación comercial (**H4**).

## Fuera de alcance hasta nuevo aviso

Microservicios/K8s/Kafka · marketplace público · ejecución arbitraria de código · telefonía, publicación
automática o pagos reales · multi‑tenancy empresarial avanzado · múltiples proveedores de IA antes de
validar `AgentRuntime` · precios publicados sin medir 3 perfiles de carga.
