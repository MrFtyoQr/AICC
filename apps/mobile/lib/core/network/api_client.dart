import 'package:dio/dio.dart';

import '../errors/app_error.dart';

/// Único cliente HTTP de la app. Ningún widget llama a la red directamente.
class ApiClient {
  ApiClient({required String baseUrl, Dio? dio})
    : dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: baseUrl,
              connectTimeout: const Duration(seconds: 5),
              receiveTimeout: const Duration(seconds: 10),
              responseType: ResponseType.json,
            ),
          );

  /// Expuesto para registrar interceptores (sesión) en el arranque.
  final Dio dio;

  String get baseUrl => dio.options.baseUrl;

  /// GET que devuelve el cuerpo JSON. [acceptedStatuses] permite tratar códigos como 503
  /// como respuesta válida cuando el cuerpo describe el problema (ej. `/health/ready`).
  Future<Map<String, dynamic>> getJson(
    String path, {
    Set<int> acceptedStatuses = const {200},
    Map<String, String>? headers,
    Map<String, Object>? query,
  }) => _send(
    () => dio.get<Map<String, dynamic>>(
      path,
      queryParameters: query,
      options: Options(
        headers: headers,
        validateStatus: (code) => acceptedStatuses.contains(code),
      ),
    ),
  );

  /// GET de una colección (la API devuelve un arreglo JSON).
  Future<List<Map<String, dynamic>>> getList(
    String path, {
    Map<String, String>? headers,
  }) async {
    try {
      final response = await dio.get<List<dynamic>>(
        path,
        options: Options(headers: headers),
      );
      return (response.data ?? const []).cast<Map<String, dynamic>>();
    } on DioException catch (error) {
      throw AppError.fromDio(error);
    }
  }

  Future<Map<String, dynamic>> postJson(String path, Object body) =>
      _send(() => dio.post<Map<String, dynamic>>(path, data: body));

  /// POST sin cuerpo de respuesta (204).
  Future<void> post(String path, Object body) =>
      _send(() => dio.post<Map<String, dynamic>>(path, data: body));

  Future<Map<String, dynamic>> _send(
    Future<Response<Map<String, dynamic>>> Function() request,
  ) async {
    try {
      final response = await request();
      return response.data ?? const {};
    } on DioException catch (error) {
      throw AppError.fromDio(error);
    }
  }
}
