# AICC — AI Command Center

Plataforma para descubrir una necesidad de negocio, diseñar una solución de IA, aprobarla, ejecutarla y
medir sus resultados desde una app móvil que funciona como centro de mando.

> **Estado:** F0 · Fundamentos. Infraestructura local (PostgreSQL + Redis) funcionando y medida; backend y app por iniciar.

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

Requisitos: Git, Docker Desktop. (Python 3.12 vía `uv` y Flutter stable entran en F0‑BE‑01 / F0‑APP‑01).

```bash
cp .env.example .env            # cambia POSTGRES_PASSWORD
docker compose up -d
docker compose ps               # postgres y redis: healthy
scripts/medir-entorno.sh mi-prueba   # opcional: medición comparativa
```

## Documentación

| Documento | Para qué |
|---|---|
| [Plan maestro](docs/planning/plan-maestro.md) | **Documento rector**: fases, frentes, tareas, gates |
| [Roadmap](docs/planning/roadmap.md) | Vista de una pantalla |
| [F0 · guía de ejecución](docs/planning/fase-0-fundamentos.md) | Orden exacto y decisiones de la fase actual |
| [Núcleo de orquestación](docs/architecture/orquestacion.md) | Modelo de dominio, estados, plan, políticas, worker, SSE |
| [App móvil incremental](docs/planning/app-movil-incremental.md) | Incrementos M0–M8 |
| [UX / UI](docs/ux/principios-ux.md) | Principios, navegación, flujos, componentes, copy |
| [Entorno local](docs/environment/entorno-local.md) | Arranque, protocolo de medición y resultados |
| [Jira](docs/planning/jira/README.md) | Estructura del proyecto e importación del backlog |
| [ADRs](docs/decisions/README.md) | Decisiones de arquitectura |
| [Guía de inicialización v1.1](docs/architecture/guia-inicializacion.md) | Documento fuente ([docx](docs/source/Guia_Inicializacion_AICC_v1.1.docx)) |

## Convenciones

- Commits: `feat:` · `fix:` · `chore:` · `docs:` · `test:` · `refactor:` + clave Jira (`AICC-123`).
- Ramas: `AICC-123-descripcion-corta`. `main` protegida; todo entra por PR con CI verde.
