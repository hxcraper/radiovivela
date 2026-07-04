import re
import unicodedata
from html import unescape


def slugify(text: str) -> str:
    """Convierte un título en una URL amigable: 'Última Hora: ¡Nuevo Show!' -> 'ultima-hora-nuevo-show'."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")  # quita tildes/ñ -> n, etc.
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "noticia"


def strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(html: str, length: int = 180) -> str:
    text = strip_html(html)
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0].strip() + "…"


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 6 * 1024 * 1024  # 6 MB
