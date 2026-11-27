"""Local extractive document QA; no persistent server document store."""
from io import BytesIO
import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

router = APIRouter(prefix="/api/documents")
MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 100
MAX_TEXT = 200_000

class Page(BaseModel):
    page: int = Field(ge=1, le=MAX_PAGES)
    text: str = Field(max_length=MAX_TEXT)

class DocumentQuery(BaseModel):
    question: str = Field(min_length=1, max_length=1500)
    pages: list[Page] = Field(min_length=1, max_length=MAX_PAGES)

def extract_pdf(data: bytes):
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Maximum upload size is 5 MB")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(415, "Expected a PDF file")
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise HTTPException(422, "Encrypted PDFs are not supported")
        if len(reader.pages) > MAX_PAGES:
            raise HTTPException(413, "Maximum 100 pages")
        pages = []
        total = 0
        for i, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            total += len(text)
            if total > MAX_TEXT:
                raise HTTPException(413, "Extracted text exceeds limit")
            if text:
                pages.append({"page": i, "text": text})
        if not pages:
            raise HTTPException(422, "No extractable text; scanned PDFs require OCR")
        return {"pages": pages, "page_count": len(reader.pages)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422, "Unable to read PDF") from exc

@router.post("/extract")
async def extract(request: Request):
    data = bytearray()
    async for block in request.stream():
        if len(data) + len(block) > MAX_BYTES:
            raise HTTPException(413, "Maximum upload size is 5 MB")
        data.extend(block)
    from starlette.concurrency import run_in_threadpool
    return await run_in_threadpool(extract_pdf, bytes(data))

def retrieve(question, pages):
    chunks = []
    for page in pages:
        # Rank short source passages rather than entire pages.
        for paragraph in re.split(r"\n\s*\n|\n(?=\s*\d+\.\s)", page.text):
            sentences = re.split(r"(?<=[.!?])\s+|\n+", paragraph.strip())
            for sentence in sentences:
                words = sentence.split()
                for start in range(0, len(words), 60):
                    passage = " ".join(words[start:start+80])
                    if passage:
                        chunks.append((page.page, passage))
    if not chunks:
        return []
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1,2))
        matrix = vectorizer.fit_transform([text for _, text in chunks])
        scores = cosine_similarity(vectorizer.transform([question]), matrix)[0]
    except ValueError:
        return []
    indices = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [{"page": chunks[i][0], "text": chunks[i][1], "score": round(float(scores[i]),4)}
            for i in indices[:3] if scores[i] >= .12]

@router.post("/query")
def query(body: DocumentQuery):
    if sum(len(p.text) for p in body.pages) > MAX_TEXT:
        raise HTTPException(413, "Document text exceeds limit")
    if not body.question.strip():
        raise HTTPException(422, "Question is required")
    if len({p.page for p in body.pages}) != len(body.pages):
        raise HTTPException(422, "Duplicate page numbers")
    citations = retrieve(body.question, body.pages)
    return {"matched": bool(citations), "answer": citations[0]["text"] if citations else "No sufficiently relevant passage found. Try a more specific question.", "citations": citations}
