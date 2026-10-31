import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/providers.dart';
import '../../../app/router/app_router.dart';
import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';

/// Command Center v1 (HU-15): escribir y enviar crea una tarea en Borrador
/// en el proyecto y ambiente del contexto activo. Toque en el campo, escribir, enviar.
class CommandBox extends ConsumerStatefulWidget {
  const CommandBox({super.key});

  @override
  ConsumerState<CommandBox> createState() => _CommandBoxState();
}

class _CommandBoxState extends ConsumerState<CommandBox> {
  final _controller = TextEditingController();
  bool _sending = false;
  AppError? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.length < 3 || _sending) return;
    final appContext = ref.read(contextProvider).value;
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final task = await ref
          .read(taskRepositoryProvider)
          .create(
            text,
            projectId: appContext?.project?.id,
            environmentId: appContext?.environment?.id,
          );
      if (!mounted) return;
      _controller.clear();
      ref.invalidate(recentTasksProvider);
      context.push(Routes.task(task.id));
    } on AppError catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Space.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('¿Qué necesitas?', style: text.titleLarge),
            const SizedBox(height: Space.md),
            TextField(
              key: const Key('command-input'),
              controller: _controller,
              minLines: 2,
              maxLines: 5,
              maxLength: 4000,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                hintText:
                    'Ej.: Responde a los leads de hoy y avísame por correo',
                counterText: '',
              ),
              onChanged: (_) => setState(() {}),
            ),
            if (_error != null) ...[
              const SizedBox(height: Space.sm),
              Text(
                _error!.message,
                style: text.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.error,
                ),
              ),
            ],
            const SizedBox(height: Space.md),
            FilledButton.icon(
              onPressed: _controller.text.trim().length >= 3 && !_sending
                  ? _send
                  : null,
              icon: _sending
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.send),
              label: const Text('Enviar'),
            ),
          ],
        ),
      ),
    );
  }
}
