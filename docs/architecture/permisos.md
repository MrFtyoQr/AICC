# Roles y permisos por workspace (HU-11)

Cada persona tiene **un rol por workspace** (tabla `memberships`). El rol decide qué puede hacer dentro de
ese workspace; fuera de él no ve nada (ver [ADR-010](../decisions/ADR-010-workspace-logico.md)).

La matriz está en código en `backend/app/core/permissions.py`. La prueba `test_matrix_matches_documentation`
lee la tabla de abajo y falla si no coincide, así que **cambiar un permiso exige cambiar ambas**.

## Matriz

<!-- matriz:inicio -->
| Permiso | owner | admin | operator | viewer |
|---|---|---|---|---|
| workspace.read | ✅ | ✅ | ✅ | ✅ |
| workspace.update | ✅ | ✅ | — | — |
| workspace.delete | ✅ | — | — | — |
| members.manage | ✅ | ✅ | — | — |
| project.write | ✅ | ✅ | — | — |
| project.delete | ✅ | ✅ | — | — |
| task.run | ✅ | ✅ | ✅ | — |
| task.approve | ✅ | ✅ | — | — |
<!-- matriz:fin -->

## Qué significa cada rol

| Rol | Pensado para |
|---|---|
| **owner** | Dueño del negocio. Único que puede borrar el workspace. Se asigna al crearlo. |
| **admin** | Gestiona proyectos, miembros y aprueba acciones de riesgo del orquestador. |
| **operator** | Lanza y sigue tareas del orquestador (O1+), sin cambiar la configuración. |
| **viewer** | Solo lectura: tableros, estado y resultados. |

## Reglas de miembros (HU-12)

- Solo un **owner** puede otorgar el rol owner (al invitar o al cambiar un rol), o cambiar/quitar a otro owner.
- Un workspace siempre conserva **al menos un owner**: no se puede degradar ni quitar al último (409).
- El workspace **personal** no se puede borrar (409). Uno de equipo solo lo borra un owner.
- Invitar deja una invitación **pendiente** con su rol; el envío por correo llega con O5.
- Toda escritura, y todo intento sin permiso, queda en el **registro de actividad** (`GET /api/v1/activity`), sin secretos.

## Respuestas de la API

| Situación | Código |
|---|---|
| El workspace (o un recurso suyo) no es tuyo o no existe | **404** — no se revela que exista |
| Eres miembro pero tu rol no tiene el permiso | **403** |
| Sin sesión o token vencido | **401** |

El workspace se elige con la cabecera `X-Workspace-Id`; si falta, se usa el workspace personal.
`GET /api/v1/workspaces/current` devuelve tu rol y la lista de permisos para que la app oculte lo que no puedes hacer.
