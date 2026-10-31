# Contenedores y despliegue

## Por qué todo el backend va en contenedores

| Motivo | Qué resuelve |
|---|---|
| **Paridad dev ↔ nube** | La imagen que pasa la CI es exactamente la que corre en la nube. Se acabó el "en mi Windows funcionaba" (ya vimos dos diferencias reales: asyncpg vs. psycopg y `localhost` IPv6). |
| **Portabilidad entre proveedores** | La guía (§20–22) exige no casarse con un proveedor: la misma imagen corre en AWS (ECS/Lightsail Containers), un VPS de Hostinger con Docker, Fly.io, Cloud Run o en la cuenta del cliente (BYOC). |
| **Despliegue reproducible y reversible** | Cada versión es una imagen inmutable etiquetada; volver atrás = desplegar la etiqueta anterior. |
| **Seguridad por defecto** | Usuario sin privilegios (UID 10001), sistema de archivos de solo lectura, sin capacidades de Linux, sin compiladores ni herramientas en la imagen final. |
| **Escalado horizontal** | Más carga = más contenedores idénticos detrás de un balanceador; el worker (O4) es la misma imagen con otro comando. |

**Qué no va en contenedor:** la app Flutter. Se distribuye como APK/AAB (Play Store) e IPA (App Store); no se
despliega en un servidor. Lo que sí podrá contenerse es su *build* en CI.

**Por qué en 0A la API corría nativa:** recarga en caliente y depurador mientras el código cambia cada minuto.
Ambos modos siguen disponibles y prueban el mismo código.

## Modos de ejecución local

| Modo | Comando | Para qué |
|---|---|---|
| Desarrollo nativo | `docker compose up -d` (solo BD/Redis) + `uv run uvicorn app.main:create_app --factory --reload` | Programar con recarga en caliente |
| Stack completo en contenedores | `docker compose --profile app up -d --build` | Probar exactamente lo que se despliega |

En el modo contenedores, `migrate` aplica las migraciones y termina; la `api` arranca solo si `migrate` acabó bien.

## La imagen `aicc-api`

- `backend/Dockerfile`, multi-stage: `builder` instala dependencias exactas de `uv.lock` en `/opt/venv`; `runtime` copia solo el venv y el código.
- Comandos del `entrypoint.sh`: `api` (por defecto), `migrate`, o cualquier comando.
- Variables: `APP_ENV`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `PORT`, `WEB_CONCURRENCY`, `FORWARDED_ALLOW_IPS`.
- `HEALTHCHECK` contra `/health`; los orquestadores deben usar `/health/ready` como *readiness*.
- Medición local (2026‑10‑31): **323 MB** de imagen, **67 MiB** de RAM en reposo, `/health` p50 3,9 ms y `/health/ready` p50 5,5 ms (secuencial).

## En la nube (Etapa B, S2 · Provisionamiento)

```
         Internet ──HTTPS──▶ Balanceador / proxy TLS
                                 │
                      ┌──────────┴──────────┐
                      ▼                     ▼
                 aicc-api (N)          aicc-worker (N)   ← misma imagen, comando distinto (O4)
                      │                     │
          PostgreSQL gestionado     Redis gestionado      Secret manager (JWT_SECRET, claves)
```

Reglas para cualquier proveedor:

1. Migraciones como **tarea previa** al despliegue (`aicc-api migrate`), nunca al arrancar cada réplica.
2. Secretos desde el gestor de secretos del proveedor, nunca horneados en la imagen.
3. PostgreSQL y Redis **sin acceso público**; solo la red privada de la API.
4. `FORWARDED_ALLOW_IPS` limitado al proxy, para que la IP real (y el rate limit) sean fiables.
5. Imágenes publicadas en un registro (GHCR por defecto) con etiqueta = commit; `latest` nunca en producción.

## CI

El job `imagen Docker` de `.github/workflows/backend.yml` construye la imagen y la arranca contra PostgreSQL y
Redis reales: migra, espera `/health/ready` y comprueba que corre como UID 10001. Publicar en GHCR se activa
cuando exista el primer entorno en la nube.
