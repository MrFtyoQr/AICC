import 'package:flutter/material.dart';

import '../core/config/app_config.dart';
import '../features/connection/data/health_repository.dart';
import '../features/connection/presentation/connection_screen.dart';
import 'theme/app_theme.dart';

class AiccApp extends StatelessWidget {
  const AiccApp({
    super.key,
    required this.config,
    required this.healthRepository,
  });

  final AppConfig config;
  final HealthRepository healthRepository;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AICC',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      home: ConnectionScreen(
        repository: healthRepository,
        appEnvironment: config.environment,
      ),
    );
  }
}
