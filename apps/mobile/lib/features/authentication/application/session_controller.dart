import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../core/errors/app_error.dart';
import '../data/auth_repository.dart';

sealed class SessionState {
  const SessionState();
}

/// Arranque: todavía no sabemos si hay sesión guardada.
final class SessionUnknown extends SessionState {
  const SessionUnknown();
}

final class SignedOut extends SessionState {
  const SignedOut({this.reason});

  /// Por qué se cerró (p. ej. sesión vencida) para avisar en la pantalla de login.
  final String? reason;
}

final class SignedIn extends SessionState {
  const SignedIn(this.user);
  final AuthUser user;
}

class SessionController extends Notifier<SessionState> {
  @override
  SessionState build() {
    Future.microtask(_restore);
    return const SessionUnknown();
  }

  AuthRepository get _repo => ref.read(authRepositoryProvider);

  Future<void> _restore() async {
    if (!await _repo.hasStoredSession()) {
      state = const SignedOut();
      return;
    }
    try {
      state = SignedIn(await _repo.me());
    } on UnauthorizedError {
      await _repo.clearLocalSession();
      state = const SignedOut();
    } on AppError {
      // Sin red al abrir: se muestra el login con el motivo, pero los tokens se conservan
      // para que la próxima apertura con red restaure la sesión sin pedir la contraseña.
      state = const SignedOut(
        reason: 'No pudimos comprobar tu sesión. Revisa tu conexión.',
      );
    }
  }

  /// Lanza [AppError] para que la pantalla muestre el mensaje.
  Future<void> signIn(String email, String password) async {
    state = SignedIn(await _repo.login(email: email, password: password));
  }

  Future<void> signUp(
    String email,
    String password,
    String? displayName,
  ) async {
    await _repo.register(
      email: email,
      password: password,
      displayName: displayName,
    );
    await signIn(email, password);
  }

  Future<void> signOut() async {
    await _repo.logout();
    state = const SignedOut();
  }

  /// Llamado por el interceptor cuando el refresh token ya no sirve.
  void sessionExpired() {
    if (state is SignedIn) {
      state = const SignedOut(
        reason: 'Tu sesión venció. Inicia sesión de nuevo.',
      );
    }
  }
}
