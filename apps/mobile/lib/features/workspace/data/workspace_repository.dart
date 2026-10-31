import '../../../core/network/api_client.dart';

/// Workspace sobre el que actúa el usuario y lo que su rol le permite (HU-09, HU-11).
class Workspace {
  const Workspace({
    required this.id,
    required this.name,
    required this.role,
    required this.isPersonal,
    required this.permissions,
  });

  factory Workspace.fromJson(Map<String, dynamic> json) => Workspace(
    id: json['id'] as String,
    name: json['name'] as String,
    role: json['role'] as String,
    isPersonal: json['is_personal'] as bool,
    permissions: Set.unmodifiable((json['permissions'] as List).cast<String>()),
  );

  final String id;
  final String name;
  final String role;
  final bool isPersonal;
  final Set<String> permissions;

  /// La app oculta lo que el rol no permite; el backend lo exige igualmente.
  bool can(String permission) => permissions.contains(permission);

  String get roleLabel => switch (role) {
    'owner' => 'Dueño',
    'admin' => 'Administrador',
    'operator' => 'Operador',
    'viewer' => 'Solo lectura',
    _ => role,
  };
}

class WorkspaceRepository {
  WorkspaceRepository(this._client);

  final ApiClient _client;

  /// Sin `X-Workspace-Id` la API responde con el workspace personal.
  Future<Workspace> current() async =>
      Workspace.fromJson(await _client.getJson('/api/v1/workspaces/current'));
}
