# Architecture Decision Records

Formato: contexto → decisión → consecuencias. Estados: *Propuesto*, *Aceptado*, *Reemplazado*.

| ADR | Decisión | Estado | Fase |
|---|---|---|---|
| [001](ADR-001-monolito-modular.md) | Backend como monolito modular + workers separados | Propuesto | F0 |
| [002](ADR-002-flutter-cliente.md) | Flutter como cliente multiplataforma sin secretos ni trabajos largos | Propuesto | F0 |
| [003](ADR-003-postgresql-fuente-verdad.md) | PostgreSQL como fuente de verdad; Redis solo cola/cache | Propuesto | F0 |
| 004 | uv + Python 3.12 como único mecanismo de dependencias | Pendiente | F0 |
| 005 | Biblioteca de cola (preferencia: arq) | Pendiente | F0 → O4 |
| 006 | Autenticación propia con JWT (access corto + refresh rotatorio) | Pendiente | F0 |
| 007 | Contrato estructurado del plan | Pendiente | O2 |
| 008 | Policy Engine propio en código (sin OPA en MVP) | Pendiente | O3 |
| 009 | SSE para tiempo real (vs. WebSocket) | Pendiente | O4 |
| 010 | Workspace lógico separado de la infraestructura física | Pendiente | F1 |
| 011 | Modalidades AICC‑managed, BYOC e híbrida | Pendiente | S1 |
| 012 | Motor determinista valida; el LLM solo propone y explica | Pendiente | O2 |
| 013 | Despliegue desde plantillas versionadas y adaptadores | Pendiente | S1–S2 |
| 014 | Aprobación precede a cualquier gasto o acción externa | Pendiente | O3 |
| 015 | Medición de costo estimado y real por proveedor y workspace | Pendiente | O6 |
| 016 | Canal de mensajería intercambiable; WhatsApp no depende solo de conexión no oficial | Pendiente | S4 |
| 017 | Uso comercial de n8n validado contra su licencia | Pendiente | O5 |
