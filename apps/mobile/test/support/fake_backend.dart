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

  Future<ResponseBody> handle(RequestOptions o) async {
    final body = switch (o.data) {
      final Map<String, dynamic> m => m,
      final String s when s.isNotEmpty => jsonDecode(s) as Map<String, dynamic>,
      _ => const <String, dynamic>{},
    };
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
