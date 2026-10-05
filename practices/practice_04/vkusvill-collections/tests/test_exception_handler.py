"""Test that DuplicateCartUrlError is handled centrally via exception handler."""


def test_duplicate_cart_url_handled_via_exception_handler_for_post(client, new_collection):
    """POST duplicate cart_url returns 409 via centralized exception handler."""
    cart = "https://vkusvill.ru/cart/share/handler_test"
    client.post("/api/collections", json=new_collection(cart_url=cart))

    response = client.post("/api/collections", json=new_collection(cart_url=cart))

    assert response.status_code == 409
    assert response.json() == {"detail": "collection with this cart_url already exists"}


def test_duplicate_cart_url_handled_via_exception_handler_for_put(client, new_collection):
    """PUT duplicate cart_url returns 409 via centralized exception handler."""
    cart_a = "https://vkusvill.ru/cart/share/handler_a"
    cart_b = "https://vkusvill.ru/cart/share/handler_b"
    first = client.post("/api/collections", json=new_collection(cart_url=cart_a)).json()
    second = client.post("/api/collections", json=new_collection(cart_url=cart_b)).json()

    response = client.put(f"/api/collections/{second['id']}", json=new_collection(cart_url=cart_a))

    assert response.status_code == 409
    assert response.json() == {"detail": "collection with this cart_url already exists"}
