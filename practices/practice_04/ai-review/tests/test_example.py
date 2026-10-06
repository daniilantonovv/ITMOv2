def test_review_returns_llm_answer(client, fake_llm):
    response = client.post("/review", json={"diff": "+print('hi')"})

    assert response.status_code == 200
    assert response.json() == {"review": "looks good"}
    assert fake_llm.calls == ["+print('hi')"]
