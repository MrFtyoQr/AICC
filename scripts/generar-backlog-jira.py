"""Genera docs/planning/jira/backlog.csv desde el plan maestro y las historias de usuario.

Jerarquía: Epic (fase del plan maestro) → Story (HU de historias-usuario.md) → Sub-task (tarea del plan).
Falla si una tarea del plan no pertenece a ninguna HU, pertenece a varias, o una HU cita una tarea inexistente.
Uso: python -I scripts/generar-backlog-jira.py
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "docs" / "planning" / "plan-maestro.md"
HUS = ROOT / "docs" / "planning" / "historias-usuario.md"
OUT = ROOT / "docs" / "planning" / "jira" / "backlog.csv"

FRENTES = {"BE": "Backend", "APP": "App movil", "UX": "UX-UI", "OPS": "DevOps", "SEC": "Seguridad", "DOC": "Documentacion"}
SECTION = re.compile(r"^## (F\d|O\d) · (.+)$")
ROW = re.compile(r"^\| ((?:F|O)\d-[A-Z]+-\d+) \| ([A-Z]+) \| (.+?) \| (.+?) \|$")
GATE = re.compile(r"^\*\*Gate .+?:\*\* (.+)$")
OBJ = re.compile(r"^\*\*Objetivo:\*\* (.+)$")
HU_HEAD = re.compile(r"^### (HU-\d+) · (.+)$")
HU_FIELD = re.compile(r"^- \*\*(\w+):\*\* (.+)$")
CRITERION = re.compile(r"^\d+\. (.+)$")


def clean(text: str) -> str:
    return text.replace("`", "").replace("✅ (hecho)", "").strip()


def parse_plan():
    epics, tasks, current = {}, {}, None
    for line in PLAN.read_text(encoding="utf-8").splitlines():
        if m := SECTION.match(line):
            current = m[1]
            epics[current] = {"name": m[2], "obj": "", "gate": ""}
        elif current and (m := OBJ.match(line)):
            epics[current]["obj"] = clean(m[1])
        elif current and (m := GATE.match(line)):
            epics[current]["gate"] = clean(m[1])
        elif current and (m := ROW.match(line)):
            code, frente, paso, criterio = m.groups()
            tasks[code] = {"phase": current, "frente": frente, "paso": clean(paso),
                           "criterio": clean(criterio), "done": "✅" in criterio}
    return epics, tasks


def parse_hus():
    hus, current, in_criteria = [], None, False
    for line in HUS.read_text(encoding="utf-8").splitlines():
        if m := HU_HEAD.match(line):
            current = {"id": m[1], "title": m[2], "criteria": []}
            hus.append(current)
            in_criteria = False
        elif current is None:
            continue
        elif m := HU_FIELD.match(line):
            current[m[1].lower()] = m[2].strip()
        elif line.startswith("**Criterios de aceptación**"):
            in_criteria = True
        elif in_criteria and (m := CRITERION.match(line)):
            current["criteria"].append(m[1])
    for hu in hus:
        hu["tareas"] = [t.strip() for t in hu.get("tareas", "").split(",") if t.strip()]
    return hus


def validate(tasks, hus):
    errors, owner = [], {}
    for hu in hus:
        for field in ("rol", "historia", "fase", "sprint", "puntos", "prioridad", "estado", "tareas"):
            if not hu.get(field):
                errors.append(f"{hu['id']}: falta el campo '{field}'")
        if not hu["criteria"]:
            errors.append(f"{hu['id']}: sin criterios de aceptación")
        for code in hu["tareas"]:
            if code not in tasks:
                errors.append(f"{hu['id']}: tarea inexistente {code}")
            elif code in owner:
                errors.append(f"{code}: asignada a {owner[code]} y {hu['id']}")
            else:
                owner[code] = hu["id"]
            if code in tasks and tasks[code]["phase"] != hu.get("fase"):
                errors.append(f"{hu['id']}: {code} es de {tasks[code]['phase']}, la HU es de {hu.get('fase')}")
    errors += [f"{code}: no pertenece a ninguna HU" for code in tasks if code not in owner]
    return errors


def main() -> int:
    epics, tasks = parse_plan()
    hus = parse_hus()
    if errors := validate(tasks, hus):
        print("Backlog inválido:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    next_id = iter(range(1, 10_000))
    epic_ids = {}
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Issue ID", "Parent ID", "Issue Type", "Summary", "Description", "Labels", "Labels",
                    "Component", "Priority", "Status", "Sprint", "Story Points"])
        for phase, epic in epics.items():
            epic_ids[phase] = str(next(next_id))
            w.writerow([epic_ids[phase], "", "Epic", f"{phase} · {epic['name']}",
                        f"Objetivo: {epic['obj']}\n\nGate de salida: {epic['gate']}\n\nRef: docs/planning/plan-maestro.md",
                        phase, "etapa-A", "", "High", "To Do", "", ""])
        for hu in hus:
            hu_id = str(next(next_id))
            criteria = "\n".join(f"{i}. {c}" for i, c in enumerate(hu["criteria"], 1))
            desc = (f"{hu['historia']}\n\nCriterios de aceptación:\n{criteria}\n\n"
                    f"Tareas: {', '.join(hu['tareas'])}\nRef: docs/planning/historias-usuario.md#{hu['id'].lower()}")
            w.writerow([hu_id, epic_ids[hu["fase"]], "Story", f"[{hu['id']}] {hu['title']}", desc,
                        hu["fase"], hu["sprint"], "", hu["prioridad"], hu["estado"],
                        f"AICC {hu['sprint']}", hu["puntos"]])
            for code in hu["tareas"]:
                t = tasks[code]
                w.writerow([str(next(next_id)), hu_id, "Sub-task", f"[{code}] {t['paso']}",
                            f"Criterio de aceptación: {t['criterio']}\n\nRef: docs/planning/plan-maestro.md",
                            t["phase"], t["frente"].lower(), FRENTES[t["frente"]],
                            "High" if t["frente"] == "SEC" else "Medium",
                            "Done" if t["done"] else "To Do", f"AICC {hu['sprint']}", ""])

    points = sum(int(h["puntos"]) for h in hus)
    print(f"{len(epics)} epics, {len(hus)} historias ({points} pts), {len(tasks)} subtareas -> "
          f"{OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
