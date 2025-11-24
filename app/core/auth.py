# app/core/auth.py
import hashlib

def hash_password(password: str) -> str:
    """
    Hashea la contraseña con SHA-256.
    (Para producción conviene usar bcrypt/argon2,
     pero SHA-256 ya es mucho mejor que texto plano).
    """
    password = (password or "").strip()
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Compara una contraseña en texto plano con su hash almacenado."""
    return hash_password(password) == (password_hash or "")
