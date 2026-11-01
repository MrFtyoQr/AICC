import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/app_harness.dart';
import '../support/fake_backend.dart';

Future<void> _createTask(WidgetTester tester, String text) async {
  await tester.enterText(find.byKey(const Key('command-input')), text);
  await tester.pump();
  await tester.tap(find.widgetWithText(FilledButton, 'Enviar'));
  await tester.pumpAndSettle();
}

void main() {
  late FakeBackend backend;

  setUp(() {
    backend = FakeBackend()..addUser(testEmail, testPassword, name: 'Ana');
  });

  testWidgets(
    'preparar plan muestra la propuesta con pasos, riesgo y supuestos',
    (tester) async {
      await pumpSignedInApp(tester, backend);
      await _createTask(tester, 'Resume las ventas de la semana');

      await tester.tap(find.text('Preparar plan'));
      await tester.pumpAndSettle();

      expect(find.text('Esperando tu aprobación'), findsOneWidget);
      expect(find.text('Propuesta de plan'), findsOneWidget);
      expect(find.text('Resumir un tema y avisarte'), findsOneWidget);
      expect(find.text('Redactar el resumen'), findsOneWidget);
      expect(find.text('Solo consulta'), findsOneWidget);
      expect(find.text('Cambia algo dentro de AICC'), findsOneWidget);
      expect(
        find.text('• El resumen se basa en conocimiento general.'),
        findsOneWidget,
      );
      expect(find.text('Preparar plan'), findsNothing);
    },
  );

  testWidgets('sin receta explica por qué y permite ajustar y reintentar', (
    tester,
  ) async {
    await pumpSignedInApp(tester, backend);
    await _createTask(tester, 'Lanza un cohete');

    await tester.tap(find.text('Preparar plan'));
    await tester.pumpAndSettle();
    expect(find.text('No pude armar un plan'), findsOneWidget);
    expect(
      find.text('Todavía no tengo una solución para ese pedido.'),
      findsOneWidget,
    );

    await tester.tap(find.text('Ajustar y reintentar'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('edit-input')),
      'Resume qué es un cohete',
    );
    await tester.tap(find.text('Guardar'));
    await tester.pumpAndSettle();
    expect(find.text('Borrador'), findsOneWidget);

    await tester.tap(find.text('Preparar plan'));
    await tester.pumpAndSettle();
    expect(find.text('Propuesta de plan'), findsOneWidget);
  });
}
