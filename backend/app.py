import os
import re
import sqlite3
import uuid

from docx import Document as DocxDocument
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import (
    ALLOWED_EXTENSIONS,
    BASE_DIR,
    DATABASE_PATH,
    JWT_SECRET_KEY,
    MAX_CONTENT_LENGTH,
    UPLOAD_FOLDER,
)
from models import get_connection, init_db, utc_now

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])
jwt = JWTManager(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def row_to_dict(row):
    return dict(row) if row else None


def get_user_by_email(email):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_connection()
    user = conn.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def user_can_access_document(user_id, document_id):
    conn = get_connection()
    doc = conn.execute(
        "SELECT id, owner_id FROM documents WHERE id = ?", (document_id,)
    ).fetchone()
    if not doc:
        conn.close()
        return None, None

    if doc["owner_id"] == user_id:
        conn.close()
        return doc, "owner"

    share = conn.execute(
        "SELECT permission FROM document_shares WHERE document_id = ? AND user_id = ?",
        (document_id, user_id),
    ).fetchone()
    conn.close()
    if share:
        return doc, share["permission"]
    return None, None


def parse_file_to_html(file_storage):
    filename = secure_filename(file_storage.filename or "")
    ext = filename.rsplit(".", 1)[1].lower()
    title = os.path.splitext(filename)[0] or "Imported Document"

    if ext == "txt":
        text = file_storage.read().decode("utf-8", errors="replace")
        paragraphs = "".join(f"<p>{line or '<br>'}</p>" for line in text.splitlines())
        return title, paragraphs or "<p></p>"

    if ext == "md":
        text = file_storage.read().decode("utf-8", errors="replace")
        html = markdown_to_simple_html(text)
        return title, html or "<p></p>"

    if ext == "docx":
        file_storage.stream.seek(0)
        doc = DocxDocument(file_storage)
        parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                parts.append("<p><br></p>")
                continue
            style = (para.style.name or "").lower()
            if "heading 1" in style:
                parts.append(f"<h1>{text}</h1>")
            elif "heading 2" in style:
                parts.append(f"<h2>{text}</h2>")
            elif "heading 3" in style:
                parts.append(f"<h3>{text}</h3>")
            else:
                parts.append(f"<p>{text}</p>")
        return title, "".join(parts) or "<p></p>"

    raise ValueError("Unsupported file type")


def markdown_to_simple_html(md_text):
    lines = md_text.splitlines()
    html_parts = []
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            close_lists()
            html_parts.append("<p><br></p>")
            continue

        if stripped.startswith("# "):
            close_lists()
            html_parts.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            close_lists()
            html_parts.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            close_lists()
            html_parts.append(f"<h3>{stripped[4:]}</h3>")
        elif re.match(r"^[-*]\s+", stripped):
            if not in_ul:
                close_lists()
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{stripped[2:]}</li>")
        elif re.match(r"^\d+\.\s+", stripped):
            if not in_ol:
                close_lists()
                html_parts.append("<ol>")
                in_ol = True
            content = re.sub(r"^\d+\.\s+", "", stripped)
            html_parts.append(f"<li>{content}</li>")
        else:
            close_lists()
            html_parts.append(f"<p>{stripped}</p>")

    close_lists()
    return "".join(html_parts)


@app.errorhandler(413)
def file_too_large(_):
    return jsonify({"error": "File too large. Maximum size is 5 MB."}), 413


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user["id"]))
    return jsonify(
        {
            "access_token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
            },
        }
    )


@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": row_to_dict(user)})


@app.route("/api/users", methods=["GET"])
@jwt_required()
def list_users():
    user_id = int(get_jwt_identity())
    conn = get_connection()
    users = conn.execute(
        "SELECT id, email, name FROM users WHERE id != ? ORDER BY name",
        (user_id,),
    ).fetchall()
    conn.close()
    return jsonify({"users": [row_to_dict(u) for u in users]})


@app.route("/api/documents", methods=["GET"])
@jwt_required()
def list_documents():
    user_id = int(get_jwt_identity())
    conn = get_connection()
    owned = conn.execute(
        """
        SELECT d.*, 'owner' AS access_type, u.name AS owner_name
        FROM documents d
        JOIN users u ON u.id = d.owner_id
        WHERE d.owner_id = ?
        ORDER BY d.updated_at DESC
        """,
        (user_id,),
    ).fetchall()

    shared = conn.execute(
        """
        SELECT d.*, ds.permission AS access_type, u.name AS owner_name
        FROM documents d
        JOIN document_shares ds ON ds.document_id = d.id
        JOIN users u ON u.id = d.owner_id
        WHERE ds.user_id = ?
        ORDER BY d.updated_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "owned": [row_to_dict(d) for d in owned],
            "shared": [row_to_dict(d) for d in shared],
        }
    )


@app.route("/api/documents", methods=["POST"])
@jwt_required()
def create_document():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Untitled Document").strip() or "Untitled Document"
    content = data.get("content") or "<p></p>"
    now = utc_now()

    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO documents (title, content, owner_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, content, user_id, now, now),
    )
    doc_id = cursor.lastrowid
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify({"document": row_to_dict(doc)}), 201


@app.route("/api/documents/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_document(doc_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404

    conn = get_connection()
    document = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    owner = conn.execute(
        "SELECT id, email, name FROM users WHERE id = ?", (document["owner_id"],)
    ).fetchone()
    shares = conn.execute(
        """
        SELECT ds.id, ds.permission, ds.created_at, u.id AS user_id, u.email, u.name
        FROM document_shares ds
        JOIN users u ON u.id = ds.user_id
        WHERE ds.document_id = ?
        """,
        (doc_id,),
    ).fetchall()
    attachments = conn.execute(
        "SELECT id, filename, uploaded_at FROM attachments WHERE document_id = ?",
        (doc_id,),
    ).fetchall()
    conn.close()

    return jsonify(
        {
            "document": row_to_dict(document),
            "access_type": access,
            "owner": row_to_dict(owner),
            "shares": [row_to_dict(s) for s in shares],
            "attachments": [row_to_dict(a) for a in attachments],
        }
    )


@app.route("/api/documents/<int:doc_id>", methods=["PUT"])
@jwt_required()
def update_document(doc_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access not in ("owner", "edit"):
        return jsonify({"error": "You do not have permission to edit this document"}), 403

    data = request.get_json(silent=True) or {}
    title = data.get("title")
    content = data.get("content")
    if title is None and content is None:
        return jsonify({"error": "Nothing to update"}), 400

    conn = get_connection()
    current = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    new_title = title.strip() if title is not None else current["title"]
    new_content = content if content is not None else current["content"]
    now = utc_now()

    conn.execute(
        "UPDATE documents SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (new_title, new_content, now, doc_id),
    )
    updated = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify({"document": row_to_dict(updated)})


@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
@jwt_required()
def delete_document(doc_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access != "owner":
        return jsonify({"error": "Only the owner can delete this document"}), 403

    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Document deleted"})


@app.route("/api/documents/<int:doc_id>/share", methods=["POST"])
@jwt_required()
def share_document(doc_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access != "owner":
        return jsonify({"error": "Only the owner can share this document"}), 403

    data = request.get_json(silent=True) or {}
    target_user_id = data.get("user_id")
    permission = data.get("permission", "edit")

    if not target_user_id:
        return jsonify({"error": "user_id is required"}), 400
    if permission not in ("view", "edit"):
        return jsonify({"error": "permission must be 'view' or 'edit'"}), 400
    if int(target_user_id) == user_id:
        return jsonify({"error": "Cannot share with yourself"}), 400

    target = get_user_by_id(int(target_user_id))
    if not target:
        return jsonify({"error": "Target user not found"}), 404

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO document_shares (document_id, user_id, permission, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(document_id, user_id) DO UPDATE SET permission = excluded.permission
            """,
            (doc_id, int(target_user_id), permission, utc_now()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Failed to share document"}), 400
    conn.close()
    return jsonify({"message": "Document shared successfully"})


@app.route("/api/documents/<int:doc_id>/share/<int:share_user_id>", methods=["DELETE"])
@jwt_required()
def unshare_document(doc_id, share_user_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access != "owner":
        return jsonify({"error": "Only the owner can manage sharing"}), 403

    conn = get_connection()
    conn.execute(
        "DELETE FROM document_shares WHERE document_id = ? AND user_id = ?",
        (doc_id, share_user_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Share removed"})


@app.route("/api/documents/import", methods=["POST"])
@jwt_required()
def import_document():
    user_id = int(get_jwt_identity())
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify(
            {"error": f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}
        ), 400

    try:
        title, content = parse_file_to_html(file)
    except Exception as exc:
        return jsonify({"error": f"Failed to parse file: {exc}"}), 400

    now = utc_now()
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO documents (title, content, owner_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (title, content, user_id, now, now),
    )
    doc_id = cursor.lastrowid

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    stored_name = f"{doc_id}_{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(UPLOAD_FOLDER, stored_name)
    file.stream.seek(0)
    file.save(stored_path)

    conn.execute(
        """
        INSERT INTO attachments (document_id, filename, stored_path, uploaded_at)
        VALUES (?, ?, ?, ?)
        """,
        (doc_id, secure_filename(file.filename), stored_path, now),
    )
    doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.commit()
    conn.close()
    return jsonify({"document": row_to_dict(doc)}), 201


@app.route("/api/documents/<int:doc_id>/attachments", methods=["POST"])
@jwt_required()
def attach_file(doc_id):
    user_id = int(get_jwt_identity())
    doc, access = user_can_access_document(user_id, doc_id)
    if not doc:
        return jsonify({"error": "Document not found or access denied"}), 404
    if access not in ("owner", "edit"):
        return jsonify({"error": "You do not have permission to attach files"}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify(
            {"error": f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}
        ), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    stored_name = f"{doc_id}_{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(UPLOAD_FOLDER, stored_name)
    file.save(stored_path)

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO attachments (document_id, filename, stored_path, uploaded_at)
        VALUES (?, ?, ?, ?)
        """,
        (doc_id, secure_filename(file.filename), stored_path, utc_now()),
    )
    attachment = conn.execute(
        "SELECT id, filename, uploaded_at FROM attachments WHERE stored_path = ?",
        (stored_path,),
    ).fetchone()
    conn.commit()
    conn.close()
    return jsonify({"attachment": row_to_dict(attachment)}), 201


FRONTEND_DIST = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")


def seed_database():
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if count == 0:
        users = [
            ("alice@ajaia.com", "password123", "Alice Chen"),
            ("bob@ajaia.com", "password123", "Bob Martinez"),
            ("carol@ajaia.com", "password123", "Carol Williams"),
        ]
        now = utc_now()
        for email, password, name in users:
            conn.execute(
                "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
                (email, generate_password_hash(password), name, now),
            )
        conn.commit()
    conn.close()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Resource not found"}), 404
    if os.path.isdir(FRONTEND_DIST):
        file_path = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, "index.html")
    return jsonify({"message": "API running. Build frontend with npm run build."})


seed_database()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
