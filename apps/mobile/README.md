# AICC mobile

App Flutter (Android e iOS), construida por incrementos M0–M8 (ver `docs/planning/app-movil-incremental.md`).
**Estado: M0**, pantalla de estado de conexión con la API.

## Ejecutar

Requisitos: Flutter **stable**, la API corriendo en el puerto 8000 (ver `backend/README.md`).

```bash
flutter pub get
flutter run -d emulator-5554 --dart-define=AICC_API_BASE_URL=http://10.0.2.2:8000 --dart-define=AICC_ENV=development
```

| Destino | `AICC_API_BASE_URL` |
|---|---|
| Emulador Android | `http://10.0.2.2:8000` (valor por defecto) |
| Dispositivo físico | `http://<IP-LAN-del-PC>:8000`; la API debe escuchar en `0.0.0.0` y hay que añadir la IP a `android/app/src/debug/res/xml/network_security_config.xml` |
| Simulador iOS (macOS) | `http://localhost:8000` |

HTTP sin TLS solo se permite en builds **debug** y solo hacia los hosts de `network_security_config.xml`.

## Verificación

```bash
dart format --set-exit-if-changed lib test
flutter analyze
flutter test
```

## Estructura (M0)

```
lib/
├── main.dart · bootstrap.dart        arranque y construcción de dependencias
├── app/                              app.dart · theme/ (tokens de diseño, tema claro/oscuro)
├── core/                             config/ (dart-define) · network/ (ApiClient único) · errors/ (AppError)
├── shared/widgets/                   StatusPill
└── features/connection/              data/ (HealthRepository) · presentation/ (ConnectionScreen)
test/                                 adaptador HTTP falso: ninguna prueba abre sockets
```
