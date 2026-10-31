# Fase 0 — Fundamentos: plan de ejecución

Objetivo: validar el circuito **Flutter → FastAPI → PostgreSQL/Redis → respuesta** con un repositorio
que cualquiera pueda clonar y arrancar. Sin agentes reales todavía.

Se divide en dos sub‑fases para poder cerrar la DoD de inicialización (sección 15) antes de abrir auth.

## Entorno verificado (2026‑10‑31, Windows 11)

| Herramienta | Detectado | Acción |
|---|---|---|
| Git / GitHub CLI | OK, cuenta `MrFtyoQr` | — |
| Docker | 29.4.3 | Confirmar Docker Desktop corriendo |
| Python | 3.15.2 (sistema) | Fijar **3.12** para el backend con `uv` (ya instalado) |
| Flutter | 3.50.0‑0.3.pre, canal **main** | Cambiar a canal **stable** (`flutter channel stable && flutter upgrade`) |
| macOS / Xcode | No disponible | iOS queda fuera de la validación de Fase 0 |

## 0A — Bootstrap (DoD de la sección 15)

| # | Tarea | Entregable | Verificación |
|---|---|---|---|
| 0A.1 | Estructura monorepo, `.gitignore`, `.env.example`, README | Carpetas `apps/ backend/ shared/ infrastructure/ docs/` | `git status` limpio, sin secretos |
| 0A.2 | Flutter `apps/mobile` (`--org com.treetech.aicc`, temporal) | Plantilla compilando | `flutter analyze`, `flutter test`, `flutter run` en emulador Android |
| 0A.3 | Backend FastAPI con `uv` + Python 3.12 | `backend/pyproject.toml`, `uv.lock`, `app/main.py` con `/health` | `GET /health` → 200; `/docs` visible |
| 0A.4 | `docker-compose.yml` con PostgreSQL 16 y Redis 7 (solo `127.0.0.1`) | Servicios con healthcheck y volúmenes | `docker compose ps` → ambos *healthy* |
| 0A.5 | `core/config.py` con pydantic‑settings | Falla explícita si faltan `DATABASE_URL`/`REDIS_URL` | Test de configuración |
| 0A.6 | `infrastructure/database` (SQLAlchemy) + Alembic inicializado | Engine/sesión + primera migración vacía | `alembic upgrade head` OK |
| 0A.7 | `/health` ampliado con estado de BD y Redis (`/health/ready`) | Readiness real | Test con servicios arriba y abajo |
| 0A.8 | Cliente HTTP central en Flutter (`core/network`, `dio`) con `AICC_API_BASE_URL` | Pantalla "Estado de conexión" | Muestra OK / timeout / API caída sin bloquear la UI |
| 0A.9 | Exportar OpenAPI a `shared/contracts/openapi.json` | Contrato versionado | Script/regla de exportación |
| 0A.10 | Lint y formato: `ruff` (Python), `flutter analyze` + `dart format` | Config en repo | Todos los analizadores en verde |
| 0A.11 | ADR‑001/002/003 aceptados | `docs/decisions/` | Revisión |

**Salida 0A:** los 8 puntos de la DoD (sección 15) se cumplen en una máquina limpia → tag `v0.1.0`.

## 0B — CI y autenticación base

| # | Tarea | Entregable | Verificación |
|---|---|---|---|
| 0B.1 | GitHub Actions: job backend (ruff + pytest con Postgres/Redis de servicio) | `.github/workflows/backend.yml` | CI verde en PR |
| 0B.2 | GitHub Actions: job Flutter (analyze + test) | `.github/workflows/mobile.yml` | CI verde en PR |
| 0B.3 | Modelo `users` + migración | Tabla y repositorio | Test con BD aislada |
| 0B.4 | Auth: registro/login, access token corto + refresh token rotatorio | `POST /api/v1/auth/*`, `GET /api/v1/me` | Tests de expiración, refresh y token inválido |
| 0B.5 | Flutter: login + `flutter_secure_storage` para la sesión, `riverpod` + `go_router` | Flujo login → pantalla de estado | Test de widget + prueba manual en emulador |
| 0B.6 | Seguridad mínima: CORS restringido, límite de tamaño, rate limit básico, logs sin secretos | Middleware | Tests |
| 0B.7 | Protección de rama `main` y plantilla de PR | Reglas en GitHub | PR requerido + CI obligatorio |

**Salida Fase 0:** CI verde, login funcional desde Android, `GET /api/v1/me` autenticado → tag `v0.2.0`.

## Decisiones abiertas (resolver antes de empezar)

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| D1 | Gestor de dependencias Python | **uv** (un único mecanismo, con `uv.lock`) |
| D2 | Versión de Python | **3.12** fijada vía `.python-version` |
| D3 | Canal Flutter | **stable** |
| D4 | Identificador de app | `com.treetech.aicc` (temporal, documentar antes de publicar) |
| D5 | Auth: propia (JWT) o proveedor externo (Supabase Auth, Firebase Auth, Auth0, Clerk) | **Propia con JWT** para no atar el MVP a un proveedor; reevaluar en Fase 1 |
| D6 | Driver PostgreSQL: síncrono o `asyncpg`/`psycopg` async | **SQLAlchemy 2 async + psycopg 3** (los adaptadores de la sección 29 son `async`) |

## Fuera de alcance de Fase 0

Workspaces (Fase 1), planner/LLM (Fase 2), worker de cola (Fase 4), iOS (requiere macOS), despliegue a nube.
