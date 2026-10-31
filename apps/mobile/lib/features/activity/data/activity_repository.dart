import '../../../core/network/api_client.dart';

class ActivityEntry {
  const ActivityEntry({
    required this.id,
    required this.createdAt,
    required this.actorName,
    required this.summary,
    required this.denied,
  });

  factory ActivityEntry.fromJson(Map<String, dynamic> json) {
    final actor = json['actor'] as Map<String, dynamic>?;
    return ActivityEntry(
      id: json['id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      actorName: actor == null
          ? 'Alguien'
          : (actor['display_name'] as String?) ?? actor['email'] as String,
      summary: json['summary'] as String,
      denied: json['outcome'] == 'denied',
    );
  }

  final String id;
  final DateTime createdAt;
  final String actorName;
  final String summary;
  final bool denied;
}

class ActivityPage {
  const ActivityPage(this.entries, this.nextCursor);
  final List<ActivityEntry> entries;
  final String? nextCursor;
}

class ActivityRepository {
  ActivityRepository(this._client);

  final ApiClient _client;

  /// El workspace lo pone el interceptor según el contexto activo.
  Future<ActivityPage> page({String? cursor, int limit = 20}) async {
    final json = await _client.getJson(
      '/api/v1/activity',
      query: {'limit': limit, 'cursor': ?cursor},
    );
    return ActivityPage([
      for (final item in json['items'] as List)
        ActivityEntry.fromJson(item as Map<String, dynamic>),
    ], json['next_cursor'] as String?);
  }
}
