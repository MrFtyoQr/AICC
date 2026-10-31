import 'package:aicc_mobile/app/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/app_harness.dart';
import '../support/fake_backend.dart';

void main() {
  late FakeBackend backend;

  setUp(() {
    backend = FakeBackend()..addUser(testEmail, testPassword, name: 'Ana');
  });

  testWidgets('el inicio muestra workspace, proyecto y ambiente', (
    tester,
  ) async {
    await pumpSignedInApp(tester, backend);

    expect(find.text('Espacio de Ana › General · Dev'), findsOneWidget);
    expect(backend.workspaceHeaders, contains('w-u-0'));
  });

  testWidgets('producción se distingue en rojo', (tester) async {
    backend.personalProjects = [
      project('Tienda', environments: [('prod', 'production')]),
    ];
    await pumpSignedInApp(tester, backend);

    final chip = tester.widget<Material>(
      find
          .ancestor(
            of: find.byKey(const Key('context-chip')),
            matching: find.byType(Material),
          )
          .first,
    );
    final context = tester.element(find.byKey(const Key('context-chip')));
    expect(find.text('Espacio de Ana › Tienda · Producción'), findsOneWidget);
    expect(
      (chip.shape! as StadiumBorder).side.color,
      context.statusColors.danger,
    );
  });

  testWidgets('el chip abre el selector y cambia de workspace en un toque', (
    tester,
  ) async {
    backend.teamWorkspaces[testEmail] = [
      FakeWorkspace(
        id: 'w-team',
        name: 'Panadería',
        projects: [
          project(
            'Pedidos',
            environments: [
              ('development', 'development'),
              ('prod', 'production'),
            ],
          ),
        ],
      ),
    ];
    await pumpSignedInApp(tester, backend);

    await tester.tap(find.byKey(const Key('context-chip')));
    await tester.pumpAndSettle();
    expect(find.text('¿Dónde quieres trabajar?'), findsOneWidget);

    await tester.tap(find.text('Panadería'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('prod · Producción'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Listo'));
    await tester.pumpAndSettle();

    expect(find.text('Panadería › Pedidos · Producción'), findsOneWidget);
    expect(backend.workspaceHeaders.last, 'w-team');
  });

  testWidgets('Actividad lista en lenguaje claro y pagina', (tester) async {
    for (var i = 0; i < 25; i++) {
      backend.activity.add({
        'id': 'a-$i',
        'created_at': DateTime.now().toUtc().toIso8601String(),
        'actor': {'email': testEmail, 'display_name': 'Ana'},
        'action': 'project.create',
        'summary': 'Creó el proyecto «P$i»',
        'outcome': i == 0 ? 'denied' : 'success',
      });
    }
    await pumpSignedInApp(tester, backend);

    await tester.tap(find.byTooltip('Actividad'));
    await tester.pumpAndSettle();

    expect(find.text('Creó el proyecto «P0»'), findsOneWidget);
    expect(find.text('Sin permiso'), findsOneWidget);
    expect(find.text('Ana · hace un momento'), findsWidgets);

    await tester.scrollUntilVisible(find.text('Ver más'), 300);
    await tester.tap(find.text('Ver más'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Creó el proyecto «P24»'), 300);

    expect(find.text('Creó el proyecto «P24»'), findsOneWidget);
    expect(find.text('Ver más'), findsNothing);
  });
}
