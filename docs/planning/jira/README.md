# Jira: estructura e importación

## Estructura del proyecto

| Elemento | Valor |
|---|---|
| Proyecto | **AI Command Center**, clave `AICC`, plantilla *Scrum* |
| Epics | Uno por fase: F0, F1, O1–O6 (Etapa B se crea al cerrar H2) |
| Tipos | `Story` para BE/APP/UX/SEC · `Task` para OPS/DOC · `Bug` · `Spike` (investigación con límite de tiempo) |
| Componentes | Backend · App movil · UX-UI · DevOps · Seguridad · Documentacion |
| Etiquetas | fase (`F0`, `O2`…) + frente (`be`, `app`, `ux`, `ops`, `sec`, `doc`) |
| Sprints | 2 semanas; un sprint no mezcla fases salvo cierre/arranque |
| Flujo | To Do → In Progress → In Review (PR abierto) → Done (merge + DoD) |

El código de cada ticket (`[O2-BE-05]`) va al inicio del Summary y enlaza con el plan maestro.

## Importar el backlog

El archivo [`backlog.csv`](backlog.csv) se **genera** desde el plan maestro; no se edita a mano:

```bash
python -I scripts/generar-backlog-jira.py
```

Pasos en Jira Cloud:

1. Crear el proyecto `AICC` (Scrum) y los 6 componentes de la tabla.
2. Configuración del sistema → **Sistema externo → CSV** (o en el proyecto: ⋯ → *Importar issues*).
3. Subir `backlog.csv`, codificación **UTF‑8**, proyecto `AICC`.
4. Mapear columnas:

| Columna CSV | Campo Jira |
|---|---|
| Issue ID | Issue Id |
| Parent ID | Parent Id (crea la relación Epic → issue) |
| Issue Type | Issue Type |
| Summary | Summary |
| Description | Description |
| Labels (×2) | Labels |
| Component | Component/s |
| Priority | Priority |
| Status | Status (mapear `To Do` / `Done`) |

5. Validar con el asistente y ejecutar. Resultado esperado: **8 epics y 91 issues** (3 ya en Done).

## Conectar Jira con Claude

Para que Claude cree y actualice tickets directamente, autoriza el conector de Atlassian ejecutando
`/mcp` en una terminal `claude` interactiva. Con eso se puede sincronizar el backlog sin importar CSV.

## Convenciones de Git ↔ Jira

- Rama: `AICC-<n>-descripcion-corta`
- Commit: `feat(tasks): máquina de estados AICC-<n>`
- PR: título con la clave; la descripción enlaza el ticket y marca la DoD.
