# F0 · Fundamentos: guía de ejecución

Los códigos de tarea son los del [plan maestro](plan-maestro.md#f0--fundamentos) y del backlog de Jira.
Este documento fija **el orden exacto** y las decisiones previas.

## Decisiones previas (proponer → aceptar como ADR)

| # | Pregunta | Propuesta | ADR |
|---|---|---|---|
| D1 | Gestor de dependencias Python | **uv** con `uv.lock` | 004 |
| D2 | Versión de Python | **3.12** (`.python-version`) | 004 |
| D3 | Canal Flutter | **stable** | — |
| D4 | Identificador de app | `com.treetech.aicc` (provisional) | — |
| D5 | Autenticación | **Propia con JWT** (access 15 min + refresh rotatorio, Argon2) | 006 |
| D6 | Acceso a BD | **SQLAlchemy 2 async + asyncpg** (psycopg async no funciona con el loop Proactor de Windows) | 003 |
| D7 | Cola de trabajos | **arq** (asíncrona, sobre Redis); alternativa Dramatiq | 005 |
| D8 | Ubicación del repo | Mover fuera de OneDrive (`C:\dev\ai-command-center`) | — |

## Orden de ejecución

### Bloque 0A — Bootstrap (cierra la DoD de la guía, sección 15)

1. ✅ **F0-OPS-01** Monorepo y documentación.
2. **F0-OPS-02** Publicar en GitHub (privado) y proteger `main`.
3. ✅ **F0-OPS-03** `docker-compose.yml` con PostgreSQL 16 + Redis 7 *healthy*.
4. ✅ **F0-OPS-04** Medición base `F0-base`.
5. ✅ **F0-OPS-06** Repo fuera de OneDrive + Flutter stable.
6. ✅ **F0-DOC-01** ADR‑004/005/006 aceptados (decisiones D1–D7).
7. ✅ **F0-BE-01** `backend/` con uv + FastAPI + `/health`.
8. ✅ **F0-BE-02** Configuración con falla explícita.
9. ✅ **F0-BE-03** SQLAlchemy async + Alembic.
10. ✅ **F0-BE-04** `/health/ready` (BD + Redis).
11. ✅ **F0-BE-05** Logging JSON + `X-Request-ID`.
12. ✅ **F0-BE-06** Exportar OpenAPI.
13. ✅ **F0-UX-01 / F0-UX-02** Principios, mapa de pantallas, tokens de diseño.
14. ✅ **F0-APP-01 → F0-APP-03** Flutter, esqueleto, pantalla de estado de conexión (M0).

→ **Checkpoint 0A:** DoD sección 15 verificada; tag `v0.1.0`; medición `F0-0A`.

### Bloque 0B — CI y autenticación

15. **F0-OPS-05** GitHub Actions backend + mobile.
16. **F0-SEC-01** Usuarios + auth JWT.
17. **F0-SEC-02** CORS, límite de body, rate limit.
18. **F0-APP-04** Login + almacenamiento seguro + Riverpod/GoRouter (M1).

→ **Gate F0 (H1):** CI verde, login desde Android, `GET /api/v1/me` autenticado; tag `v0.2.0`; medición `F0-gate`.

## Verificación de la DoD (sección 15 de la guía)

| Punto | Cómo se comprueba |
|---|---|
| Se clona y arranca en otra máquina | Clon limpio en carpeta temporal + pasos del README ✅ |
| Flutter corre en Android | `flutter run` en emulador ✅ (Medium_Phone, API 37) |
| FastAPI `/health` + OpenAPI local | `curl` + `/docs` ✅ |
| PostgreSQL y Redis *healthy* | `docker compose ps` ✅ |
| Configuración desde entorno, sin secretos versionados | Test ✅ · `gitleaks` en CI (0B) |
| Flutter llama a la API con URL configurable | `--dart-define=AICC_API_BASE_URL` ✅ |
| Pruebas y analizadores pasan | Local ✅ (12 backend + 9 Flutter) · CI en 0B |
| README y `.env.example` sin credenciales reales | Revisión ✅ |

## Fuera de alcance de F0

Workspaces (F1), planner/LLM (O2), worker (O4), iOS, despliegue en la nube.
