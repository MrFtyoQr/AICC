import pytest


def test_health_returns_expected_schema(offline_client):
    response = offline_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "aicc-api",
        "version": "0.1.0",
        "environment": "test",
    }


def test_every_response_carries_a_request_id(offline_client):
    response = offline_client.get("/health")

    assert len(response.headers["x-request-id"]) == 32


def test_valid_client_request_id_is_reused(offline_client):
    response = offline_client.get("/health", headers={"X-Request-ID": "app-123"})

    assert response.headers["x-request-id"] == "app-123"


def test_malformed_client_request_id_is_replaced(offline_client):
    response = offline_client.get("/health", headers={"X-Request-ID": "bad id\nwith newline"})

    assert response.headers["x-request-id"] != "bad id\nwith newline"


def test_ready_reports_degraded_without_dependencies(offline_client):
    response = offline_client.get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"]["status"] == "error"
    assert body["checks"]["redis"]["status"] == "error"


def test_ready_does_not_leak_connection_details(offline_client):
    body = offline_client.get("/health/ready").text

    assert "127.0.0.1" not in body
    assert "aicc:x" not in body


@pytest.mark.integration
def test_ready_ok_with_compose_services(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "database": {"status": "ok", "detail": None},
            "redis": {"status": "ok", "detail": None},
        },
    }
