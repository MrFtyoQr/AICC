# Jira: estructura e importación

## Estructura del proyecto

| Elemento | Valor |
|---|---|
| Proyecto | **AI Command Center**, clave `AICC`, plantilla *Scrum* |
| Jerarquía | **Epic** (fase F0…O6) → **Story** (historia de usuario HU‑NN) → **Sub-task** (tarea técnica del plan, ej. `O2-BE-05`) |
| Componentes | Backend · App movil · UX-UI · DevOps · Seguridad · Documentacion (en las subtareas) |
| Etiquetas | fase (`F0`, `O2`…) + sprint (`S1`…) en historias · fase + frente (`be`, `app`…) en subtareas |
| Sprints | `AICC S0` … `AICC S13`, de 2 semanas (ver [sprints.md](../sprints.md)) |
| Estimación | Story points en las historias (Fibonacci) |
| Flujo | To Do → In Progress → In Review (PR abierto) → Done (merge + DoD) |

Fuentes: [plan-maestro.md](../plan-maestro.md) (epics y tareas) y [historias-usuario.md](../historias-usuario.md) (historias, criterios, sprint, puntos).

## Generar el backlog

```bash
python -I scripts/generar-backlog-jira.py
```

El script **falla** si una tarea del plan no está en ninguna historia, está en dos, o una historia cita una
tarea inexistente. Resultado actual: **8 epics, 41 historias (244 pts), 91 subtareas**.

## Importar por CSV (mientras el conector no esté autorizado)

1. Crear el proyecto `AICC` (Scrum, *company-managed* recomendado) y los 6 componentes.
2. Crear los sprints `AICC S0` … `AICC S13` en el backlog (el importador asigna por nombre).
3. ⚙ → **Sistema → Importación externa → CSV**. Subir `backlog.csv` en **UTF‑8**.
4. Mapear columnas:

| Columna CSV | Campo Jira |
|---|---|
| Issue ID | Issue Id |
| Parent ID | Parent Id (Epic → Story → Sub-task) |
| Issue Type | Issue Type |
| Summary / Description | Summary / Description |
| Labels (×2) | Labels |
| Component | Component/s |
| Priority | Priority |
| Status | Status (`To Do`, `Done`) |
| Sprint | Sprint |
| Story Points | Story Points (en *team-managed*: "Story point estimate") |

5. Validar y ejecutar. Deben quedar 140 issues; S0 con 4 historias y 16 subtareas en *Done*.

Con el conector de Atlassian autorizado (ver [conexiones.md](../conexiones.md)) este paso lo hace Claude directamente.

## Convenciones Git ↔ Jira

- Rama: `AICC-<n>-descripcion-corta` (mientras no haya claves Jira: `HU-NN-descripcion`).
- Commit: `feat(auth): login con refresh rotatorio AICC-<n>`.
- PR: título con la clave; la descripción enlaza la historia y marca su DoD.
