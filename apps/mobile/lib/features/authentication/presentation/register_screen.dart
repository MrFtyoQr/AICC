import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/providers.dart';
import '../../../app/router/app_router.dart';
import '../../../core/errors/app_error.dart';
import 'auth_form.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  static const minPasswordLength = 12;

  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  AppError? _error;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final name = _name.text.trim();
      await ref
          .read(sessionProvider.notifier)
          .signUp(
            _email.text.trim(),
            _password.text,
            name.isEmpty ? null : name,
          );
    } on AppError catch (e) {
      if (mounted) setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _form,
      child: AuthScaffold(
        title: 'Crea tu cuenta',
        subtitle: 'En un minuto tendrás tu espacio de trabajo listo.',
        error: _error,
        busy: _busy,
        primaryLabel: 'Crear cuenta',
        onPrimary: _submit,
        fields: [
          TextFormField(
            controller: _name,
            autofillHints: const [AutofillHints.name],
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: 'Tu nombre (opcional)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            textInputAction: TextInputAction.next,
            validator: validateEmail,
            decoration: const InputDecoration(
              labelText: 'Email',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _password,
            label: 'Contraseña',
            helper: 'Mínimo $minPasswordLength caracteres',
            newPassword: true,
            validator: (v) => (v == null || v.length < minPasswordLength)
                ? 'Usa al menos $minPasswordLength caracteres'
                : null,
            onSubmitted: _submit,
          ),
        ],
        secondary: TextButton(
          onPressed: _busy ? null : () => context.go(Routes.login),
          child: const Text('Ya tengo cuenta'),
        ),
      ),
    );
  }
}
