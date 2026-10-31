# AICC backend

FastAPI (monolito modular) + SQLAlchemy 2 async (asyncpg) + Alembic + Redis. Python 3.12 gestionado con `uv` (ADR‑004).

## Arranque

Desde la raíz del repo, levanta PostgreSQL y Redis (`docker compose up -d`) y copia `.env.example` a `.env`.

```bash
cd backend
uv sync                                   # crea .venv con Python 3.12 y dependencias exactas de uv.lock
uv run alembic upgrade head               # aplica migraciones
uv run uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

- `http://127.0.0.1:8000/health`: la API está viva (no toca dependencias).
- `http://127.0.0.1:8000/health/ready`: BD y Redis responden (200) o no (503, con el detalle por dependencia).
- `http://127.0.0.1:8000/docs`: documentación interactiva, solo en `development` y `test`.

## Verificación

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest                              # incluye pruebas de integración (requieren docker compose)
uv run pytest -m "not integration"         # sin servicios
uv run python scripts/export_openapi.py    # regenera shared/contracts/openapi.json tras cambiar la API
```

## Estructura

```
app/
├── main.py              create_app(): lifespan (engine, sesiones, Redis), middlewares, routers
├── core/                config (pydantic-settings), logging JSON, middleware X-Request-ID
├── api/                 health.py · v1/ (rutas de negocio desde 0B)
└── infrastructure/      database.py (engine, Base, sesión) · redis.py
migrations/              Alembic (async); la URL sale de DATABASE_URL, nunca de alembic.ini
scripts/export_openapi.py
tests/
```

Los módulos `domain/`, `application/`, `orchestration/` y `workers/` se crean cuando exista su primera responsabilidad real (F1/O1/O4).

## Notas de Windows

- `.env` usa `127.0.0.1` y no `localhost`: `localhost` se resuelve primero a `::1` y Docker publica solo IPv4, lo que añade unos 2 s por conexión.
- El driver es **asyncpg**: psycopg en modo async no funciona con el `ProactorEventLoop` por defecto de Windows.
