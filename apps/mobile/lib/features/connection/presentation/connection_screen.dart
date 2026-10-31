import 'package:flutter/material.dart';

import '../../../app/theme/tokens.dart';
import '../../../core/errors/app_error.dart';
import '../../../shared/widgets/status_pill.dart';
import '../data/health_repository.dart';

/// M0: muestra si la app llega a la API y si la API llega a sus dependencias.
class ConnectionScreen extends StatefulWidget {
  const ConnectionScreen({
    super.key,
    required this.repository,
    required this.appEnvironment,
    this.title = 'AICC · Estado',
    this.actions = const [],
  });

  final HealthRepository repository;
  final String appEnvironment;
  final String title;
  final List<Widget> actions;

  @override
  State<ConnectionScreen> createState() => _ConnectionScreenState();
}

class _ConnectionScreenState extends State<ConnectionScreen> {
  late Future<ApiStatus> _status;

  @override
  void initState() {
    super.initState();
    _status = widget.repository.fetchStatus();
  }

  void _retry() {
    setState(() {
      _status = widget.repository.fetchStatus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title), actions: widget.actions),
      body: SafeArea(
        child: FutureBuilder<ApiStatus>(
          future: _status,
          builder: (context, snapshot) {
            final Widget content = switch (snapshot) {
              AsyncSnapshot(connectionState: ConnectionState.waiting) =>
                const _Checking(),
              AsyncSnapshot(:final ApiStatus data) => _Connected(status: data),
              AsyncSnapshot(:final Object error) => _Failed(
                error: error is AppError ? error : const UnexpectedError(),
              ),
              _ => const _Checking(),
            };
            return ListView(
              padding: const EdgeInsets.all(Space.lg),
              children: [
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  child: content,
                ),
                const SizedBox(height: Space.xl),
                _Details(
                  apiBaseUrl: widget.repository.apiBaseUrl,
                  appEnvironment: widget.appEnvironment,
                ),
              ],
            );
          },
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(Space.lg),
          child: FilledButton.icon(
            onPressed: _retry,
            icon: const Icon(Icons.refresh),
            label: const Text('Volver a comprobar'),
          ),
        ),
      ),
    );
  }
}

class _Checking extends StatelessWidget {
  const _Checking();

  @override
  Widget build(BuildContext context) {
    return const _StatusCard(
      key: ValueKey('checking'),
      pill: StatusPill(kind: StatusKind.running, label: 'Comprobando…'),
      title: 'Conectando con AICC',
      body: 'Esto tarda solo un momento.',
      trailing: LinearProgressIndicator(),
    );
  }
}

class _Connected extends StatelessWidget {
  const _Connected({required this.status});

  final ApiStatus status;

  @override
  Widget build(BuildContext context) {
    final ready = status.isReady;
    return _StatusCard(
      key: const ValueKey('connected'),
      pill: ready
          ? const StatusPill(kind: StatusKind.success, label: 'Todo en orden')
          : const StatusPill(
              kind: StatusKind.warning,
              label: 'Funcionando a medias',
            ),
      title: ready ? 'AICC está listo' : 'La API responde, pero falta algo',
      body: 'Versión ${status.version} · entorno ${status.environment}',
      trailing: Column(
        children: [
          for (final entry in status.dependencies.entries)
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text(_dependencyLabel(entry.key)),
              trailing: entry.value == DependencyState.ok
                  ? const StatusPill(kind: StatusKind.success, label: 'OK')
                  : const StatusPill(
                      kind: StatusKind.danger,
                      label: 'Sin respuesta',
                    ),
            ),
        ],
      ),
    );
  }

  static String _dependencyLabel(String key) => switch (key) {
    'database' => 'Base de datos',
    'redis' => 'Cola de trabajos',
    _ => key,
  };
}

class _Failed extends StatelessWidget {
  const _Failed({required this.error});

  final AppError error;

  @override
  Widget build(BuildContext context) {
    return _StatusCard(
      key: const ValueKey('failed'),
      pill: const StatusPill(kind: StatusKind.danger, label: 'Sin conexión'),
      title: error.title,
      body: error.message,
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({
    super.key,
    required this.pill,
    required this.title,
    required this.body,
    this.trailing,
  });

  final Widget pill;
  final String title;
  final String body;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Space.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            pill,
            const SizedBox(height: Space.md),
            Text(title, style: text.headlineSmall),
            const SizedBox(height: Space.sm),
            Text(body, style: text.bodyLarge),
            if (trailing != null) ...[
              const SizedBox(height: Space.lg),
              trailing!,
            ],
          ],
        ),
      ),
    );
  }
}

class _Details extends StatelessWidget {
  const _Details({required this.apiBaseUrl, required this.appEnvironment});

  final String apiBaseUrl;
  final String appEnvironment;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.bodySmall;
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text('Detalles técnicos'),
      children: [
        ListTile(
          dense: true,
          title: const Text('API'),
          subtitle: Text(apiBaseUrl, style: style),
        ),
        ListTile(
          dense: true,
          title: const Text('Entorno de la app'),
          subtitle: Text(appEnvironment, style: style),
        ),
      ],
    );
  }
}
