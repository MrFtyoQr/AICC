# Roadmap AICC por fases

Derivado de las secciones 14–17 y 34–35 de la [guía](../architecture/guia-inicializacion.md).
Cada fase solo empieza cuando la anterior cumple su criterio de salida.

## Visión en una línea

El usuario expresa el resultado que necesita; AICC lo convierte en una solución técnica y comercial
verificable (orquestar · generar · provisionar · administrar · optimizar).

## Principios que aplican a todas las fases

1. **Monolito modular + workers.** Nada de microservicios, Kubernetes ni Kafka hasta que la carga real lo exija.
2. **El LLM propone, el código decide.** Autorización, presupuestos y selección de proveedor son deterministas.
3. **Cotizar → aprobar → gastar.** Ningún recurso ni costo se crea sin aprobación explícita.
4. **Aislamiento por workspace** verificado en servidor en cada consulta.
5. **Secretos fuera del cliente y del repo**; referencias cifradas en BD.
6. **Incremental.** Cada dependencia o módulo entra cuando existe una responsabilidad real.

## Fases

| # | Fase | Entregable | Criterio de salida | Depende de |
|---|---|---|---|---|
| 0 | **Fundamentos** | Monorepo, Flutter, FastAPI `/health`, PostgreSQL + Redis en Compose, config por entorno, pruebas, CI, auth base | DoD de la sección 15 + CI verde + login funcional | — |
| 1 | **Workspace** | Workspaces, miembros/roles, proyectos, environments, audit log | Prueba automatizada: un usuario no puede leer recursos de otro workspace | 0 |
| 2 | **Command Center** | Chat de descubrimiento, tareas en `DRAFT`, `POST /tasks/plan`, Policy Engine, `AgentRuntime` con un proveedor | Ningún plan se ejecuta sin política + aprobación humana | 1 |
| 3 | **Catálogo y cotizador** | Solution Templates versionadas, perfiles de carga, comparador de proveedores, `quotes` + `quote_items`, budgets (70/90/100 %) | Costos, supuestos y fecha visibles antes de desplegar | 2 |
| 4 | **Provisionamiento** | Cola + primer worker, primer `InfrastructureProvider` (Docker/VPS), `provisioning_jobs` idempotentes, ciclo de vida | Despliegue idempotente, health check y rollback probados | 3 |
| 5 | **Primera solución** | *Lead Capture Starter*: webhook → n8n → almacenamiento → dedupe → notificación | Captura, deduplicación, notificación y pruebas end‑to‑end | 4 |
| 6 | **Mensajería** | `MessagingProvider` email; evaluación WhatsApp (piloto Evolution → Cloud API oficial) | Políticas, consentimiento, escalamiento humano y medición | 5 |
| 7 | **Media Studio** | Pipeline de video por etapas con estimación, generación y aprobación | Costo por etapa y límites de regeneración | 3, 4 |
| 8 | **Operación comercial** | Planes Starter/Managed/Business, facturación, soporte, alertas, métricas | Margen y costo de servicio medidos en pilotos | 5, 6 |

### Hitos de negocio

- **H1 – Base técnica (fin Fase 0):** circuito cliente → API → datos/cola → respuesta validado.
- **H2 – Plataforma segura (fin Fase 2):** multi‑workspace con planes propuestos y aprobados, sin ejecución.
- **H3 – MVP comercial (fin Fase 5):** Lead Capture Starter vendible a pequeños negocios (managed + BYOC).
- **H4 – Expansión (Fases 6–8):** canales, media y operación comercial con márgenes medidos.

## Fuera de alcance hasta nuevo aviso

Microservicios/K8s/Kafka · marketplace público · ejecución arbitraria de código · telefonía, publicación
automática o pagos reales en el primer incremento · multi‑tenancy empresarial avanzado · múltiples
proveedores de IA antes de tener `AgentRuntime` y un caso validado · precios publicados sin medir 3 perfiles de carga.

## Riesgos principales a vigilar

| Riesgo | Mitigación |
|---|---|
| Licencia n8n para uso comercial | ADR‑017: validar antes de ofrecer edición/hosting a clientes |
| WhatsApp no oficial (Baileys) puede caerse o bloquear cuentas | ADR‑016: canal intercambiable; solo piloto con consentimiento |
| Precios de proveedores cambian | Cotizaciones fechadas; nunca constantes en código |
| Desarrollo solo en Windows | iOS no se valida hasta disponer de macOS |
