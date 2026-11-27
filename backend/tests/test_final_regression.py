import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.engine import FAQEngine
from app.documents import Page, retrieve, extract_pdf
from app.main import app
from app.playground import Evaluation, evaluate
from fastapi import HTTPException

@pytest.fixture
def engine(monkeypatch):
    monkeypatch.setenv("QUERYMIND_SEMANTIC", "0")
    return FAQEngine(json.loads((Path(__file__).resolve().parents[1] / "data/faqs.json").read_text()))

@pytest.mark.parametrize("question,expected", [
    ("How can I rest my pasword?", "How do I reset my password?"),
    ("How can I trak my order?", "How do I track my order?"),
    ("What is the stock market prediction?", None),
])
def test_retrieval(engine, question, expected):
    assert engine.respond(question)["matched_question"] == expected

def test_production_evaluation(engine):
    question = engine.faqs[0]["question"]
    result = evaluate(engine, Evaluation(production=True, cases=[{"question": question, "expected": question}]))
    assert result["accuracy"] == 1
    assert result["evaluation_mode"] == "production"
    assert result["effective_threshold"] == engine.threshold

def test_concise_document():
    citations = retrieve("How long does the warranty last?", [Page(page=2, text="Shipping costs $9.99. The warranty lasts 24 months.")])
    assert citations[0]["text"] == "The warranty lasts 24 months."
    assert citations[0]["page"] == 2

def test_pdf_size_boundary():
    with pytest.raises(HTTPException) as error:
        extract_pdf(b"x" * (5 * 1024 * 1024 + 1))
    assert error.value.status_code == 413

def test_duplicate_document_pages():
    with TestClient(app) as client:
        result = client.post("/api/documents/query", json={"question":"warranty", "pages":[{"page":1,"text":"Warranty"},{"page":1,"text":"Duplicate"}]})
    assert result.status_code == 422

def test_admin_blank_fields(monkeypatch):
    monkeypatch.setenv("QUERYMIND_ADMIN_TOKEN", "regression-only")
    with TestClient(app) as client:
        result = client.put("/api/admin/faqs", headers={"Authorization":"Bearer regression-only"}, json={"faqs":[{"id":1,"question":" ","answer":"answer","category":"account"}]})
    assert result.status_code == 422
