from fastapi.testclient import TestClient
from app.main import app, get_engine
from app.security import RequestGuard

def client():
    return TestClient(app)

def test_blank_chat():
    assert client().post("/api/chat", json={"message": "   "}).status_code == 422

def test_invalid_pdf():
    assert client().post("/api/documents/extract", content=b"not pdf").status_code == 415

def test_document_retrieval():
    response = client().post("/api/documents/query", json={"question": "refund policy", "pages": [{"page": 2, "text": "Refund policy allows refunds within thirty days."}]})
    assert response.status_code == 200
    assert response.json()["citations"][0]["page"] == 2

def test_evaluation():
    question = get_engine().faqs[0]["question"]
    response = client().post("/api/playground/evaluate", json={"cases": [{"question": question, "expected": question}]})
    assert response.status_code == 200
    assert response.json()["accuracy"] == 1

def test_ticket_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYMIND_TICKET_DB", str(tmp_path / "tickets.db"))
    monkeypatch.setenv("QUERYMIND_ADMIN_TOKEN", "test-only")
    c = client()
    response = c.post("/api/tickets", json={"question": "Unresolved issue"})
    assert response.status_code == 200
    ticket_id = response.json()["id"]
    assert c.get("/api/admin/tickets").status_code == 401
    headers = {"Authorization": "Bearer test-only"}
    assert c.put("/api/admin/tickets/" + ticket_id, headers=headers, json={"status": "resolved", "note": "Done"}).status_code == 200
    assert c.get("/api/admin/tickets", headers=headers).json()["tickets"][0]["status"] == "resolved"
    assert c.get("/api/monitor", headers=headers).status_code == 200

def test_body_and_rate_limits():
    with TestClient(RequestGuard(app)) as c:
        assert c.post("/api/documents/extract", content=b"x" * (5*1024*1024+1)).status_code == 413
        for _ in range(10):
            result = c.post("/api/documents/extract", content=b"x")
        assert result.status_code == 429
