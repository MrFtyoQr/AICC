import 'package:flutter/material.dart';

import '../../app/theme/app_theme.dart';
import '../../app/theme/tokens.dart';

enum StatusKind { success, warning, danger, info, running, waiting, neutral }

/// Estado con color + icono + texto (nunca solo color, por accesibilidad).
class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.kind, required this.label});

  final StatusKind kind;
  final String label;

  @override
  Widget build(BuildContext context) {
    final colors = context.statusColors;
    final (color, icon) = switch (kind) {
      StatusKind.success => (colors.success, Icons.check_circle),
      StatusKind.warning => (colors.warning, Icons.warning_amber_rounded),
      StatusKind.danger => (colors.danger, Icons.error),
      StatusKind.info => (colors.info, Icons.info),
      StatusKind.running => (colors.running, Icons.autorenew),
      StatusKind.waiting => (colors.waiting, Icons.hourglass_top),
      StatusKind.neutral => (colors.neutral, Icons.circle_outlined),
    };
    return Semantics(
      label: label,
      excludeSemantics: true,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: Space.md,
          vertical: Space.xs,
        ),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(width: Space.xs),
            Text(
              label,
              style: Theme.of(context).textTheme.labelLarge
                  ?.copyWith(color: color, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}
