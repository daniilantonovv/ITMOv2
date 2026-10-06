"""The collection-approval skill script, run as the agent runs it: a subprocess."""

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".opencode/skills/collection-approval"
SCRIPT = SKILL / "scripts/preview.py"
EXAMPLE = SKILL / "examples/dinner.json"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, cwd=ROOT
    )


def test_valid_collection_prints_receipt_and_approval_question():
    result = run(str(EXAMPLE), "--offline")

    assert result.returncode == 0, result.stderr
    assert "Паста за 20 минут" in result.stdout
    assert "Итого: 687,00 ₽" in result.stdout
    assert "2 400 ккал" in result.stdout
    assert "Сохранить эту подборку на дашборд? Ответьте «да» или опишите правки." in result.stdout


def test_invalid_collection_lists_field_errors(tmp_path):
    bad = json.loads(EXAMPLE.read_text())
    bad["cart_url"] = "http://evil.example/cart"
    bad["products"][1]["price"] = -5
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad, ensure_ascii=False))

    result = run(str(path), "--offline")

    assert result.returncode == 1
    assert "cart_url" in result.stdout
    assert "products.1.price" in result.stdout
    assert "Сохранить" not in result.stdout


def test_already_saved_cart_is_reported_before_asking(tmp_path, monkeypatch):
    from app.main import create_app

    api = TestClient(create_app(db_path=tmp_path / "skill.db"))
    data = json.loads(EXAMPLE.read_text())
    api.post("/api/collections", json=data)
    saved = api.get("/api/collections", params={"limit": 100}).json()
    listing = tmp_path / "listing.json"
    listing.write_text(json.dumps(saved, ensure_ascii=False))

    result = run(str(EXAMPLE), "--listing", str(listing))

    assert result.returncode == 2
    assert "уже сохранена" in result.stdout
    assert "Сохранить" not in result.stdout


def test_unreachable_api_is_a_warning_not_a_failure():
    result = run(str(EXAMPLE), "--api", "http://127.0.0.1:9")

    assert result.returncode == 0
    assert "не удалось проверить дубликаты" in result.stdout
