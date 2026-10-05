def test_dashboard_page_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "/api/collections" in client.get("/static/app.js").text
