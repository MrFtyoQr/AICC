"""Roles y matriz de permisos por workspace (HU-11).

La matriz vive aquí, en código, y `docs/architecture/permisos.md` la documenta; una prueba
comprueba que ambas coinciden para que nunca se desincronicen.
"""

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Permission(StrEnum):
    WORKSPACE_READ = "workspace.read"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_DELETE = "workspace.delete"
    MEMBERS_MANAGE = "members.manage"
    PROJECT_WRITE = "project.write"
    PROJECT_DELETE = "project.delete"
    TASK_RUN = "task.run"
    TASK_APPROVE = "task.approve"


_VIEWER = {Permission.WORKSPACE_READ}
_OPERATOR = _VIEWER | {Permission.TASK_RUN}
_ADMIN = _OPERATOR | {
    Permission.WORKSPACE_UPDATE,
    Permission.MEMBERS_MANAGE,
    Permission.PROJECT_WRITE,
    Permission.PROJECT_DELETE,
    Permission.TASK_APPROVE,
}
_OWNER = _ADMIN | {Permission.WORKSPACE_DELETE}

MATRIX: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(_OWNER),
    Role.ADMIN: frozenset(_ADMIN),
    Role.OPERATOR: frozenset(_OPERATOR),
    Role.VIEWER: frozenset(_VIEWER),
}


def can(role: str, permission: Permission) -> bool:
    try:
        return permission in MATRIX[Role(role)]
    except ValueError:
        return False
