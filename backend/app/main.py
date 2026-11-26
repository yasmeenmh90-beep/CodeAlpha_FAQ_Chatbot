"""QueryMind FAQ service: no paid API keys, no external inference calls."""
import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .engine import FAQEngine

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "faqs.json"
app = FastAPI(title="QueryMind AI API", version="1.0.0", description="CodeAlpha Task 2 — NLP FAQ chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache
def get_engine() -> FAQEngine:
    faqs = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return FAQEngine(faqs)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)
    category: str = Field(default="all", max_length=40)


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
    return get_engine().respond(request.message, request.category)
