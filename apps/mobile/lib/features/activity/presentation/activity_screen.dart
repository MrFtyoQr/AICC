import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../../../shared/widgets/status_pill.dart';
import '../../context/presentation/context_chip.dart';
import '../data/activity_repository.dart';

/// Quién hizo qué y cuándo en el workspace actual (HU-13), en lenguaje claro.
class ActivityScreen extends ConsumerStatefulWidget {
  const ActivityScreen({super.key});

  @override
  ConsumerState<ActivityScreen> createState() => _ActivityScreenState();
}

class _ActivityScreenState extends ConsumerState<ActivityScreen> {
  final _entries = <ActivityEntry>[];
  String? _cursor;
  bool _loading = false;
  bool _done = false;
  AppError? _error;

  @override
  void initState() {
    super.initState();
    _loadMore();
  }

  Future<void> _reload() async {
    setState(() {
      _entries.clear();
      _cursor = null;
      _done = false;
    });
    await _loadMore();
  }

  Future<void> _loadMore() async {
    if (_loading || _done) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await ref
          .read(activityRepositoryProvider)
          .page(cursor: _cursor);
      if (!mounted) return;
      setState(() {
        _entries.addAll(page.entries);
        _cursor = page.nextCursor;
        _done = page.nextCursor == null;
      });
    } on AppError catch (error) {
      if (mounted) setState(() => _error = error);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Cambiar de workspace cambia el registro que se muestra.
    ref.listen(contextProvider.select((c) => c.value?.workspace.id), (
      previous,
      next,
    ) {
      if (previous != null && previous != next) _reload();
    });
    return Scaffold(
      appBar: AppBar(title: const Text('Actividad')),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: ListView(
          padding: const EdgeInsets.all(Space.lg),
          children: [
            const Align(alignment: Alignment.centerLeft, child: ContextChip()),
            const SizedBox(height: Space.lg),
            for (final entry in _entries) _ActivityTile(entry: entry),
            if (_error != null)
              ListTile(
                leading: const Icon(Icons.error_outline),
                title: Text(_error!.title),
                subtitle: Text(_error!.message),
              ),
            if (_loading)
              const Padding(
                padding: EdgeInsets.all(Space.lg),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (!_done)
              OutlinedButton(onPressed: _loadMore, child: const Text('Ver más'))
            else if (_entries.isEmpty)
              const Padding(
                padding: EdgeInsets.all(Space.xl),
                child: Text('Todavía no hay actividad en este workspace.'),
              ),
          ],
        ),
      ),
    );
  }
}

class _ActivityTile extends StatelessWidget {
  const _ActivityTile({required this.entry});

  final ActivityEntry entry;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(entry.denied ? Icons.block : Icons.history),
      title: Text(entry.summary),
      subtitle: Text('${entry.actorName} · ${_when(entry.createdAt)}'),
      trailing: entry.denied
          ? const StatusPill(kind: StatusKind.danger, label: 'Sin permiso')
          : null,
    );
  }

  static String _when(DateTime at) {
    final diff = DateTime.now().difference(at);
    if (diff.inMinutes < 1) return 'hace un momento';
    if (diff.inHours < 1) return 'hace ${diff.inMinutes} min';
    if (diff.inDays < 1) return 'hace ${diff.inHours} h';
    if (diff.inDays < 7) return 'hace ${diff.inDays} d';
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(at.day)}/${two(at.month)}/${at.year}';
  }
}
