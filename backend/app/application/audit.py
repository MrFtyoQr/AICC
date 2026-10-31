"""Registro de actividad (HU-13).

`audit()` añade la entrada a la misma sesión que el comando: se confirma junto con el cambio o no se
guarda. Los detalles pasan por `sanitize()`, que nunca deja salir contraseñas, tokens ni secretos.
"""

import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import request_id_var
from app.infrastructure.models import AuditLog

REDACTED = "[oculto]"
_SENSITIVE = re.compile(r"pass|secret|token|key|credential|authorization|cookie", re.I)
_MAX_TEXT = 200


def sanitize(value: Any) -> Any:
    """Copia los detalles sin campos de nombre sensible y con los textos largos recortados."""
    if isinstance(value, dict):
        return {
            str(k): REDACTED if _SENSITIVE.search(str(k)) else sanitize(v) for k, v in value.items()
        }
    if isinstance(value, list | tuple):
        return [sanitize(v) for v in value]
    if isinstance(value, str):
        return value[:_MAX_TEXT]
    if isinstance(value, uuid.UUID):
        return str(value)
    if value is None or isinstance(value, bool | int | float):
        return value
    return str(value)[:_MAX_TEXT]


def audit(
    session: AsyncSession,
    *,
    workspace_id: uuid.UUID,
    actor_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None,
    summary: str,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            summary=summary[:300],
            details=sanitize(details or {}),
            request_id=request_id_var.get(),
        )
    )
