import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../data/task_repository.dart';
import 'task_status.dart';

/// Detalle de tarea: qué se pidió, en qué estado está, su historial y lo que se puede hacer.
class TaskDetailScreen extends ConsumerStatefulWidget {
  const TaskDetailScreen({super.key, required this.taskId});

  final String taskId;

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  late Future<(Task, List<TaskEvent>)> _data = _load();
  bool _busy = false;

  TaskRepository get _repo => ref.read(taskRepositoryProvider);

  Future<(Task, List<TaskEvent>)> _load() async =>
      (await _repo.get(widget.taskId), await _repo.events(widget.taskId));

  Future<void> _cancel(Task task) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('¿Cancelar esta tarea?'),
        content: const Text('No se ejecutará nada más de ella.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('No'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Sí, cancelar'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      await _repo.cancel(task);
      ref.invalidate(recentTasksProvider);
    } on AppError catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.message)));
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _data = _load();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Tarea')),
      body: FutureBuilder<(Task, List<TaskEvent>)>(
        future: _data,
        builder: (context, snapshot) {
          if (snapshot.error case final AppError error) {
            return ListTile(
              leading: const Icon(Icons.error_outline),
              title: Text(error.title),
              subtitle: Text(error.message),
            );
          }
          final data = snapshot.data;
          if (data == null) {
            return const Center(child: CircularProgressIndicator());
          }
          final (task, events) = data;
          return ListView(
            padding: const EdgeInsets.all(Space.lg),
            children: [
              TaskStatusPill(status: task.status, label: task.statusLabel),
              const SizedBox(height: Space.md),
              Text(task.title, style: text.headlineSmall),
              const SizedBox(height: Space.xs),
              Text(
                '${task.projectName} · ${task.environmentName}',
                style: text.bodySmall,
              ),
              // Si lo pedido cabe en el título, no se repite.
              if (task.description != task.title) ...[
                const SizedBox(height: Space.lg),
                Text(task.description, style: text.bodyLarge),
              ],
              const SizedBox(height: Space.xl),
              Text('Historial', style: text.titleMedium),
              for (final event in events)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.timeline),
                  title: Text(event.summary),
                  subtitle: Text(_when(event.createdAt)),
                ),
            ],
          );
        },
      ),
      bottomNavigationBar: FutureBuilder<(Task, List<TaskEvent>)>(
        future: _data,
        builder: (context, snapshot) {
          final task = snapshot.data?.$1;
          if (task == null || !task.canCancel) return const SizedBox.shrink();
          return SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(Space.lg),
              child: OutlinedButton.icon(
                onPressed: _busy ? null : () => _cancel(task),
                icon: const Icon(Icons.close),
                label: const Text('Cancelar tarea'),
              ),
            ),
          );
        },
      ),
    );
  }

  static String _when(DateTime at) {
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(at.day)}/${two(at.month)} ${two(at.hour)}:${two(at.minute)}';
  }
}
