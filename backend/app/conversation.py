"""Conservative follow-up resolution and explicitly requested external translation."""
import re

LANGUAGES = {"en", "fr", "ur", "ar", "es", "de"}
FOLLOWUP = re.compile(r"\b(it|that|this|they|them|those|there|one)\b|^(and|what about|how about)\b", re.I)

def translate(text: str, source: str, target: str) -> str:
    if source == target:
        return text
    from deep_translator import GoogleTranslator
    translator = GoogleTranslator(source=source, target=target)
    # Provider limits individual strings to 5000 characters.
    parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
    return " ".join(translator.translate(part) for part in parts)

def respond(engine, message, category, previous, language):
    query = translate(message, "auto", "en") if language != "en" else message
    result = engine.respond(query, category)
    used = False
    # Never let context override an independently matched question.
    if not result["matched"] and previous and FOLLOWUP.search(query) and len(query.split()) <= 12:
        known = next((row for row in engine.faqs if row["question"] == previous
                      and category in ("all", row["category"])), None)
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
