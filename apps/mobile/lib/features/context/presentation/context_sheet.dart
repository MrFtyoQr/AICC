import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/tokens.dart';

Future<void> showContextSheet(BuildContext context) => showModalBottomSheet(
  context: context,
  showDragHandle: true,
  isScrollControlled: true,
  builder: (_) => const ContextSheet(),
);

/// Cambiar de contexto en un toque: cada elección se aplica al instante.
class ContextSheet extends ConsumerWidget {
  const ContextSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(contextProvider);
    final controller = ref.read(contextProvider.notifier);
    final appContext = state.value;
    if (appContext == null) {
      return const Padding(
        padding: EdgeInsets.all(Space.xl),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    final text = Theme.of(context).textTheme;
    return SafeArea(
      child: ListView(
        shrinkWrap: true,
        padding: const EdgeInsets.fromLTRB(Space.lg, 0, Space.lg, Space.lg),
        children: [
          Text('¿Dónde quieres trabajar?', style: text.titleLarge),
          if (state.isLoading) const LinearProgressIndicator(),
          const SizedBox(height: Space.lg),
          Text('Workspace', style: text.labelLarge),
          for (final w in appContext.workspaces)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                w.isPersonal ? Icons.person_outline : Icons.groups_outlined,
              ),
              title: Text(w.name),
              subtitle: Text(w.roleLabel),
              trailing: w.id == appContext.workspace.id
                  ? const Icon(Icons.check)
                  : null,
              onTap: () => controller.selectWorkspace(w.id),
            ),
          const Divider(),
          Text('Proyecto', style: text.labelLarge),
          const SizedBox(height: Space.sm),
          Wrap(
            spacing: Space.sm,
            runSpacing: Space.sm,
            children: [
              for (final p in appContext.projects)
                ChoiceChip(
                  label: Text(p.name),
                  selected: p.id == appContext.project?.id,
                  onSelected: (_) => controller.selectProject(p.id),
                ),
            ],
          ),
          const SizedBox(height: Space.lg),
          Text('Ambiente', style: text.labelLarge),
          const SizedBox(height: Space.sm),
          Wrap(
            spacing: Space.sm,
            runSpacing: Space.sm,
            children: [
              for (final e in appContext.project?.environments ?? const [])
                ChoiceChip(
                  label: Text('${e.name} · ${e.kind.label}'),
                  selected: e.id == appContext.environment?.id,
                  onSelected: (_) => controller.selectEnvironment(e.id),
                ),
            ],
          ),
          const SizedBox(height: Space.xl),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Listo'),
          ),
        ],
      ),
    );
  }
}
