# App móvil: construcción incremental

La app Flutter se construye en **incrementos M0–M8**. Cada incremento:

- es instalable y usable por sí mismo (nunca hay pantallas "en construcción" en `main`);
- depende de una fase de backend concreta del [plan maestro](plan-maestro.md);
- tiene su diseño UX aprobado **antes** de programarse;
- añade solo los paquetes que necesita.

## Mapa de incrementos

| Inc. | Nombre | Fase backend | Pantallas / capacidades nuevas | Paquetes que entran |
|---|---|---|---|---|
| **M0** | Esqueleto y conexión | F0 | Splash → Estado de conexión (API, versión, entorno) | `dio` |
| **M1** | Sesión | F0 | Login, registro, cerrar sesión, refresh automático | `flutter_riverpod`, `go_router`, `flutter_secure_storage`, `freezed`, `json_serializable` |
| **M2** | Contexto | F1 | Chip de contexto (workspace › proyecto › ambiente), selector, Actividad | — |
| **M3** | Command Center v1 | O1 | Entrada "¿Qué necesitas?", lista de tareas, detalle de tarea, cancelar | — |
| **M4** | Propuesta de plan | O2 | Vista de plan (pasos, costo, supuestos), pedir plan, versiones | — |
| **M5** | Aprobaciones | O3 | Bandeja de aprobaciones, aprobar/rechazar/pedir cambios, deslizar para confirmar | — |
| **M6** | Ejecución en vivo | O4 | Línea de tiempo viva (SSE), artefactos, notificación in‑app | cliente SSE (`http` streaming o paquete evaluado en ticket) |
| **M7** | Conectores | O5 | Lista de conectores, conectar en 3 pasos, probar, desconectar | — |
| **M8** | Dashboard y consumo | O6 | Home con resumen, consumo, presupuesto | librería de gráficos (evaluar en ticket) |
| M9+ | Etapa B | S1–S6 | Propuesta de solución, infraestructura, Media Studio, facturación | según fase |

## Estructura que crece con los incrementos

```
lib/
├── main.dart                 M0
├── bootstrap.dart            M0  (lee AICC_API_BASE_URL, inicia logging)
├── app/
│   ├── app.dart              M0
│   ├── router/               M1  (GoRouter; guardas de sesión)
│   └── theme/                M0  (tokens de diseño → ThemeData claro/oscuro)
├── core/
│   ├── config/               M0
│   ├── network/              M0  (ApiClient único; interceptores auth/request-id/errores en M1)
│   ├── errors/               M0  (AppError tipado: network, timeout, unauthorized, conflict, server)
│   ├── realtime/             M6  (cliente SSE con reconexión y Last-Event-ID)
│   └── security/             M1  (almacenamiento de tokens)
├── shared/widgets/           M0+ (componentes del sistema de diseño)
└── features/
    ├── connection/           M0
    ├── authentication/       M1
    ├── context/              M2  (workspace/proyecto/ambiente)
    ├── activity/             M2
    ├── command_center/       M3
    ├── tasks/                M3
    ├── plans/                M4
    ├── approvals/            M5
    ├── executions/           M6
    ├── artifacts/            M6
    ├── connectors/           M7
    ├── dashboard/            M8
    └── usage/                M8
```

Dentro de cada feature: `presentation/` (widgets + controladores Riverpod), `data/` (repositorio + DTOs).
`domain/` solo cuando haya reglas propias del cliente.

## Criterios comunes por incremento

| Aspecto | Requisito |
|---|---|
| Estados | Cada pantalla maneja *cargando*, *vacío*, *error recuperable* y *contenido* |
| Errores | Mensaje humano + acción ("Reintentar"), nunca un stacktrace |
| Accesibilidad | Contraste AA, tamaños táctiles ≥ 48 dp, `Semantics` en iconos, escala de texto 200 % sin romper |
| Rendimiento | Primer render < 1 s en emulador; listas paginadas |
| Pruebas | Widget tests de cada pantalla + golden tests de componentes del sistema de diseño |
| Offline | Mostrar último estado conocido con indicador "sin conexión" (caché simple; `drift` solo si se necesita) |
| Seguridad | Sin secretos en el binario; tokens en almacenamiento seguro; logs sin datos personales |

## Destinos de ejecución

| Destino | URL de API | Cuándo |
|---|---|---|
| Emulador Android | `http://10.0.2.2:8000` | Desde M0 |
| Dispositivo Android físico | `http://<IP-LAN>:8000` (firewall abierto solo en red local) | Desde M1 |
| Simulador iOS | `http://localhost:8000` | Cuando haya macOS |
| Staging / producción | `https://…` | Etapa B |

Comando tipo:

```bash
flutter run --dart-define=AICC_API_BASE_URL=http://10.0.2.2:8000 --dart-define=AICC_ENV=development
```
