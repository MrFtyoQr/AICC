import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app

VALID = {
    "database_url": "postgresql+asyncpg://u:p@h/db",
    "redis_url": "redis://h/0",
    "jwt_secret": "s" * 32,
}


@pytest.fixture
def clean_env(monkeypatch):
    for var in ("DATABASE_URL", "REDIS_URL", "APP_ENV", "JWT_SECRET"):
        monkeypatch.delenv(var, raising=False)


@pytest.mark.parametrize("missing", ["database_url", "redis_url", "jwt_secret"])
def test_missing_required_variable_fails_explicitly(clean_env, missing):
    values = {k: v for k, v in VALID.items() if k != missing}

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **values)

    assert missing in str(error.value)


def test_short_jwt_secret_is_rejected(clean_env):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{**VALID, "jwt_secret": "corto"})


def test_unknown_environment_is_rejected(clean_env):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="prod", **VALID)


def test_interactive_docs_disabled_in_production(clean_env):
    settings = Settings(_env_file=None, app_env="production", **VALID)

    app = create_app(settings)

    assert app.docs_url is None
    assert app.openapi_url is None
