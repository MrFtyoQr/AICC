import '../../../core/network/api_client.dart';

enum DependencyState { ok, error }

class ApiStatus {
  const ApiStatus({
    required this.version,
    required this.environment,
    required this.dependencies,
  });

  final String version;
  final String environment;

  /// Nombre de la dependencia (database, redis…) → estado.
  final Map<String, DependencyState> dependencies;

  bool get isReady => dependencies.values.every((d) => d == DependencyState.ok);
}

class HealthRepository {
  HealthRepository(this._client);

  final ApiClient _client;

  String get apiBaseUrl => _client.baseUrl;

  Future<ApiStatus> fetchStatus() async {
    final results = await Future.wait([
      _client.getJson('/health'),
      _client.getJson('/health/ready', acceptedStatuses: const {200, 503}),
    ]);
    final health = results[0];
    final checks = (results[1]['checks'] as Map<String, dynamic>? ?? const {});
    return ApiStatus(
      version: health['version'] as String? ?? '?',
      environment: health['environment'] as String? ?? '?',
      dependencies: {
        for (final entry in checks.entries)
          entry.key: (entry.value as Map<String, dynamic>)['status'] == 'ok'
              ? DependencyState.ok
              : DependencyState.error,
      },
    );
  }
}
