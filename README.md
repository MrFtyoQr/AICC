# AICC — AI Command Center

Plataforma para descubrir una necesidad de negocio, diseñar una solución de IA, cotizarla,
desplegarla, administrarla y medir sus resultados desde una app móvil (centro de mando).

> **Estado:** Fase 0 — Fundamentos (planificación). Todavía no hay código ejecutable.

## Arquitectura resumida

```
Flutter (Android / iOS)  ──HTTPS/JSON/SSE──▶  FastAPI (monolito modular)
                                                  │            │
                                             PostgreSQL      Redis ──▶ Python Worker ──▶ Proveedores / MCP / n8n
```

- Flutter solo presenta estados y envía solicitudes; nunca guarda secretos de proveedores ni ejecuta trabajos largos.
- El backend impone identidad, autorización, políticas, presupuestos y auditoría con código determinista.
- Ningún LLM autoriza sus propias acciones: el modelo propone, el motor determinista valida y el usuario aprueba.

## Documentación

| Documento | Contenido |
|---|---|
| [Guía de inicialización v1.1](docs/architecture/guia-inicializacion.md) | Guía técnica completa + ampliación estratégica (fuente: [docx](docs/source/Guia_Inicializacion_AICC_v1.1.docx)) |
| [Roadmap por fases](docs/planning/roadmap.md) | Fases 0–8, entregables, criterios de salida y dependencias |
| [Plan de ejecución Fase 0](docs/planning/fase-0-fundamentos.md) | Tareas concretas, orden, DoD y decisiones abiertas |
| [ADRs](docs/decisions/README.md) | Registro de decisiones de arquitectura |

## Estructura objetivo del monorepo

```
apps/mobile/          Flutter (Android e iOS)
backend/              FastAPI + workers
shared/contracts/     OpenAPI exportado y ejemplos
infrastructure/       docker/, migrations/
docs/                 architecture/, decisions/, security/, api/, planning/
```

## Convención de commits

`feat:` · `fix:` · `chore:` · `docs:` · `test:` · `refactor:`
