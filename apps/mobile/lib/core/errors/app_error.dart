import 'package:dio/dio.dart';

/// Errores de la app con un mensaje pensado para personas, nunca un stacktrace.
sealed class AppError implements Exception {
  const AppError();

  String get title;
  String get message;

  factory AppError.fromDio(DioException error) => switch (error.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout => const TimeoutError(),
    DioExceptionType.connectionError => const NetworkError(),
    DioExceptionType.badResponse => AppError.fromStatus(
      error.response?.statusCode,
      detail: _detail(error.response?.data),
    ),
    _ => const UnexpectedError(),
  };

  factory AppError.fromStatus(int? status, {String? detail}) =>
      switch (status) {
        401 => UnauthorizedError(detail),
        409 => ConflictError(detail),
        422 => const ValidationError(),
        429 => const RateLimitedError(),
        _ => ServerError(status),
      };

  static String? _detail(Object? data) =>
      data is Map && data['detail'] is String ? data['detail'] as String : null;
}

final class NetworkError extends AppError {
  const NetworkError();
  @override
  String get title => 'Sin conexión con AICC';
  @override
  String get message =>
      'No pudimos llegar al servidor. Revisa tu red o que la API esté encendida.';
}

final class TimeoutError extends AppError {
  const TimeoutError();
  @override
  String get title => 'El servidor tarda demasiado';
  @override
  String get message =>
      'La solicitud superó el tiempo de espera. Inténtalo de nuevo en un momento.';
}

final class UnauthorizedError extends AppError {
  const UnauthorizedError([this.detail]);
  final String? detail;
  @override
  String get title => 'No pudimos verificar tu identidad';
  @override
  String get message => detail ?? 'Inicia sesión de nuevo.';
}

final class ConflictError extends AppError {
  const ConflictError([this.detail]);
  final String? detail;
  @override
  String get title => 'Ya existe';
  @override
  String get message => detail ?? 'Ese recurso ya existe.';
}

final class ValidationError extends AppError {
  const ValidationError();
  @override
  String get title => 'Revisa los datos';
  @override
  String get message => 'Algún campo no tiene el formato esperado.';
}

final class RateLimitedError extends AppError {
  const RateLimitedError();
  @override
  String get title => 'Demasiados intentos';
  @override
  String get message => 'Espera un minuto antes de volver a intentarlo.';
}

final class ServerError extends AppError {
  const ServerError(this.statusCode);
  final int? statusCode;
  @override
  String get title => 'El servidor respondió con un error';
  @override
  String get message =>
      'Código ${statusCode ?? 'desconocido'}. No se perdió nada de tu trabajo.';
}

final class UnexpectedError extends AppError {
  const UnexpectedError();
  @override
  String get title => 'Algo salió mal';
  @override
  String get message => 'Ocurrió un error inesperado. Inténtalo de nuevo.';
}
