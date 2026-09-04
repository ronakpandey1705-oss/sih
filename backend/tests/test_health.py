def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "packsure-backend"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        data = response.json()
        assert "docs" in data or "message" in data
    else:
        assert b"PackSure" in response.content
