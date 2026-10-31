import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/app_theme.dart';
import '../../../app/theme/tokens.dart';
import '../data/context_repository.dart';
import 'context_sheet.dart';

/// "Siempre sabes dónde estás" (principios-ux §1.4): `Workspace › Proyecto · Ambiente`.
/// Producción en rojo y staging en ámbar, siempre con icono y texto. Un toque abre el selector.
class ContextChip extends ConsumerWidget {
  const ContextChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final appContext = ref.watch(contextProvider).value;
    if (appContext == null) return const SizedBox.shrink();
    final colors = context.statusColors;
    final kind = appContext.environment?.kind;
    final (color, icon) = switch (kind) {
      EnvironmentKind.production => (
        colors.danger,
        Icons.local_fire_department,
      ),
      EnvironmentKind.staging => (colors.warning, Icons.science_outlined),
      _ => (colors.neutral, Icons.code),
    };
    final parts = [
      appContext.workspace.name,
      if (appContext.project != null) '› ${appContext.project!.name}',
      if (kind != null) '· ${kind.label}',
    ];
    return Semantics(
      button: true,
      label: 'Contexto actual: ${parts.join(' ')}. Toca para cambiar.',
      excludeSemantics: true,
      child: Material(
        color: color.withValues(alpha: 0.12),
        shape: StadiumBorder(side: BorderSide(color: color)),
        child: InkWell(
          key: const Key('context-chip'),
          customBorder: const StadiumBorder(),
          onTap: () => showContextSheet(context),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: Space.md,
              vertical: Space.sm,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 18, color: color),
                const SizedBox(width: Space.sm),
                Flexible(
                  child: Text(
                    parts.join(' '),
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelLarge,
                  ),
                ),
                const SizedBox(width: Space.xs),
                const Icon(Icons.expand_more, size: 18),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
