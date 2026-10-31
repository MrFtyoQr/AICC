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
    DioExceptionType.badResponse => ServerError(error.response?.statusCode),
    _ => const UnexpectedError(),
  };
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
