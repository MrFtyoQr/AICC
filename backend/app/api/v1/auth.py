import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import CurrentUser, SessionDep, SettingsDep
from app.application.auth import (
    AuthService,
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidRefreshToken,
    TokenPair,
)

router = APIRouter(tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - esquema OAuth2, no una credencial
    expires_in: int

    @classmethod
    def of(cls, pair: TokenPair) -> "TokenResponse":
        return cls(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            expires_in=pair.expires_in,
        )


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None


_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos"
)
_INVALID_REFRESH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión vencida; inicia sesión de nuevo"
)


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta",
    responses={409: {"description": "El email ya está registrado"}},
)
async def register(body: RegisterRequest, session: SessionDep, settings: SettingsDep):
    try:
        user = await AuthService(session, settings).register(
            body.email, body.password, body.display_name
        )
    except EmailAlreadyRegistered:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado") from None
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    responses={401: {"description": "Credenciales inválidas"}},
)
async def login(body: LoginRequest, session: SessionDep, settings: SettingsDep):
    try:
        pair = await AuthService(session, settings).login(body.email, body.password)
    except InvalidCredentials:
        raise _INVALID_CREDENTIALS from None
    return TokenResponse.of(pair)


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    summary="Rotar el refresh token y obtener un access token nuevo",
    responses={401: {"description": "Refresh token inválido, vencido o reutilizado"}},
)
async def refresh(body: RefreshRequest, session: SessionDep, settings: SettingsDep):
    try:
        pair = await AuthService(session, settings).refresh(body.refresh_token)
    except InvalidRefreshToken:
        raise _INVALID_REFRESH from None
    return TokenResponse.of(pair)


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar la sesión (revoca todos los refresh tokens de esa sesión)",
)
async def logout(body: RefreshRequest, session: SessionDep, settings: SettingsDep) -> None:
    await AuthService(session, settings).logout(body.refresh_token)


@router.get("/me", response_model=UserResponse, summary="Usuario autenticado")
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)
