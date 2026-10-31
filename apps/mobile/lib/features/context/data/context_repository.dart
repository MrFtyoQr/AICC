import '../../../core/network/api_client.dart';

/// Workspace del usuario y lo que su rol le permite (HU-09, HU-11).
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

enum EnvironmentKind {
  development('Dev'),
  staging('Staging'),
  production('Producción');

  const EnvironmentKind(this.label);
  final String label;

  static EnvironmentKind parse(String value) => EnvironmentKind.values
      .firstWhere((k) => k.name == value, orElse: () => development);
}

class Environment {
  const Environment({required this.id, required this.name, required this.kind});

  factory Environment.fromJson(Map<String, dynamic> json) => Environment(
    id: json['id'] as String,
    name: json['name'] as String,
    kind: EnvironmentKind.parse(json['kind'] as String),
  );

  final String id;
  final String name;
  final EnvironmentKind kind;
}

class Project {
  const Project({
    required this.id,
    required this.name,
    required this.environments,
  });

  factory Project.fromJson(Map<String, dynamic> json) => Project(
    id: json['id'] as String,
    name: json['name'] as String,
    environments: [
      for (final e in json['environments'] as List)
        Environment.fromJson(e as Map<String, dynamic>),
    ],
  );

  final String id;
  final String name;
  final List<Environment> environments;
}

class ContextRepository {
  ContextRepository(this._client);

  final ApiClient _client;

  Future<List<Workspace>> workspaces() async => [
    for (final json in await _client.getList('/api/v1/workspaces'))
      Workspace.fromJson(json),
  ];

  /// El workspace va explícito: al cambiar de contexto se consultan sus proyectos
  /// antes de que pase a ser el contexto activo.
  Future<List<Project>> projects(String workspaceId) async => [
    for (final json in await _client.getList(
      '/api/v1/projects',
      headers: {workspaceHeader: workspaceId},
    ))
      Project.fromJson(json),
  ];
}

const workspaceHeader = 'X-Workspace-Id';
