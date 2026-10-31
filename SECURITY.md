# Política de seguridad

AICC está en desarrollo temprano (Etapa A). No hay versiones en producción todavía.

## Reportar una vulnerabilidad

**No abras un issue público.** Usa *Security → Report a vulnerability* en este repositorio (reporte privado de
GitHub). Incluye pasos para reproducir y el impacto que observaste. Responderemos lo antes posible.

## Prácticas del proyecto

- Ningún secreto en el repositorio: configuración por variables de entorno; `.env` está excluido.
- Escaneo de secretos (gitleaks) en cada PR y en `main`.
- Contraseñas con Argon2id; tokens de refresco guardados solo como hash y rotados en cada uso.
- La API corre en contenedores sin privilegios y con sistema de archivos de solo lectura.
- Ningún modelo de IA autoriza acciones: las políticas y aprobaciones se aplican en código determinista.
