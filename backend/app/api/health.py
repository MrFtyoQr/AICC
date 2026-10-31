import asyncio
import logging
from collections.abc import Awaitable
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.infrastructure import database, redis

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


class Health(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str


class DependencyStatus(BaseModel):
    status: Literal["ok", "error"]
    detail: str | None = None


class Readiness(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, DependencyStatus]


@router.get("/health", response_model=Health, summary="La API está viva")
async def health(request: Request) -> Health:
    settings = request.app.state.settings
    return Health(
        status="ok", service="aicc-api", version=settings.app_version, environment=settings.app_env
    )


async def _check(name: str, probe: Awaitable[None], timeout_s: float) -> DependencyStatus:
    try:
        await asyncio.wait_for(probe, timeout=timeout_s)
        return DependencyStatus(status="ok")
    except Exception as exc:
        # Solo se expone el tipo de error: el mensaje puede contener host o credenciales.
        logger.warning("readiness check failed", extra={"check": name}, exc_info=exc)
        return DependencyStatus(status="error", detail=type(exc).__name__)


@router.get(
    "/health/ready",
    response_model=Readiness,
    summary="La API y sus dependencias están listas",
    responses={503: {"model": Readiness, "description": "Alguna dependencia no responde"}},
)
async def ready(request: Request, response: Response) -> Readiness:
    state = request.app.state
    timeout = state.settings.dependency_timeout_s
    db, rd = await asyncio.gather(
        _check("database", database.ping(state.engine), timeout),
        _check("redis", redis.ping(state.redis), timeout),
    )
    checks = {"database": db, "redis": rd}
    healthy = all(c.status == "ok" for c in checks.values())
    if not healthy:
        response.status_code = 503
    return Readiness(status="ok" if healthy else "degraded", checks=checks)
