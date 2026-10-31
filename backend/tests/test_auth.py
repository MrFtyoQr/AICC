import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from app.core import security
from app.infrastructure.models import RefreshToken, User
from tests.conftest import TEST_JWT_SECRET

pytestmark = pytest.mark.integration

PASSWORD = "una-clave-larga-segura"


def register(client, email="ana@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def login(client, email="ana@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Registro ---------------------------------------------------------------


def test_register_stores_only_an_argon2id_hash(client, db):
    response = register(client, email="Ana@Example.com")

    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"
    user = db(lambda s: s.scalar(select(User)))
    assert user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash


def test_register_rejects_duplicate_email_case_insensitive(client):
    register(client)

    response = register(client, email="ANA@example.com")

    assert response.status_code == 409


@pytest.mark.parametrize("password", ["corta", "x" * 129])
def test_register_enforces_password_length(client, password):
    assert register(client, password=password).status_code == 422


def test_register_rejects_invalid_email(client):
    assert register(client, email="no-es-un-email").status_code == 422


# --- Login ------------------------------------------------------------------


def test_login_returns_short_lived_access_and_refresh_tokens(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert body["refresh_token"]
    me = client.get("/api/v1/me", headers=bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"


def test_login_error_is_identical_for_wrong_password_and_unknown_email(client):
    register(client)

    wrong_password = login(client, password="otra-clave-larga-123")
    unknown_email = login(client, email="nadie@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_inactive_user_cannot_log_in(client, db):
    register(client)

    async def deactivate(session):
        await session.execute(update(User).values(is_active=False))
        await session.commit()

    db(deactivate)

    assert login(client).status_code == 401


# --- Refresh ----------------------------------------------------------------


def test_refresh_rotates_and_revokes_previous_token(client):
    register(client)
    first = login(client).json()

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})

    assert rotated.status_code == 200
    second = rotated.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/api/v1/me", headers=bearer(second["access_token"])).status_code == 200


def test_reusing_a_rotated_refresh_token_revokes_the_whole_family(client):
    register(client)
    first = login(client).json()
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()

    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    legit = client.post("/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]})

    assert reuse.status_code == 401
    assert legit.status_code == 401, "el token legítimo también debe quedar revocado"


def test_reuse_does_not_affect_other_sessions(client):
    register(client)
    phone = login(client).json()
    tablet = login(client).json()
    client.post("/api/v1/auth/refresh", json={"refresh_token": phone["refresh_token"]})

    client.post("/api/v1/auth/refresh", json={"refresh_token": phone["refresh_token"]})

    other = client.post("/api/v1/auth/refresh", json={"refresh_token": tablet["refresh_token"]})
    assert other.status_code == 200


def test_expired_refresh_token_is_rejected(client, db):
    register(client)
    tokens = login(client).json()

    async def expire(session):
        await session.execute(
            update(RefreshToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        await session.commit()

    db(expire)

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401


def test_unknown_refresh_token_is_rejected(client):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "x" * 43})

    assert response.status_code == 401


def test_refresh_tokens_are_stored_hashed(client, db):
    register(client)
    raw = login(client).json()["refresh_token"]

    stored = db(lambda s: s.scalar(select(RefreshToken.token_hash)))

    assert stored != raw
    assert stored == security.hash_refresh_token(raw)


# --- Logout -----------------------------------------------------------------


def test_logout_revokes_the_session(client):
    register(client)
    tokens = login(client).json()

    out = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    after = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert out.status_code == 204
    assert after.status_code == 401


# --- /me y tokens de acceso --------------------------------------------------


def test_me_requires_a_token(client):
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        "basura",
        security.create_access_token(
            uuid.uuid4(),
            secret="otra-clave-de-32-caracteres-minimo!!",
            issuer="aicc-api",
            ttl_s=60,
        ),
        security.create_access_token(
            uuid.uuid4(), secret=TEST_JWT_SECRET, issuer="aicc-api", ttl_s=-1
        ),
        security.create_access_token(
            uuid.uuid4(), secret=TEST_JWT_SECRET, issuer="otro-emisor", ttl_s=60
        ),
    ],
    ids=["mal-formado", "otra-firma", "vencido", "otro-emisor"],
)
def test_me_rejects_invalid_access_tokens(client, token):
    assert client.get("/api/v1/me", headers=bearer(token)).status_code == 401


def test_access_token_of_deleted_user_is_rejected(client, db):
    register(client)
    access = login(client).json()["access_token"]

    async def delete_all(session):
        await session.execute(User.__table__.delete())
        await session.commit()

    db(delete_all)

    assert client.get("/api/v1/me", headers=bearer(access)).status_code == 401
