import 'package:aicc_mobile/app/app.dart';
import 'package:aicc_mobile/app/providers.dart';
import 'package:aicc_mobile/core/config/app_config.dart';
import 'package:aicc_mobile/core/network/api_client.dart';
import 'package:aicc_mobile/core/security/token_storage.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_backend.dart';
import '../support/fake_http.dart';

const _email = 'ana@example.com';
const _password = 'clave-larga-123';

Future<void> _pumpApp(
  WidgetTester tester,
  FakeBackend backend,
  TokenStorage storage,
) async {
  final dio = Dio(BaseOptions(baseUrl: 'http://api.test'))
    ..httpClientAdapter = FakeAdapter(backend.handle);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        appConfigProvider.overrideWithValue(
          const AppConfig(apiBaseUrl: 'http://api.test', environment: 'test'),
        ),
        tokenStorageProvider.overrideWithValue(storage),
        baseApiClientProvider.overrideWithValue(
          ApiClient(baseUrl: 'http://api.test', dio: dio),
        ),
      ],
      child: const AiccApp(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _fillAndSubmitLogin(WidgetTester tester, String password) async {
  await tester.enterText(find.widgetWithText(TextFormField, 'Email'), _email);
  await tester.enterText(
    find.widgetWithText(TextFormField, 'Contraseña'),
    password,
  );
  await tester.tap(find.widgetWithText(FilledButton, 'Entrar'));
  await tester.pumpAndSettle();
}

void main() {
  late FakeBackend backend;
  late InMemoryTokenStorage storage;

  setUp(() {
    backend = FakeBackend()..addUser(_email, _password, name: 'Ana');
    storage = InMemoryTokenStorage();
  });

  testWidgets('sin sesión guardada se abre el login', (tester) async {
    await _pumpApp(tester, backend, storage);

    expect(find.text('Bienvenido a AICC'), findsOneWidget);
  });

  testWidgets('login correcto lleva al inicio y guarda la sesión', (
    tester,
  ) async {
    await _pumpApp(tester, backend, storage);

    await _fillAndSubmitLogin(tester, _password);

    expect(find.text('Hola, Ana'), findsOneWidget);
    expect(find.text('Espacio de Ana › General · Dev'), findsOneWidget);
    expect(find.text('AICC está listo'), findsOneWidget);
    expect(await storage.read(), isNotNull);
  });

  testWidgets('credenciales incorrectas muestran un error humano', (
    tester,
  ) async {
    await _pumpApp(tester, backend, storage);

    await _fillAndSubmitLogin(tester, 'otra-clave-123');

    expect(
      find.textContaining('Email o contraseña incorrectos'),
      findsOneWidget,
    );
    expect(find.text('Bienvenido a AICC'), findsOneWidget);
    expect(await storage.read(), isNull);
  });

  testWidgets('valida campos antes de llamar al servidor', (tester) async {
    await _pumpApp(tester, backend, storage);

    await tester.tap(find.widgetWithText(FilledButton, 'Entrar'));
    await tester.pumpAndSettle();

    expect(find.text('Escribe tu email'), findsOneWidget);
    expect(find.text('Escribe tu contraseña'), findsOneWidget);
  });

  testWidgets('sesión guardada se restaura sin pedir contraseña', (
    tester,
  ) async {
    final tokens = await backend.handle(
      RequestOptions(
        path: '/api/v1/auth/login',
        data: {'email': _email, 'password': _password},
      ),
    );
    expect(tokens.statusCode, 200);
    final issued = backend.validRefresh.keys.single;
    await storage.save(
      StoredTokens(
        accessToken: backend.validAccess.keys.single,
        refreshToken: issued,
      ),
    );

    await _pumpApp(tester, backend, storage);

    expect(find.text('Hola, Ana'), findsOneWidget);
  });

  testWidgets('cerrar sesión vuelve al login y borra los tokens', (
    tester,
  ) async {
    await _pumpApp(tester, backend, storage);
    await _fillAndSubmitLogin(tester, _password);

    await tester.tap(find.byTooltip('Cerrar sesión'));
    await tester.pumpAndSettle();

    expect(find.text('Bienvenido a AICC'), findsOneWidget);
    expect(await storage.read(), isNull);
  });

  testWidgets('registro crea la cuenta y entra directamente', (tester) async {
    await _pumpApp(tester, backend, storage);
    await tester.tap(find.text('¿No tienes cuenta? Crear cuenta'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Tu nombre (opcional)'),
      'Luis',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'luis@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Contraseña'),
      'otra-clave-muy-larga',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Crear cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Hola, Luis'), findsOneWidget);
  });

  testWidgets('registro exige contraseña de 12 caracteres', (tester) async {
    await _pumpApp(tester, backend, storage);
    await tester.tap(find.text('¿No tienes cuenta? Crear cuenta'));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'luis@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Contraseña'),
      'corta',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Crear cuenta'));
    await tester.pumpAndSettle();

    expect(find.text('Usa al menos 12 caracteres'), findsOneWidget);
    expect(backend.users.containsKey('luis@example.com'), isFalse);
  });
}
