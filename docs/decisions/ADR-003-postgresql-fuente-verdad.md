# ADR-003: PostgreSQL como fuente de verdad

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
Usuarios, tareas, cotizaciones y auditoría necesitan consistencia transaccional y trazabilidad.

## Decisión
PostgreSQL es la única fuente de verdad; el esquema se gestiona con migraciones Alembic (no `create_all()`).
Redis se usa solo para cola, coordinación y cache; nada en Redis es irrecuperable.

## Consecuencias
- Historial de esquema controlado desde el inicio.
- Los workers deben poder reconstruir su estado desde PostgreSQL.
- Acceso con SQLAlchemy 2 async + **asyncpg** (2026-10-31): psycopg 3 en modo async no funciona con el `ProactorEventLoop` por defecto de Windows, que es el entorno de desarrollo.
