"""HU-07: límites de tamaño, frecuencia y origen."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.conftest import UNREACHABLE, clear_rate_limits

LOGIN = {"email": "nadie@example.com", "password": "no-importa-123"}


def test_declared_oversized_body_is_rejected_with_413(offline_client):
    response = offline_client.post(
        "/api/v1/auth/login",
        content=b"{}",
        headers={"Content-Type": "application/json", "Content-Length": str(2_000_000)},
    )

    assert response.status_code == 413


def test_streamed_oversized_body_is_rejected_with_413():
    settings = UNREACHABLE.model_copy(update={"max_body_bytes": 100})

    def chunks() -> Iterator[bytes]:
        yield b'{"email": "a@b.com", "password": "'
        yield b"x" * 200
        yield b'"}'

    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/auth/login", content=chunks(), headers={"Content-Type": "application/json"}
        )

    assert response.status_code == 413


def test_body_within_limit_is_processed(offline_client):
    response = offline_client.post("/api/v1/auth/register", json={"email": "x"})

    assert response.status_code == 422


@pytest.mark.integration
def test_login_rate_limit_returns_429_with_retry_after(test_settings, db):
    settings = test_settings.model_copy(update={"rate_limit_login": 3})
    clear_rate_limits(settings)

    with TestClient(create_app(settings)) as client:
        statuses = [client.post("/api/v1/auth/login", json=LOGIN).status_code for _ in range(4)]
        last = client.post("/api/v1/auth/login", json=LOGIN)

    assert statuses[:3] == [401, 401, 401]
    assert statuses[3] == 429
    assert last.status_code == 429
    assert 0 < int(last.headers["retry-after"]) <= settings.rate_limit_window_s


@pytest.mark.integration
def test_limits_are_independent_per_endpoint(test_settings, db):
    settings = test_settings.model_copy(update={"rate_limit_login": 1})
    clear_rate_limits(settings)

    with TestClient(create_app(settings)) as client:
        client.post("/api/v1/auth/login", json=LOGIN)
        client.post("/api/v1/auth/login", json=LOGIN)
        refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": "x" * 43})

    assert refresh.status_code == 401, "refresh no comparte el contador de login"


def test_rate_limiter_fails_open_when_redis_is_down():
    # Sin Redis (puerto inalcanzable) el login no queda bloqueado por el limitador:
    # llega al caso de uso, que falla por la BD (500), nunca 429.
    settings = UNREACHABLE.model_copy(update={"rate_limit_login": 1})
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        responses = [client.post("/api/v1/auth/login", json=LOGIN) for _ in range(3)]

    assert all(r.status_code != 429 for r in responses)


def test_cors_allows_only_configured_origins():
    settings = UNREACHABLE.model_copy(update={"cors_origins": ["https://app.aicc.example"]})
    preflight = {"Access-Control-Request-Method": "POST"}

    with TestClient(create_app(settings)) as client:
        allowed = client.options(
            "/api/v1/auth/login", headers={"Origin": "https://app.aicc.example", **preflight}
        )
        denied = client.options(
            "/api/v1/auth/login", headers={"Origin": "https://evil.example", **preflight}
        )

    assert allowed.headers.get("access-control-allow-origin") == "https://app.aicc.example"
    assert "access-control-allow-origin" not in denied.headers


def test_no_cors_headers_when_no_origin_configured(offline_client):
    response = offline_client.get("/health", headers={"Origin": "https://evil.example"})

    assert "access-control-allow-origin" not in response.headers
