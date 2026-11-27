"""Conservative follow-up resolution and explicitly requested external translation."""
import re
import time
from threading import Lock, BoundedSemaphore
from concurrent.futures import ThreadPoolExecutor, TimeoutError

_translation_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='translation')

LANGUAGES = {"en", "fr", "ur", "ar", "es", "de"}
FOLLOWUP = re.compile(r"\b(it|that|this|they|them|those|there|one)\b|^(and|what about|how about)\b", re.I)

LOCALES = {"en": "en-GB", "fr": "fr-FR", "ar": "ar-SA", "ur": "ur-PK", "es": "es-ES", "de": "de-DE"}
_provider_lock = Lock()
_google_retry_at = 0.0
_translation_slots = BoundedSemaphore(4)

def translate(text: str, source: str, target: str) -> str:
    if source == target or not text.strip():
        return text
    if not _translation_slots.acquire(blocking=False):
        raise ValueError("Translation service busy")
    try:
        future = _translation_pool.submit(_translate, text, source, target)
    except BaseException:
        _translation_slots.release()
        raise
    future.add_done_callback(lambda _: _translation_slots.release())
    try:
        return future.result(timeout=25)
    except TimeoutError as exc:
        raise ValueError("Translation provider deadline exceeded") from exc

def _translate(text: str, source: str, target: str) -> str:
    global _google_retry_at
    if source == target or not text.strip():
        return text
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    with _provider_lock:
        google_available = time.monotonic() >= _google_retry_at
    if google_available:
        try:
            translator = GoogleTranslator(source=source, target=target)
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            answers = [translator.translate(part) for part in parts]
            if not all(isinstance(a, str) and a.strip() for a in answers):
                raise ValueError("Empty translation")
            return " ".join(answers)
        except Exception:
            with _provider_lock:
                _google_retry_at = time.monotonic() + 300
    # MyMemory requires explicit source and target locales.
    translator = MyMemoryTranslator(source=LOCALES[source], target=LOCALES[target])
    # Keep each request below MyMemory's 500-byte limit, including Unicode.
    parts, part = [], ""
    for word in text.split():
        for i in range(0, len(word), 100):
            piece = word[i:i+100]
            candidate = (part + " " + piece).strip()
            if len(candidate.encode("utf-8")) > 450:
                parts.append(part)
                part = piece
            else:
                part = candidate
    if part:
        parts.append(part)
    answers = [translator.translate(p) for p in parts]
    if not all(isinstance(a, str) and a.strip() and "MYMEMORY WARNING" not in a.upper() for a in answers):
        raise ValueError("Translation fallback unavailable")
    return " ".join(answers)

def respond(engine, message, category, previous, language):
    query = translate(message, language, "en") if language != "en" else message
    result = engine.respond(query, category)
    used = False
    # For short explicit references, restrict ambiguous follow-ups to the known topic.
    if previous and FOLLOWUP.search(query) and len(query.split()) <= 12:
        known = next((row for row in engine.faqs if row["question"] == previous and category in ("all", None, row["category"])), None)
        if known and not result["matched"]:
            scoped = engine.respond(query, known["category"])
            if scoped["matched"] and scoped["matched_question"] != previous:
                result, used = scoped, True
    # Never let context override an independently matched question.
    if not result["matched"] and previous and FOLLOWUP.search(query) and len(query.split()) <= 12:
        known = next((row for row in engine.faqs if row["question"] == previous
                      and category in ("all", None, row["category"])), None)
        if known:
            # Replace only explicit references; do not answer by repeating the old question.
            subject = re.sub(r"^(how|what|where|when|why|can|do|does|is|are)\s+", "", previous.rstrip("?"), flags=re.I)
            expanded = re.sub(r"\b(it|that|this|they|them|those|there|one)\b", lambda _: subject, query, flags=re.I)
            if expanded != query:
                candidate = engine.respond(expanded, category)
                if candidate["matched"] and candidate["matched_question"] != previous:
                    result, used = candidate, True
    result["context_used"] = used
    result["language"] = language
    if language != "en":
        result["answer"] = translate(result["answer"], "en", language)
    return result
