#!/usr/bin/env bash
# Protocolo de medición del entorno local AICC (ver docs/environment/entorno-local.md).
# Uso: scripts/medir-entorno.sh <etiqueta>   p. ej. scripts/medir-entorno.sh F0-base
set -euo pipefail
cd "$(dirname "$0")/.."
LABEL="${1:-sin-etiqueta}"
OUT="docs/environment/resultados/${LABEL}.md"
mkdir -p docs/environment/resultados

ms() { python -I -c "import time;print(int(time.time()*1000))"; }

echo "== Arranque en frío (contenedores recreados, volúmenes conservados)"
docker compose down >/dev/null 2>&1 || true
T0=$(ms)
docker compose up -d >/dev/null
until [ "$(docker inspect -f '{{.State.Health.Status}}' aicc-postgres)" = healthy ] && \
      [ "$(docker inspect -f '{{.State.Health.Status}}' aicc-redis)" = healthy ]; do sleep 0.5; done
T1=$(ms); BOOT=$((T1 - T0))

echo "== Reposo (10 s)"; sleep 10
STATS=$(docker stats --no-stream --format '| {{.Name}} | {{.CPUPerc}} | {{.MemUsage}} |' aicc-postgres aicc-redis)

echo "== PostgreSQL: pgbench (escala 10, 8 clientes, 20 s)"
# Base temporal: la base de la aplicación nunca se ensucia con tablas de pgbench.
docker compose exec -T postgres psql -q -U aicc -d aicc -c "DROP DATABASE IF EXISTS aicc_bench" -c "CREATE DATABASE aicc_bench" >/dev/null
docker compose exec -T postgres pgbench -U aicc -i -s 10 -q aicc_bench >/dev/null 2>&1
PGB=$(docker compose exec -T postgres pgbench -U aicc -c 8 -j 4 -T 20 aicc_bench 2>/dev/null | grep -E "^(tps|latency average)" | tr '\n' ';')
docker compose exec -T postgres psql -q -U aicc -d aicc -c "DROP DATABASE aicc_bench" >/dev/null

echo "== Redis: redis-benchmark (SET/GET/LPUSH/RPOP, 100k ops)"
RB=$(docker compose exec -T redis redis-benchmark -q -n 100000 -t set,get,lpush,rpop 2>/dev/null | tr '\r' '\n' | grep -o '[A-Z]*: [0-9.]* requests per second, p50=[0-9.]* msec' | sed 's/^/- /')

PGV=$(docker compose exec -T postgres postgres --version | tr -d '\r')
RV=$(docker compose exec -T redis redis-server --version | awk '{print $3}' | tr -d '\r')
DV=$(docker info --format '{{.ServerVersion}} · {{.NCPU}} CPU · {{.MemTotal}} B RAM VM')

cat > "$OUT" <<MD
# Medición: ${LABEL}

- Fecha: $(date '+%Y-%m-%d %H:%M')
- Host: $(uname -s) · Docker ${DV}
- Versiones: ${PGV} · Redis ${RV}

| Métrica | Valor |
|---|---|
| Arranque hasta *healthy* (ms) | ${BOOT} |
| pgbench | ${PGB} |

Uso en reposo:

| Contenedor | CPU | Memoria |
|---|---|---|
${STATS}

Redis benchmark:

${RB}
MD
echo "Resultado escrito en ${OUT}"; cat "$OUT"
