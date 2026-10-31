import 'package:dio/dio.dart';

import '../security/token_storage.dart';

/// Añade el access token y, ante un 401, renueva la sesión una sola vez y reintenta.
///
/// Es un [QueuedInterceptor]: si varias peticiones fallan a la vez, la primera renueva y
/// las demás ven el token nuevo y solo reintentan (nunca dos renovaciones en paralelo,
/// que el backend interpretaría como reutilización de refresh token).
class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({
    required this.dio,
    required this.storage,
    required this.onSessionExpired,
  }) : _refreshDio = Dio(
         BaseOptions(
           baseUrl: dio.options.baseUrl,
           connectTimeout: dio.options.connectTimeout,
           receiveTimeout: dio.options.receiveTimeout,
         ),
       )..httpClientAdapter = dio.httpClientAdapter;

  final Dio dio;
  final TokenStorage storage;
  final void Function() onSessionExpired;
  final Dio _refreshDio;

  static const _retriedFlag = 'aicc.retried';
  static const _refreshPath = '/api/v1/auth/refresh';

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (!_isAuthEndpoint(options.path)) {
      final tokens = await storage.read();
      if (tokens != null) {
        options.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final options = err.requestOptions;
    final unauthorized = err.response?.statusCode == 401;
    if (!unauthorized ||
        _isAuthEndpoint(options.path) ||
        options.extra[_retriedFlag] == true) {
      return handler.next(err);
    }

    final tokens = await storage.read();
    if (tokens == null) {
      onSessionExpired();
      return handler.next(err);
    }

    final usedToken = (options.headers['Authorization'] as String?)
        ?.replaceFirst('Bearer ', '');
    var current = tokens;
    if (usedToken == tokens.accessToken) {
      final renewed = await _refresh(tokens.refreshToken);
      if (renewed == null) {
        await storage.clear();
        onSessionExpired();
        return handler.next(err);
      }
      await storage.save(renewed);
      current = renewed;
    }

    try {
      options.headers['Authorization'] = 'Bearer ${current.accessToken}';
      options.extra[_retriedFlag] = true;
      handler.resolve(await dio.fetch<dynamic>(options));
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  Future<StoredTokens?> _refresh(String refreshToken) async {
    try {
      final response = await _refreshDio.post<Map<String, dynamic>>(
        _refreshPath,
        data: {'refresh_token': refreshToken},
      );
      final body = response.data!;
      return StoredTokens(
        accessToken: body['access_token'] as String,
        refreshToken: body['refresh_token'] as String,
      );
    } on DioException {
      return null;
    }
  }

  static bool _isAuthEndpoint(String path) => path.startsWith('/api/v1/auth/');
}
