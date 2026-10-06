MAX_DIFF = 20_000


def test_too_large_diff_is_rejected_with_413(client, fake_llm):
    response = client.post("/review", json={"diff": "x" * (MAX_DIFF + 1)})

    assert response.status_code == 413
    assert response.json() == {"detail": "diff too large: max 20000 characters"}
    assert fake_llm.calls == []


def test_diff_at_limit_is_accepted(client, fake_llm):
    diff = "x" * MAX_DIFF

    response = client.post("/review", json={"diff": diff})

    assert response.status_code == 200
    assert fake_llm.calls == [diff]


def test_empty_diff_is_rejected_with_422(client, fake_llm):
    response = client.post("/review", json={"diff": ""})

    assert response.status_code == 422
    assert fake_llm.calls == []


def test_whitespace_only_diff_is_rejected_with_422(client, fake_llm):
    response = client.post("/review", json={"diff": " \n\t "})

    assert response.status_code == 422
    assert fake_llm.calls == []


def test_missing_diff_is_rejected_with_422(client, fake_llm):
    response = client.post("/review", json={})

    assert response.status_code == 422
    assert fake_llm.calls == []
