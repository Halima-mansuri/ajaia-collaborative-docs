# Submission Checklist — Ajaia LLC Assignment

**Candidate:** Halima Mansuri  
**Email:** mansurihalima3@gmail.com  
**Project:** Ajaia Docs — Collaborative Document Editor

## Included in This Repository

| Item | Location |
|------|----------|
| Source code (Flask backend) | `backend/` |
| Source code (React frontend) | `frontend/` |
| README with setup instructions | `README.md` |
| Architecture note | `ARCHITECTURE.md` |
| AI workflow note | `AI_WORKFLOW.md` |
| This submission manifest | `SUBMISSION.md` |
| Walkthrough video URL | `VIDEO_URL.txt` |
| Deployment config | `render.yaml`, `Procfile` |
| Automated tests | `backend/tests/test_api.py` |

## Live Deployment

**URL:** = **https://ajaia-collaborative-docs.onrender.com**

## Test Credentials

| Email | Password | Role |
|-------|----------|------|
| alice@ajaia.com | password123 | Primary demo user (owner) |
| bob@ajaia.com | password123 | Share recipient |
| carol@ajaia.com | password123 | Additional user |

## What Works End-to-End

- [x] Login with JWT authentication
- [x] Create new documents
- [x] Rename documents (title field, auto-saved)
- [x] Rich-text editing (bold, italic, underline, H1–H3, bullet/numbered lists)
- [x] Auto-save and reopen with formatting preserved
- [x] Import `.txt`, `.md`, `.docx` files as new documents
- [x] Attach files to existing documents
- [x] Share documents with other users (edit or view permission)
- [x] Separate "My documents" and "Shared with me" lists
- [x] Owner can delete documents; shared users cannot
- [x] Data persists across refresh (SQLite)
- [x] API integration tests (pytest)

## What Is Incomplete / Deprioritized

- Real-time collaborative editing (no WebSockets)
- Document version history
- Full CommonMark Markdown support
- User registration (seeded accounts only)
- Email notifications for sharing

## What I Would Build Next (2–4 Hours)

1. Docker Compose for one-command local setup
2. Document search and filtering
3. Improved docx import (bold/italic within paragraphs)
4. Deploy to Render and verify production JWT + SQLite persistence
5. Record 3–5 minute Loom walkthrough

## Google Drive Folder

_(Add Google Drive link before final submission)_

## Quick Start for Reviewers

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && venv\Scripts\activate   # or source venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 → sign in as `alice@ajaia.com` / `password123`
