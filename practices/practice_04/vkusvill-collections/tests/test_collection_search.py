"""Search contract: literal Unicode title matching before the newest-first limit."""

import pytest


def add(client, new_collection, title, category="Завтраки", **fields):
    response = client.post("/api/collections", json=new_collection(title=title, category=category, **fields))
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("query", ["ЗАВТРАК", "завТрак", "  завтрак  "])
def test_search_matches_russian_title_ignoring_case_and_outer_spaces(client, new_collection, query):
    expected = add(client, new_collection, "Завтрак на двоих")
    add(client, new_collection, "Ужин")
    response = client.get("/api/collections", params={"q": query})
    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [expected["id"]]
    assert response.json()[0]["totals"] == expected["totals"]
    assert response.json()[0]["product_count"] == 2
    assert "products" not in response.json()[0]


def test_search_combines_with_exact_category_and_keeps_newest_first(client, new_collection):
    old = add(client, new_collection, "Обед первый", "Обеды")
    add(client, new_collection, "Обед другой", "Ужины")
    newest = add(client, new_collection, "Обед второй", "Обеды")
    add(client, new_collection, "Ужин", "Обеды")
    result = client.get("/api/collections", params={"q": "ОБЕД", "category": "Обеды"}).json()
    assert [c["id"] for c in result] == [newest["id"], old["id"]]


def test_search_filters_before_limit_even_beyond_first_ten(client, new_collection):
    expected = add(client, new_collection, "Редкая подборка")
    for i in range(12):
        add(client, new_collection, f"Ужин {i}")
    response = client.get("/api/collections", params={"q": "редкая", "limit": 1})
    assert [c["id"] for c in response.json()] == [expected["id"]]


def test_search_does_not_match_product_names_or_categories(client, new_collection):
    add(client, new_collection, "Утро", "Сырники", products=[{"name": "Сырники", "price": 100}])
    assert client.get("/api/collections", params={"q": "сырники"}).json() == []


@pytest.mark.parametrize("query", ["%", "_", "' OR 1=1 --", "\\", "<script>"])
def test_search_characters_are_literal(client, new_collection, query):
    wanted = add(client, new_collection, f"Набор {query} сегодня")
    add(client, new_collection, "Обычная подборка")
    response = client.get("/api/collections", params={"q": query})
    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == [wanted["id"]]
    assert len(client.get("/api/collections").json()) == 2


@pytest.mark.parametrize("query", ["", "   ", "\t \n"])
def test_empty_search_preserves_original_list_and_category(client, new_collection, query):
    add(client, new_collection, "Первый", "A")
    add(client, new_collection, "Второй", "B")
    add(client, new_collection, "Третий", "A")
    original = client.get("/api/collections", params={"category": "A", "limit": 1}).json()
    searched = client.get("/api/collections", params={"category": "A", "limit": 1, "q": query})
    assert searched.status_code == 200
    assert searched.json() == original


def test_search_query_boundary_is_validated_without_mutation(client, new_collection):
    expected = add(client, new_collection, "я" * 120)
    assert client.get("/api/collections", params={"q": "Я" * 120}).json()[0]["id"] == expected["id"]
    before = client.get("/api/collections").json()
    for query in ("я" * 121, " " * 121):
        response = client.get("/api/collections", params={"q": query})
        assert response.status_code == 422
        assert client.get("/api/collections").json() == before


def test_search_uses_full_unicode_casefold(client, new_collection):
    expected = add(client, new_collection, "Straße")
    add(client, new_collection, "Другой набор")
    assert [c["id"] for c in client.get("/api/collections", params={"q": "STRASSE"}).json()] == [expected["id"]]


def test_search_empty_result_and_category_counts(client, new_collection):
    add(client, new_collection, "Завтрак", "Завтраки")
    before = client.get("/api/categories").json()
    assert client.get("/api/collections", params={"q": "Несуществующая"}).json() == []
    assert client.get("/api/categories").json() == before
