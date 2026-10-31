/// Configuración inyectada en compilación con `--dart-define`.
///
/// ```
/// flutter run --dart-define=AICC_API_BASE_URL=http://10.0.2.2:8000 --dart-define=AICC_ENV=development
/// ```
/// El valor por defecto solo sirve para el emulador Android contra la API local.
class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.environment});

  const AppConfig.fromEnvironment()
    : apiBaseUrl = const String.fromEnvironment(
        'AICC_API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
      environment = const String.fromEnvironment(
        'AICC_ENV',
        defaultValue: 'development',
      );

  final String apiBaseUrl;
  final String environment;
}
