# Architecture Note — Ajaia Docs

**Author:** Halima Mansuri  
**Assignment:** Ajaia LLC AI-Native Full Stack Developer

## Overview

Ajaia Docs is a monorepo with a **Flask REST API** backend and a **React SPA** frontend. Data is persisted in **SQLite**. Authentication uses **JWT bearer tokens** (Flask-JWT-Extended). The rich-text editor is **TipTap** (ProseMirror-based), storing content as HTML in the database.

```
┌─────────────┐     JWT      ┌──────────────┐     SQL      ┌─────────┐
│  React SPA  │ ──────────►  │  Flask API   │ ──────────►  │ SQLite  │
│  (Vite)     │   /api/*     │  (Gunicorn)  │              │  .db    │
└─────────────┘              └──────────────┘              └─────────┘
                                    │
                                    ▼
                             uploads/ (files)
```

## What I Prioritized (and Why)

### 1. End-to-end document flow first

The core product loop — create → edit → save → reopen — had to work reliably before anything else. I chose TipTap over building a custom `contentEditable` wrapper because it handles selection, lists, and headings correctly out of the box. Content is stored as HTML, which preserves formatting across save/reload without a custom schema.

### 2. JWT auth with seeded users

A full registration flow would eat time without adding evaluation signal. Three seeded accounts with a simple login screen let reviewers immediately test sharing between Alice, Bob, and Carol. JWT keeps the API stateless and is standard for SPA backends.

### 3. Sharing model with clear ownership

Three tables define the model:

- `users` — identity
- `documents` — content + `owner_id`
- `document_shares` — `(document_id, user_id, permission)` where permission is `view` or `edit`

The document list API returns separate `owned` and `shared` arrays. The UI badges each document accordingly. Access checks run on every document endpoint via `user_can_access_document()`.

### 4. File upload as product workflow

Two upload paths, both product-relevant:

1. **Import** — creates a new document from `.txt`, `.md`, or `.docx`
2. **Attach** — associates a file with an existing document

Parsing is server-side (python-docx for Word files, a lightweight Markdown-to-HTML converter for `.md`). The original file is stored in `uploads/` with a metadata row in `attachments`.

### 5. Auto-save over explicit save button

Google Docs doesn't have a Save button. I debounce PUT requests (800 ms) on title/content changes and show a "Saving… / Saved" indicator. This matches user expectations and reduces API chatter.

## Intentional Tradeoffs

| Decision | Tradeoff |
|----------|----------|
| SQLite | Simple for assignment scope; would move to Postgres for multi-instance deploy |
| HTML storage | Easy formatting preservation; harder to diff/merge for real-time collab |
| No WebSockets | Real-time co-editing deprioritized; would need OT/CRDT layer |
| Basic Markdown parser | Covers headings/lists only; not a full CommonMark implementation |
| Monolithic Flask app | Fast to ship; would split API + worker if file processing grew |

## API Design

RESTful JSON under `/api`:

- `POST /api/auth/login` — returns JWT
- `GET/POST /api/documents` — list (owned + shared) / create
- `GET/PUT/DELETE /api/documents/:id` — CRUD with access control
- `POST /api/documents/:id/share` — grant access
- `POST /api/documents/import` — file → new document
- `POST /api/documents/:id/attachments` — attach file

All document routes require `@jwt_required()`. Errors return `{ "error": "message" }` with appropriate HTTP status codes.

## Security Considerations

- Passwords hashed with Werkzeug `generate_password_hash`
- JWT secret configurable via environment variable
- File uploads validated by extension and 5 MB size limit
- `secure_filename()` on all uploaded filenames
- Foreign keys enforced in SQLite (`PRAGMA foreign_keys = ON`)
- Users cannot share documents with themselves

## Testing

`backend/tests/test_api.py` covers:

- Health check
- Invalid login
- Document create/update/rename
- Full sharing flow (Alice → Bob)
- File import from Markdown

Tests use a temporary SQLite database to avoid polluting dev data.

## Deployment

Production mode builds the React app (`frontend/dist`) and Flask serves it as a catch-all route, while `/api/*` routes hit the API. Gunicorn is the production WSGI server. A `render.yaml` blueprint automates build + deploy on Render.
