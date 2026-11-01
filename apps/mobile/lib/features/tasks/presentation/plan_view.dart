import 'package:flutter/material.dart';

import '../../../app/theme/tokens.dart';
import '../../../shared/widgets/status_pill.dart';
import '../data/task_repository.dart';

/// "Propuesta de plan" (O2-APP-01): la solución elegida y sus pasos en lenguaje claro,
/// con el nivel de riesgo de cada uno y los supuestos. Nada de esto se ha ejecutado.
class PlanView extends StatelessWidget {
  const PlanView({super.key, required this.plan});

  final TaskPlan plan;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Space.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Propuesta de plan', style: text.labelLarge),
            const SizedBox(height: Space.xs),
            Text(plan.recipeTitle, style: text.titleLarge),
            const SizedBox(height: Space.xs),
            Text(
              'Versión ${plan.version} · todavía no se ha ejecutado nada',
              style: text.bodySmall,
            ),
            const SizedBox(height: Space.md),
            for (final (i, step) in plan.steps.indexed)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(radius: 14, child: Text('${i + 1}')),
                title: Text(step.title),
                subtitle: Align(
                  alignment: Alignment.centerLeft,
                  child: Padding(
                    padding: const EdgeInsets.only(top: Space.xs),
                    child: StatusPill(
                      kind: _riskKind(step.riskLevel),
                      label: step.riskLabel,
                    ),
                  ),
                ),
              ),
            if (plan.assumptions.isNotEmpty) ...[
              const SizedBox(height: Space.md),
              Text('Supuestos', style: text.labelLarge),
              for (final assumption in plan.assumptions)
                Padding(
                  padding: const EdgeInsets.only(top: Space.xs),
                  child: Text('• $assumption', style: text.bodyMedium),
                ),
            ],
          ],
        ),
      ),
    );
  }

  static StatusKind _riskKind(String risk) => switch (risk) {
    'read' => StatusKind.success,
    'write_internal' => StatusKind.info,
    'write_external' || 'spend' => StatusKind.warning,
    _ => StatusKind.danger,
  };
}
