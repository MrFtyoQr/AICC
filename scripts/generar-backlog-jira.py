"""Genera docs/planning/jira/backlog.csv a partir de docs/planning/plan-maestro.md.

El plan maestro es la única fuente de verdad: cada sección '## <FASE> · <nombre>' es un Epic
y cada fila '| CÓDIGO | FRENTE | Paso | Criterio |' es una Story (o Task para OPS/DOC).
Uso: python -I scripts/generar-backlog-jira.py
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "planning" / "plan-maestro.md"
OUT = ROOT / "docs" / "planning" / "jira" / "backlog.csv"

FRENTES = {"BE": "Backend", "APP": "App movil", "UX": "UX-UI", "OPS": "DevOps", "SEC": "Seguridad", "DOC": "Documentacion"}
SECTION = re.compile(r"^## (F\d|O\d) · (.+)$")
ROW = re.compile(r"^\| ((?:F|O)\d-[A-Z]+-\d+) \| ([A-Z]+) \| (.+?) \| (.+?) \|$")
GATE = re.compile(r"^\*\*Gate .+?:\*\* (.+)$")
OBJ = re.compile(r"^\*\*Objetivo:\*\* (.+)$")

rows, epic, n = [], None, 0
for line in PLAN.read_text(encoding="utf-8").splitlines():
    if m := SECTION.match(line):
        n += 1
        epic = {"id": str(n), "phase": m[1], "name": m[2], "obj": "", "gate": ""}
        rows.append(epic)
        continue
    if epic is None:
        continue
    if m := OBJ.match(line):
        epic["obj"] = m[1]
    elif m := GATE.match(line):
        epic["gate"] = m[1]
    elif m := ROW.match(line):
        code, frente, paso, criterio = m.groups()
        done = "✅" in criterio
        rows.append({
            "code": code, "frente": frente, "paso": paso.replace("`", ""),
            "criterio": criterio.replace("✅ (hecho)", "").replace("`", "").strip(),
            "parent": epic["id"], "phase": epic["phase"], "done": done,
        })

OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Issue ID", "Parent ID", "Issue Type", "Summary", "Description", "Labels", "Labels", "Component", "Priority", "Status"])
    for r in rows:
        if "name" in r:
            w.writerow([r["id"], "", "Epic", f"{r['phase']} · {r['name']}",
                        f"Objetivo: {r['obj']}\n\nGate de salida: {r['gate']}\n\nRef: docs/planning/plan-maestro.md",
                        r["phase"], "etapa-A", "", "High", "To Do"])
        else:
            kind = "Task" if r["frente"] in ("OPS", "DOC") else "Story"
            prio = "High" if r["frente"] == "SEC" or r["code"].endswith("-01") else "Medium"
            w.writerow(["", r["parent"], kind, f"[{r['code']}] {r['paso']}",
                        f"Criterio de aceptación: {r['criterio']}\n\nRef: docs/planning/plan-maestro.md#{r['phase'].lower()}",
                        r["phase"], r["frente"].lower(), FRENTES[r["frente"]], prio,
                        "Done" if r["done"] else "To Do"])

epics = sum(1 for r in rows if "name" in r)
print(f"{epics} epics, {len(rows) - epics} issues -> {OUT.relative_to(ROOT)}")
