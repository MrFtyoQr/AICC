# Entorno local y medición comparativa

Objetivo: saber **cómo se comporta AICC en este equipo** en cada fase y detectar a tiempo cualquier
regresión (más RAM, arranque más lento, menos rendimiento). Las mismas mediciones servirán después para
comparar contra un VPS o una nube (Etapa B, S2).

## 1. Equipo de referencia

| Elemento | Valor |
|---|---|
| Sistema | Windows 11 Home 10.0.26300 |
| Docker | Docker Desktop 29.4.3 (motor Linux, WSL2) |
| Recursos de la VM Docker | 32 CPU lógicas · 7,36 GiB RAM |
| Python backend | 3.12.14 vía `uv` (sistema: 3.15.2) |
| Flutter | 3.47.9 stable (cambiado desde `main` el 2026‑10‑31) |
| Ubicación del repo | `C:\dev\ai-command-center` (fuera de OneDrive desde el 2026‑10‑31) |

## 2. Arranque

```bash
cp .env.example .env        # y cambia POSTGRES_PASSWORD (o deja el .env generado)
docker compose up -d
docker compose ps           # ambos deben estar "healthy"
```

Apagar sin perder datos: `docker compose down`. Borrar también datos: `docker compose down -v` (destructivo).

Perfiles previstos (se añaden en su fase):

| Perfil | Servicios | Fase |
|---|---|---|
| *(por defecto)* | postgres, redis | F0 |
| `app` | migrate + api (imagen `aicc-api`); worker en O4 | F0 ✅ / O4 |
| `connectors` | n8n | O5 |
| `observability` | prometheus, grafana | O6 |

## 3. Protocolo de medición

Se ejecuta **al cerrar cada gate** y cuando un cambio pueda afectar al rendimiento:

```bash
scripts/medir-entorno.sh <ETIQUETA>     # p. ej. F0-base, F0-gate, O4-gate
```

El script recrea los contenedores (conserva volúmenes) y registra en `docs/environment/resultados/<ETIQUETA>.md`:

1. Tiempo de arranque hasta *healthy*.
2. CPU y RAM en reposo por contenedor.
3. PostgreSQL: `pgbench` escala 10, 8 clientes, 20 s (TPS y latencia media).
4. Redis: `redis-benchmark` 100 000 operaciones SET/GET/LPUSH/RPOP (LPUSH/RPOP ≈ comportamiento de cola).

Métricas que se agregan conforme existan los componentes:

| Desde | Métrica | Herramienta |
|---|---|---|
| F0 | Latencia p50/p95 de `GET /health` y `/health/ready` | `hey` o `oha` en contenedor |
| F0 | RAM de la API en reposo | `docker stats` |
| O4 | Tiempo encolar → inicio de step; duración por step; RAM del worker | eventos + `docker stats` |
| O4 | Throughput: runs/min con FakeRuntime | script de carga |
| O6 | Costo por run (estimado vs. real) | `usage_events` |

## 4. Resultados

| Etiqueta | Fecha | Arranque (ms) | RAM reposo PG / Redis | pgbench TPS (lat.) | Redis SET / RPOP (rps) | Notas |
|---|---|---|---|---|---|---|
| [F0-base](resultados/F0-base.md) | 2026‑10‑31 | 7 055 | 18,9 MiB / 4,3 MiB | 2 682 (2,98 ms) | 76 628 / 72 359 | Solo infraestructura; sin API |
| [F0-0A](resultados/F0-0A.md) | 2026‑10‑31 | 8 745 | 21,2 MiB / 4,8 MiB | 2 192 (3,65 ms) | ver archivo | API activa + emulador Android en paralelo. `/health` p50 3,3 ms (secuencial), `/health/ready` p50 9,8 ms |
| F0-docker | 2026‑10‑31 | — | API en contenedor: 67 MiB | — | — | Imagen `aicc-api` 323 MB. `/health` p50 3,9 ms, `/health/ready` p50 5,5 ms (secuencial) |

Lectura de F0-0A: con la API y el emulador encendidos, PostgreSQL baja de ~2 700 a ~2 200 TPS (la máquina comparte CPU con el emulador). La API sola responde en ~1 ms; ver notas del archivo.

Lectura de la línea base: la infraestructura consume ~23 MiB en reposo y arranca en ~7 s; el margen
de la VM (7,36 GiB) sobra para API + worker + n8n. Redis supera 70 000 operaciones de cola por segundo:
la cola no será el cuello de botella en la Etapa A.

## 5. Riesgos del entorno

| Riesgo | Efecto | Acción |
|---|---|---|
| Repo dentro de OneDrive | Resuelto: el repo vive en `C:\dev\ai-command-center`; la copia de OneDrive queda como respaldo y ya no se usa | — |
| Flutter en canal `main` | Builds inestables | `flutter channel stable && flutter upgrade` |
| Python 3.15 del sistema | Dependencias sin wheels | `uv python install 3.12` + `.python-version` |
| Sin macOS | No hay validación iOS | Android primero; runner macOS en CI más adelante |
| Puertos 5432/6379 ocupados por otra instalación | El compose no arranca | Cambiar el puerto del host en `.env` (variable a añadir si ocurre) |
