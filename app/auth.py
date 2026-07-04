"""
Autenticación simple basada en sesión (cookie firmada), pensada para un
equipo pequeño que administra el blog. No es un sistema multiusuario
complejo con roles y permisos: es "usuario y contraseña" tal como se pidió.
"""
from passlib.context import CryptContext
from fastapi import Request

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def login_user(request: Request, user_id: int, username: str):
    request.session["user_id"] = user_id
    request.session["username"] = username


def logout_user(request: Request):
    request.session.clear()


def current_user(request: Request):
    if "user_id" in request.session:
        return {"id": request.session["user_id"], "username": request.session["username"]}
    return None
