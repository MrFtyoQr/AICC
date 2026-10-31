from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status

from app.application.workspaces import Conflict, NameTaken, NotAllowed, NotFound

NOT_FOUND = {404: {"description": "No existe o pertenece a otro workspace"}}
FORBIDDEN = {403: {"description": "Tu rol no permite esta acción"}}
CONFLICT = {409: {"description": "La acción rompe una regla (nombre repetido, último dueño…)"}}


@contextmanager
def domain_errors(not_found: str = "No encontrado") -> Iterator[None]:
    """Traduce los errores de dominio a HTTP con mensajes que la app muestra tal cual."""
    try:
        yield
    except NotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, not_found) from None
    except NameTaken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe uno con ese nombre") from None
    except Conflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    except NotAllowed as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from None
