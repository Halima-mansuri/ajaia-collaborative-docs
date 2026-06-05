# Ajaia Docs — Collaborative Document Editor

A lightweight collaborative document editor built for the **Ajaia LLC AI-Native Full Stack Developer Assignment**.

**Stack:** Python Flask · React (Vite) · SQLite · JWT authentication · TipTap rich-text editor

## Features

| Feature | Status |
|---------|--------|
| Create, rename, edit, save documents | ✅ |
| Rich text (bold, italic, underline, headings, lists) | ✅ |
| Auto-save with debounce | ✅ |
| File import (.txt, .md, .docx) → new document | ✅ |
| File attachment on existing documents | ✅ |
| Document sharing (owner / edit / view) | ✅ |
| Owned vs shared document lists | ✅ |
| JWT login with seeded demo users | ✅ |
| SQLite persistence | ✅ |
| Automated API tests | ✅ |

## Demo Accounts

| Email | Password | Name |
|-------|----------|------|
| alice@ajaia.com | password123 | Alice Chen |
| bob@ajaia.com | password123 | Bob Martinez |
| carol@ajaia.com | password123 | Carol Williams |

**Sharing demo:** Log in as Alice, create a document, click **Share**, grant Bob edit access. Sign out, log in as Bob — the document appears under **Shared with me**.

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python seed.py
python app.py
```

API runs at **http://127.0.0.1:5000**

### 2. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

App runs at **http://localhost:5173** (proxies `/api` to Flask)

### 3. Run tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## Production Build (single server)

```bash
cd frontend && npm install && npm run build
cd ../backend && pip install -r requirements.txt && python seed.py
python app.py
```

Flask serves the built React app from `frontend/dist` at http://127.0.0.1:5000

## Deployment

A `render.yaml` blueprint is included for [Render](https://render.com). After connecting the repo:

1. Render builds frontend + installs backend deps
2. Gunicorn serves Flask (API + static frontend)
3. Set `JWT_SECRET_KEY` in environment variables

**Live URL:** = **https://ajaia-collaborative-docs.onrender.com**

## Supported File Types

- `.txt` — plain text, converted to paragraphs
- `.md` — basic Markdown (headings, lists)
- `.docx` — Word documents (paragraphs and heading styles)

Max upload size: **5 MB**. Unsupported types are rejected with a clear error message in the UI.

## Project Structure

```
ajaia_task1_project/
├── backend/
│   ├── app.py              # Flask API + static serving
│   ├── models.py           # SQLite schema
│   ├── config.py
│   ├── seed.py
│   ├── tests/test_api.py
│   └── uploads/
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/     # RichTextEditor, ShareModal
│   │   ├── context/        # AuthContext (JWT)
│   │   └── pages/          # Login, Dashboard
│   └── package.json
├── ARCHITECTURE.md
├── AI_WORKFLOW.md
├── SUBMISSION.md
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | dev secret | JWT signing key — **change in production** |
| `DATABASE_PATH` | `backend/app.db` | SQLite database file path |
| `UPLOAD_FOLDER` | `backend/uploads` | Uploaded file storage |
| `PORT` | `5000` | Server port |
| `VITE_API_URL` | `/api` | Frontend API base (set for cross-origin deploys) |

## What's Partial / Next Steps

With 2–4 more hours I would add:

- Real-time collaborative editing (WebSockets / CRDT)
- Document version history
- Full Markdown rendering (tables, code blocks)
- Email-based share invitations
- Docker Compose for one-command local setup
