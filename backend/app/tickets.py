from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, Field

class TicketCreate(BaseModel):
    question: str = Field(min_length=1, max_length=1500)
    priority: Literal["low", "normal", "high"] = "normal"

class TicketUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]
    note: str = Field(default="", max_length=2000)

@contextmanager
def db():
    path = os.getenv("QUERYMIND_TICKET_DB", str(Path(__file__).resolve().parents[1] / "data" / "tickets.sqlite3"))
    connection = sqlite3.connect(path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY, question TEXT NOT NULL, priority TEXT NOT NULL,
                status TEXT NOT NULL, note TEXT NOT NULL, created TEXT NOT NULL,
                updated TEXT NOT NULL)""")
            yield connection
    finally:
        connection.close()

def now():
    return datetime.now(timezone.utc).isoformat()

def create_ticket(body):
    question = body.question.strip()
    if not question:
        raise HTTPException(422, "Question is required")
    ticket_id = uuid4().hex
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] >= 1000:
            raise HTTPException(409, "Ticket storage limit reached")
        stamp = now()
        conn.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?)",
                     (ticket_id, question, body.priority, "open", "", stamp, stamp))
    return {"id": ticket_id, "status": "open"}

def list_tickets():
    with db() as conn:
        return {"tickets": [dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY created DESC LIMIT 1000")]}

def update_ticket(ticket_id, body):
    with db() as conn:
        changed = conn.execute("UPDATE tickets SET status=?, note=?, updated=? WHERE id=?",
                               (body.status, body.note, now(), ticket_id))
        if not changed.rowcount:
            raise HTTPException(404, "Ticket not found")
    return {"status": body.status}
