import 'package:flutter/material.dart';

import '../../../shared/widgets/status_pill.dart';

/// Color de cada estado según el diccionario (principios-ux §6). El texto llega de la API.
StatusKind statusKind(String status) => switch (status) {
  'PLANNING' || 'RUNNING' => StatusKind.running,
  'AWAITING_APPROVAL' || 'PAUSED' => StatusKind.waiting,
  'PLANNING_FAILED' || 'REJECTED_BY_POLICY' || 'FAILED' => StatusKind.danger,
  'APPROVED' => StatusKind.info,
  'DONE' => StatusKind.success,
  _ => StatusKind.neutral,
};

/// Filtros de la lista agrupados por lo que el usuario quiere ver (HU-17).
enum TaskFilter {
  all('Todas', []),
  attention('Necesitan atención', ['AWAITING_APPROVAL', 'PAUSED']),
  active('En curso', ['PLANNING', 'APPROVED', 'RUNNING']),
  drafts('Borradores', ['DRAFT']),
  finished('Terminadas', ['DONE']),
  problems('Con problemas', [
    'PLANNING_FAILED',
    'REJECTED_BY_POLICY',
    'FAILED',
  ]),
  closed('Canceladas o rechazadas', ['CANCELLED', 'REJECTED']);

  const TaskFilter(this.label, this.statuses);
  final String label;
  final List<String> statuses;
}

class TaskStatusPill extends StatelessWidget {
  const TaskStatusPill({super.key, required this.status, required this.label});

  final String status;
  final String label;

  @override
  Widget build(BuildContext context) =>
      StatusPill(kind: statusKind(status), label: label);
}
