# DreamAI — AI-Based Dream Analysis System

> **EEC10212 Integrated Project 1 · National University · BSc ITMB · Spring 2026**

DreamAI is a full-stack web application that lets users record their dreams by text or voice, receive AI-generated emotional analysis, track recurring symbols across entries over time, and view their patterns on a visual dashboard. It was built as a team final-year project following an Agile (Scrum-inspired) development lifecycle.

---

## Team

| Name                        | Student No. | Role                      |
| --------------------------- | ----------- | ------------------------- |
| Zayana Ishaq Rabia Alnadabi | 230391      | System Design & Research  |
| Noor Talib Albusaidi        | 230393      | UI & Frontend Development |
| Maram Rabei Alsulaimi       | 230376      | AI Model & Analysis       |
| Reem Khalfan Aljabri        | 230390      | Database & Testing        |

**Module Tutors:** Ms. Deepali · Ms. Amalu · Ms. Silpa Shankaran

---

## Project Structure

```
dream-ai-project/
├── backend/
│   ├── app.py                ← Flask REST API (auth, dreams, dashboard, export)
│   ├── ai_model.py           ← Emotion classifier + TF-IDF pattern detection
│   ├── models.py             ← SQLAlchemy ORM models (User, Dream, AnalysisResult)
│   ├── extensions.py         ← Shared SQLAlchemy db instance
│   ├── password_utils.py     ← PBKDF2-SHA256 password hashing (stdlib only)
│   ├── test_backend.py       ← Unit + integration tests (20 tests)
│   ├── requirements.txt      ← Core runtime dependencies (lightweight)
│   └── requirements-ai.txt  ← Optional AI/NLP stack (transformers, torch, etc.)
├── database/
│   ├── init_db.py            ← Creates tables + seeds demo data
│   └── dreams.db             ← SQLite database file (auto-created)
├── docs/
│   ├── ASSESSMENT_ALIGNMENT.md     ← Maps code to coursework criteria
│   ├── FINAL_REPORT_OUTLINE.md     ← Section-by-section report guide
│   ├── GROUP_MEETING_TEMPLATE.md   ← Appendix B meeting notes template
│   ├── PROJECT_MANAGEMENT_PACK.md  ← Risk register, budget, Gantt, stakeholders
│   └── SETUP_INSTRUCTIONS.txt      ← Full step-by-step setup guide
├── frontend/
│   ├── index.html            ← Single-page app (auth, record, dashboard, history)
│   ├── css/style.css         ← Dark navy responsive stylesheet
│   └── js/app.js             ← API calls, Chart.js, Web Speech API integration
└── README.md                 ← This file
```

---

## Features

| Feature                       | Description                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| **User accounts**       | Register, login, logout — secure session-based auth                                           |
| **Dream recording**     | Title + long-form description; 10–5000 character limit                                        |
| **Voice input**         | Browser Web Speech API (Chrome-first; graceful fallback on unsupported browsers)               |
| **Emotion analysis**    | Labels dreams as `fear`, `stress`, `sadness`, `happiness`, `neutral`, or `unknown` |
| **Keyword extraction**  | Stores top-5 meaningful keywords per dream via TF-IDF                                          |
| **Pattern tracking**    | Detects recurring words and phrases across the full dream history                              |
| **Dashboard analytics** | Total dreams, top emotion, doughnut chart, 14-day activity bar chart, symbol tags              |
| **Dream history**       | Browse, read full detail, and delete any past entry                                            |
| **Data export**         | Download all dream data as a JSON file                                                         |

---

## Quick Start

> Full instructions with troubleshooting are in `docs/SETUP_INSTRUCTIONS.txt`.

### 1 · Create and activate a virtual environment

**Windows (PowerShell)**

```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2 · Install core dependencies

```bash
pip install -r backend/requirements.txt
```

This installs only the lightweight runtime stack (Flask, SQLAlchemy, Flask-CORS, numpy). No large model downloads at this stage.

### 3 · Initialise the database

```bash
python database/init_db.py
```

Expected output:

```
Database initialised at: .../database/dreams.db
Tables created: users, dreams, analysis_results
Tables confirmed: ['users', 'dreams', 'analysis_results']
Demo data seeded: user 'demo' created with 5 sample dreams.
Login with: username=demo, password=demo123
```

### 4 · Run the backend

```bash
python backend/app.py
```

Expected output:

```
Database tables created/verified.
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 5 · Open the app

Navigate to **http://127.0.0.1:5000/** in your browser.

> ⚠️ **Always use the Flask-served URL** (`http://127.0.0.1:5000/`) rather than opening `index.html` directly. Opening as a file (`file://`) can cause session cookie and API issues.

Log in with the demo account:

- **Username:** `demo`
- **Password:** `demo123`

---

## Optional: Full AI Stack

By default DreamAI uses a fast built-in rule-based emotion classifier so the app starts instantly without downloading large models. To enable the Hugging Face BERT-based classifier:

### Step 1 · Install the AI dependencies

```bash
pip install -r backend/requirements-ai.txt
```

> Requires Python **3.10 or 3.11** for best compatibility. This downloads approximately 1–2 GB (torch + transformers + scikit-learn + spaCy).

Also download the spaCy language model:

```bash
python -m spacy download en_core_web_sm
```

### Step 2 · Enable the transformer at runtime

**Windows (PowerShell)**

```powershell
$env:DREAMAI_ENABLE_TRANSFORMER = "1"
python backend/app.py
```

**macOS / Linux**

```bash
DREAMAI_ENABLE_TRANSFORMER=1 python backend/app.py
```

The first run will download and cache the model (`bhadresh-savani/bert-base-uncased-emotion`, ~430 MB). Subsequent runs load it from cache in approximately 5 seconds.

---

## Running the Tests

```bash
python backend/test_backend.py
```

The test suite (20 tests across 5 classes) covers:

| Test Class                | What it covers                                                    |
| ------------------------- | ----------------------------------------------------------------- |
| `TestEmotionAnalysis`   | Rule-based fallback, pattern detection, keyword extraction        |
| `TestInputValidation`   | Username/password/dream text length rules                         |
| `TestPasswordHashing`   | PBKDF2 hash + verify + salt uniqueness                            |
| `TestJSONSerialisation` | Keyword list round-trip through JSON                              |
| `TestFlaskIntegration`  | Full API flow: register → dream → dashboard → export → delete |

Expected output:

```
Ran 20 tests in X.XXXs
OK
```

---

## API Reference

All endpoints require a valid session cookie except `/api/register` and `/api/login`.

| Method     | Endpoint             | Description                                                                    |
| ---------- | -------------------- | ------------------------------------------------------------------------------ |
| `POST`   | `/api/register`    | Create account `{username, password, email?}`                                |
| `POST`   | `/api/login`       | Authenticate `{username, password}`                                          |
| `POST`   | `/api/logout`      | Clear session                                                                  |
| `GET`    | `/api/me`          | Return current user info                                                       |
| `POST`   | `/api/dreams`      | Submit dream `{text, title?}` → returns `{dream_id, emotion, confidence}` |
| `GET`    | `/api/dreams`      | List all dreams (newest first, content truncated to 200 chars)                 |
| `GET`    | `/api/dreams/<id>` | Get single dream with full text and keywords                                   |
| `DELETE` | `/api/dreams/<id>` | Delete dream and its analysis                                                  |
| `GET`    | `/api/dashboard`   | Emotion distribution, patterns, 14-day timeline                                |
| `GET`    | `/api/export`      | Download all user data as JSON                                                 |

### Example: submit a dream (curl)

```bash
# Step 1: register and save session cookie

curl -X POST http://localhost:5000/api/register \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"test123"}' \
     -c cookies.txt

# Step 2: submit a dream
curl -X POST http://localhost:5000/api/dreams \
     -H "Content-Type: application/json" \
     -d '{"text":"I was running through dark corridors trying to find an exam room but kept getting lost.","title":"Exam Nightmare"}' \
     -b cookies.txt -c cookies.txt

# Step 3: view dashboard
curl http://localhost:5000/api/dashboard -b cookies.txt
```

---

## Security Design

| Concern                           | How it is handled                                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Password storage**        | `pbkdf2_sha256` with 260,000 iterations and a 16-byte random salt (stdlib `hashlib` — no external bcrypt required) |
| **SQL injection**           | All queries go through SQLAlchemy ORM parameterised methods                                                             |
| **Session security**        | Server-side sessions with an opaque cookie; 7-day rolling expiry                                                        |
| **Input validation**        | Length checks at API entry point before any database write                                                              |
| **CORS**                    | `Flask-CORS` restricts cross-origin requests with `supports_credentials=True`                                       |
| **Data privacy disclaimer** | Shown on every analysis result page; data is local only — nothing sent to third parties                                |

---

## Technical Stack

| Layer                          | Technology                                                                                                      |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Backend**              | Python 3.10–3.14, Flask 3.1.3, Flask-SQLAlchemy 3.1.1, Flask-CORS 6.0.2                                        |
| **Database**             | SQLite 3 via SQLAlchemy 2.0 ORM                                                                                 |
| **Password hashing**     | stdlib `hashlib.pbkdf2_hmac` (PBKDF2-SHA256, 260,000 iterations)                                              |
| **AI / NLP — default**  | Rule-based keyword and emotion fallback (no install required)                                                   |
| **AI / NLP — optional** | HuggingFace Transformers + BERT (`bhadresh-savani/bert-base-uncased-emotion`), scikit-learn TF-IDF, spaCy NER |
| **Frontend**             | HTML5, CSS3, Vanilla JavaScript                                                                                 |
| **Charts**               | Chart.js (CDN)                                                                                                  |
| **Voice input**          | Web Speech API (browser-native, Chrome-first)                                                                   |

---

## AI Model Details

### Default: rule-based fallback

Available immediately with no downloads. Classifies emotion using scored keyword sets for `fear`, `happiness`, `sadness`, and `stress`. Returns `neutral` when no category scores. Confidence fixed at `0.65` for matched categories, `0.50` for neutral.

### Optional: BERT transformer classifier

Model: **`bhadresh-savani/bert-base-uncased-emotion`** (Hugging Face)
Base: BERT-base-uncased (Devlin et al., 2019)
Training data: ~20,000 labelled English tweets (Saravia et al., 2018) — 6 emotion classes
Output mapping: `joy/love → happiness`, `anger → stress`, `surprise → neutral`, `fear → fear`, `sadness → sadness`
Augmentation: stress-keyword heuristic override (≥3 stress keywords found → elevate to `stress`)
Input truncation: 1,800 characters (~512 BERT tokens)
Average CPU inference time: 1.2–2.8 seconds

### Pattern detection (both modes)

Uses **scikit-learn TF-IDF** (`TfidfVectorizer`) across the user's full dream corpus. Tokens must appear in ≥2 dreams (`min_df=2`). Short tokens (<3 characters) and English stop words are filtered. Bigrams included (`ngram_range=(1,2)`). Results sorted by summed TF-IDF score. Returns top 15 patterns, top 8 shown on dashboard.

---

## Database Schema

```sql
-- users
CREATE TABLE users (
    id            INTEGER   PRIMARY KEY AUTOINCREMENT,
    username      TEXT      NOT NULL UNIQUE,
    email         TEXT,
    password_hash TEXT      NOT NULL,
    created_at    DATETIME  DEFAULT CURRENT_TIMESTAMP
);

-- dreams
CREATE TABLE dreams (
    id         INTEGER   PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT      DEFAULT 'Untitled Dream',
    content    TEXT      NOT NULL,
    created_at DATETIME  DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_dreams_user ON dreams(user_id, created_at DESC);

-- analysis_results
CREATE TABLE analysis_results (
    id          INTEGER   PRIMARY KEY AUTOINCREMENT,
    dream_id    INTEGER   NOT NULL UNIQUE REFERENCES dreams(id) ON DELETE CASCADE,
    emotion     TEXT      NOT NULL,
    confidence  REAL      DEFAULT 0.0,
    keywords    TEXT      DEFAULT '[]',   -- JSON array of strings
    analysed_at DATETIME  DEFAULT CURRENT_TIMESTAMP
);
```

---

## Common Issues

| Problem                                                   | Fix                                                                                                                     |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `No module named 'flask'`                               | Virtual environment not active — run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (macOS/Linux) |
| `sqlite3.OperationalError: no such table`               | Run `python database/init_db.py`                                                                                      |
| `Address already in use` (port 5000)                    | Change port in `app.py`: `app.run(debug=True, port=5001)` — also update `API_BASE` in `frontend/js/app.js`     |
| Voice input button not showing                            | Browser does not support Web Speech API — use text input; works best in Google Chrome                                  |
| `ModuleNotFoundError: No module named 'en_core_web_sm'` | Run `python -m spacy download en_core_web_sm` (only needed with AI stack)                                             |
| Model download hanging                                    | First transformer run downloads ~430 MB from Hugging Face — check network connection                                   |
| Tests fail with `SQLALCHEMY_DATABASE_URI` error         | Run tests from project root:`python backend/test_backend.py`                                                          |

---

## Coursework Documents

| File                                | Purpose                                                             |
| ----------------------------------- | ------------------------------------------------------------------- |
| `docs/ASSESSMENT_ALIGNMENT.md`    | Maps every file to the specific coursework criteria it satisfies    |
| `docs/PROJECT_MANAGEMENT_PACK.md` | Risk register (20 risks), budget, Gantt chart, stakeholder table    |
| `docs/FINAL_REPORT_OUTLINE.md`    | Section-by-section guide matching the 10,000-word report format     |
| `docs/GROUP_MEETING_TEMPLATE.md`  | Appendix B meeting notes template (pre-filled with Sprint examples) |
| `docs/SETUP_INSTRUCTIONS.txt`     | Full setup guide with common error fixes and demo tips              |

---

## Important Disclaimer

DreamAI is a personal reflection tool, not a medical or psychological diagnostic system. All emotion analysis results are generated algorithmically and should not be interpreted as clinical assessments. If you are experiencing mental health difficulties, please speak to a qualified professional or contact your university student support service.

---

*Submitted: 23 April 2026 · EEC10212 Integrated Project 1 · National University*
