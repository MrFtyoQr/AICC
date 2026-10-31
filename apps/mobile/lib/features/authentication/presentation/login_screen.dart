import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/providers.dart';
import '../../../app/router/app_router.dart';
import '../../../core/errors/app_error.dart';
import '../application/session_controller.dart';
import 'auth_form.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  AppError? _error;

  @override
  void dispose() {
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
      await ref
          .read(sessionProvider.notifier)
          .signIn(_email.text.trim(), _password.text);
    } on AppError catch (e) {
      if (mounted) setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    return Form(
      key: _form,
      child: AuthScaffold(
        title: 'Bienvenido a AICC',
        subtitle: 'Tu centro de mando para automatizar con IA.',
        notice: session is SignedOut ? session.reason : null,
        error: _error,
        busy: _busy,
        primaryLabel: 'Entrar',
        onPrimary: _submit,
        fields: [
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
            validator: (v) =>
                (v == null || v.isEmpty) ? 'Escribe tu contraseña' : null,
            onSubmitted: _submit,
          ),
        ],
        secondary: TextButton(
          onPressed: _busy ? null : () => context.go(Routes.register),
          child: const Text('¿No tienes cuenta? Crear cuenta'),
        ),
      ),
    );
  }
}
