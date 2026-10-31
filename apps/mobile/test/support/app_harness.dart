import 'package:aicc_mobile/app/app.dart';
import 'package:aicc_mobile/app/providers.dart';
import 'package:aicc_mobile/core/config/app_config.dart';
import 'package:aicc_mobile/core/network/api_client.dart';
import 'package:aicc_mobile/core/security/token_storage.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'fake_backend.dart';
import 'fake_http.dart';

const testEmail = 'ana@example.com';
const testPassword = 'clave-larga-123';

/// Arranca la app completa contra [backend] con la sesión de Ana ya iniciada.
Future<void> pumpSignedInApp(WidgetTester tester, FakeBackend backend) async {
  final dio = Dio(BaseOptions(baseUrl: 'http://api.test'))
    ..httpClientAdapter = FakeAdapter(backend.handle);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        appConfigProvider.overrideWithValue(
          const AppConfig(apiBaseUrl: 'http://api.test', environment: 'test'),
        ),
        tokenStorageProvider.overrideWithValue(InMemoryTokenStorage()),
        baseApiClientProvider.overrideWithValue(
          ApiClient(baseUrl: 'http://api.test', dio: dio),
        ),
      ],
      child: const AiccApp(),
    ),
  );
  await tester.pumpAndSettle();
  await tester.enterText(
    find.widgetWithText(TextFormField, 'Email'),
    testEmail,
  );
  await tester.enterText(
    find.widgetWithText(TextFormField, 'Contraseña'),
    testPassword,
  );
  await tester.tap(find.widgetWithText(FilledButton, 'Entrar'));
  await tester.pumpAndSettle();
}
