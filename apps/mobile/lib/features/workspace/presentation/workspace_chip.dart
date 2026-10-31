import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';

/// Contexto actual siempre a la vista: "dónde estoy y con qué rol".
/// En S3 (HU-14) se vuelve tocable para cambiar de workspace/proyecto/ambiente.
class WorkspaceChip extends ConsumerWidget {
  const WorkspaceChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final workspace = ref.watch(currentWorkspaceProvider).value;
    if (workspace == null) return const SizedBox.shrink();
    return Align(
      alignment: Alignment.centerLeft,
      child: Chip(
        avatar: Icon(
          workspace.isPersonal ? Icons.person_outline : Icons.groups_outlined,
          size: 18,
        ),
        label: Text('${workspace.name} · ${workspace.roleLabel}'),
      ),
    );
  }
}
