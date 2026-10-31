import asyncio
from collections.abc import Callable, Coroutine, Iterator
from pathlib import Path
from typing import Any

import asyncpg
import pytest
import redis
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DB = "aicc_test"
TEST_JWT_SECRET = "test-secret-only-for-pytest-0123456789abcdef"
TABLES = (
    "events",
    "tasks",
    "audit_logs",
    "invitations",
    "environments",
    "projects",
    "memberships",
    "workspaces",
    "refresh_tokens",
    "users",
)

# Puertos donde no escucha nadie: las conexiones fallan al instante.
UNREACHABLE = Settings(
    _env_file=None,
    app_env="test",
    database_url="postgresql+asyncpg://aicc:x@127.0.0.1:1/aicc",
    redis_url="redis://127.0.0.1:1/0",
    jwt_secret=TEST_JWT_SECRET,
    dependency_timeout_s=1.0,
)


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    """Ejecuta código async de preparación fuera del event loop de TestClient."""
    return asyncio.run(coro)


@pytest.fixture
def offline_client() -> Iterator[TestClient]:
    """API sin dependencias disponibles; sirve para pruebas que no tocan BD ni Redis."""
    with TestClient(create_app(UNREACHABLE)) as client:
        yield client


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Configuración real (de .env o del entorno de CI) apuntando a la base aislada aicc_test."""
    base = get_settings()
    url = make_url(base.database_url).set(database=TEST_DB)
    return base.model_copy(
        update={
            "app_env": "test",
            "database_url": url.render_as_string(hide_password=False),
            "jwt_secret": TEST_JWT_SECRET,
        }
    )


@pytest.fixture(scope="session")
def migrated_db(test_settings: Settings) -> str:
    """Recrea aicc_test y comprueba que las migraciones suben, bajan y vuelven a subir."""
    url = make_url(test_settings.database_url)

    async def recreate() -> None:
        conn = await asyncpg.connect(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            database="postgres",
        )
        try:
            await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')
            await conn.execute(f'CREATE DATABASE "{TEST_DB}"')
        finally:
            await conn.close()

    run(recreate())
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", test_settings.database_url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    return test_settings.database_url


@pytest.fixture
def db(migrated_db: str) -> Callable[[Callable[[AsyncSession], Coroutine]], Any]:
    """Vacía las tablas y devuelve un helper para consultar la BD desde las pruebas."""

    def query(fn: Callable[[AsyncSession], Coroutine]) -> Any:
        async def go() -> Any:
            engine = create_async_engine(migrated_db, poolclass=NullPool)
            try:
                async with AsyncSession(engine, expire_on_commit=False) as session:
                    return await fn(session)
            finally:
                await engine.dispose()

        return run(go())

    async def truncate(session: AsyncSession) -> None:
        await session.execute(text(f"TRUNCATE {', '.join(TABLES)} CASCADE"))
        await session.commit()

    query(truncate)
    return query


def clear_rate_limits(settings: Settings) -> None:
    r = redis.Redis.from_url(settings.redis_url)
    try:
        keys = list(r.scan_iter("rl:*"))
        if keys:
            r.delete(*keys)
    finally:
        r.close()


@pytest.fixture
def client(test_settings: Settings, db) -> Iterator[TestClient]:
    """API conectada a la base aislada y al Redis de docker compose (o de CI)."""
    clear_rate_limits(test_settings)
    with TestClient(create_app(test_settings)) as c:
        yield c
