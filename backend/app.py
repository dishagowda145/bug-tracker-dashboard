"""Bug Tracker API (Flask + SQLite).

Security features: hashed passwords, signed expiring tokens, input validation,
role-based access (admin vs user), parameterised SQL (no SQL injection).
"""
import os
import re
import sqlite3
import time
from functools import wraps

from flask import Flask, g, jsonify, request, send_from_directory
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

STATUSES = ("open", "in_progress", "resolved")
PRIORITIES = ("low", "medium", "high")
TOKEN_MAX_AGE = 60 * 60 * 8  # 8 hours
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_LOGIN_FAILURES = 5          # per client + email ...
LOGIN_LOCK_SECONDS = 5 * 60     # ... within this window

# Bugs are always read with the reporter and assignee emails so the UI can show names.
BUG_SQL = """
    SELECT b.*, r.email AS reporter_email, a.email AS assignee_email
    FROM bugs b
    JOIN users r ON r.id = b.reporter_id
    LEFT JOIN users a ON a.id = b.assignee_id
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
);
CREATE TABLE IF NOT EXISTS bugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
    reporter_id INTEGER NOT NULL REFERENCES users(id),
    assignee_id INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def create_app(db_path=None, secret_key=None):
    app = Flask(__name__, static_folder=None)
    app.config["DB_PATH"] = db_path or os.path.join(BASE_DIR, "bugs.db")
    # Set SECRET_KEY in the environment for real use; the fallback is for local dev only.
    app.config["SECRET_KEY"] = secret_key or os.environ.get("SECRET_KEY", "dev-only-change-me")
    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)
        get_db().commit()

    # ---------- helpers ----------
    def error(message, code=400):
        return jsonify({"error": message}), code

    def login_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return error("Missing token", 401)
            try:
                data = serializer.loads(header[7:], max_age=TOKEN_MAX_AGE)
            except SignatureExpired:
                return error("Token expired", 401)
            except BadSignature:
                return error("Invalid token", 401)
            user = get_db().execute(
                "SELECT id, email, role FROM users WHERE id = ?", (data["uid"],)
            ).fetchone()
            if user is None:
                return error("User not found", 401)
            g.user = user
            return fn(*args, **kwargs)
        return wrapper

    def bug_to_dict(row):
        return {k: row[k] for k in row.keys()}

    def fetch_bug(db, bug_id):
        return db.execute(BUG_SQL + " WHERE b.id = ?", (bug_id,)).fetchone()

    # In-memory login throttle (per process). Slows password guessing; a shared store
    # such as Redis would be needed to enforce it across several workers.
    failures = {}

    def throttle_key(email):
        return (request.remote_addr, email)

    def is_locked(key):
        count, first = failures.get(key, (0, 0.0))
        if count and time.monotonic() - first > LOGIN_LOCK_SECONDS:
            failures.pop(key, None)
            return False
        return count >= MAX_LOGIN_FAILURES

    def record_failure(key):
        count, first = failures.get(key, (0, time.monotonic()))
        failures[key] = (count + 1, first)

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    # ---------- auth ----------
    @app.post("/api/register")
    def register():
        body = request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip().lower()
        password = str(body.get("password", ""))
        if not EMAIL_RE.match(email):
            return error("Enter a valid email")
        if len(password) < 8:
            return error("Password must be at least 8 characters")
        db = get_db()
        # First registered user becomes admin so the app is usable out of the box.
        is_first = db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        try:
            db.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                (email, generate_password_hash(password), "admin" if is_first else "user"),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return error("Email already registered", 409)
        return jsonify({"message": "Registered"}), 201

    @app.post("/api/login")
    def login():
        body = request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip().lower()
        password = str(body.get("password", ""))
        key = throttle_key(email)
        if is_locked(key):
            return error("Too many failed attempts. Try again in a few minutes.", 429)
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        # Same message for unknown email and wrong password: do not leak which accounts exist.
        if user is None or not check_password_hash(user["password_hash"], password):
            record_failure(key)
            return error("Invalid email or password", 401)
        failures.pop(key, None)
        token = serializer.dumps({"uid": user["id"]})
        return jsonify({"token": token, "email": user["email"], "role": user["role"]})

    @app.get("/api/users")
    @login_required
    def list_users():
        rows = get_db().execute("SELECT id, email, role FROM users ORDER BY email").fetchall()
        return jsonify([bug_to_dict(r) for r in rows])

    # ---------- bugs ----------
    @app.get("/api/bugs")
    @login_required
    def list_bugs():
        sql = BUG_SQL
        params = []
        status = request.args.get("status")
        if status:
            if status not in STATUSES:
                return error("Invalid status filter")
            sql += " WHERE b.status = ?"
            params.append(status)
        sql += " ORDER BY b.id DESC"
        rows = get_db().execute(sql, params).fetchall()
        return jsonify([bug_to_dict(r) for r in rows])

    @app.post("/api/bugs")
    @login_required
    def create_bug():
        body = request.get_json(silent=True) or {}
        title = str(body.get("title", "")).strip()
        description = str(body.get("description", "")).strip()
        priority = body.get("priority", "medium")
        if not 3 <= len(title) <= 120:
            return error("Title must be 3 to 120 characters")
        if len(description) > 2000:
            return error("Description must be at most 2000 characters")
        if priority not in PRIORITIES:
            return error("Priority must be low, medium or high")
        db = get_db()
        cur = db.execute(
            "INSERT INTO bugs (title, description, priority, reporter_id) VALUES (?, ?, ?, ?)",
            (title, description, priority, g.user["id"]),
        )
        db.commit()
        row = fetch_bug(db, cur.lastrowid)
        return jsonify(bug_to_dict(row)), 201

    @app.patch("/api/bugs/<int:bug_id>")
    @login_required
    def update_bug(bug_id):
        db = get_db()
        bug = db.execute("SELECT * FROM bugs WHERE id = ?", (bug_id,)).fetchone()
        if bug is None:
            return error("Bug not found", 404)
        body = request.get_json(silent=True) or {}
        is_admin = g.user["role"] == "admin"
        is_owner = bug["reporter_id"] == g.user["id"]
        if not (is_admin or is_owner or bug["assignee_id"] == g.user["id"]):
            return error("Not allowed", 403)

        fields, params = [], []
        if "status" in body:
            if body["status"] not in STATUSES:
                return error("Invalid status")
            fields.append("status = ?")
            params.append(body["status"])
        if "priority" in body:
            if body["priority"] not in PRIORITIES:
                return error("Invalid priority")
            fields.append("priority = ?")
            params.append(body["priority"])
        if "assignee_id" in body:
            if not is_admin:
                return error("Only admins can assign bugs", 403)
            assignee = body["assignee_id"]
            if assignee is not None:
                exists = db.execute("SELECT 1 FROM users WHERE id = ?", (assignee,)).fetchone()
                if exists is None:
                    return error("Assignee not found")
            fields.append("assignee_id = ?")
            params.append(assignee)
        if not fields:
            return error("Nothing to update")
        params.append(bug_id)
        db.execute(f"UPDATE bugs SET {', '.join(fields)} WHERE id = ?", params)
        db.commit()
        row = fetch_bug(db, bug_id)
        return jsonify(bug_to_dict(row))

    @app.delete("/api/bugs/<int:bug_id>")
    @login_required
    def delete_bug(bug_id):
        if g.user["role"] != "admin":
            return error("Only admins can delete bugs", 403)
        db = get_db()
        cur = db.execute("DELETE FROM bugs WHERE id = ?", (bug_id,))
        db.commit()
        if cur.rowcount == 0:
            return error("Bug not found", 404)
        return "", 204

    @app.get("/api/stats")
    @login_required
    def stats():
        rows = get_db().execute("SELECT status, COUNT(*) AS n FROM bugs GROUP BY status").fetchall()
        counts = {s: 0 for s in STATUSES}
        counts.update({r["status"]: r["n"] for r in rows})
        return jsonify(counts)

    # ---------- frontend ----------
    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:name>")
    def static_files(name):
        return send_from_directory(FRONTEND_DIR, name)

    return app


if __name__ == "__main__":
    create_app().run(
        host="0.0.0.0" if os.environ.get("PORT") else "127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
