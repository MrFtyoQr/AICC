import 'dart:async';

import 'package:aicc_mobile/app/theme/app_theme.dart';
import 'package:aicc_mobile/features/connection/data/health_repository.dart';
import 'package:aicc_mobile/features/connection/presentation/connection_screen.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_http.dart';

Widget _screen(Responder respond) => MaterialApp(
  theme: AppTheme.light(),
  home: ConnectionScreen(
    repository: HealthRepository(fakeClient(respond)),
    appEnvironment: 'test',
  ),
);

void main() {
  testWidgets('muestra "Comprobando" mientras espera sin bloquear la UI', (
    tester,
  ) async {
    final pending = Completer<ResponseBody>();
    await tester.pumpWidget(_screen((_) => pending.future));

    expect(find.text('Comprobando…'), findsOneWidget);
    expect(find.text('Volver a comprobar'), findsOneWidget);

    pending.complete(await healthyApi(RequestOptions(path: '/health')));
    await tester.pumpAndSettle();
  });

  testWidgets('API y dependencias sanas → "AICC está listo"', (tester) async {
    await tester.pumpWidget(_screen(healthyApi));
    await tester.pumpAndSettle();

    expect(find.text('AICC está listo'), findsOneWidget);
    expect(find.text('Base de datos'), findsOneWidget);
    expect(find.text('Cola de trabajos'), findsOneWidget);
    expect(find.textContaining('Versión 0.1.0'), findsOneWidget);
  });

  testWidgets('dependencia caída → aviso parcial con detalle', (tester) async {
    await tester.pumpWidget(_screen(degradedApi));
    await tester.pumpAndSettle();

    expect(find.text('Funcionando a medias'), findsOneWidget);
    expect(find.text('Sin respuesta'), findsOneWidget);
  });

  testWidgets('API caída → mensaje humano y reintento que recupera', (
    tester,
  ) async {
    var apiUp = false;
    await tester.pumpWidget(
      _screen((o) => apiUp ? healthyApi(o) : unreachableApi(o)),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sin conexión con AICC'), findsOneWidget);

    apiUp = true;
    await tester.tap(find.text('Volver a comprobar'));
    await tester.pumpAndSettle();

    expect(find.text('AICC está listo'), findsOneWidget);
  });

  testWidgets('tema oscuro también renderiza los estados', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: ConnectionScreen(
          repository: HealthRepository(fakeClient(healthyApi)),
          appEnvironment: 'test',
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Todo en orden'), findsOneWidget);
  });
}
