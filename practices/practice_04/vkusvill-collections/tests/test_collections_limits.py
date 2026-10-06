import pytest

MAX_COLLECTIONS = 100


def test_creating_101st_collection_evicts_the_oldest(client, new_collection):
    ids = [
        client.post("/api/collections", json=new_collection(title=f"c{i}")).json()["id"]
        for i in range(MAX_COLLECTIONS + 1)
    ]

    assert client.get(f"/api/collections/{ids[0]}").status_code == 404
    assert client.get(f"/api/collections/{ids[1]}").status_code == 200
    assert len(client.get("/api/collections?limit=100").json()) == MAX_COLLECTIONS
    assert sum(c["count"] for c in client.get("/api/categories").json()) == MAX_COLLECTIONS


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": "   "},
        {"title": "x" * 121},
        {"category": ""},
        {"category": "x" * 51},
        {"cart_url": "http://vkusvill.ru/cart/1"},
        {"cart_url": "https://evil.example/cart/1"},
        {"cart_url": "https://vkusvill.ru.evil.example/cart"},
        {"cart_url": "javascript:alert(1)"},
        {"products": []},
        {"products": [{"name": "x", "price": 1}] * 101},
        {"products": [{"name": "", "price": 1}]},
        {"products": [{"name": "x", "price": -1}]},
        {"products": [{"name": "x", "price": 1, "quantity": 0}]},
        {"products": [{"name": "x", "price": 1, "kcal": -5}]},
    ],
    ids=lambda overrides: next(iter(overrides)),
)
def test_invalid_collection_is_rejected_and_not_stored(client, new_collection, overrides):
    response = client.post("/api/collections", json=new_collection(**overrides))

    assert response.status_code == 422
    assert client.get("/api/collections").json() == []


def test_subdomain_cart_url_is_accepted(client, new_collection):
    url = "https://m.vkusvill.ru/cart/share/1"

    response = client.post("/api/collections", json=new_collection(cart_url=url))

    assert response.status_code == 201


def test_title_and_category_are_trimmed(client, new_collection):
    body = client.post(
        "/api/collections", json=new_collection(title="  Ужин  ", category=" Ужины ")
    ).json()

    assert (body["title"], body["category"]) == ("Ужин", "Ужины")
