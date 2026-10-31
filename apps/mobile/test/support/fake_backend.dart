import 'dart:convert';

import 'package:dio/dio.dart';

import 'fake_http.dart';

/// Backend AICC en memoria con las reglas reales de auth: tokens rotatorios y 401 si vencen.
class FakeBackend {
  final users = <String, ({String password, String id, String? name})>{};
  final validAccess = <String, String>{}; // access token -> email
  final validRefresh = <String, String>{}; // refresh token -> email
  int refreshCalls = 0;
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
        final token = (o.headers['Authorization'] as String?)?.replaceFirst(
          'Bearer ',
          '',
        );
        final email = validAccess[token];
        if (email == null) return jsonBody(401, {'detail': 'No autenticado'});
        final u = users[email]!;
        return jsonBody(200, {
          'id': u.id,
          'email': email,
          'display_name': u.name,
        });
    }
    return jsonBody(404, {'detail': 'not found'});
  }
}
