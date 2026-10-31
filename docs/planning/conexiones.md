# Conexiones, cuentas y accesos pendientes

Lista única de lo que **solo tú puedes autorizar** (cuentas, licencias, claves). Cada fila dice para qué se
usa y en qué sprint se necesita. Estado revisado el 2026‑10‑31 (tarde).

## Conectores de Claude (para que Claude trabaje directamente en esas herramientas)

| Conector | Estado | Para qué en AICC | Se necesita en | Cómo autorizar |
|---|---|---|---|---|
| **Atlassian (Jira + Confluence)** | ✅ Conectado (sitio `mrrobotqr.atlassian.net`) | Backlog, sprints y tickets; docs en Confluence | **Ya** | Falta crear el proyecto Scrum `AICC` (el conector no crea proyectos; ver abajo) |
| **Figma** | ✅ Conectado (equipo Starter, asiento View) | Diagramas en FigJam ([figma.md](../design/figma.md)); pantallas M2+ | S2 | Reclamar los 4 diagramas; para editar pantallas desde Claude puede hacer falta asiento Full/Dev |
| GitHub (conector) | ⛔ Sin autorizar | Opcional: el CLI `gh` ya funciona con tu cuenta `MrFtyoQr` | — | No hace falta por ahora |
| Google Drive | ✅ Conectado | Opcional: copia de documentos para compartir con no técnicos | — | — |

### Crear el proyecto `AICC` en Jira (1 minuto, solo tú puedes)

1. Abre https://mrrobotqr.atlassian.net → **Proyectos → Crear proyecto**.
2. Plantilla **Scrum** (no Kanban: KAN "TreeTechStudio" es Kanban y no admite sprints).
3. Nombre **AI Command Center**, clave **AICC**, tipo *gestionado por el equipo*.
4. Avísame: cargo epics, historias, subtareas y sprints con el conector.

## Cuentas y claves del producto (las usa el backend, nunca la app)

| Recurso | Estado | Para qué | Se necesita en | Acción tuya |
|---|---|---|---|---|
| Licencias del SDK de Android + `cmdline-tools` | ⚠️ Pendiente | `flutter doctor` limpio; algunas compilaciones futuras pueden requerirlo | S1 | `flutter doctor --android-licenses` (aceptar términos) e instalar *Android SDK Command-line Tools* desde Android Studio → SDK Manager |
| Protección de rama `main` en GitHub | ⚠️ Repo ya público: falta activar el ruleset | Impedir pushes directos y exigir CI verde | S1 (HU‑05) | Activar el ruleset de [proteccion-main.md](proteccion-main.md) (o autorizarme a crearlo) |
| Clave de proveedor LLM (Anthropic) | ⏳ Futuro | Primer `AgentRuntime` real (O2‑BE‑03) | S5 | Crear clave en console.anthropic.com con límite de gasto; se guardará en `.env` del backend |
| Proveedor de email transaccional (modo sandbox) | ⏳ Futuro | Capacidad `email.send` (O5‑BE‑04) | S10 | Elegir proveedor (Resend, Postmark o Mailgun) y crear cuenta de prueba |
| n8n | ✅ Sin cuenta | Corre local en Docker (O5) | S11 | Ninguna; revisar licencia antes de ofrecerlo a clientes (ADR‑017) |
| macOS / Xcode | ⛔ No disponible | Compilar y probar iOS | Cuando se decida publicar en iOS | Mac propio o runner macOS en CI |

## Qué haré cuando autorices Atlassian

1. Crear (o usar) el proyecto `AICC` tipo Scrum con los 6 componentes.
2. Cargar los 8 epics, 41 historias y 91 subtareas del backlog, con sprint y puntos.
3. Crear los sprints S0–S13; cerrar S0 con sus 4 historias en *Done*.
4. Desde ese momento, cada PR enlazará su clave `AICC-n` y el ticket se moverá al avanzar.
