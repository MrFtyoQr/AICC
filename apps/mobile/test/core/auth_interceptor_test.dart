import 'package:aicc_mobile/core/errors/app_error.dart';
import 'package:aicc_mobile/core/network/api_client.dart';
import 'package:aicc_mobile/core/network/auth_interceptor.dart';
import 'package:aicc_mobile/core/security/token_storage.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import '../support/fake_http.dart';

void main() {
  late FakeBackend backend;
  late InMemoryTokenStorage storage;
  late ApiClient client;
  late int expiredCalls;

  setUp(() async {
    backend = FakeBackend()..addUser('ana@example.com', 'clave-larga-123');
    storage = InMemoryTokenStorage();
    expiredCalls = 0;
    final dio = Dio(BaseOptions(baseUrl: 'http://api.test'))
      ..httpClientAdapter = FakeAdapter(backend.handle);
    dio.interceptors.add(
      AuthInterceptor(
        dio: dio,
        storage: storage,
        onSessionExpired: () => expiredCalls++,
      ),
    );
    client = ApiClient(baseUrl: 'http://api.test', dio: dio);
    final tokens = await client.postJson('/api/v1/auth/login', {
      'email': 'ana@example.com',
      'password': 'clave-larga-123',
    });
    await storage.save(
      StoredTokens(
        accessToken: tokens['access_token'] as String,
        refreshToken: tokens['refresh_token'] as String,
      ),
    );
  });

  test('adjunta el access token', () async {
    final me = await client.getJson('/api/v1/me');

    expect(me['email'], 'ana@example.com');
    expect(backend.refreshCalls, 0);
  });

  test(
    'access vencido: renueva una vez, guarda el par nuevo y reintenta',
    () async {
      final before = await storage.read();
      backend.expireAccessTokens();

      final me = await client.getJson('/api/v1/me');

      expect(me['email'], 'ana@example.com');
      expect(backend.refreshCalls, 1);
      final after = await storage.read();
      expect(after!.refreshToken, isNot(before!.refreshToken));
    },
  );

  test(
    'varias peticiones con 401 a la vez provocan una sola renovación',
    () async {
      backend.expireAccessTokens();

      final results = await Future.wait([
        client.getJson('/api/v1/me'),
        client.getJson('/api/v1/me'),
        client.getJson('/api/v1/me'),
      ]);

      expect(results.map((r) => r['email']), everyElement('ana@example.com'));
      expect(backend.refreshCalls, 1);
    },
  );

  test('refresh inválido: borra la sesión y avisa que venció', () async {
    backend.revokeAll();

    await expectLater(
      client.getJson('/api/v1/me'),
      throwsA(isA<UnauthorizedError>()),
    );
    expect(await storage.read(), isNull);
    expect(expiredCalls, 1);
  });

  test(
    'los endpoints de auth no llevan token ni disparan renovación',
    () async {
      await expectLater(
        client.postJson('/api/v1/auth/login', {
          'email': 'ana@example.com',
          'password': 'mal',
        }),
        throwsA(isA<UnauthorizedError>()),
      );
      expect(backend.refreshCalls, 0);
      expect(expiredCalls, 0);
    },
  );
}
