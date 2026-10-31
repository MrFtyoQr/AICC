import 'package:aicc_mobile/core/errors/app_error.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import '../support/fake_http.dart';

void main() {
  test('devuelve el cuerpo JSON en 200', () async {
    final client = fakeClient(healthyApi);

    final body = await client.getJson('/health');

    expect(body['status'], 'ok');
  });

  test('acepta 503 solo cuando se pide explícitamente', () async {
    final client = fakeClient(degradedApi);

    expect(
      await client.getJson('/health/ready', acceptedStatuses: {200, 503}),
      containsPair('status', 'degraded'),
    );
    await expectLater(
      client.getJson('/health/ready'),
      throwsA(isA<ServerError>()),
    );
  });

  test('API caída se traduce a NetworkError', () async {
    final client = fakeClient(unreachableApi);

    await expectLater(client.getJson('/health'), throwsA(isA<NetworkError>()));
  });

  test('timeout se traduce a TimeoutError', () async {
    final client = fakeClient(
      (options) async => throw DioException.receiveTimeout(
        timeout: const Duration(seconds: 1),
        requestOptions: options,
      ),
    );

    await expectLater(client.getJson('/health'), throwsA(isA<TimeoutError>()));
  });
}
