import '../../../core/network/api_client.dart';
import '../../../core/security/token_storage.dart';

class AuthUser {
  const AuthUser({required this.id, required this.email, this.displayName});

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
    id: json['id'] as String,
    email: json['email'] as String,
    displayName: json['display_name'] as String?,
  );

  final String id;
  final String email;
  final String? displayName;
}

class AuthRepository {
  AuthRepository(this._client, this._storage);

  final ApiClient _client;
  final TokenStorage _storage;

  Future<bool> hasStoredSession() async => await _storage.read() != null;

  Future<void> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    await _client.postJson('/api/v1/auth/register', {
      'email': email,
      'password': password,
      'display_name': ?displayName,
    });
  }

  Future<AuthUser> login({
    required String email,
    required String password,
  }) async {
    final body = await _client.postJson('/api/v1/auth/login', {
      'email': email,
      'password': password,
    });
    await _storage.save(
      StoredTokens(
        accessToken: body['access_token'] as String,
        refreshToken: body['refresh_token'] as String,
      ),
    );
    return me();
  }

  Future<AuthUser> me() async =>
      AuthUser.fromJson(await _client.getJson('/api/v1/me'));

  /// Revoca la sesión en el servidor si se puede; localmente se borra siempre.
  Future<void> logout() async {
    final tokens = await _storage.read();
    await _storage.clear();
    if (tokens == null) return;
    try {
      await _client.post('/api/v1/auth/logout', {
        'refresh_token': tokens.refreshToken,
      });
    } on Exception {
      // Sin red el token caduca solo; la sesión local ya no existe.
    }
  }

  Future<void> clearLocalSession() => _storage.clear();
}
