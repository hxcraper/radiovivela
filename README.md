# Blog de Noticias — Radio Vívela

Sistema de blog administrable para que el equipo de la radio pueda publicar,
editar y eliminar noticias desde un panel web, **sin tocar código**.

- Panel de administración con usuario y contraseña
- Editor de texto enriquecido (Quill) para redactar noticias
- Subida de imagen destacada por noticia
- Estado **borrador** / **publicado**
- Sitio público de noticias con URLs amigables (`/noticias/titulo-de-la-noticia`)
- API REST en JSON para conectar las noticias con otras páginas del sitio (ej. el home de la radio)
- **El home (`/`) es el propio sitio de Radio Vívela**, con la sección "Noticias y novedades" conectada en vivo a lo que se publica desde el panel — ya no hay noticias fijas escritas a mano en el HTML.

## 1.1 Cómo quedó conectado el sitio de la radio

- La sección **"Noticias y novedades"** del home ahora recorre las últimas 4 noticias publicadas: la más reciente se muestra como destacada (tarjeta grande) y las otras 3 como tarjetas normales, igual que el diseño original.
- Si todavía no hay ninguna noticia publicada, esa sección muestra un aviso ("El equipo de prensa está preparando las primeras novedades") en vez de tarjetas vacías o de ejemplo.
- El botón **"Ver todas"** de esa sección lleva a `/noticias`, el listado completo con paginación.
- Cada tarjeta enlaza a la noticia completa en `/noticias/{slug}`.
- Al final del footer hay un link discreto **"Panel del equipo"** que lleva a `/admin/login`, para que el equipo de la radio encuentre el acceso sin que sea visible como un botón protagonista para el público general.

## 1. Arquitectura

Se eligió una arquitectura simple a propósito, para que sea fácil de mantener
sin un equipo de desarrollo grande detrás:

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend | **FastAPI** (Python) | Rápido de levantar, documentación automática, fácil de extender |
| Base de datos | **SQLite** (`app/blog.db`) | Un solo archivo, cero configuración, ideal para hosting simple. Si más adelante se necesita MySQL, solo hay que reemplazar `app/database.py` |
| Plantillas | **Jinja2** (HTML renderizado en el servidor) | No requiere build de frontend aparte ni Node.js en el servidor |
| Editor de texto | **Quill.js** (CDN, gratis, sin API key) | Editor tipo Word, liviano |
| Sesión de admin | Cookie firmada (`SessionMiddleware` de Starlette) + contraseña con `bcrypt` | Simple y suficientemente seguro para un equipo pequeño |

No hay build step, ni Node.js, ni frontend separado: todo corre desde un solo
proceso de Python.

## 2. Instalación

Requiere **Python 3.10+**.

```bash
cd blog-radio
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Ejecutar en desarrollo

```bash
uvicorn app.main:app --reload
```

Abre:
- Sitio público: http://localhost:8000/
- Panel de administración: http://localhost:8000/admin/login

**La primera vez que se ejecuta**, la aplicación crea automáticamente la base
de datos (`app/blog.db`) y un usuario administrador. Verás algo así en la
consola:

```
================================================================
 Se creó el usuario administrador inicial:
   Usuario:    admin
   Contraseña: CambiaEsta123!
 Cámbiala apenas ingreses al panel (ver README.md).
================================================================
```

⚠️ **Cambia esa contraseña antes de usar el sistema en producción.** Ver
sección 6 (Cambiar la contraseña de administrador).

## 4. Uso diario (para el equipo de la radio)

1. Entra a `/admin/login` con tu usuario y contraseña.
2. En el **Dashboard** verás todas las noticias, publicadas y en borrador.
3. Clic en **"➕ Nueva noticia"** para crear una:
   - Escribe el título (la URL se genera sola, ej: *"Vívela lanza nuevo programa"* → `/noticias/vivela-lanza-nuevo-programa`)
   - Sube una imagen destacada (opcional)
   - Escribe el contenido con el editor (negrita, títulos, listas, links, imágenes por URL, etc.)
   - Elige **Borrador** (mientras la preparas) o **Publicado** (para que salga en el sitio inmediatamente)
   - Clic en **"💾 Guardar noticia"**
4. Para editar o eliminar una noticia existente, usa los botones de la tabla del Dashboard.
5. Clic en **"🌐 Ver sitio público"** para ver cómo se ve en vivo.

No se necesita ningún conocimiento técnico para el uso diario.

## 5. La API para conectar con otras páginas del sitio

El sistema expone una API JSON de solo lectura, pensada para que el sitio
principal de la radio (por ejemplo, la sección "Noticias" del home) pueda
mostrar las últimas publicaciones sin duplicar el contenido:

```
GET /api/posts?limit=5&page=1
```
```json
{
  "total": 12,
  "page": 1,
  "per_page": 5,
  "results": [
    {
      "id": 8,
      "title": "Vívela lanza nuevo programa",
      "slug": "vivela-lanza-nuevo-programa",
      "excerpt": "Un adelanto de lo que se viene...",
      "featured_image": "/static/uploads/ab12cd34.jpg",
      "published_at": "2026-07-04T12:00:00+00:00",
      "url": "/noticias/vivela-lanza-nuevo-programa"
    }
  ]
}
```

```
GET /api/posts/{slug}
```
Devuelve el mismo objeto, agregando `content_html` con el contenido completo.

Solo devuelve noticias con estado **publicado**; los borradores nunca se
exponen por la API ni por el sitio público.

## 6. Gestionar usuarios (crear, editar, eliminar)

Todavía no hay una pantalla en el panel para esto — se hace llamando a estos
endpoints por HTTP, **desde tu computador**, usando `curl` (funciona igual en
local o contra tu app ya desplegada en Render, sin necesitar Shell ni plan
pago). Reemplaza `http://localhost:8000` por tu URL de Render si es en
producción, por ejemplo `https://radiovivela.onrender.com`.

**Paso 1 — Inicia sesión y guarda la cookie de sesión:**
```bash
curl -c cookies.txt -X POST http://localhost:8000/admin/login \
  -d "username=admin&password=TU_CONTRASEÑA_ACTUAL"
```
Esto crea un archivo `cookies.txt` que los siguientes comandos usan para
demostrar que estás autenticado.

**Ver todos los usuarios:**
```bash
curl -b cookies.txt http://localhost:8000/admin/usuarios
```

**Crear un usuario nuevo:**
```bash
curl -b cookies.txt -H "Content-Type: application/json" \
  -X POST http://localhost:8000/admin/usuarios \
  -d '{"username":"nuevo_usuario","password":"UnaContraseñaSegura123"}'
```

**Eliminar un usuario** (no puedes eliminar el usuario con el que iniciaste sesión):
```bash
curl -b cookies.txt -X DELETE http://localhost:8000/admin/usuarios/nombre_usuario
```

**Cambiar el nombre y/o la contraseña de un usuario específico:**
```bash
curl -b cookies.txt -H "Content-Type: application/json" \
  -X PUT http://localhost:8000/admin/usuarios/nombre_usuario \
  -d '{"new_username":"otro_nombre", "new_password":"OtraClave123"}'
```
(Puedes mandar solo `new_username`, solo `new_password`, o ambos.)

**Cambiar la contraseña del usuario con el que tienes la sesión iniciada**
(la forma más simple de cambiar tu propia contraseña de `admin`):
```bash
curl -b cookies.txt -H "Content-Type: application/json" \
  -X PUT http://localhost:8000/admin/cambiar-password \
  -d '{"new_password":"MiNuevaContraseñaSegura"}'
```

⚠️ Estos endpoints están protegidos por sesión (tienes que estar logueado para
usarlos), pero no tienen una capa extra de permisos por rol — cualquier
usuario logueado puede crear o borrar a otro. Para un equipo pequeño esto es
razonable; si el equipo crece, conviene agregar roles (ej. solo "admin" puede
gestionar usuarios).

## 7. Cambiar la contraseña de administrador (método alternativo, por consola)

Si tienes acceso a una consola local o a la Shell de Render (planes pagos),
también puedes hacerlo así:

```bash
python -c "
from app import database as db, auth
db.init_db()
user = db.get_user_by_username('admin')
db.update_user_password(user['id'], auth.hash_password('TU_NUEVA_CONTRASEÑA'))
print('Contraseña actualizada.')
"
```

También puedes definir usuario y contraseña iniciales por variables de
entorno **antes del primer arranque** (si `blog.db` ya existe, esto no tiene
efecto porque el usuario ya fue creado):

```bash
export ADMIN_USERNAME="tu_usuario"
export ADMIN_PASSWORD="una-contraseña-segura"
export BLOG_SECRET_KEY="una-clave-larga-y-aleatoria"
uvicorn app.main:app
```

## 8. Despliegue en producción

- Corre la app detrás de un proceso persistente, por ejemplo con `gunicorn` + `uvicorn.workers.UvicornWorker`, o con `systemd` ejecutando `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Pon un proxy inverso (Nginx / Caddy) delante para servir HTTPS.
- Define siempre `BLOG_SECRET_KEY` como variable de entorno en producción (no dejes el valor por defecto del código).
- Haz respaldo periódico del archivo `app/blog.db` y de la carpeta `app/static/uploads/` — ahí vive todo el contenido.
- Si el hosting solo permite MySQL (no SQLite), lo único que hay que adaptar es `app/database.py`; el resto de la aplicación no cambia.

## 9. Estructura del proyecto

```
blog-radio/
├── requirements.txt
├── README.md
└── app/
    ├── main.py            # Rutas: público, admin y API
    ├── database.py        # Acceso a SQLite (sin ORM)
    ├── auth.py             # Hash de contraseña y sesión de login
    ├── utils.py            # Slug amigable y generación de resumen
    ├── blog.db             # Se crea solo, al primer arranque
    ├── static/
    │   ├── css/style.css
    │   └── uploads/        # Imágenes destacadas subidas desde el panel
    └── templates/
        ├── public/         # Home, lista y detalle de noticias
        └── admin/          # Login, dashboard y formulario de noticias
```

## 10. Notas de seguridad (a tener en cuenta antes de producción)

- Las contraseñas se guardan con hash `bcrypt`, nunca en texto plano.
- La sesión de administrador usa una cookie firmada (`httpOnly`), no un token expuesto al JavaScript del cliente.
- Este proyecto **no incluye protección CSRF explícita** en los formularios del panel; dado que es de uso interno para un equipo pequeño, el riesgo es bajo, pero si el panel va a quedar accesible públicamente en internet, se recomienda agregar tokens CSRF a los formularios de creación/edición/eliminación antes de salir a producción.
- Se recomienda servir el panel de administración únicamente por HTTPS.
