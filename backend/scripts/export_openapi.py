"""Exporta el contrato OpenAPI a shared/contracts/openapi.json.

Uso (desde backend/):
    uv run python scripts/export_openapi.py          # escribe el archivo
    uv run python scripts/export_openapi.py --check  # falla si el archivo no está al día (CI)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import REPO_ROOT, Settings
from app.main import create_app

TARGET = REPO_ROOT / "shared" / "contracts" / "openapi.json"


def render() -> str:
    # Valores ficticios: el contrato no depende de la configuración real.
    settings = Settings(_env_file=None, app_env="test", database_url="unused", redis_url="unused")
    spec = create_app(settings).openapi()
    return json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> int:
    content = render()
    if "--check" in sys.argv:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != content:
            print(
                f"{TARGET} está desactualizado: ejecuta scripts/export_openapi.py", file=sys.stderr
            )
            return 1
        print("Contrato OpenAPI al día")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8")
    print(f"Escrito {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
