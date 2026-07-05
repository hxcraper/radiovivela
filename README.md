📻 Blog de Noticias — Radio Vívela

Sistema de blog administrable para que el equipo de la radio pueda publicar y gestionar noticias sin tocar código, mediante un panel web intuitivo.

🚀 Funcionalidades
🧑‍💻 Panel de administración con autenticación de usuarios
✍️ Editor de texto enriquecido para creación de noticias
🖼️ Subida de imagen destacada por publicación
🟡 Estados de contenido: borrador / publicado
🌐 Sitio público con URLs amigables
🔌 API de integración para el sitio principal
🏠 Home conectado dinámicamente con las últimas noticias publicadas
🧠 Integración con el sitio principal

El sitio de Radio Vívela consume automáticamente el contenido del sistema:

Muestra las últimas 4 noticias publicadas
Destaca la noticia más reciente
Mantiene diseño dinámico sin contenido manual en HTML
Incluye acceso discreto al panel administrativo desde el sitio
🏗️ Arquitectura

Proyecto construido con una arquitectura simple, modular y fácil de mantener.

Capa	Tecnología	Descripción
Backend	FastAPI (Python)	API ligera y extensible
Base de datos	SQLite	Almacenamiento simple en archivo único
Frontend	Jinja2	Renderizado server-side
Editor	Quill.js	Editor visual de contenido
Autenticación	Sesiones seguras	Manejo de login de usuarios

👉 Sin dependencias complejas de frontend ni frameworks adicionales.

⚙️ Instalación

Requiere Python 3.10+

git clone <repo>
cd blog-radio

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
▶️ Ejecución en desarrollo
uvicorn app.main:app --reload

Acceso:

Sitio público: http://localhost:8000/
Panel de administración: http://localhost:8000/admin/login
📝 Uso del sistema
Ingresar al panel de administración
Crear nueva noticia
Definir título, contenido e imagen destacada
Guardar como borrador o publicar
Administrar contenido desde el dashboard

👉 Diseñado para uso simple por equipos no técnicos.

🔌 API de integración

El sistema expone endpoints para consumo interno del sitio principal.

Permite:

Obtener listado de noticias publicadas
Obtener contenido individual por slug
Integración en tiempo real con el home
👤 Gestión de usuarios

El sistema incluye gestión de usuarios dentro del panel administrativo.

Creación de usuarios
Edición de credenciales
Eliminación de cuentas

⚠️ El acceso está protegido mediante sesión autenticada.

🌍 Despliegue

Recomendaciones para producción:

Ejecutar con servidor ASGI como Gunicorn + Uvicorn
Usar proxy inverso (Nginx o Caddy)
Activar HTTPS
Definir variables de entorno para configuración sensible
Realizar backups periódicos de la base de datos y archivos subidos
📁 Estructura del proyecto
blog-radio/
├── requirements.txt
├── README.md
└── app/
    ├── main.py
    ├── database.py
    ├── auth.py
    ├── utils.py
    ├── blog.db
    ├── static/
    │   ├── css/
    │   └── uploads/
    └── templates/
        ├── public/
        └── admin/
🛡️ Seguridad
Contraseñas almacenadas con hashing seguro
Sesiones protegidas mediante cookies firmadas
Separación entre contenido público y privado
Borradores nunca expuestos públicamente
Mejores prácticas recomendadas
Implementar protección CSRF en panel administrativo
Agregar rate limiting en autenticación
Considerar sistema de roles (admin / editor)
Monitoreo de accesos en producción
📌 Resumen

Este proyecto está diseñado para ser:

✔️ Fácil de usar
✔️ Fácil de mantener
✔️ Escalable
✔️ Integrable con sitios externos
✔️ Listo para producción ligera
