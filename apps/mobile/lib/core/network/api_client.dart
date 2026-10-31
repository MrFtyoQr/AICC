import 'package:dio/dio.dart';

import '../errors/app_error.dart';

/// Único cliente HTTP de la app. Ningún widget llama a la red directamente.
class ApiClient {
  ApiClient({required String baseUrl, Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: baseUrl,
              connectTimeout: const Duration(seconds: 5),
              receiveTimeout: const Duration(seconds: 10),
              responseType: ResponseType.json,
            ),
          );

  final Dio _dio;

  String get baseUrl => _dio.options.baseUrl;

  /// GET que devuelve el cuerpo JSON. [acceptedStatuses] permite tratar códigos como 503
  /// como respuesta válida cuando el cuerpo describe el problema (ej. `/health/ready`).
  Future<Map<String, dynamic>> getJson(
    String path, {
    Set<int> acceptedStatuses = const {200},
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        path,
        options: Options(
          validateStatus: (code) => acceptedStatuses.contains(code),
        ),
      );
      return response.data ?? const {};
    } on DioException catch (error) {
      throw AppError.fromDio(error);
    }
  }
}
