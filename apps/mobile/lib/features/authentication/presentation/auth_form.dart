import 'package:flutter/material.dart';

import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../../../shared/widgets/status_pill.dart';

/// Esqueleto común de login y registro: marca, título, aviso, campos y acción principal abajo.
class AuthScaffold extends StatelessWidget {
  const AuthScaffold({
    super.key,
    required this.title,
    required this.subtitle,
    required this.fields,
    required this.primaryLabel,
    required this.onPrimary,
    required this.busy,
    required this.secondary,
    this.notice,
    this.error,
  });

  final String title;
  final String subtitle;
  final List<Widget> fields;
  final String primaryLabel;
  final VoidCallback onPrimary;
  final bool busy;
  final Widget secondary;
  final String? notice;
  final AppError? error;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(Space.xl),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: AutofillGroup(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(
                      Icons.hub_outlined,
                      size: 48,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: Space.lg),
                    Text(title, style: text.headlineMedium),
                    const SizedBox(height: Space.sm),
                    Text(subtitle, style: text.bodyLarge),
                    const SizedBox(height: Space.xl),
                    if (notice != null) ...[
                      _Banner(kind: StatusKind.info, text: notice!),
                      const SizedBox(height: Space.lg),
                    ],
                    if (error != null) ...[
                      _Banner(
                        kind: StatusKind.danger,
                        text: '${error!.title}. ${error!.message}',
                      ),
                      const SizedBox(height: Space.lg),
                    ],
                    ...fields,
                    const SizedBox(height: Space.xl),
                    FilledButton(
                      onPressed: busy ? null : onPrimary,
                      child: busy
                          ? const SizedBox.square(
                              dimension: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(primaryLabel),
                    ),
                    const SizedBox(height: Space.md),
                    secondary,
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({required this.kind, required this.text});

  final StatusKind kind;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(Space.md),
          child: Row(
            children: [
              StatusPill(
                kind: kind,
                label: kind == StatusKind.danger ? 'Error' : 'Aviso',
              ),
              const SizedBox(width: Space.md),
              Expanded(child: Text(text)),
            ],
          ),
        ),
      ),
    );
  }
}

class PasswordField extends StatefulWidget {
  const PasswordField({
    super.key,
    required this.controller,
    required this.label,
    this.helper,
    this.validator,
    this.newPassword = false,
    this.onSubmitted,
  });

  final TextEditingController controller;
  final String label;
  final String? helper;
  final FormFieldValidator<String>? validator;
  final bool newPassword;
  final VoidCallback? onSubmitted;

  @override
  State<PasswordField> createState() => _PasswordFieldState();
}

class _PasswordFieldState extends State<PasswordField> {
  bool _obscured = true;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: widget.controller,
      obscureText: _obscured,
      autofillHints: [
        widget.newPassword ? AutofillHints.newPassword : AutofillHints.password,
      ],
      textInputAction: TextInputAction.done,
      onFieldSubmitted: (_) => widget.onSubmitted?.call(),
      validator: widget.validator,
      decoration: InputDecoration(
        labelText: widget.label,
        helperText: widget.helper,
        border: const OutlineInputBorder(),
        suffixIcon: IconButton(
          tooltip: _obscured ? 'Mostrar contraseña' : 'Ocultar contraseña',
          icon: Icon(_obscured ? Icons.visibility : Icons.visibility_off),
          onPressed: () => setState(() => _obscured = !_obscured),
        ),
      ),
    );
  }
}

String? validateEmail(String? value) {
  final v = value?.trim() ?? '';
  if (v.isEmpty) return 'Escribe tu email';
  if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v)) {
    return 'Ese email no parece válido';
  }
  return null;
}
