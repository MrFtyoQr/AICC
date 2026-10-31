# AICC — AI Command Center

Plataforma para descubrir una necesidad de negocio, diseñar una solución de IA, aprobarla, ejecutarla y
medir sus resultados desde una app móvil que funciona como centro de mando.

> **Estado:** F0 · bloque 0A. PostgreSQL + Redis en Docker, API FastAPI con `/health` y `/health/ready`, app Flutter M0 (estado de conexión).

## Arquitectura resumida

```
Flutter (Android / iOS)  ──HTTPS/JSON/SSE──▶  FastAPI (monolito modular)
                                                  │            │
                                             PostgreSQL      Redis ──▶ Worker ──▶ Conectores (LLM, HTTP, email, n8n, MCP)
```

- Flutter solo presenta estados y envía solicitudes; nunca guarda secretos ni ejecuta trabajos largos.
- El backend impone identidad, autorización, políticas, presupuestos y auditoría con código determinista.
- **El LLM propone, el código valida y la persona aprueba.**

## Arranque local

Requisitos: Git, Docker Desktop, [uv](https://docs.astral.sh/uv/) y Flutter **stable** con Android SDK.

```bash
# 1. Infraestructura
cp .env.example .env            # cambia POSTGRES_PASSWORD (y la misma en DATABASE_URL)
docker compose up -d
docker compose ps               # postgres y redis: healthy

# 2. API
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000

# 3. App (otra terminal, con el emulador Android abierto)
cd apps/mobile
flutter run --dart-define=AICC_API_BASE_URL=http://10.0.2.2:8000
```

**Todo en contenedores** (lo mismo que se despliega en la nube): `docker compose --profile app up -d --build`.

Detalles en [backend/README.md](backend/README.md) y [apps/mobile/README.md](apps/mobile/README.md).
Medición comparativa del entorno: `scripts/medir-entorno.sh <etiqueta>` y `cd backend && uv run python scripts/bench_api.py`.

## Documentación

| Documento | Para qué |
|---|---|
| [Plan maestro](docs/planning/plan-maestro.md) | **Documento rector**: fases, frentes, tareas, gates |
| [Roadmap](docs/planning/roadmap.md) | Vista de una pantalla |
| [Historias de usuario](docs/planning/historias-usuario.md) | 41 HU con criterios, puntos y tareas |
| [Sprints](docs/planning/sprints.md) | Calendario S0–S13, sprint actual y velocidad |
| [Conexiones pendientes](docs/planning/conexiones.md) | Lo que solo tú puedes autorizar y cuándo se necesita |
| [F0 · guía de ejecución](docs/planning/fase-0-fundamentos.md) | Orden exacto y decisiones de la fase actual |
| [Núcleo de orquestación](docs/architecture/orquestacion.md) | Modelo de dominio, estados, plan, políticas, worker, SSE |
| [App móvil incremental](docs/planning/app-movil-incremental.md) | Incrementos M0–M8 |
| [UX / UI](docs/ux/principios-ux.md) | Principios, navegación, flujos, componentes, copy |
| [Entorno local](docs/environment/entorno-local.md) | Arranque, protocolo de medición y resultados |
| [Contenedores y despliegue](docs/deployment/contenedores.md) | Por qué todo el backend va en Docker, imagen, Compose y nube |
| [Jira](docs/planning/jira/README.md) | Estructura del proyecto e importación del backlog |
| [ADRs](docs/decisions/README.md) | Decisiones de arquitectura |
| [Guía de inicialización v1.1](docs/architecture/guia-inicializacion.md) | Documento fuente ([docx](docs/source/Guia_Inicializacion_AICC_v1.1.docx)) |

## Convenciones

- Commits: `feat:` · `fix:` · `chore:` · `docs:` · `test:` · `refactor:` + clave Jira (`AICC-123`).
- Ramas: `AICC-123-descripcion-corta`. `main` protegida; todo entra por PR con CI verde.
