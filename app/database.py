"""
Capa de datos — SQLite simple, sin ORM.

Se eligió sqlite3 puro (en vez de un ORM) para que el proyecto sea fácil
de leer y modificar por cualquier desarrollador, y porque SQLite no
requiere un servidor de base de datos aparte: basta con el archivo
`blog.db` que se genera solo la primera vez que corre la aplicación.

Si más adelante se necesita migrar a MySQL (por ejemplo, por el tipo de
hosting contratado), solo hay que reemplazar las funciones de este
archivo — el resto de la aplicación no depende de sqlite3 directamente.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "blog.db"


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Crea las tablas si no existen. Seguro de llamar en cada arranque."""
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                excerpt TEXT NOT NULL DEFAULT '',
                content_html TEXT NOT NULL DEFAULT '',
                featured_image TEXT,
                status TEXT NOT NULL DEFAULT 'borrador' CHECK(status IN ('borrador','publicado')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                published_at TEXT
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug);")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
def get_user_by_username(username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return _row_to_dict(row) if row else None


def count_users() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]


def create_user(username: str, password_hash: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now_iso()),
        )


def update_user_password(user_id: int, password_hash: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))


# ---------------------------------------------------------------------------
# POSTS
# ---------------------------------------------------------------------------
def slug_exists(slug: str, exclude_id: int | None = None) -> bool:
    with get_conn() as conn:
        if exclude_id:
            row = conn.execute(
                "SELECT id FROM posts WHERE slug = ? AND id != ?", (slug, exclude_id)
            ).fetchone()
        else:
            row = conn.execute("SELECT id FROM posts WHERE slug = ?", (slug,)).fetchone()
        return row is not None


def create_post(title, slug, excerpt, content_html, featured_image, status) -> int:
    ts = now_iso()
    published_at = ts if status == "publicado" else None
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO posts
               (title, slug, excerpt, content_html, featured_image, status, created_at, updated_at, published_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, slug, excerpt, content_html, featured_image, status, ts, ts, published_at),
        )
        return cur.lastrowid


def update_post(post_id, title, slug, excerpt, content_html, featured_image, status):
    with get_conn() as conn:
        current = conn.execute("SELECT status, published_at FROM posts WHERE id = ?", (post_id,)).fetchone()
        if current is None:
            return False
        published_at = current["published_at"]
        # Si pasa de borrador a publicado por primera vez, fijamos la fecha de publicación ahora.
        if status == "publicado" and not published_at:
            published_at = now_iso()
        conn.execute(
            """UPDATE posts SET title=?, slug=?, excerpt=?, content_html=?, featured_image=?,
               status=?, updated_at=?, published_at=? WHERE id=?""",
            (title, slug, excerpt, content_html, featured_image, status, now_iso(), published_at, post_id),
        )
        return True


def delete_post(post_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))


def get_post_by_id(post_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return _row_to_dict(row) if row else None


def get_post_by_slug(slug, published_only=True):
    with get_conn() as conn:
        if published_only:
            row = conn.execute(
                "SELECT * FROM posts WHERE slug = ? AND status = 'publicado'", (slug,)
            ).fetchone()
        else:
            row = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
        return _row_to_dict(row) if row else None


def list_posts(status=None, page=1, per_page=10):
    offset = (page - 1) * per_page
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                """SELECT * FROM posts WHERE status = ?
                   ORDER BY COALESCE(published_at, created_at) DESC LIMIT ? OFFSET ?""",
                (status, per_page, offset),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) AS c FROM posts WHERE status = ?", (status,)).fetchone()["c"]
        else:
            rows = conn.execute(
                """SELECT * FROM posts
                   ORDER BY COALESCE(published_at, created_at) DESC LIMIT ? OFFSET ?""",
                (per_page, offset),
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"]
        return [_row_to_dict(r) for r in rows], total
