# ADR-006: Autenticación propia con JWT

**Estado:** Aceptado · **Fecha:** 2026-10-31 · **Uso:** F0 bloque 0B

## Contexto
Hace falta login desde F0. Un proveedor externo (Supabase, Firebase, Auth0, Clerk) acelera, pero ata el modelo de usuarios y workspaces a terceros antes de validar el producto.

## Decisión
- Tabla `users` propia; contraseñas con **Argon2id**.
- Access token JWT de **15 min**; refresh token opaco de 30 días, **rotatorio**, guardado como hash; reutilizar un refresh revocado invalida toda la familia.
- La app guarda los tokens con `flutter_secure_storage`.
- Se reevalúa un proveedor externo (SSO, MFA) al cerrar F1.

## Consecuencias
- Control total del modelo de identidad; más responsabilidad de seguridad (pruebas obligatorias de expiración, rotación y reuso).
