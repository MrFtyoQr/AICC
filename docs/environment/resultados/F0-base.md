# Medición: F0-base

- Fecha: 2026-10-31 01:40
- Host: MINGW64_NT-10.0-26300 · Docker 29.4.3 · 32 CPU · 7902089216 B RAM VM
- Versiones: postgres (PostgreSQL) 16.15 (Debian 16.15-1.pgdg13+2) · Redis v=7.4.12

| Métrica | Valor |
|---|---|
| Arranque hasta *healthy* (ms) | 7055 |
| pgbench | latency average = 2.983 ms;tps = 2681.544096 (without initial connection time); |

Uso en reposo:

| Contenedor | CPU | Memoria |
|---|---|---|
| aicc-postgres | 0.04% | 18.89MiB / 7.359GiB |
| aicc-redis | 0.28% | 4.285MiB / 7.359GiB |

Redis benchmark:

- SET: 76628.36 requests per second, p50=0.335 msec
- GET: 71684.59 requests per second, p50=0.367 msec
- LPUSH: 73529.41 requests per second, p50=0.343 msec
- RPOP: 72358.90 requests per second, p50=0.343 msec
