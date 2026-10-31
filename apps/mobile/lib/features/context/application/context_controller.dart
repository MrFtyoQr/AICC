import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../data/context_repository.dart';

/// Dónde está trabajando el usuario: workspace › proyecto › ambiente (HU-14).
class AppContext {
  const AppContext({
    required this.workspaces,
    required this.workspace,
    required this.projects,
    required this.project,
    required this.environment,
  });

  final List<Workspace> workspaces;
  final Workspace workspace;
  final List<Project> projects;
  final Project? project;
  final Environment? environment;

  bool get isProduction => environment?.kind == EnvironmentKind.production;
}

/// Workspace activo para las llamadas a la API. Lo escribe [ContextController]
/// y lo lee [WorkspaceHeaderInterceptor]; vacío = workspace personal.
class ActiveWorkspace {
  String? id;
}

/// Añade `X-Workspace-Id` a toda petición que no lo traiga ya.
class WorkspaceHeaderInterceptor extends Interceptor {
  WorkspaceHeaderInterceptor(this._active);

  final ActiveWorkspace _active;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final id = _active.id;
    if (id != null) options.headers.putIfAbsent(workspaceHeader, () => id);
    handler.next(options);
  }
}

class ContextController extends AsyncNotifier<AppContext> {
  ContextRepository get _repo => ref.read(contextRepositoryProvider);

  @override
  Future<AppContext> build() async {
    // Se recalcula al cambiar la sesión, para no mostrar el contexto de otro usuario.
    ref.watch(sessionProvider);
    final workspaces = await _repo.workspaces();
    return _load(workspaces, workspaces.first);
  }

  Future<AppContext> _load(
    List<Workspace> workspaces,
    Workspace workspace, {
    String? projectId,
    String? environmentId,
  }) async {
    final projects = await _repo.projects(workspace.id);
    final project = projects.isEmpty
        ? null
        : projects.firstWhere(
            (p) => p.id == projectId,
            orElse: () => projects.first,
          );
    final environments = project?.environments ?? const <Environment>[];
    final environment = environments.isEmpty
        ? null
        : environments.firstWhere(
            (e) => e.id == environmentId,
            orElse: () => environments.first,
          );
    ref.read(activeWorkspaceProvider).id = workspace.id;
    return AppContext(
      workspaces: workspaces,
      workspace: workspace,
      projects: projects,
      project: project,
      environment: environment,
    );
  }

  Future<void> selectWorkspace(String workspaceId) async {
    final current = state.requireValue;
    final workspace = current.workspaces.firstWhere((w) => w.id == workspaceId);
    state = AsyncData(await _load(current.workspaces, workspace));
  }

  void selectProject(String projectId) {
    final current = state.requireValue;
    final project = current.projects.firstWhere((p) => p.id == projectId);
    state = AsyncData(
      AppContext(
        workspaces: current.workspaces,
        workspace: current.workspace,
        projects: current.projects,
        project: project,
        environment: project.environments.firstOrNull,
      ),
    );
  }

  void selectEnvironment(String environmentId) {
    final current = state.requireValue;
    state = AsyncData(
      AppContext(
        workspaces: current.workspaces,
        workspace: current.workspace,
        projects: current.projects,
        project: current.project,
        environment: current.project!.environments.firstWhere(
          (e) => e.id == environmentId,
        ),
      ),
    );
  }
}
