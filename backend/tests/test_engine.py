from app.engine import FAQEngine, preprocess


FAQS = [
    {"id": 1, "category": "account", "question": "How do I reset my password?", "alternatives": ["forgotten password recover access"], "answer": "Reset it."},
    {"id": 2, "category": "billing", "question": "How can I get a refund?", "alternatives": ["return my payment"], "answer": "Request a refund."},
]


def test_preprocess_normalizes_words():
    assert "password" in preprocess("How do I RESET my Password?").split()


def test_matches_paraphrase():
    result = FAQEngine(FAQS).respond("I have forgotten my password")
    assert result["matched"] is True
    assert result["matched_question"] == FAQS[0]["question"]


def test_filters_by_category():
    assert FAQEngine(FAQS).respond("reset my password", "billing")["matched"] is False


def test_unknown_question_abstains():
    result = FAQEngine(FAQS).respond("quantum banana pineapple spaceship")
    assert result["matched"] is False
    assert result["matched_question"] is None


def test_empty_faq_data_rejected():
    import pytest
    with pytest.raises(ValueError):
        FAQEngine([])
