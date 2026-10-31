import 'dart:convert';

import 'package:dio/dio.dart';

import 'fake_http.dart';

/// Backend AICC en memoria con las reglas reales de auth: tokens rotatorios y 401 si vencen.
class FakeBackend {
  final users = <String, ({String password, String id, String? name})>{};
  final validAccess = <String, String>{}; // access token -> email
  final validRefresh = <String, String>{}; // refresh token -> email
  int refreshCalls = 0;

  /// Workspaces adicionales (de equipo) por email, además del personal.
  final teamWorkspaces = <String, List<FakeWorkspace>>{};

  /// Proyectos del workspace personal; por defecto "General" con `development`.
  List<Map<String, dynamic>> personalProjects = [project('General')];

  /// Entradas que devuelve `/api/v1/activity`, más reciente primero.
  final activity = <Map<String, dynamic>>[];

  /// Valor de `X-Workspace-Id` recibido en cada llamada que depende del workspace.
  final workspaceHeaders = <String?>[];

  List<FakeWorkspace> workspacesOf(String email) {
    final u = users[email]!;
    return [
      FakeWorkspace(
        id: 'w-${u.id}',
        name: 'Espacio de ${u.name ?? email.split('@').first}',
        personal: true,
        role: 'owner',
        projects: personalProjects,
      ),
      ...?teamWorkspaces[email],
    ];
  }

  int _seq = 0;

  void addUser(String email, String password, {String? name}) =>
      users[email] = (password: password, id: 'u-${users.length}', name: name);

  /// Simula el vencimiento del access token (el refresh sigue siendo válido).
  void expireAccessTokens() => validAccess.clear();

  void revokeAll() {
    validAccess.clear();
    validRefresh.clear();
  }

  Map<String, String> _issue(String email) {
    _seq++;
    final access = 'access-$_seq';
    final refresh = 'refresh-$_seq';
    validAccess[access] = email;
    validRefresh[refresh] = email;
    return {
      'access_token': access,
      'refresh_token': refresh,
      'token_type': 'bearer',
    };
  }

  String? _authenticated(RequestOptions o) {
    final header = o.headers['Authorization'] as String?;
    return validAccess[header?.replaceFirst('Bearer ', '')];
  }

  /// Tareas creadas (más reciente primero) y su historial, como en la API real.
  final tasks = <Map<String, dynamic>>[];
  final taskEvents = <String, List<Map<String, dynamic>>>{};

  static const _labels = {'DRAFT': 'Borrador', 'CANCELLED': 'Cancelada'};

  ResponseBody? _handleTasks(RequestOptions o, Map<String, dynamic> body) {
    if (!o.path.startsWith('/api/v1/tasks')) return null;
    final email = _authenticated(o);
    if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
    final now = DateTime.now().toUtc().toIso8601String();
    final segments = o.path.split('/').skip(4).toList(); // tras /api/v1/tasks
    if (segments.isEmpty && o.method == 'POST') {
      final id = 't-${tasks.length}';
      final project = personalProjects.firstWhere(
        (p) => p['id'] == body['project_id'],
        orElse: () => personalProjects.first,
      );
      final task = {
        'id': id,
        'title': (body['text'] as String).split('\n').first,
        'description': body['text'],
        'status': 'DRAFT',
        'status_label': 'Borrador',
        'project': {'id': project['id'], 'name': project['name']},
        'environment': (project['environments'] as List).first,
        'version': 1,
        'allowed_commands': ['plan', 'cancel'],
        'created_at': now,
        'updated_at': now,
      };
      tasks.insert(0, task);
      taskEvents[id] = [
        {
          'id': 1,
          'type': 'task.created',
          'summary': 'Se creó la tarea',
          'payload': {},
          'created_at': now,
        },
      ];
      return jsonBody(201, task);
    }
    if (segments.isEmpty) {
      final statuses = switch (o.queryParameters['status']) {
        final List<dynamic> list => list.cast<String>(),
        final String one => [one],
        _ => const <String>[],
      };
      return jsonBody(200, {
        'items': [
          for (final t in tasks)
            if (statuses.isEmpty || statuses.contains(t['status'])) t,
        ],
        'next_cursor': null,
      });
    }
    final task = tasks.where((t) => t['id'] == segments.first).firstOrNull;
    if (task == null) return jsonBody(404, {'detail': 'Tarea no encontrada'});
    if (segments.length == 1) return jsonBody(200, task);
    if (segments[1] == 'events') return jsonBody(200, taskEvents[task['id']]!);
    if (segments[1] == 'cancel') {
      if (body['version'] != task['version']) {
        return jsonBody(409, {
          'detail': 'La tarea cambió mientras tanto; recárgala',
        });
      }
      final from = task['status'] as String;
      task
        ..['status'] = 'CANCELLED'
        ..['status_label'] = 'Cancelada'
        ..['version'] = (task['version'] as int) + 1
        ..['allowed_commands'] = <String>[];
      taskEvents[task['id']]!.add({
        'id': 2,
        'type': 'task.state_changed',
        'summary': '${_labels[from]} → Cancelada',
        'payload': {},
        'created_at': now,
      });
      return jsonBody(200, task);
    }
    return jsonBody(404, {'detail': 'not found'});
  }

  Future<ResponseBody> handle(RequestOptions o) async {
    final body = switch (o.data) {
      final Map<String, dynamic> m => m,
      final String s when s.isNotEmpty => jsonDecode(s) as Map<String, dynamic>,
      _ => const <String, dynamic>{},
    };
    if (_handleTasks(o, body) case final response?) return response;
    switch (o.path) {
      case '/health':
        return healthyApi(o);
      case '/health/ready':
        return healthyApi(o);
      case '/api/v1/auth/register':
        final email = body['email'] as String;
        if (users.containsKey(email)) {
          return jsonBody(409, {'detail': 'El email ya está registrado'});
        }
        addUser(
          email,
          body['password'] as String,
          name: body['display_name'] as String?,
        );
        final u = users[email]!;
        return jsonBody(201, {
          'id': u.id,
          'email': email,
          'display_name': u.name,
        });
      case '/api/v1/auth/login':
        final u = users[body['email']];
        if (u == null || u.password != body['password']) {
          return jsonBody(401, {'detail': 'Email o contraseña incorrectos'});
        }
        return jsonBody(200, _issue(body['email'] as String));
      case '/api/v1/auth/refresh':
        refreshCalls++;
        final email = validRefresh.remove(body['refresh_token']);
        if (email == null) {
          return jsonBody(401, {
            'detail': 'Sesión vencida; inicia sesión de nuevo',
          });
        }
        return jsonBody(200, _issue(email));
      case '/api/v1/auth/logout':
        validRefresh.remove(body['refresh_token']);
        return ResponseBody.fromString('', 204);
      case '/api/v1/me':
        final email = _authenticated(o);
        if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
        final u = users[email]!;
        return jsonBody(200, {
          'id': u.id,
          'email': email,
          'display_name': u.name,
        });
      case '/api/v1/workspaces':
        final email = _authenticated(o);
        if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
        return jsonBody(200, [
          for (final w in workspacesOf(email))
            {
              'id': w.id,
              'name': w.name,
              'is_personal': w.personal,
              'role': w.role,
              'permissions': ['project.write', 'workspace.read'],
            },
        ]);
      case '/api/v1/projects':
        final email = _authenticated(o);
        if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
        final workspaceId = o.headers['X-Workspace-Id'] as String?;
        workspaceHeaders.add(workspaceId);
        final workspace = workspacesOf(email)
            .where((w) => w.id == workspaceId)
            .firstOrNull;
        if (workspace == null) {
          return jsonBody(404, {'detail': 'Workspace no encontrado'});
        }
        return jsonBody(200, workspace.projects);
      case '/api/v1/activity':
        final email = _authenticated(o);
        if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
        workspaceHeaders.add(o.headers['X-Workspace-Id'] as String?);
        final cursor = o.queryParameters['cursor'] as String?;
        final start = cursor == null ? 0 : int.parse(cursor);
        final end = (start + 20).clamp(0, activity.length);
        return jsonBody(200, {
          'items': activity.sublist(start, end),
          'next_cursor': end < activity.length ? '$end' : null,
        });
    }
    return jsonBody(404, {'detail': 'not found'});
  }
}

class FakeWorkspace {
  const FakeWorkspace({
    required this.id,
    required this.name,
    required this.projects,
    this.personal = false,
    this.role = 'admin',
  });

  final String id;
  final String name;
  final bool personal;
  final String role;
  final List<Map<String, dynamic>> projects;
}

int _ids = 0;

Map<String, dynamic> project(
  String name, {
  List<(String, String)> environments = const [('development', 'development')],
}) => {
  'id': 'p-${_ids++}',
  'name': name,
  'description': null,
  'environments': [
    for (final (envName, kind) in environments)
      {'id': 'e-${_ids++}', 'name': envName, 'kind': kind},
  ],
};
