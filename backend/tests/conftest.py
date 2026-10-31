from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app

# Puertos donde no escucha nadie: las conexiones fallan al instante.
UNREACHABLE = Settings(
    _env_file=None,
    app_env="test",
    database_url="postgresql+asyncpg://aicc:x@127.0.0.1:1/aicc",
    redis_url="redis://127.0.0.1:1/0",
    dependency_timeout_s=1.0,
)


@pytest.fixture
def offline_client() -> Iterator[TestClient]:
    """API sin dependencias disponibles; sirve para pruebas que no tocan BD ni Redis."""
    with TestClient(create_app(UNREACHABLE)) as client:
        yield client


@pytest.fixture
def live_client() -> Iterator[TestClient]:
    """API conectada al PostgreSQL y Redis de docker compose (lee el .env del repo)."""
    settings = get_settings().model_copy(update={"app_env": "test"})
    with TestClient(create_app(settings)) as client:
        yield client
