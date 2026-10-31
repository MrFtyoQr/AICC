import 'dart:convert';
import 'dart:typed_data';

import 'package:aicc_mobile/core/network/api_client.dart';
import 'package:dio/dio.dart';

typedef Responder = Future<ResponseBody> Function(RequestOptions options);

/// Adaptador HTTP en memoria: las pruebas nunca abren sockets.
class FakeAdapter implements HttpClientAdapter {
  FakeAdapter(this.respond);

  final Responder respond;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) => respond(options);

  @override
  void close({bool force = false}) {}
}

ResponseBody jsonBody(int status, Object body) => ResponseBody.fromString(
  jsonEncode(body),
  status,
  headers: {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  },
);

ApiClient fakeClient(Responder respond) {
  final dio = Dio(BaseOptions(baseUrl: 'http://api.test'))
    ..httpClientAdapter = FakeAdapter(respond);
  return ApiClient(baseUrl: 'http://api.test', dio: dio);
}

Future<ResponseBody> healthyApi(RequestOptions options) async =>
    switch (options.path) {
      '/health' => jsonBody(200, {
        'status': 'ok',
        'service': 'aicc-api',
        'version': '0.1.0',
        'environment': 'development',
      }),
      '/health/ready' => jsonBody(200, {
        'status': 'ok',
        'checks': {
          'database': {'status': 'ok'},
          'redis': {'status': 'ok'},
        },
      }),
      _ => jsonBody(404, {}),
    };

Future<ResponseBody> degradedApi(RequestOptions options) async =>
    switch (options.path) {
      '/health/ready' => jsonBody(503, {
        'status': 'degraded',
        'checks': {
          'database': {'status': 'ok'},
          'redis': {'status': 'error', 'detail': 'TimeoutError'},
        },
      }),
      _ => healthyApi(options),
    };

Future<ResponseBody> unreachableApi(RequestOptions options) async =>
    throw DioException.connectionError(
      requestOptions: options,
      reason: 'refused',
    );
