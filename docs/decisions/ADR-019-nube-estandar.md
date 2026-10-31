# ADR-019: Nube estándar de AICC y nubes soportadas para BYOC

**Estado:** Propuesto (pendiente de confirmación del dueño del producto) · **Fecha:** 2026-10-31

## Contexto
AICC estandariza pasos para montar y operar soluciones. Eso solo funciona con pocos destinos bien probados.
Hay que elegir **una** nube para el camino Administrado (y para el plano de control de AICC) y fijar en qué orden se
soportan las demás para BYOC. Candidatas: AWS, Google Cloud y Azure. Cloudflare ya se usa en Forja para bots ligeros.

## Opciones

| Criterio | AWS | Google Cloud | Azure |
|---|---|---|---|
| Acceso delegado para un tercero (BYOC) | Rol entre cuentas con `ExternalId`: el patrón más extendido entre SaaS intermediarios | Cuenta de servicio con impersonation / WIF | App multi-tenant / Lighthouse; más pasos para el cliente |
| Cuenta aislada por cliente (Administrado) | AWS Organizations: cuenta hija por cliente, facturación consolidada, transferible | Proyectos por cliente bajo una organización | Suscripciones por cliente; más pesado de automatizar |
| Correr nuestra imagen (ADR-018) | ECS Fargate / App Runner / Lightsail Containers | Cloud Run (el más simple) | Container Apps |
| Región en México | Sí | Sí | Sí |
| Presencia entre pymes de LATAM | Alta | Media | Media (fuerte en corporativos) |

Las tres tienen región en México; los servicios disponibles por región se verifican en el spike V-B1.

## Decisión propuesta
1. **AWS es la nube estándar** del camino Administrado y del plano de control de AICC.
2. Orden de soporte para BYOC: **AWS → Google Cloud → Azure**. Cada nube nueva entra solo cuando su adaptador pasa la
   misma batería de pruebas de recetas que AWS.
3. **Cloudflare** se mantiene como destino de **recetas ligeras de borde** (bots tipo Forja), en BYOC y Administrado.
4. Un adaptador genérico "VPS por SSH + Docker" cubre Hostinger y similares solo como BYOC, sin compromiso de operación administrada.

## Consecuencias
- Etapa B S2 empieza con el adaptador de AWS (antes se planeaba "Docker/VPS primero").
- El spike V-B1/V-C1 (modelo-operacion.md §6) valida acceso delegado, cuenta por cliente y costos reales antes de construir.
- Si el dueño del producto elige otra nube estándar, solo cambia este ADR y el orden de S2; el resto del modelo no.
