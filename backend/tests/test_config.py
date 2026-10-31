import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def clean_env(monkeypatch):
    for var in ("DATABASE_URL", "REDIS_URL", "APP_ENV"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.parametrize("missing", ["database_url", "redis_url"])
def test_missing_required_variable_fails_explicitly(clean_env, missing):
    values = {"database_url": "postgresql+asyncpg://u:p@h/db", "redis_url": "redis://h/0"}
    values.pop(missing)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **values)

    assert missing in str(error.value)


def test_unknown_environment_is_rejected(clean_env):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="prod", database_url="x", redis_url="y")


def test_interactive_docs_disabled_in_production(clean_env):
    settings = Settings(_env_file=None, app_env="production", database_url="x", redis_url="y")

    app = create_app(settings)

    assert app.docs_url is None
    assert app.openapi_url is None
