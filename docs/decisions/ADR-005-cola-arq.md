# ADR-005: arq como cola de trabajos

**Estado:** Aceptado · **Fecha:** 2026-10-31 · **Uso:** O4

## Contexto
El worker debe ejecutar planes fuera de HTTP. El backend es asíncrono (FastAPI + SQLAlchemy async) y Redis ya es parte del stack.
Candidatas: arq (async nativo, mínimo), Dramatiq (sync, robusto), Celery (completo, pesado).

## Decisión
**arq** sobre Redis. Redis solo transporta el `run_id`; el estado vive en PostgreSQL (ADR-003).
La lógica de ejecución se aísla tras una interfaz `JobQueue` para poder sustituir la biblioteca.

## Consecuencias
- Un solo modelo de concurrencia (asyncio) en API y worker.
- Funcionalidades avanzadas (prioridades complejas, workflows de Celery) no están disponibles; no se necesitan en la Etapa A.
