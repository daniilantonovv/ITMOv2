def test_create_returns_201_with_id_and_totals(client, new_collection):
    response = client.post("/api/collections", json=new_collection())

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["created_at"]
    assert body["products"][1]["quantity"] == 1
    assert body["totals"] == {
        "price": 468.8,
        "kcal": 600,
        "protein": 32.6,
        "fat": 34,
        "carbs": 43.6,
    }


def test_get_returns_created_collection(client, new_collection):
    created = client.post("/api/collections", json=new_collection()).json()

    response = client.get(f"/api/collections/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_returns_404(client):
    response = client.get("/api/collections/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "collection not found"}


def test_list_returns_newest_first_summaries(client, new_collection):
    for title in ["first", "second", "third"]:
        client.post("/api/collections", json=new_collection(title=title))

    response = client.get("/api/collections")

    assert response.status_code == 200
    items = response.json()
    assert [item["title"] for item in items] == ["third", "second", "first"]
    assert "products" not in items[0]
    assert items[0]["product_count"] == 2
    assert items[0]["totals"]["price"] == 468.8


def test_list_defaults_to_10_items(client, new_collection):
    for i in range(12):
        client.post("/api/collections", json=new_collection(title=f"c{i}"))

    items = client.get("/api/collections").json()

    assert len(items) == 10
    assert items[0]["title"] == "c11"


def test_list_respects_limit(client, new_collection):
    for i in range(3):
        client.post("/api/collections", json=new_collection(title=f"c{i}"))

    assert len(client.get("/api/collections?limit=2").json()) == 2


def test_list_rejects_limit_out_of_range(client):
    assert client.get("/api/collections?limit=0").status_code == 422
    assert client.get("/api/collections?limit=101").status_code == 422


def test_list_filters_by_category(client, new_collection):
    client.post("/api/collections", json=new_collection(title="a", category="Завтраки"))
    client.post("/api/collections", json=new_collection(title="b", category="Ужины"))

    items = client.get("/api/collections", params={"category": "Ужины"}).json()

    assert [item["title"] for item in items] == ["b"]


def test_categories_are_grouped_with_counts(client, new_collection):
    for category in ["Ужины", "Завтраки", "Ужины"]:
        client.post("/api/collections", json=new_collection(category=category))

    response = client.get("/api/categories")

    assert response.status_code == 200
    assert response.json() == [
        {"category": "Завтраки", "count": 1},
        {"category": "Ужины", "count": 2},
    ]


def test_update_replaces_fields_but_keeps_id_and_created_at(client, new_collection):
    created = client.post("/api/collections", json=new_collection()).json()
    changed = new_collection(
        title="Новое название",
        category="Ужины",
        products=[{"name": "Паста", "price": 120}],
    )

    response = client.put(f"/api/collections/{created['id']}", json=changed)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["created_at"] == created["created_at"]
    assert body["title"] == "Новое название"
    assert body["category"] == "Ужины"
    assert body["totals"]["price"] == 120
    assert client.get(f"/api/collections/{created['id']}").json() == body


def test_update_missing_returns_404(client, new_collection):
    response = client.put("/api/collections/999", json=new_collection())

    assert response.status_code == 404


def test_delete_removes_collection(client, new_collection):
    created = client.post("/api/collections", json=new_collection()).json()

    response = client.delete(f"/api/collections/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/api/collections/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/api/collections/999").status_code == 404


def test_data_survives_app_restart(tmp_path, new_collection):
    from fastapi.testclient import TestClient

    from app.main import create_app

    db = tmp_path / "persist.db"
    created = TestClient(create_app(db_path=db)).post(
        "/api/collections", json=new_collection()
    ).json()

    reopened = TestClient(create_app(db_path=db))

    assert reopened.get(f"/api/collections/{created['id']}").json() == created
