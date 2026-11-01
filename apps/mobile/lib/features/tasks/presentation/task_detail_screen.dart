import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../data/task_repository.dart';
import 'plan_view.dart';
import 'task_status.dart';

typedef _Detail = (Task, List<TaskEvent>, TaskPlan?);

/// Detalle de tarea: qué se pidió, en qué estado está, su plan, su historial y lo que se puede hacer.
class TaskDetailScreen extends ConsumerStatefulWidget {
  const TaskDetailScreen({super.key, required this.taskId});

  final String taskId;

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  late Future<_Detail> _data = _load();
  bool _busy = false;

  TaskRepository get _repo => ref.read(taskRepositoryProvider);

  Future<_Detail> _load() async => (
    await _repo.get(widget.taskId),
    await _repo.events(widget.taskId),
    await _repo.latestPlan(widget.taskId),
  );

  /// Ejecuta un comando, muestra el error si lo hay y recarga el detalle.
  Future<void> _run(Future<Task> Function() command) async {
    setState(() => _busy = true);
    try {
      await command();
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
    if (confirmed == true && mounted) await _run(() => _repo.cancel(task));
  }

  Future<void> _edit(Task task) async {
    final text = await showDialog<String>(
      context: context,
      builder: (_) => _EditDialog(initial: task.description),
    );
    if (text == null || text.length < 3 || !mounted) return;
    await _run(() => _repo.edit(task, text: text));
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Tarea')),
      body: FutureBuilder<_Detail>(
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
          final (task, events, plan) = data;
          return ListView(
            padding: const EdgeInsets.all(Space.lg),
            children: [
              TaskStatusPill(status: task.status, label: task.statusLabel),
              if (task.statusReason != null) ...[
                const SizedBox(height: Space.sm),
                Text(task.statusReason!, style: text.bodyMedium),
              ],
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
              if (plan != null) ...[
                const SizedBox(height: Space.xl),
                PlanView(plan: plan),
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
      bottomNavigationBar: FutureBuilder<_Detail>(
        future: _data,
        builder: (context, snapshot) {
          final task = snapshot.data?.$1;
          if (task == null) return const SizedBox.shrink();
          final actions = [
            if (task.canPlan)
              FilledButton.icon(
                onPressed: _busy ? null : () => _run(() => _repo.plan(task)),
                icon: _busy
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.auto_awesome),
                label: const Text('Preparar plan'),
              ),
            if (task.canEdit)
              FilledButton.icon(
                onPressed: _busy ? null : () => _edit(task),
                icon: const Icon(Icons.edit),
                label: const Text('Ajustar y reintentar'),
              ),
            if (task.canCancel)
              OutlinedButton.icon(
                onPressed: _busy ? null : () => _cancel(task),
                icon: const Icon(Icons.close),
                label: const Text('Cancelar tarea'),
              ),
          ];
          if (actions.isEmpty) return const SizedBox.shrink();
          return SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(Space.lg),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  for (final (i, action) in actions.indexed) ...[
                    if (i > 0) const SizedBox(height: Space.sm),
                    action,
                  ],
                ],
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

/// Diálogo con su propio controlador: se libera cuando el diálogo termina de cerrarse.
class _EditDialog extends StatefulWidget {
  const _EditDialog({required this.initial});

  final String initial;

  @override
  State<_EditDialog> createState() => _EditDialogState();
}

class _EditDialogState extends State<_EditDialog> {
  late final _controller = TextEditingController(text: widget.initial);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Ajusta tu pedido'),
    content: TextField(
      key: const Key('edit-input'),
      controller: _controller,
      minLines: 2,
      maxLines: 5,
      autofocus: true,
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancelar'),
      ),
      FilledButton(
        onPressed: () => Navigator.pop(context, _controller.text.trim()),
        child: const Text('Guardar'),
      ),
    ],
  );
}
