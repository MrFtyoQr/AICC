# AICC mobile

App Flutter (Android e iOS), construida por incrementos M0–M8 (ver `docs/planning/app-movil-incremental.md`).
**Estado: M1**: inicio de sesión, registro, sesión segura con renovación automática y pantalla de estado de conexión.

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

## Estructura (M1)

```
lib/
├── main.dart · bootstrap.dart        arranque (ProviderScope)
├── app/                              app.dart · providers.dart (dependencias) · router/ (guardas de sesión) · theme/
├── core/                             config/ · network/ (ApiClient + AuthInterceptor) · errors/ (AppError) · security/ (TokenStorage)
├── shared/widgets/                   StatusPill
└── features/
    ├── authentication/               data/ (AuthRepository) · application/ (SessionController) · presentation/ (login, registro)
    ├── connection/                   estado de API y dependencias
    └── home/                         inicio provisional (saludo + estado)
test/                                 backend en memoria (fake_backend.dart): ninguna prueba abre sockets
```

## Sesión

- Tokens en Keystore/Keychain (`flutter_secure_storage`), nunca en preferencias planas.
- `AuthInterceptor` adjunta el access token; ante un 401 renueva **una sola vez** aunque fallen varias peticiones a la vez
  y reintenta. Si el refresh ya no sirve, borra la sesión y la app vuelve al login con el motivo.
- Al reabrir la app con sesión guardada se entra directo al inicio.
