import '../../../core/network/api_client.dart';

/// Tarea tal como la expone la API (O1). El texto del estado viene del servidor
/// (diccionario de estados), así la app y el backend nunca discrepan.
class Task {
  const Task({
    required this.id,
    required this.title,
    required this.description,
    required this.status,
    required this.statusLabel,
    required this.projectName,
    required this.environmentName,
    required this.environmentKind,
    required this.version,
    required this.allowedCommands,
    required this.createdAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    final environment = json['environment'] as Map<String, dynamic>;
    return Task(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      status: json['status'] as String,
      statusLabel: json['status_label'] as String,
      projectName: (json['project'] as Map<String, dynamic>)['name'] as String,
      environmentName: environment['name'] as String,
      environmentKind: environment['kind'] as String,
      version: json['version'] as int,
      allowedCommands: Set.unmodifiable(
        (json['allowed_commands'] as List).cast<String>(),
      ),
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
    );
  }

  final String id;
  final String title;
  final String description;
  final String status;
  final String statusLabel;
  final String projectName;
  final String environmentName;
  final String environmentKind;
  final int version;
  final Set<String> allowedCommands;
  final DateTime createdAt;

  bool get canCancel => allowedCommands.contains('cancel');
}

class TaskEvent {
  const TaskEvent({required this.summary, required this.createdAt});

  factory TaskEvent.fromJson(Map<String, dynamic> json) => TaskEvent(
    summary: json['summary'] as String,
    createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
  );

  final String summary;
  final DateTime createdAt;
}

class TaskRepository {
  TaskRepository(this._client);

  final ApiClient _client;

  /// El workspace lo añade el interceptor según el contexto activo.
  Future<Task> create(
    String text, {
    String? projectId,
    String? environmentId,
  }) async => Task.fromJson(
    await _client.postJson('/api/v1/tasks', {
      'text': text,
      'project_id': ?projectId,
      'environment_id': ?environmentId,
    }),
  );

  Future<List<Task>> list({
    List<String> statuses = const [],
    int limit = 20,
  }) async {
    final json = await _client.getJson(
      '/api/v1/tasks',
      query: {'limit': limit, if (statuses.isNotEmpty) 'status': statuses},
    );
    return [
      for (final item in json['items'] as List)
        Task.fromJson(item as Map<String, dynamic>),
    ];
  }

  Future<Task> get(String id) async =>
      Task.fromJson(await _client.getJson('/api/v1/tasks/$id'));

  Future<List<TaskEvent>> events(String id) async => [
    for (final json in await _client.getList('/api/v1/tasks/$id/events'))
      TaskEvent.fromJson(json),
  ];

  Future<Task> cancel(Task task) async => Task.fromJson(
    await _client.postJson('/api/v1/tasks/${task.id}/cancel', {
      'version': task.version,
    }),
  );
}
