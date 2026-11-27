"""Deterministic, offline FAQ retrieval using NLTK + TF-IDF cosine similarity."""
import re
import os
from difflib import get_close_matches
import numpy as np
from dataclasses import dataclass
from typing import Any

from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_stemmer = SnowballStemmer("english")
_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset({
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been",
    "to", "of", "for", "and", "or", "in", "on", "at", "from", "with",
    "i", "me", "my", "you", "your", "we", "our", "it", "this", "that",
    "do", "does", "did", "can", "could", "would", "should", "please",
    "how", "what", "where", "when", "why", "which", "tell", "about",
})


def preprocess(text: str) -> str:
    words = _WORD.findall(text.lower())
    return " ".join(_stemmer.stem(word) for word in words if word not in _STOP)


@dataclass(frozen=True)
class Match:
    faq: dict[str, Any]
    score: float


class FAQEngine:
    def __init__(self, faqs: list[dict[str, Any]], threshold: float = 0.20):
        if not faqs:
            raise ValueError("FAQ database must not be empty")
        self.faqs = faqs
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(
            preprocessor=preprocess,
            tokenizer=str.split,
            token_pattern=None,
            lowercase=False,
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        corpus = [" ".join([faq["question"], *faq.get("alternatives", [])]) for faq in faqs]
        self.matrix = self.vectorizer.fit_transform(corpus)
        self.words = set(_WORD.findall(' '.join(corpus).lower())) | set(_STOP)
        self.semantic = None
        self.embeddings = None
        if os.getenv('QUERYMIND_SEMANTIC') == '1':
            from sentence_transformers import SentenceTransformer
            self.semantic = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            self.embeddings = self.semantic.encode(corpus, normalize_embeddings=True)

    def search(self, question: str, category: str | None = None, limit: int = 3) -> list[Match]:
        if not question.strip() or (not self.semantic and not preprocess(question)):
            return []
        query = self.vectorizer.transform([question])
        if query.nnz == 0 and self.semantic is None:
            return []
        scores = cosine_similarity(query, self.matrix)[0]
        if self.semantic is not None:
            embedding = self.semantic.encode([question], normalize_embeddings=True)[0]
            semantic = np.clip(self.embeddings @ embedding, 0, 1)
            scores = 0.25 * scores + 0.75 * semantic
        matches = [
            Match(faq, round(float(scores[index]), 4))
            for index, faq in enumerate(self.faqs)
            if category in (None, "all", faq["category"])
        ]
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:limit]

    def correct(self, question: str) -> str:
        def replace_word(match):
            word = match.group().lower()
            if len(word) < 5 or word in self.words or word.isdigit():
                return match.group()
            candidates = get_close_matches(word, sorted(self.words), n=2, cutoff=.85)
            return candidates[0] if len(candidates) == 1 else match.group()
        return re.sub(r"[A-Za-z]+", replace_word, question)

    def respond(self, question: str, category: str | None = None) -> dict[str, Any]:
        matches = self.search(question, category)
        best = matches[0] if matches else None
        confident = best is not None and best.score >= (max(self.threshold, 0.45) if self.semantic is not None else self.threshold)
        corrected = self.correct(question) if not confident and self.semantic is None else question
        if corrected != question:
            revised = self.search(corrected, category)
            if revised and revised[0].score >= max(self.threshold, .35):
                matches, best, confident = revised, revised[0], True
        return {
            "corrected_question": corrected if confident and corrected != question else None,
            "engine": "hybrid" if self.semantic is not None else "tfidf",
            "answer": best.faq["answer"] if confident else
                "I couldn't find a reliable answer to that question. Try rephrasing it or selecting one of the suggested FAQs.",
            "matched_question": best.faq["question"] if confident else None,
            "confidence": best.score if best else 0.0,
            "matched": confident,
            "category": best.faq["category"] if confident else None,
            "suggestions": [
                item.faq["question"] for item in (matches[1:] if confident else matches)
                if item.score >= 0.05
            ][:3],
        }
