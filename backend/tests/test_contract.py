import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_openapi.py"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_openapi", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exported_contract_is_up_to_date():
    exporter = _load_exporter()

    assert exporter.TARGET.read_text(encoding="utf-8") == exporter.render(), (
        "Regenera el contrato: uv run python scripts/export_openapi.py"
    )
