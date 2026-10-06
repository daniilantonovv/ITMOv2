"""Feature A — no duplicate carts (POST and PUT reject duplicate cart_url)."""
import pytest


def test_post_duplicate_cart_url_returns_409(client, new_collection):
    """POST with a cart_url that already exists returns 409 and does not store."""
    cart = "https://vkusvill.ru/cart/share/abc123"
    client.post("/api/collections", json=new_collection(cart_url=cart))

    response = client.post("/api/collections", json=new_collection(cart_url=cart, title="Another"))

    assert response.status_code == 409
    assert response.json() == {"detail": "collection with this cart_url already exists"}
    # Check nothing was stored
    all_collections = client.get("/api/collections?limit=100").json()
    assert len(all_collections) == 1
    assert all_collections[0]["title"] != "Another"


def test_post_duplicate_cart_url_does_not_modify_original(client, new_collection):
    """POST with duplicate cart_url leaves the original collection unchanged."""
    cart = "https://vkusvill.ru/cart/share/xyz"
    original = client.post("/api/collections", json=new_collection(cart_url=cart, title="Original")).json()

    client.post("/api/collections", json=new_collection(cart_url=cart, title="Duplicate"))

    unchanged = client.get(f"/api/collections/{original['id']}").json()
    assert unchanged == original


def test_put_to_another_collections_cart_url_returns_409(client, new_collection):
    """PUT that tries to use another collection's cart_url returns 409."""
    cart_a = "https://vkusvill.ru/cart/share/aaa"
    cart_b = "https://vkusvill.ru/cart/share/bbb"
    first = client.post("/api/collections", json=new_collection(cart_url=cart_a, title="First")).json()
    second = client.post("/api/collections", json=new_collection(cart_url=cart_b, title="Second")).json()

    response = client.put(
        f"/api/collections/{second['id']}", json=new_collection(cart_url=cart_a, title="Changed")
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "collection with this cart_url already exists"}
    # Verify second collection is unchanged
    unchanged = client.get(f"/api/collections/{second['id']}").json()
    assert unchanged["cart_url"] == cart_b
    assert unchanged["title"] == "Second"


def test_put_keeping_own_cart_url_is_allowed(client, new_collection):
    """PUT that keeps the same cart_url succeeds."""
    cart = "https://vkusvill.ru/cart/share/keep"
    created = client.post("/api/collections", json=new_collection(cart_url=cart, title="Old Title")).json()

    response = client.put(
        f"/api/collections/{created['id']}",
        json=new_collection(cart_url=cart, title="New Title"),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["cart_url"] == cart


def test_deleted_cart_url_can_be_reused(client, new_collection):
    """After DELETE, the cart_url can be used in a new collection."""
    cart = "https://vkusvill.ru/cart/share/reuse"
    first = client.post("/api/collections", json=new_collection(cart_url=cart, title="First")).json()

    client.delete(f"/api/collections/{first['id']}")
    response = client.post("/api/collections", json=new_collection(cart_url=cart, title="Reused"))

    assert response.status_code == 201
    assert response.json()["cart_url"] == cart


def test_evicted_cart_url_can_be_reused(client, new_collection):
    """After eviction (100+ cap), the cart_url can be used again."""
    MAX_COLLECTIONS = 100
    evicted_cart = "https://vkusvill.ru/cart/share/evict_me"
    client.post("/api/collections", json=new_collection(cart_url=evicted_cart, title="Evicted"))

    # Fill up to MAX_COLLECTIONS, evicting the first one
    for i in range(MAX_COLLECTIONS):
        client.post("/api/collections", json=new_collection(cart_url=f"https://vkusvill.ru/cart/{i}", title=f"c{i}"))

    # Now the evicted_cart should be available again
    response = client.post("/api/collections", json=new_collection(cart_url=evicted_cart, title="Reused After Eviction"))

    assert response.status_code == 201
    assert response.json()["cart_url"] == evicted_cart


def test_cart_urls_are_compared_exactly(client, new_collection):
    """Different cart_urls (e.g., different query params) are treated as distinct."""
    cart1 = "https://vkusvill.ru/cart/share/abc123"
    cart2 = "https://vkusvill.ru/cart/share/abc124"
    client.post("/api/collections", json=new_collection(cart_url=cart1))

    response = client.post("/api/collections", json=new_collection(cart_url=cart2))

    assert response.status_code == 201


def test_duplicate_cart_url_rejected_at_storage_level(tmp_path, new_collection):
    """Database ensures uniqueness: two CollectionStore instances on same file reject duplicate cart_url."""
    from app.storage import CollectionStore, DuplicateCartUrlError

    db_path = tmp_path / "shared.db"
    store1 = CollectionStore(db_path)
    store2 = CollectionStore(db_path)

    cart = "https://vkusvill.ru/cart/share/race"
    from app.models import CollectionIn

    data = CollectionIn(**new_collection(cart_url=cart))
    store1.create(data)

    # Second store on same db must reject duplicate cart_url
    with pytest.raises(DuplicateCartUrlError):
        store2.create(CollectionIn(**new_collection(cart_url=cart, title="Duplicate")))

