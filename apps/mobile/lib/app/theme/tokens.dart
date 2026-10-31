import 'package:flutter/material.dart';

/// Tokens de diseño de docs/ux/principios-ux.md §5. Cambiar aquí, nunca en las pantallas.
abstract final class Space {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 24.0;
  static const xxl = 32.0;
}

abstract final class Radii {
  static const control = 8.0;
  static const card = 16.0;
  static const sheet = 28.0;
}

/// Semilla del color primario (provisional hasta cerrar la identidad visual, F0-UX-02).
const brandSeed = Color(0xFF3355FF);

/// Colores semánticos de estado. Siempre acompañados de icono y texto, nunca solos.
@immutable
class StatusColors extends ThemeExtension<StatusColors> {
  const StatusColors({
    required this.success,
    required this.warning,
    required this.danger,
    required this.info,
    required this.running,
    required this.waiting,
    required this.neutral,
  });

  final Color success;
  final Color warning;
  final Color danger;
  final Color info;
  final Color running;
  final Color waiting;
  final Color neutral;

  static const light = StatusColors(
    success: Color(0xFF1E7D45),
    warning: Color(0xFF9A6200),
    danger: Color(0xFFB3261E),
    info: Color(0xFF1B5FAD),
    running: Color(0xFF5B3FC4),
    waiting: Color(0xFFA34F00),
    neutral: Color(0xFF5F6368),
  );

  static const dark = StatusColors(
    success: Color(0xFF7BD89E),
    warning: Color(0xFFF2C46B),
    danger: Color(0xFFF2B8B5),
    info: Color(0xFF9CC4FF),
    running: Color(0xFFC6B6FF),
    waiting: Color(0xFFFFB77A),
    neutral: Color(0xFFBDC1C6),
  );

  @override
  StatusColors copyWith({
    Color? success,
    Color? warning,
    Color? danger,
    Color? info,
    Color? running,
    Color? waiting,
    Color? neutral,
  }) => StatusColors(
    success: success ?? this.success,
    warning: warning ?? this.warning,
    danger: danger ?? this.danger,
    info: info ?? this.info,
    running: running ?? this.running,
    waiting: waiting ?? this.waiting,
    neutral: neutral ?? this.neutral,
  );

  @override
  StatusColors lerp(StatusColors? other, double t) {
    if (other == null) return this;
    return StatusColors(
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      info: Color.lerp(info, other.info, t)!,
      running: Color.lerp(running, other.running, t)!,
      waiting: Color.lerp(waiting, other.waiting, t)!,
      neutral: Color.lerp(neutral, other.neutral, t)!,
    );
  }
}
