# ADR-001: Backend como monolito modular con workers separados

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
El dominio (agentes, cotización, provisionamiento) y la carga real aún no están validados.
Microservicios, Kubernetes o Kafka multiplicarían las piezas operativas sin beneficio demostrado.

## Decisión
Un único servicio FastAPI organizado en módulos (`api`, `application`, `domain`, `infrastructure`,
`orchestration`, `workers`, `core`) y procesos worker separados que consumen una cola en Redis.

## Consecuencias
- Despliegue y depuración simples; límites de módulo explícitos facilitan extraer servicios más adelante.
- Requiere disciplina para no acoplar módulos entre sí (dependencias solo hacia `domain`/`core`).
