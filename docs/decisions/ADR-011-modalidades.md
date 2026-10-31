# ADR-011: Tres caminos de operación — Conectar, BYOC y Administrado

**Estado:** Aceptado · **Fecha:** 2026-10-31

## Contexto
La guía (§20) planteaba tres modalidades de infraestructura: administrada, BYOC e híbrida. Faltaba el caso más
común entre los primeros clientes: ya tienen su propio stack de automatización (OpenClaw, n8n, Hermes o algo a medida) y
solo quieren mandarlo desde la app. Además, "BYOK" (llaves de IA) y "BYOC" (cuenta de nube) se estaban mezclando.

## Decisión
- AICC ofrece **tres caminos**, combinables en un proyecto (híbrido):
  - **A · Conectar:** AICC orquesta runtimes del cliente mediante adaptadores con un contrato común
    (`health`, `list_actions`, `trigger`, `status`/callback, `result`). Lo que corre es infraestructura del cliente.
  - **B · BYOC:** AICC despliega recetas estándar en la cuenta de nube del cliente con acceso delegado, de permisos
    mínimos y revocable. Nunca pide la contraseña principal.
  - **C · Administrado:** AICC despliega en su nube estándar (ADR-019), en una cuenta aislada por cliente, y factura.
- **BYOK** es un eje independiente: las llaves de IA pueden ser del cliente o de AICC en cualquier camino.
- B y C usan **las mismas recetas y los mismos pasos**; solo cambia de quién es la cuenta.
- Cada recurso registra camino, dueño de la cuenta, quién paga, proveedor, región e identificador externo.

## Consecuencias
- Los conectores de O5 se diseñan como **runtimes externos**, no como integraciones sueltas.
- Etapa B necesita un `InfrastructureProvider` por nube con dos modos de credencial (cuenta AICC / cuenta delegada).
- Pasar de C a B es transferir la cuenta del cliente; no hay redeploy.
- Detalle y pruebas de validación: [modelo-operacion.md](../architecture/modelo-operacion.md).
