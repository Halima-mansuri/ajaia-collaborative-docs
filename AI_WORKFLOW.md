# AI Workflow Note

**Author:** Halima Mansuri  
**Assignment:** Ajaia LLC AI-Native Full Stack Developer

## Tools Used

- **Cursor IDE** (Claude-based agent) — primary coding assistant for scaffolding, implementation, and iteration
- **Built-in terminal** — running pytest, npm, and Flask locally to verify behavior
- **Chatgpt** - AI coding assistant for debugging, implmentation and testing 

## Where AI Materially Sped Up Work

1. **Project scaffolding** — Generating the full monorepo structure (Flask routes, SQLite schema, React components, Vite config) in one pass saved roughly 1–2 hours vs. manual boilerplate.
2. **TipTap editor integration** — AI provided the correct extension setup (StarterKit + Underline) and toolbar wiring, which I would otherwise have looked up in docs.
3. **File parsing logic** — The Markdown-to-HTML converter and docx paragraph extraction were drafted quickly; I reviewed edge cases (empty lines, list nesting) before accepting.
4. **Test suite** — AI generated pytest fixtures and a sharing-flow integration test that caught a missing `sqlite3` import in the share endpoint.
5. **Documentation** — README, architecture note, and submission checklist were drafted from the assignment requirements, then edited for accuracy.

## What I Changed or Rejected

| AI Output | My Decision |
|-----------|-------------|
| Suggested PostgreSQL + SQLAlchemy ORM | Rejected — SQLite is sufficient for scope and matches assignment flexibility; kept raw SQL for transparency |
| Suggested Quill editor | Rejected — chose TipTap for better React integration and heading/list support |
| Generic error middleware | Simplified — kept explicit error handlers for 413/404/500 only |
| User registration endpoint | Rejected — seeded accounts are faster to demo sharing |
| Real-time WebSocket collab | Rejected — out of scope for 4–6 hour timebox; documented as next step |
| `import sqlite3` placed at bottom of file | Fixed — moved to top after test failure |

## How I Verified Correctness

1. **Automated tests** — `pytest tests/ -v` covers auth, CRUD, sharing, and file import
2. **Manual flow testing** — Logged in as Alice, created/edited/renamed a document, confirmed auto-save and reload preserved HTML formatting
3. **Sharing verification** — Shared doc with Bob, confirmed it appears in Bob's "Shared with me" with correct edit permission; tested view-only mode
4. **File upload** — Imported `.md` and `.txt` files, confirmed content appeared in editor with correct headings/lists
5. **Error paths** — Tested invalid login, unsupported file type, and unauthorized document access (403/404 responses)
6. **Refresh persistence** — Confirmed documents survive browser refresh and server restart (SQLite file)

## Judgment Over Volume

I used AI as a **drafting and acceleration tool**, not a substitute for product decisions. Key choices — SQLite over Postgres, seeded users over registration, HTML storage, auto-save debounce, owned/shared list separation — were mine. AI generated code was always read, tested, and adjusted before acceptance.
