import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/app_harness.dart';
import '../support/fake_backend.dart';

void main() {
  late FakeBackend backend;

  setUp(() {
    backend = FakeBackend()..addUser(testEmail, testPassword, name: 'Ana');
  });

  testWidgets('escribir y enviar crea una tarea en Borrador (3 toques)', (
    tester,
  ) async {
    await pumpSignedInApp(tester, backend);
    expect(
      find.text('Aún no has pedido nada. Escribe arriba qué necesitas.'),
      findsOneWidget,
    );

    // Toque 1: el campo. Toque 2: el teclado (escribir). Toque 3: Enviar.
    await tester.tap(find.byKey(const Key('command-input')));
    await tester.enterText(
      find.byKey(const Key('command-input')),
      'Responde a los leads de hoy',
    );
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Enviar'));
    await tester.pumpAndSettle();

    expect(find.text('Tarea'), findsOneWidget);
    expect(find.text('Responde a los leads de hoy'), findsWidgets);
    expect(find.text('Borrador'), findsOneWidget);
    expect(find.text('Se creó la tarea'), findsOneWidget);
    expect(backend.tasks.single['project']['name'], 'General');

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.text('Responde a los leads de hoy'), findsOneWidget);
  });

  testWidgets('enviar está deshabilitado sin texto suficiente', (tester) async {
    await pumpSignedInApp(tester, backend);

    final button = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Enviar'),
    );

    expect(button.onPressed, isNull);
  });

  testWidgets('cancelar desde el detalle deja la tarea Cancelada', (
    tester,
  ) async {
    await pumpSignedInApp(tester, backend);
    await tester.enterText(
      find.byKey(const Key('command-input')),
      'Tarea para cancelar',
    );
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Enviar'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Cancelar tarea'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Sí, cancelar'));
    await tester.pumpAndSettle();

    expect(find.text('Cancelada'), findsOneWidget);
    expect(find.text('Borrador → Cancelada'), findsOneWidget);
    expect(find.text('Cancelar tarea'), findsNothing);
    expect(backend.tasks.single['version'], 2);
  });

  testWidgets('la lista filtra por estado', (tester) async {
    await pumpSignedInApp(tester, backend);
    for (final text in ['Primera tarea', 'Segunda tarea']) {
      await tester.enterText(find.byKey(const Key('command-input')), text);
      await tester.pump();
      await tester.tap(find.widgetWithText(FilledButton, 'Enviar'));
      await tester.pumpAndSettle();
      await tester.pageBack();
      await tester.pumpAndSettle();
    }
    backend.tasks.last
      ..['status'] = 'CANCELLED'
      ..['status_label'] = 'Cancelada';

    await tester.tap(find.text('Ver todas'));
    await tester.pumpAndSettle();
    expect(find.text('Primera tarea'), findsOneWidget);
    expect(find.text('Segunda tarea'), findsOneWidget);

    await tester.tap(find.text('Borradores'));
    await tester.pumpAndSettle();
    expect(find.text('Segunda tarea'), findsOneWidget);
    expect(find.text('Primera tarea'), findsNothing);

    await tester.scrollUntilVisible(
      find.text('Canceladas o rechazadas'),
      200,
      scrollable: find.byType(Scrollable).last,
    );
    await tester.tap(find.text('Canceladas o rechazadas'));
    await tester.pumpAndSettle();
    expect(find.text('Primera tarea'), findsOneWidget);
    expect(find.text('Segunda tarea'), findsNothing);
  });
}
