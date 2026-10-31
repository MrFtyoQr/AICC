import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router/app_router.dart';
import '../../../app/theme/tokens.dart';
import '../data/task_repository.dart';
import 'task_status.dart';

/// Tarjeta de tarea: el componente central del Command Center (O1-UX-01).
class TaskCard extends StatelessWidget {
  const TaskCard({super.key, required this.task});

  final Task task;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(Radii.card),
        onTap: () => context.push(Routes.task(task.id)),
        child: Padding(
          padding: const EdgeInsets.all(Space.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TaskStatusPill(status: task.status, label: task.statusLabel),
              const SizedBox(height: Space.sm),
              Text(
                task.title,
                style: text.titleMedium,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: Space.xs),
              Text(
                '${task.projectName} · ${task.environmentName}',
                style: text.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
