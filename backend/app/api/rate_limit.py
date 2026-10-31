"""Límite de frecuencia por IP con ventana fija en Redis (HU-07).

Si Redis no responde se deja pasar la petición y se registra un aviso: preferimos no bloquear
el inicio de sesión de todos por una caída de la cola. Detrás de un proxy habrá que tomar la IP
de X-Forwarded-For solo desde proxies de confianza (pendiente hasta tener despliegue).
"""

import logging
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


def rate_limit(scope: str, limit_setting: str) -> Callable:
    async def dependency(request: Request) -> None:
        settings = request.app.state.settings
        limit: int = getattr(settings, limit_setting)
        window = settings.rate_limit_window_s
        now = int(time.time())
        bucket = now // window
        client_ip = request.client.host if request.client else "unknown"
        key = f"rl:{scope}:{client_ip}:{bucket}"
        try:
            pipe = request.app.state.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window, nx=True)
            count, _ = await pipe.execute()
        except RedisError:
            logger.warning("rate limiter unavailable, allowing request", extra={"check": scope})
            return
        if count > limit:
            retry_after = window - (now % window)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos; espera un momento",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
