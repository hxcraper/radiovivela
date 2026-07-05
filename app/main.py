"""
Blog administrable para radio online — aplicación principal.

Cómo correrlo (ver README.md para más detalle):
    pip install -r requirements.txt
    uvicorn app.main:app --reload

Panel de administración: http://localhost:8000/admin/login
Usuario / contraseña por defecto: se crean en el primer arranque,
ver variables ADMIN_USERNAME / ADMIN_PASSWORD en README.md.
"""
import math
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Form, File, UploadFile, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import database as db
from app import auth
from app.utils import slugify, make_excerpt, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_BYTES

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "static" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("BLOG_SECRET_KEY", "cambia-esta-clave-en-produccion")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "CambiaEsta123!")
POSTS_PER_PAGE = 9

app = FastAPI(title="Blog Radio — Panel de noticias")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="blogradio_session")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup():
    db.init_db()
    if db.count_users() == 0:
        db.create_user(ADMIN_USERNAME, auth.hash_password(ADMIN_PASSWORD))
        print("=" * 64)
        print(" Se creó el usuario administrador inicial:")
        print(f"   Usuario:    {ADMIN_USERNAME}")
        print(f"   Contraseña: {ADMIN_PASSWORD}")
        print(" Cámbiala apenas ingreses al panel (ver README.md).")
        print("=" * 64)


def tpl_context(request: Request, **extra):
    ctx = {"request": request, "user": auth.current_user(request)}
    ctx.update(extra)
    return ctx


# =============================================================================
# FRONTEND PÚBLICO
# =============================================================================
@app.get("/")
def home(request: Request):
    latest, _ = db.list_posts(status="publicado", page=1, per_page=4)
    return templates.TemplateResponse(
        "public/home.html", tpl_context(request, posts=latest)
    )


@app.get("/noticias")
def noticias_list(request: Request, page: int = Query(1, ge=1)):
    posts, total = db.list_posts(status="publicado", page=page, per_page=POSTS_PER_PAGE)
    total_pages = max(1, math.ceil(total / POSTS_PER_PAGE))
    return templates.TemplateResponse(
        "public/noticias_list.html",
        tpl_context(request, posts=posts, page=page, total_pages=total_pages),
    )


@app.get("/noticias/{slug}")
def noticia_detail(request: Request, slug: str):
    post = db.get_post_by_slug(slug, published_only=True)
    if not post:
        return templates.TemplateResponse(
            "public/not_found.html", tpl_context(request), status_code=404
        )
    return templates.TemplateResponse(
        "public/noticia_detail.html", tpl_context(request, post=post)
    )


# =============================================================================
# API REST (para conectar con otras páginas del sitio, ej. el home de la radio)
# =============================================================================
def _post_to_public_json(p: dict) -> dict:
    return {
        "id": p["id"],
        "title": p["title"],
        "slug": p["slug"],
        "excerpt": p["excerpt"],
        "featured_image": f"/static/uploads/{p['featured_image']}" if p["featured_image"] else None,
        "published_at": p["published_at"],
        "url": f"/noticias/{p['slug']}",
    }


@app.get("/api/posts")
def api_list_posts(limit: int = Query(10, ge=1, le=50), page: int = Query(1, ge=1)):
    posts, total = db.list_posts(status="publicado", page=page, per_page=limit)
    return {
        "total": total,
        "page": page,
        "per_page": limit,
        "results": [_post_to_public_json(p) for p in posts],
    }


@app.get("/api/posts/{slug}")
def api_post_detail(slug: str):
    post = db.get_post_by_slug(slug, published_only=True)
    if not post:
        return JSONResponse({"error": "No encontrado"}, status_code=404)
    data = _post_to_public_json(post)
    data["content_html"] = post["content_html"]
    return data


# =============================================================================
# ADMIN — AUTENTICACIÓN
# =============================================================================
@app.get("/admin/login")
def admin_login_form(request: Request):
    if auth.current_user(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", tpl_context(request, error=None))


@app.post("/admin/login")
def admin_login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    user = db.get_user_by_username(username.strip())
    if not user or not auth.verify_password(password, user["password_hash"]):
        return templates.TemplateResponse(
            "admin/login.html",
            tpl_context(request, error="Usuario o contraseña incorrectos."),
            status_code=401,
        )
    auth.login_user(request, user["id"], user["username"])
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/logout")
def admin_logout(request: Request):
    auth.logout_user(request)
    return RedirectResponse("/admin/login", status_code=303)


def _require_login_or_redirect(request: Request):
    """Devuelve None si hay sesión activa, o una RedirectResponse si no la hay."""
    if not auth.current_user(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


# =============================================================================
# ADMIN — DASHBOARD Y CRUD DE NOTICIAS
# =============================================================================
@app.get("/admin")
def admin_dashboard(request: Request, page: int = Query(1, ge=1)):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect
    posts, total = db.list_posts(status=None, page=page, per_page=15)
    total_pages = max(1, math.ceil(total / 15))
    published_count, _ = db.list_posts(status="publicado", page=1, per_page=1)
    draft_count, _ = db.list_posts(status="borrador", page=1, per_page=1)
    _, total_published = db.list_posts(status="publicado", page=1, per_page=1)
    _, total_draft = db.list_posts(status="borrador", page=1, per_page=1)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        tpl_context(
            request,
            posts=posts,
            page=page,
            total_pages=total_pages,
            total_published=total_published,
            total_draft=total_draft,
        ),
    )


@app.get("/admin/posts/new")
def admin_post_new_form(request: Request):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "admin/post_form.html", tpl_context(request, post=None, error=None)
    )


def _save_uploaded_image(file: UploadFile) -> str | None:
    if not file or not file.filename:
        return None
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato de imagen no permitido. Usa JPG, PNG, WEBP o GIF.")
    contents = file.file.read()
    if len(contents) > MAX_IMAGE_BYTES:
        raise ValueError("La imagen supera el tamaño máximo permitido (6 MB).")
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(UPLOADS_DIR / filename, "wb") as out:
        out.write(contents)
    return filename


@app.post("/admin/posts/new")
def admin_post_new_submit(
    request: Request,
    title: str = Form(...),
    content_html: str = Form(""),
    excerpt: str = Form(""),
    status: str = Form("borrador"),
    featured_image: UploadFile = File(None),
):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect

    title = title.strip()
    if not title:
        return templates.TemplateResponse(
            "admin/post_form.html",
            tpl_context(request, post=None, error="El título es obligatorio."),
            status_code=400,
        )

    base_slug = slugify(title)
    slug = base_slug
    n = 2
    while db.slug_exists(slug):
        slug = f"{base_slug}-{n}"
        n += 1

    try:
        image_filename = _save_uploaded_image(featured_image)
    except ValueError as e:
        return templates.TemplateResponse(
            "admin/post_form.html", tpl_context(request, post=None, error=str(e)), status_code=400
        )

    final_excerpt = excerpt.strip() or make_excerpt(content_html)
    post_id = db.create_post(title, slug, final_excerpt, content_html, image_filename, status)
    return RedirectResponse(f"/admin/posts/{post_id}/edit?saved=1", status_code=303)


@app.get("/admin/posts/{post_id}/edit")
def admin_post_edit_form(request: Request, post_id: int, saved: int = 0):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect
    post = db.get_post_by_id(post_id)
    if not post:
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(
        "admin/post_form.html", tpl_context(request, post=post, error=None, saved=bool(saved))
    )


@app.post("/admin/posts/{post_id}/edit")
def admin_post_edit_submit(
    request: Request,
    post_id: int,
    title: str = Form(...),
    content_html: str = Form(""),
    excerpt: str = Form(""),
    status: str = Form("borrador"),
    remove_image: str = Form(""),
    featured_image: UploadFile = File(None),
):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect

    existing = db.get_post_by_id(post_id)
    if not existing:
        return RedirectResponse("/admin", status_code=303)

    title = title.strip()
    if not title:
        return templates.TemplateResponse(
            "admin/post_form.html",
            tpl_context(request, post=existing, error="El título es obligatorio."),
            status_code=400,
        )

    base_slug = slugify(title)
    slug = base_slug
    n = 2
    while db.slug_exists(slug, exclude_id=post_id):
        slug = f"{base_slug}-{n}"
        n += 1

    image_filename = existing["featured_image"]
    try:
        new_image = _save_uploaded_image(featured_image)
    except ValueError as e:
        return templates.TemplateResponse(
            "admin/post_form.html", tpl_context(request, post=existing, error=str(e)), status_code=400
        )
    if new_image:
        image_filename = new_image
    elif remove_image == "1":
        image_filename = None

    final_excerpt = excerpt.strip() or make_excerpt(content_html)
    db.update_post(post_id, title, slug, final_excerpt, content_html, image_filename, status)
    return RedirectResponse(f"/admin/posts/{post_id}/edit?saved=1", status_code=303)


@app.post("/admin/posts/{post_id}/delete")
def admin_post_delete(request: Request, post_id: int):
    redirect = _require_login_or_redirect(request)
    if redirect:
        return redirect
    db.delete_post(post_id)
    return RedirectResponse("/admin", status_code=303)


@app.get("/crear-usuario-temporal")
def crear_usuario_temporal():
    from app import auth
    if db.get_user_by_username("nombre_usuario"):
        return {"mensaje": "Ese usuario ya existe"}
    db.create_user("nombre_usuario", auth.hash_password("SuContraseñaSegura"))
    return {"mensaje": "Usuario creado correctamente"}