import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../authentication/application/session_controller.dart';
import '../connection/presentation/connection_screen.dart';

/// M1: inicio provisional con saludo y estado de conexión.
/// En M2/M3 se convierte en la navegación inferior (Inicio · Comando · Aprobar · Más).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final user = session is SignedIn ? session.user : null;
    final name = user?.displayName ?? user?.email ?? '';
    return ConnectionScreen(
      repository: ref.watch(healthRepositoryProvider),
      appEnvironment: ref.watch(appConfigProvider).environment,
      title: 'Hola, $name',
      actions: [
        IconButton(
          tooltip: 'Cerrar sesión',
          icon: const Icon(Icons.logout),
          onPressed: () => ref.read(sessionProvider.notifier).signOut(),
        ),
      ],
    );
  }
}
