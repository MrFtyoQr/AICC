# ADR-010: El workspace es lógico, no infraestructura

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
AICC es multi-cliente. Hay que decidir si cada cliente obtiene su propia base de datos/servidor o si comparten
la plataforma con separación lógica. La guía pide además poder desplegar en la nube del cliente (BYOC) más adelante.

## Decisión
- Un **workspace** es una frontera lógica en la base compartida: tablas `workspaces`, `memberships(role)`,
  `projects`, `environments`.
- **Toda tabla de cliente lleva `workspace_id`**, aunque se pueda deducir por otra relación, para filtrar siempre
  de forma directa.
- El workspace se resuelve **por membresía** en una sola dependencia (`get_current_workspace`, cabecera
  `X-Workspace-Id`). Los servicios reciben el `workspace_id` ya validado y filtran por él en cada consulta.
- Un workspace o recurso ajeno responde **404**, igual que uno inexistente.
- La infraestructura del cliente (servidores, nubes) se modela aparte, en Etapa B, y se **vincula** a un
  ambiente; no se crea por workspace.

## Consecuencias
- Coste por cliente casi nulo y un solo esquema que migrar.
- El riesgo es una consulta que olvide el filtro: lo cubre la **suite de aislamiento** (`pytest -m isolation`),
  que corre en cada PR del backend y es el gate de F1.
- Si un cliente exige aislamiento físico, se le despliega una instancia completa (ADR-018), no un esquema aparte.
- Row-Level Security de PostgreSQL queda como defensa adicional a evaluar cuando haya más tablas de cliente.
