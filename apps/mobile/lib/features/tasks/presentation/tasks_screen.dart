import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../../context/presentation/context_chip.dart';
import '../data/task_repository.dart';
import 'task_card.dart';
import 'task_status.dart';

/// Lista de tareas del workspace con filtro por estado (HU-17).
class TasksScreen extends ConsumerStatefulWidget {
  const TasksScreen({super.key});

  @override
  ConsumerState<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends ConsumerState<TasksScreen> {
  TaskFilter _filter = TaskFilter.all;
  late Future<List<Task>> _tasks = _load();

  Future<List<Task>> _load() => ref
      .read(taskRepositoryProvider)
      .list(statuses: _filter.statuses, limit: 50);

  void _select(TaskFilter filter) => setState(() {
    _filter = filter;
    _tasks = _load();
  });

  @override
  Widget build(BuildContext context) {
    ref.listen(contextProvider.select((c) => c.value?.workspace.id), (
      previous,
      next,
    ) {
      if (previous != null && previous != next) _select(_filter);
    });
    return Scaffold(
      appBar: AppBar(title: const Text('Tareas')),
      body: RefreshIndicator(
        onRefresh: () async {
          _select(_filter);
          await _tasks;
        },
        child: ListView(
          padding: const EdgeInsets.all(Space.lg),
          children: [
            const Align(alignment: Alignment.centerLeft, child: ContextChip()),
            const SizedBox(height: Space.md),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final filter in TaskFilter.values)
                    Padding(
                      padding: const EdgeInsets.only(right: Space.sm),
                      child: ChoiceChip(
                        label: Text(filter.label),
                        selected: filter == _filter,
                        onSelected: (_) => _select(filter),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: Space.md),
            FutureBuilder<List<Task>>(
              future: _tasks,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Padding(
                    padding: EdgeInsets.all(Space.xl),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                if (snapshot.error case final AppError error) {
                  return ListTile(
                    leading: const Icon(Icons.error_outline),
                    title: Text(error.title),
                    subtitle: Text(error.message),
                  );
                }
                final tasks = snapshot.data ?? const <Task>[];
                if (tasks.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.all(Space.xl),
                    child: Text('No hay tareas con este filtro.'),
                  );
                }
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [for (final task in tasks) TaskCard(task: task)],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
