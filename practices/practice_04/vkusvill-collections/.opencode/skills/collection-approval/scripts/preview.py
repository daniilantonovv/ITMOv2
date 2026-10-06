"""Validate a collection against the service contract and print a receipt for the operator.

Usage (from the project root):
  .venv/bin/python .opencode/skills/collection-approval/scripts/preview.py FILE.json [--api URL | --offline | --listing FILE]

Exit codes: 0 = valid, show it and ask for approval; 1 = invalid input; 2 = cart already saved.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.models import CollectionIn, Totals  # noqa: E402

QUESTION = "Сохранить эту подборку на дашборд? Ответьте «да» или опишите правки."


def rub(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


def grams(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def saved_listing(args: argparse.Namespace) -> list[dict] | None:
    """Collections already in the service, or None if they could not be fetched."""
    if args.listing:
        return json.loads(Path(args.listing).read_text())
    if args.offline:
        return []
    try:
        response = httpx.get(f"{args.api}/api/collections", params={"limit": 100}, timeout=5)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return None


def receipt(data: CollectionIn) -> str:
    totals = Totals.of(data.products)
    width = max(len(p.name) for p in data.products) + 2
    lines = [f"Подборка: {data.title}", f"Категория: {data.category}", ""]
    for p in data.products:
        lines.append(f"  {p.name.ljust(width, '.')} {p.quantity} × {rub(p.price)} = {rub(p.price * p.quantity)}")
    lines += [
        "",
        f"Итого: {rub(totals.price)}",
        f"КБЖУ: {grams(totals.kcal)} ккал, белки {grams(totals.protein)} г, "
        f"жиры {grams(totals.fat)} г, углеводы {grams(totals.carbs)} г",
        f"Корзина: {data.cart_url}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", type=Path)
    parser.add_argument("--api", default="http://127.0.0.1:8010", help="service URL for the duplicate check")
    parser.add_argument("--offline", action="store_true", help="skip the duplicate check")
    parser.add_argument("--listing", help="JSON file with saved collections, instead of calling the API")
    args = parser.parse_args()

    try:
        data = CollectionIn.model_validate_json(args.file.read_text())
    except ValidationError as error:
        print("НЕВАЛИДНО — не показывайте оператору, исправьте данные:")
        for e in error.errors():
            location = ".".join(str(p) for p in e["loc"])
            print(f"  - {location}: {e['msg']}")
        return 1

    listing = saved_listing(args)
    if listing is None:
        print(f"Предупреждение: не удалось проверить дубликаты ({args.api} недоступен).\n")
    else:
        duplicate = next((c for c in listing if c["cart_url"] == data.cart_url), None)
        if duplicate:
            print(f"Эта корзина уже сохранена: подборка №{duplicate['id']} «{duplicate['title']}».")
            print("Не сохраняйте повторно; спросите оператора, нужно ли изменить существующую.")
            return 2

    print(receipt(data))
    print()
    print(QUESTION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
