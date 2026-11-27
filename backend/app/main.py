"""QueryMind FAQ service: no paid API keys, no external inference calls."""
import json
import os
import secrets
import tempfile
from threading import RLock
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import FAQEngine
from .conversation import respond, LANGUAGES

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "faqs.json"
app = FastAPI(title="QueryMind AI API", version="1.0.0", description="CodeAlpha Task 2 — NLP FAQ chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)


@lru_cache
def get_engine() -> FAQEngine:
    faqs = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return FAQEngine(faqs)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)
    category: str = Field(default="all", max_length=40)
    previous_question: str | None = Field(default=None, max_length=1500)
    language: str = Field(default="en", max_length=2)


@app.get("/api/health")
def health():
    return {"status": "ok", "faq_count": len(get_engine().faqs)}


@app.get("/api/faqs")
def faqs(category: str = Query(default="all", max_length=40)):
    rows = get_engine().faqs
    if category != "all":
        rows = [row for row in rows if row["category"] == category]
    return {"faqs": [{"id": item["id"], "question": item["question"], "category": item["category"]} for item in rows]}


@app.get("/api/categories")
def categories():
    return {"categories": sorted({row["category"] for row in get_engine().faqs})}


@app.post("/api/chat")
def chat(request: ChatRequest):
    categories = {row["category"] for row in get_engine().faqs}
    if request.category != "all" and request.category not in categories:
        raise HTTPException(status_code=422, detail="Unknown category")
    if request.language not in LANGUAGES:
        raise HTTPException(422, "Unsupported language")
    try:
        return respond(get_engine(), request.message, request.category, request.previous_question, request.language)
    except Exception as exc:
        if request.language == "en":
            raise
        raise HTTPException(502, "Translation service unavailable; try English") from exc


# Administrative replacement of the complete knowledge base.
_admin_lock = RLock()


class FAQRecord(BaseModel):
    id: str | int
    question: str = Field(min_length=1, max_length=1500)
    answer: str = Field(min_length=1, max_length=10000)
    category: str = Field(min_length=1, max_length=40)
    alternatives: list[str] = Field(default_factory=list, max_length=30)


class KnowledgeUpdate(BaseModel):
    faqs: list[FAQRecord] = Field(min_length=1, max_length=2000)


def require_admin(authorization: str = ""):
    token = os.getenv("QUERYMIND_ADMIN_TOKEN")
    if not token:
        raise HTTPException(503, "Administration is disabled")
    if not secrets.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(401, "Invalid administration token")


@app.get("/api/admin/faqs")
def admin_faqs(authorization: str = Header(default="")):
    require_admin(authorization)
    with _admin_lock:
        return {"faqs": get_engine().faqs}


@app.put("/api/admin/faqs")
def replace_faqs(request: KnowledgeUpdate, authorization: str = Header(default="")):
    require_admin(authorization)
    rows = [item.model_dump() for item in request.faqs]
    if len({str(row["id"]) for row in rows}) != len(rows):
        raise HTTPException(422, "Duplicate FAQ IDs")
    if len({row["question"].strip().casefold() for row in rows}) != len(rows):
        raise HTTPException(422, "Duplicate questions")
    with _admin_lock:
        try:
            FAQEngine(rows)
        except ValueError as exc:
            raise HTTPException(422, "Knowledge base cannot be indexed") from exc
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=DATA_FILE.parent, delete=False) as stream:
                temp = Path(stream.name)
                json.dump(rows, stream, ensure_ascii=False, indent=2)
            os.replace(temp, DATA_FILE)
            get_engine.cache_clear()
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return {"status": "updated", "faq_count": len(rows)}

from .documents import router as document_router
app.include_router(document_router)

from .playground import Experiment, Evaluation, rank, evaluate

@app.get("/api/playground/modes")
def playground_modes():
    return {"modes": ["tfidf", "hybrid"] if get_engine().semantic is not None else ["tfidf"]}

@app.post("/api/playground/rank")
def playground_rank(body: Experiment):
    return rank(get_engine(), body.question, body.threshold, body.mode)

@app.post("/api/playground/evaluate")
def playground_evaluate(body: Evaluation):
    return evaluate(get_engine(), body)

from .monitor import monitor, snapshot
from .tickets import TicketCreate, TicketUpdate, create_ticket, list_tickets, update_ticket

app.middleware("http")(monitor)

@app.get("/api/monitor")
def system_monitor(authorization: str = Header(default="")):
    require_admin(authorization)
    return {**snapshot(), "engine": "hybrid" if get_engine().semantic is not None else "tfidf"}

@app.post("/api/tickets")
def submit_ticket(body: TicketCreate):
    return create_ticket(body)

@app.get("/api/admin/tickets")
def admin_tickets(authorization: str = Header(default="")):
    require_admin(authorization)
    return list_tickets()

@app.put("/api/admin/tickets/{ticket_id}")
def admin_update_ticket(ticket_id: str, body: TicketUpdate, authorization: str = Header(default="")):
    require_admin(authorization)
    return update_ticket(ticket_id, body)
