# ADR-002: Flutter como cliente multiplataforma

**Estado:** Propuesto · **Fecha:** 2026-10-31

## Contexto
El producto es un centro de mando móvil para Android e iOS (web en fase posterior).

## Decisión
Una sola app Flutter/Dart. El cliente solo envía solicitudes y presenta estados: no contiene secretos
de proveedores ni ejecuta trabajos largos. URL de API configurable con `--dart-define`.

## Consecuencias
- Un código para ambas plataformas; las tareas continúan aunque el usuario cierre la app.
- La compilación y firma iOS requieren macOS (no disponible en el entorno actual).
