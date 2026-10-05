import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(db_path=tmp_path / "test.db"))


_cart_counter = 0


def make_collection(**overrides) -> dict:
    global _cart_counter
    _cart_counter += 1
    collection = {
        "title": "Завтрак на двоих",
        "category": "Завтраки",
        "cart_url": f"https://vkusvill.ru/cart/share/unique{_cart_counter}",
        "products": [
            {"name": "Сырники", "price": 189.9, "quantity": 2,
             "kcal": 220, "protein": 15, "fat": 9.5, "carbs": 20},
            {"name": "Сметана 15%", "price": 89, "kcal": 160,
             "protein": 2.6, "fat": 15, "carbs": 3.6},
        ],
    }
    collection.update(overrides)
    return collection


@pytest.fixture
def new_collection():
    return make_collection
