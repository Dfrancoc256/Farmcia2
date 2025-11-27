# scripts/crear_usuario_admin.py

import os
from app.repos.users_repo import create_user


def ensure_db_env():
    """
    Asegura la configuración de BD:

    - Si estás en el VPS (ya hiciste export DB_HOST=127.0.0.1), NO toca nada.
    - Si NO hay variables definidas (tu PC), usa las credenciales por defecto
      para Supabase (solo modo desarrollo).
    """
    if os.getenv("DB_HOST"):
        print("Usando configuración de BD desde variables de entorno.")
        return

    print("⚠️ DB_HOST no está definido. Usando configuración por defecto (Supabase).")
    os.environ["DB_HOST"] = "db.qiuhnugcvouffmrzclln.supabase.co"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_PASS"] = "6789juanpatito."
    os.environ["DB_NAME"] = "postgres"
    os.environ["DB_SSLMODE"] = "require"


def main():
    print("=== Crear usuario administrador ===")
    ensure_db_env()

    print("DEBUG DB_HOST:", os.getenv("DB_HOST"))
    print("DEBUG DB_PORT:", os.getenv("DB_PORT"))

    username = input("Usuario: ").strip()
    pwd1 = input("Contraseña: ").strip()
    pwd2 = input("Repite la contraseña: ").strip()

    if pwd1 != pwd2:
        print("❌ Las contraseñas no coinciden.")
        return

    try:
        user_id = create_user(username, pwd1, rol="Administrador")
        print(f"✅ Usuario creado con ID: {user_id}")
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")


if __name__ == "__main__":
    main()
