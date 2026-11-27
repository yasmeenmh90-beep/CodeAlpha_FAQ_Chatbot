"""Read-only retrieval experiments against the current knowledge base."""
from time import perf_counter
from typing import Literal
import numpy as np
from pydantic import BaseModel, Field
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import HTTPException

class Experiment(BaseModel):
    question: str = Field(min_length=1, max_length=1500)
    threshold: float = Field(default=.2, ge=0, le=1)
    mode: Literal["tfidf", "hybrid"] = "tfidf"

class Example(BaseModel):
    question: str = Field(min_length=1, max_length=1500)
    expected: str | None = Field(default=None, max_length=1500)

class Evaluation(BaseModel):
    cases: list[Example] = Field(min_length=1, max_length=100)
    threshold: float = Field(default=.2, ge=0, le=1)
    mode: Literal["tfidf", "hybrid"] = "tfidf"

def rank(engine, question, threshold, mode):
    if mode == "hybrid" and engine.semantic is None:
        raise HTTPException(409, "Hybrid unavailable; enable QUERYMIND_SEMANTIC=1")
    start = perf_counter()
    scores = cosine_similarity(engine.vectorizer.transform([question]), engine.matrix)[0]
    if mode == "hybrid":
        embedding = engine.semantic.encode([question], normalize_embeddings=True)[0]
        scores = .25 * scores + .75 * np.clip(engine.embeddings @ embedding, 0, 1)
    indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
    candidates = [{"question": engine.faqs[i]["question"], "category": engine.faqs[i]["category"],
                   "score": float(scores[i])} for i in indices if scores[i] > 0]
    predicted = candidates[0]["question"] if candidates and candidates[0]["score"] >= threshold else None
    return {"candidates": candidates, "predicted": predicted, "latency_ms": (perf_counter()-start)*1000}

def evaluate(engine, body):
    known = {row["question"] for row in engine.faqs}
    if any(c.expected is not None and c.expected not in known for c in body.cases):
        raise HTTPException(422, "Expected labels must be exact FAQ questions or null")
    rows = []
    tp = fp = fn = correct = hits = reciprocal = positives = 0
    for case in body.cases:
        result = rank(engine, case.question, body.threshold, body.mode)
        predicted = result["predicted"]
        correct += int(predicted == case.expected)
        tp += int(predicted is not None and predicted == case.expected)
        fp += int(predicted is not None and predicted != case.expected)
        fn += int(case.expected is not None and predicted != case.expected)
        if case.expected is not None:
            positives += 1
            for i, candidate in enumerate(result["candidates"], 1):
                if candidate["question"] == case.expected:
                    hits += 1
                    reciprocal += 1/i
                    break
        rows.append({"question": case.question, "expected": case.expected, **result})
    precision = tp/(tp+fp) if tp+fp else 0
    recall = tp/(tp+fn) if tp+fn else 0
    return {"accuracy": correct/len(rows), "precision": precision, "recall": recall,
            "f1": 2*precision*recall/(precision+recall) if precision+recall else 0,
            "recall_at_5": hits/positives if positives else None,
            "mrr_at_5": reciprocal/positives if positives else None,
            "mean_latency_ms": sum(r["latency_ms"] for r in rows)/len(rows), "rows": rows}
