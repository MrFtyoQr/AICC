import uuid

import jwt
import pytest

from app.core import security

SECRET = "unit-test-secret-0123456789abcdefghij"


def test_password_round_trip():
    hashed = security.hash_password("clave-correcta-123")

    assert security.verify_password("clave-correcta-123", hashed)
    assert not security.verify_password("clave-incorrecta-123", hashed)


def test_verify_without_hash_is_false_but_still_runs():
    assert security.verify_password("lo-que-sea", None) is False


def test_corrupted_hash_is_rejected_without_exception():
    assert security.verify_password("x", "no-es-un-hash") is False


def test_access_token_round_trip():
    user_id = uuid.uuid4()
    token = security.create_access_token(user_id, secret=SECRET, issuer="aicc-api", ttl_s=60)

    assert security.decode_access_token(token, secret=SECRET, issuer="aicc-api") == user_id


def test_token_of_another_type_is_rejected():
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": "aicc-api",
            "iat": 0,
            "exp": 9_999_999_999,
            "type": "refresh",
        },
        SECRET,
        algorithm="HS256",
    )

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(forged, secret=SECRET, issuer="aicc-api")


def test_unsigned_token_is_rejected():
    forged = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": "aicc-api",
            "iat": 0,
            "exp": 9_999_999_999,
            "type": "access",
        },
        key=None,
        algorithm="none",
    )

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(forged, secret=SECRET, issuer="aicc-api")


def test_refresh_tokens_are_unique_and_hash_is_stable():
    a, b = security.new_refresh_token(), security.new_refresh_token()

    assert a != b
    assert security.hash_refresh_token(a) == security.hash_refresh_token(a)
    assert len(security.hash_refresh_token(a)) == 64
