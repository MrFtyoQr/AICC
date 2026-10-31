# ADR-018: El contenedor es la unidad de despliegue del backend

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
AICC debe desplegarse en infraestructura propia, de la nube que elija el cliente (BYOC) o híbrida (guía §20).
En desarrollo ya aparecieron diferencias entre Windows y Linux. Hace falta un artefacto único y portable.

## Decisión
- El backend se empaqueta en **una imagen OCI** (`aicc-api`), multi-stage, sin root, solo lectura.
- API y worker comparten imagen; cambian de comando (`api`, `migrate`, y desde O4 `worker`).
- Docker Compose es el entorno local de referencia (perfil `app` = stack completo).
- La CI construye y arranca la imagen en cada cambio del backend.
- La app Flutter no se conteneriza para desplegarse (se distribuye por tiendas).

## Consecuencias
- Cualquier proveedor que ejecute contenedores sirve; el adaptador de provisionamiento (S2) despliega la misma imagen.
- Configuración solo por variables de entorno (12-factor); secretos desde el gestor de secretos del proveedor.
- Coste: ~320 MB por imagen y un paso de build en CI (cacheado).
