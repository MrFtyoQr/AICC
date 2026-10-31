#!/bin/sh
# Comandos de la imagen AICC. Uso: docker run aicc-api [api|migrate|<comando>]
set -eu

case "${1:-api}" in
  api)
    # Varios workers solo si se pide; en la nube se escala con más contenedores, no con más procesos.
    exec uvicorn app.main:create_app --factory \
      --host 0.0.0.0 --port "${PORT:-8000}" \
      --workers "${WEB_CONCURRENCY:-1}" \
      --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}" \
      --no-access-log
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  *)
    exec "$@"
    ;;
esac
