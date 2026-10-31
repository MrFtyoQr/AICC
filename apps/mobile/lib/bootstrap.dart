import 'package:flutter/material.dart';

import 'app/app.dart';
import 'core/config/app_config.dart';
import 'core/network/api_client.dart';
import 'features/connection/data/health_repository.dart';

/// Punto único de arranque: lee la configuración del entorno y construye las dependencias.
void bootstrap() {
  WidgetsFlutterBinding.ensureInitialized();
  const config = AppConfig.fromEnvironment();
  final apiClient = ApiClient(baseUrl: config.apiBaseUrl);
  runApp(
    AiccApp(config: config, healthRepository: HealthRepository(apiClient)),
  );
}
