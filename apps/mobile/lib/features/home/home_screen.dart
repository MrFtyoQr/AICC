import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/providers.dart';
import '../../app/router/app_router.dart';
import '../../app/theme/tokens.dart';
import '../authentication/application/session_controller.dart';
import '../context/presentation/context_chip.dart';
import '../tasks/presentation/command_box.dart';
import '../tasks/presentation/task_card.dart';

/// M3: Command Center. Contexto arriba, "¿Qué necesitas?" y las tareas recientes.
/// El estado de la conexión pasa a su propia pantalla (icono de la barra).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final user = session is SignedIn ? session.user : null;
    final name = user?.displayName ?? user?.email ?? '';
    final recent = ref.watch(recentTasksProvider);
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(
        title: Text('Hola, $name'),
        actions: [
          IconButton(
            tooltip: 'Estado de AICC',
            icon: const Icon(Icons.wifi_tethering),
            onPressed: () => context.push(Routes.status),
          ),
          IconButton(
            tooltip: 'Actividad',
            icon: const Icon(Icons.history),
            onPressed: () => context.push(Routes.activity),
          ),
          IconButton(
            tooltip: 'Cerrar sesión',
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(sessionProvider.notifier).signOut(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(recentTasksProvider.future),
        child: ListView(
          padding: const EdgeInsets.all(Space.lg),
          children: [
            const Align(alignment: Alignment.centerLeft, child: ContextChip()),
            const SizedBox(height: Space.md),
            const CommandBox(),
            const SizedBox(height: Space.xl),
            Row(
              children: [
                Expanded(
                  child: Text('Tareas recientes', style: text.titleMedium),
                ),
                TextButton(
                  onPressed: () => context.push(Routes.tasks),
                  child: const Text('Ver todas'),
                ),
              ],
            ),
            ...switch (recent) {
              AsyncData(:final value) when value.isEmpty => [
                const Padding(
                  padding: EdgeInsets.all(Space.lg),
                  child: Text(
                    'Aún no has pedido nada. Escribe arriba qué necesitas.',
                  ),
                ),
              ],
              AsyncData(:final value) => [
                for (final task in value) TaskCard(task: task),
              ],
              AsyncError() => [
                const ListTile(
                  leading: Icon(Icons.error_outline),
                  title: Text('No pudimos cargar tus tareas'),
                ),
              ],
              _ => [const Center(child: CircularProgressIndicator())],
            },
          ],
        ),
      ),
    );
  }
}
