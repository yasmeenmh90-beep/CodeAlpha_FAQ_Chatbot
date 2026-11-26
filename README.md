# ✨ QueryMind AI — Intelligent FAQ Chatbot

**CodeAlpha Artificial Intelligence Internship · Task 2: Chatbot for FAQs**

QueryMind is a responsive FAQ assistant that uses **NLTK preprocessing**, **TF-IDF vectorization**, and **cosine similarity** to retrieve relevant answers from a curated knowledge base. It operates locally without paid API credentials.

## V2 interface upgrade

- Animated assistant orb, orbital rings, message transitions and responsive luminous styling.
- Light/dark themes and conversation history stored in browser localStorage.
- Browser speech recognition (where supported and permitted), speech synthesis, transcript downloads and per-message feedback held in session state.
- Reduced-motion support. Browser speech recognition may use a browser vendor's external speech service.

## Features

- 🧠 NLP cleaning, tokenization, stemming, stop-word removal
- 🔎 TF-IDF unigram/bigram retrieval and cosine similarity
- 🛡️ Confidence-based fallback for unknown questions
- 💬 Responsive chat UI with suggested questions and follow-up recommendations
- 📚 Searchable FAQ library with topic filtering
- 📋 Copyable conversation transcript
- 📊 Lightweight live conversation statistics
- ✅ FastAPI input validation and automated Pytest coverage
- 🔐 No server-side chat history or LLM API keys

> **Demo disclaimer:** FAQs describe an imaginary ecommerce support product. Answers are examples, not real store terms.

## Stack

| Layer | Tools |
| --- | --- |
| Frontend | React 18, TypeScript, Vite, Lucide |
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Retrieval | NLTK SnowballStemmer, scikit-learn TF-IDF + cosine similarity |
| Data | Versioned JSON knowledge base |
| Tests | Pytest + FastAPI TestClient |

## Quick start (Mac / Linux, no Docker)

**1. Backend**

```bash
git clone https://github.com/yasmeenmh90-beep/CodeAlpha_FAQ_Chatbot.git
cd CodeAlpha_FAQ_Chatbot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (new terminal; requires Node.js 20+)

```bash
cd CodeAlpha_FAQ_Chatbot/frontend
npm install
npm run dev
```

Open **http://localhost:5173**. FastAPI interactive documentation: **http://127.0.0.1:8000/docs**.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health + number of FAQs |
| GET | `/api/faqs?category=all` | List FAQ questions |
| GET | `/api/categories` | Available categories |
| POST | `/api/chat` | Return top answer + confidence |

Example:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I forgot my password","category":"all"}'
```

A successful response includes `answer`, `matched_question`, `confidence` (cosine similarity, **not a calibrated probability**), `matched`, `category`, and `suggestions`.

## Testing

```bash
cd backend
python -m pytest -q
```

```bash
cd frontend
npm run build
```

> Runtime and build checks should be executed locally or in CI after installation.

## How NLP matching works

1. Read 20 curated FAQ entries from `backend/data/faqs.json`.
2. Normalize question text to lowercase, tokenize with regex, discard common stop words and stem English tokens with NLTK.
3. Build TF-IDF vectors (including 1–2 token phrases) for FAQ questions and their alternative phrasings.
4. Transform the user's message using the same preprocessing pipeline.
5. Rank candidates by cosine similarity, restricting to the selected topic if supplied.
6. Answer only if the best score is at least **0.20**; otherwise abstain.

The score is a **lexical similarity** measurement rather than a probability that the answer is correct. The demo does not yet include transformer embeddings or a trained intent classifier.

## Project structure

```text
backend/
  app/main.py       REST API
  app/engine.py     NLP retrieval engine
  data/faqs.json    Editable FAQ knowledge base
  tests/            API and matching tests
frontend/
  src/App.tsx       Chat, filters, FAQ library
  src/styles.css    Responsive dark design
```

## Customizing

Edit `backend/data/faqs.json` to supply your own FAQs. Every entry must include an `id`, `category`, `question`, `answer`, and optional `alternatives` list. Restart the backend to reload the index.

## Deployment notes

The React build can be deployed to Vercel and FastAPI to Render. Set `VITE_API_URL` to your public API base URL **before frontend build**. Configure `allow_origins` in `backend/app/main.py` to include the deployed frontend URL. Do not set wildcard CORS on production systems with user credentials.

## CodeAlpha checklist

- [x] Collect topic-specific FAQs and answers
- [x] NLP preprocessing with NLTK
- [x] Match user questions using cosine similarity
- [x] Display the most relevant answer as a chatbot response
- [x] Simple, responsive chat UI
- [x] Unknown-question fallback and automated test coverage
- [ ] Verify local install/build and record demo video
- [ ] Deploy and add live URL

**Built for educational demonstration as CodeAlpha Internship Task 2.**
