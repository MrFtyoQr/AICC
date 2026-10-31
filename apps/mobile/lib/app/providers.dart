import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/config/app_config.dart';
import '../core/network/api_client.dart';
import '../core/network/auth_interceptor.dart';
import '../core/security/token_storage.dart';
import '../features/authentication/application/session_controller.dart';
import '../features/authentication/data/auth_repository.dart';
import '../features/connection/data/health_repository.dart';
import '../features/activity/data/activity_repository.dart';
import '../features/context/application/context_controller.dart';
import '../features/context/data/context_repository.dart';

/// Dependencias de la app. `bootstrap.dart` y las pruebas sobrescriben config, almacenamiento
/// y, si hace falta, el cliente HTTP.
final appConfigProvider = Provider<AppConfig>(
  (ref) => const AppConfig.fromEnvironment(),
);

final tokenStorageProvider = Provider<TokenStorage>(
  (ref) => SecureTokenStorage(),
);

final baseApiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(baseUrl: ref.watch(appConfigProvider).apiBaseUrl),
);

final activeWorkspaceProvider = Provider<ActiveWorkspace>(
  (ref) => ActiveWorkspace(),
);

/// Cliente con sesión: adjunta el workspace activo y el token, y renueva ante 401.
final apiClientProvider = Provider<ApiClient>((ref) {
  final client = ref.watch(baseApiClientProvider);
  client.dio.interceptors.add(
    WorkspaceHeaderInterceptor(ref.watch(activeWorkspaceProvider)),
  );
  client.dio.interceptors.add(
    AuthInterceptor(
      dio: client.dio,
      storage: ref.watch(tokenStorageProvider),
      onSessionExpired: () =>
          ref.read(sessionProvider.notifier).sessionExpired(),
    ),
  );
  return client;
});

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(tokenStorageProvider),
  ),
);

final healthRepositoryProvider = Provider<HealthRepository>(
  (ref) => HealthRepository(ref.watch(apiClientProvider)),
);

final sessionProvider = NotifierProvider<SessionController, SessionState>(
  SessionController.new,
);

final contextRepositoryProvider = Provider<ContextRepository>(
  (ref) => ContextRepository(ref.watch(apiClientProvider)),
);

/// Workspace › proyecto › ambiente activos (HU-14).
final contextProvider = AsyncNotifierProvider<ContextController, AppContext>(
  ContextController.new,
);

final activityRepositoryProvider = Provider<ActivityRepository>(
  (ref) => ActivityRepository(ref.watch(apiClientProvider)),
);
