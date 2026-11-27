<div align="center">

# QueryMind AI

### Intelligent FAQ Retrieval & Knowledge Operations

**CodeAlpha Artificial Intelligence Internship — Task 2**

![Python](https://img.shields.io/badge/Python-3.10%2B-CBB17A?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-172330?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-18-CBB17A?style=for-the-badge&logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-172330?style=for-the-badge&logo=typescript)
![NLP](https://img.shields.io/badge/AI-Hybrid%20Retrieval-CBB17A?style=for-the-badge)

*Ask. Retrieve. Understand. Improve.*

[Features](#features) · [Architecture](#architecture) · [Installation](#local-installation) · [Knowledge Studio](#knowledge-studio) · [API](#api-reference) · [Roadmap](#roadmap)

</div>

---

## Overview

QueryMind is an NLP-powered customer support demonstration that retrieves grounded answers from a curated FAQ knowledge base. It combines a React workspace, FastAPI service, explainable retrieval, browser voice capabilities, conversation analytics and administrator-controlled knowledge management.

The original lexical NLP engine remains the default. An optional multilingual Sentence Transformer model adds semantic matching without requiring a paid LLM API.

> Educational demonstration: the supplied ecommerce FAQs describe an imaginary business. QueryMind is a retrieval assistant, not a general-purpose generative AI or a production customer support platform.

## Features

| Workspace | Capabilities |
| --- | --- |
| AI Assistant | Topic-aware FAQ chat, suggested questions, fallback responses, response actions and expandable conversation view |
| Response Intelligence | Similarity scores, matched source, category, client-measured latency and retrieval pipeline summary |
| Conversation History | Browser-local saved conversations, search, rename, delete, copy and transcript download |
| FAQ Library | Searchable questions, category navigation and one-click questions |
| Voice Controls | Browser speech recognition, speech synthesis, available voice selection, playback speed and stop controls |
| Analytics | 7/14/30-day windows, six KPI cards, activity line chart, outcome donut, topic distribution, feedback and unmatched-question review, CSV export |
| Knowledge Studio | Token-protected FAQ management, draft editing, category filters, JSON import/export, duplicate checks and explicit publishing |
| Interface | Navy/champagne-gold design, light/dark themes, responsive layout and independently scrollable conversation area |
| AI Engine | Default NLTK/TF-IDF retrieval and optional multilingual semantic/lexical fusion |

## Architecture

```mermaid
flowchart LR
    U[User] --> UI[React workspace]
    UI --> API[FastAPI REST API]
    UI --> LS[Browser localStorage]
    LS --> A[Analytics dashboard]
    API --> E[FAQ retrieval engine]
    E --> L[NLTK and TF-IDF]
    E --> S[Optional Sentence Transformer]
    L --> R[Similarity ranking]
    S --> R
    R --> T{Threshold met?}
    T -->|Yes| F[Stored FAQ answer and source]
    T -->|No| B[Fallback and suggestions]
    F --> UI
    B --> UI
    K[Knowledge Studio] --> P[Bearer-token admin endpoints]
    P --> V[Validation and atomic JSON replacement]
    V --> D[FAQ JSON dataset]
    D --> E
```

## Retrieval methodology

The lexical pipeline normalizes English text, removes custom stop words, applies NLTK Snowball stemming, and fits scikit-learn TF-IDF unigram/bigram vectors on questions and their alternative phrasings. Queries are ranked by cosine similarity with optional category restriction.

| Configuration | Lexical engine (default) | Hybrid engine (optional) |
| --- | --- | --- |
| Model | TF-IDF | paraphrase-multilingual-MiniLM-L12-v2 |
| Ranking | Lexical cosine similarity | 25% lexical + 75% semantic similarity |
| Default threshold | 0.20 | 0.45 |
| Language | English preprocessing | Multilingual query embeddings |
| Output | Stored FAQ answer | Stored FAQ answer |

Scores are similarity measurements, **not calibrated probabilities or verified answer accuracy**. Hybrid weights and thresholds are initial heuristics and require evaluation. Multilingual retrieval does not translate the stored answers. The current intelligence panel summarizes retrieval rather than exposing actual model execution traces; its lexical pipeline labels do not fully reflect hybrid mode.

## Technology stack

| Layer | Technology |
| --- | --- |
| UI | React 18, TypeScript 5, Vite 5, Lucide React, CSS, SVG |
| API | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| NLP | NLTK, scikit-learn, NumPy |
| Optional semantic model | Sentence Transformers |
| Persistence | JSON FAQ file and browser localStorage |
| Voice | Web Speech APIs |
| Testing | Pytest, FastAPI TestClient, TypeScript/Vite build; Vitest script |

## Local installation

### Prerequisites

Python 3.10+ (3.11 or 3.12 recommended for optional ML dependencies), Node.js 20+, Git. Docker is not required.

### 1. Clone

```bash
cd ~/Documents
git clone https://github.com/yasmeenmh90-beep/CodeAlpha_FAQ_Chatbot.git
cd CodeAlpha_FAQ_Chatbot/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt python-dotenv
```

### 2. Configure a persistent local administrator token

Run from the backend directory. This preserves an existing token and protects the local environment file from accidental Git uploads.

```bash
python - <<'PY'
from pathlib import Path
import secrets

p = Path(".env")
lines = p.read_text().splitlines() if p.exists() else []
if not any(line.startswith("QUERYMIND_ADMIN_TOKEN=") for line in lines):
    lines.append("QUERYMIND_ADMIN_TOKEN=" + secrets.token_hex(24))
p.write_text("\n".join(lines) + "\n")
p.chmod(0o600)
ignore = Path(".gitignore")
old = ignore.read_text() if ignore.exists() else ""
if ".env" not in old.splitlines():
    ignore.write_text(old + "\n.env\n")
PY
git check-ignore .env
```

Keep the token private. Read it locally from the file when unlocking Knowledge Studio. Never commit .env or publish credentials.

### 3. Start backend

```bash
python -m uvicorn app.main:app --reload --port 8000 --env-file .env
```

### 4. Start frontend in a second terminal

```bash
cd ~/Documents/CodeAlpha_FAQ_Chatbot/frontend
npm install
npm run dev
```

| Service | URL |
| --- | --- |
| Workspace | http://localhost:5173 |
| API | http://127.0.0.1:8000 |
| Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/api/health |

The Vite development server proxies /api requests to port 8000. Keep both terminals running.

### Optional: enable hybrid retrieval

Stop the backend, activate its virtual environment and run:

```bash
python -m pip install sentence-transformers
export QUERYMIND_SEMANTIC=1
python -m uvicorn app.main:app --reload --port 8000 --env-file .env
```

The first model initialization may download model files and take time. To return to lexical mode, stop the server, unset QUERYMIND_SEMANTIC and remove any corresponding setting in .env before restarting.

## Knowledge Studio

1. Open Knowledge Studio in the sidebar.
2. Enter the administrator token from backend/.env and unlock.
3. Search or filter records; add, edit or delete FAQ drafts.
4. Import or export JSON as needed.
5. Select Publish changes and confirm the complete dataset replacement.

The server validates the proposed dataset, rejects duplicate IDs and questions, writes a replacement file atomically and invalidates the cached retrieval engine. The next retrieval rebuilds the index. Keep a JSON backup before publishing. The file-based design is intended for single-process local use, not concurrent multi-user editing.

Example FAQ record:

```json
{
  "id": "faq-example",
  "category": "account",
  "question": "How do I reset my password?",
  "answer": "Use the password reset option on the sign-in page.",
  "alternatives": ["I forgot my password"]
}
```

## Analytics dashboard

Analytics uses current and saved conversations available in the browser, not centralized production telemetry. Match rate is matched responses divided by evaluated retrieval responses, not independently measured accuracy. Latency is client-measured request duration. Feedback is based on explicit user ratings. Missing measurements are shown as unavailable. CSV export contains daily questions and matched replies.

## API reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /api/health | Service health and FAQ count |
| GET | /api/faqs | List FAQ questions, optionally by category |
| GET | /api/categories | Available categories |
| POST | /api/chat | Retrieve answer, score, category and suggestions |
| GET | /api/admin/faqs | Read complete knowledge base (protected) |
| PUT | /api/admin/faqs | Replace complete knowledge base (protected) |

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"I forgot my password","category":"all"}'
```

Response fields: engine, answer, matched_question, confidence, matched, category, suggestions. Admin endpoints require Authorization: Bearer TOKEN. The PUT body contains a faqs array of records.

## Troubleshooting

| Issue | Solution |
| --- | --- |
| No module named app | Run Uvicorn from the backend directory with its virtual environment activated |
| Admin 503 | Start backend with --env-file .env and ensure QUERYMIND_ADMIN_TOKEN is configured |
| Admin 401 | Enter the exact current token |
| Admin 404 | Pull latest main and restart backend |
| Connection refused | Verify the backend is running on port 8000 |
| Model initialization slow | Allow first download or disable optional semantic mode |
| Microphone unavailable | Use a supported browser and grant microphone permission |
| Old UI after changes | Pull latest main and refresh the browser |

## Testing and quality

From backend with the virtual environment activated:

```bash
python -m pytest -q
```

From frontend:

```bash
npm install
npm run build
```

Existing tests cover baseline matching and API behavior. Recent enhancements still require comprehensive regression testing, semantic retrieval evaluation and browser verification. No new passing test results are claimed here.

Recommended evaluation: top-1 accuracy on labeled FAQ queries, recall@3, abstention on unrelated queries, multilingual paraphrases, latency and admin authorization tests.

## Privacy and security

- Chat history and feedback are stored in browser localStorage; they are not a server-side chat database.
- Queries are sent to the FastAPI backend for retrieval.
- Browser speech recognition may use the browser vendor's external speech service.
- Admin access is disabled unless a token is configured; tokens are compared server-side.
- Use HTTPS for remote deployments, keep secrets on the server and restrict CORS.
- Publishing FAQ changes modifies a server-side JSON file. Use backups and persistent storage.
- Production authentication, rate limiting, audit logging and concurrent editing controls remain future work.

## Deployment

The frontend can be built for static hosting such as Vercel, with FastAPI hosted separately on Render or an equivalent service. Configure VITE_API_URL before building the frontend, add the deployed frontend origin to the backend CORS allowlist, set secrets through the hosting environment and provide persistent storage for knowledge changes. A live deployment has not been verified.

## Project structure

```text
CodeAlpha_FAQ_Chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py          API and admin operations
│   │   └── engine.py        Lexical and optional hybrid retrieval
│   ├── data/faqs.json       Knowledge base
│   ├── tests/               Baseline automated tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx           Assistant and workspace navigation
│   │   ├── Analytics.tsx     Analytics and charts
│   │   ├── KnowledgeAdmin.tsx Knowledge Studio
│   │   └── styles.css        Responsive themes and UI
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Roadmap

| Capability | Status |
| --- | --- |
| FAQ assistant, history, voice controls and library | Implemented |
| Analytics dashboard and response intelligence | Implemented |
| Optional hybrid multilingual retrieval | Implemented in code; evaluation pending |
| Knowledge Studio and protected API | Implemented; regression testing pending |
| Dedicated voice mode with live waveform | Planned |
| PDF ingestion and document RAG | Planned |
| AI Playground | Planned |
| System Monitor | Planned |
| Support Tickets | Planned |
| Settings Studio | Planned |
| Multilingual answer translation | Planned |
| Full regression, CI/CD and live deployment | Pending |

---

<div align="center">

**Built for the CodeAlpha Artificial Intelligence Internship**

Task 2 — Chatbot for FAQs

[GitHub repository](https://github.com/yasmeenmh90-beep/CodeAlpha_FAQ_Chatbot)

</div>
