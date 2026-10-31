# Plan de sprints (Etapa A)

Sprints de **2 semanas**, de lunes a viernes. El calendario es **indicativo**: se recalibra al cerrar S1 con la
velocidad real (puntos entregados por sprint). Las historias están en [historias-usuario.md](historias-usuario.md).

## Ceremonias

| Momento | Qué se hace | Salida |
|---|---|---|
| Inicio del sprint | Planificación: se toman HU del siguiente sprint que cumplan la DoR | Objetivo del sprint + HU comprometidas en Jira |
| Diario (asíncrono) | Qué hice, qué haré, qué me bloquea | Comentario en el ticket o nota en el PR |
| Fin del sprint | Revisión: demo en el emulador de lo terminado | Video o capturas en `docs/sprints/` |
| Fin del sprint | Retrospectiva | 1–3 acciones de mejora |
| Fin de fase | Gate + medición `scripts/medir-entorno.sh <fase>-gate` | Fila en `docs/environment/entorno-local.md` |

## Calendario

| Sprint | Fechas | Objetivo | Historias | Puntos | Gate al cerrar |
|---|---|---|---|---|---|
| **S0** | 2026‑10‑31 | Bootstrap: entorno, API observable, contrato, app M0 | HU‑01, HU‑02, HU‑03, HU‑04 | 16 | Bloque 0A ✅ |
| **S1** | 2026‑11‑02 → 11‑13 | Calidad automática y sesión segura | HU‑05, HU‑06, HU‑07, HU‑08 | 24 | **F0 / H1** |
| **S2** | 2026‑11‑16 → 11‑27 | Workspace y aislamiento | HU‑09, HU‑10, HU‑11 | 18 | — |
| **S3** | 2026‑11‑30 → 12‑11 | Gestión, auditoría y contexto en la app | HU‑12, HU‑13, HU‑14 | 18 | **F1 / H1.5** |
| **S4** | 2026‑12‑14 → 12‑25 | Tareas y máquina de estados | HU‑15, HU‑16, HU‑17 | 19 | **O1** |
| **S5** | 2026‑12‑28 → 2027‑01‑08 | Capacidades, motor de IA y plan | HU‑18, HU‑19, HU‑20 | 18 | — |
| **S6** | 2027‑01‑11 → 01‑22 | Planes seguros y vista de plan | HU‑21, HU‑22 | 16 | **O2** |
| **S7** | 2027‑01‑25 → 02‑05 | Políticas y aprobaciones | HU‑23, HU‑24, HU‑25 | 21 | **O3** |
| **S8** | 2027‑02‑08 → 02‑19 | Worker y ejecución por pasos | HU‑26, HU‑27 | 16 | — |
| **S9** | 2027‑02‑22 → 03‑05 | Cancelación, tiempo real y resultados | HU‑28, HU‑29, HU‑30 | 16 | **O4** |
| **S10** | 2027‑03‑08 → 03‑19 | Conectores base: secretos, HTTP, email | HU‑31, HU‑32, HU‑33 | 18 | — |
| **S11** | 2027‑03‑22 → 04‑02 | n8n, MCP y conectores en la app | HU‑34, HU‑35, HU‑36 | 18 | **O5** |
| **S12** | 2027‑04‑05 → 04‑16 | Consumo, presupuestos y métricas | HU‑37, HU‑38, HU‑39 | 16 | — |
| **S13** | 2027‑04‑19 → 04‑30 | Dashboard y validación con usuarios | HU‑40, HU‑41 | 10 | **O6 / H2 Orquestador MVP** |

Notas:

- S4 y S5 cruzan festividades de fin de año: si la capacidad baja, HU‑17 pasa a S5 y HU‑20 a S6.
- Cada sprint reserva ~20 % para bugs, deuda técnica y diseño UX del sprint siguiente (el diseño va un sprint por delante del código).

## Sprint actual: S1 · Calidad automática y sesión segura

**Objetivo:** cerrar F0. Todo PR pasa por CI, y un usuario puede registrarse, iniciar sesión en el móvil y mantener la sesión de forma segura.

| HU | Tareas | Estado |
|---|---|---|
| HU‑05 Calidad automática | F0-OPS-05 (CI) ✅, F0-OPS-02 (protección de `main`) ⏳ decisión pendiente | En curso |
| HU‑06 Cuenta e inicio de sesión | F0-SEC-01 | ✅ Hecho (31 pruebas de auth) |
| HU‑07 API protegida | F0-SEC-02 | ✅ Hecho |
| HU‑08 Sesión en el móvil | F0-APP-04 | ✅ Hecho, verificado en emulador contra la API en Docker |
| Extra | Imagen Docker de producción + perfil `app` + CI de imagen (ADR‑018) | ✅ Hecho |

**Riesgos del sprint:** protección de ramas no disponible en repos privados del plan gratuito de GitHub (alternativa: regla de trabajo + CI obligatoria por convención); licencias del SDK de Android pendientes de aceptar.

## Registro de sprints cerrados

| Sprint | Comprometido | Entregado | Velocidad | Notas |
|---|---|---|---|---|
| S0 | 16 pts | 16 pts | 16 | [PR #1](https://github.com/MrFtyoQr/AICC/pull/1): bootstrap completo, verificado en emulador |
