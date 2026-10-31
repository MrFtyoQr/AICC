"""Casos de uso de autenticación: registro, login, rotación de refresh token y logout."""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.core.config import Settings
from app.infrastructure.models import RefreshToken, User

logger = logging.getLogger(__name__)


class EmailAlreadyRegistered(Exception):
    pass


class InvalidCredentials(Exception):
    """Mismo error para email inexistente, contraseña incorrecta o cuenta inactiva."""


class InvalidRefreshToken(Exception):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def register(self, email: str, password: str, display_name: str | None) -> User:
        user = User(
            email=email.strip().lower(),
            password_hash=security.hash_password(password),
            display_name=display_name,
        )
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise EmailAlreadyRegistered from exc
        return user

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.session.scalar(select(User).where(User.email == email.strip().lower()))
        # verify_password siempre ejecuta Argon2, exista o no el usuario.
        valid = security.verify_password(password, user.password_hash if user else None)
        if not (valid and user and user.is_active):
            raise InvalidCredentials
        if security.password_needs_rehash(user.password_hash):
            user.password_hash = security.hash_password(password)
        pair = await self._issue(user.id, family_id=uuid.uuid4())
        await self.session.commit()
        return pair

    async def refresh(self, raw_token: str) -> TokenPair:
        now = datetime.now(UTC)
        token = await self.session.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == security.hash_refresh_token(raw_token))
            .with_for_update()
        )
        if token is None:
            raise InvalidRefreshToken
        if token.revoked_at is not None:
            # Reutilización de un token ya rotado: posible robo. Se corta toda la sesión.
            await self._revoke_family(token.family_id, now)
            await self.session.commit()
            logger.warning("refresh token reuse detected", extra={"check": str(token.family_id)})
            raise InvalidRefreshToken
        user = await self.session.get(User, token.user_id)
        if token.expires_at <= now or user is None or not user.is_active:
            raise InvalidRefreshToken
        token.revoked_at = now
        pair = await self._issue(token.user_id, family_id=token.family_id)
        await self.session.commit()
        return pair

    async def logout(self, raw_token: str) -> None:
        token = await self.session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == security.hash_refresh_token(raw_token)
            )
        )
        if token is not None:
            await self._revoke_family(token.family_id, datetime.now(UTC))
            await self.session.commit()

    async def _issue(self, user_id: uuid.UUID, *, family_id: uuid.UUID) -> TokenPair:
        raw_refresh = security.new_refresh_token()
        self.session.add(
            RefreshToken(
                user_id=user_id,
                family_id=family_id,
                token_hash=security.hash_refresh_token(raw_refresh),
                expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_ttl_days),
            )
        )
        access = security.create_access_token(
            user_id,
            secret=self.settings.jwt_secret,
            issuer=self.settings.jwt_issuer,
            ttl_s=self.settings.access_token_ttl_s,
        )
        return TokenPair(access, raw_refresh, self.settings.access_token_ttl_s)

    async def _revoke_family(self, family_id: uuid.UUID, now: datetime) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
