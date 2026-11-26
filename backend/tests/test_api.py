from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["faq_count"] >= 15


def test_chat():
    response = client.post("/api/chat", json={"message": "How can I reset my password?"})
    assert response.status_code == 200
    assert response.json()["matched"] is True


def test_validation():
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert client.post("/api/chat", json={"message": "test", "category": "nonexistent"}).status_code == 422


def test_list_and_categories():
    assert client.get("/api/faqs").json()["faqs"]
    assert "account" in client.get("/api/categories").json()["categories"]
