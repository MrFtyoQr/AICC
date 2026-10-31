"""Primitivas criptográficas de autenticación (ADR-006). Sin estado ni acceso a BD."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()  # Argon2id con los parámetros recomendados por la biblioteca
# Hash válido de una contraseña aleatoria: se verifica contra él cuando el email no existe,
# para que el tiempo de respuesta no revele si una cuenta está registrada.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))

ACCESS_TOKEN_TYPE = "access"  # noqa: S105 - es un tipo de token, no una credencial


class InvalidTokenError(Exception):
    """El token está mal formado, vencido, firmado con otra clave o no es de acceso."""


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(
    user_id: uuid.UUID, *, secret: str, issuer: str, ttl_s: int, now: datetime | None = None
) -> str:
    now = now or datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iss": issuer,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_s),
        "jti": uuid.uuid4().hex,
        "type": ACCESS_TOKEN_TYPE,
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def decode_access_token(token: str, *, secret: str, issuer: str) -> uuid.UUID:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            options={"require": ["sub", "exp", "iat", "iss", "type"]},
        )
        if claims["type"] != ACCESS_TOKEN_TYPE:
            raise InvalidTokenError
        return uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidTokenError from exc


def new_refresh_token() -> str:
    """Token opaco de 256 bits. Solo se entrega al cliente; en BD se guarda su hash."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    # SHA-256 basta: el token ya tiene 256 bits de entropía, no es una contraseña.
    return hashlib.sha256(token.encode()).hexdigest()
