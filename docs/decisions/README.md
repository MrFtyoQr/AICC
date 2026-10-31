# Architecture Decision Records

Formato: contexto → decisión → consecuencias. Estados: *Propuesto*, *Aceptado*, *Reemplazado*.

| ADR | Decisión | Estado | Fase |
|---|---|---|---|
| [001](ADR-001-monolito-modular.md) | Backend como monolito modular + workers separados | Propuesto | 0 |
| [002](ADR-002-flutter-cliente.md) | Flutter como cliente multiplataforma sin secretos ni trabajos largos | Propuesto | 0 |
| [003](ADR-003-postgresql-fuente-verdad.md) | PostgreSQL como fuente de verdad; Redis solo cola/cache | Propuesto | 0 |
| 010 | Workspace lógico separado de la infraestructura física | Pendiente | 1 |
| 011 | Modalidades AICC‑managed, BYOC e híbrida | Pendiente | 3 |
| 012 | Motor determinista compara proveedores; el LLM solo propone y explica | Pendiente | 2–3 |
| 013 | Despliegue desde plantillas versionadas y adaptadores | Pendiente | 3–4 |
| 014 | Cotización y aprobación preceden a cualquier gasto o provisionamiento | Pendiente | 3 |
| 015 | Medición de costo estimado y real por proveedor y workspace | Pendiente | 3 |
| 016 | Canal de mensajería intercambiable; WhatsApp no depende solo de conexión no oficial | Pendiente | 6 |
| 017 | Uso comercial de n8n validado contra su licencia | Pendiente | 5 |
