# scripts/crear_usuario_admin.py

import os
from getpass import getpass

# ⚠️ Configuración SOLO para uso local de este script.
# La app en Streamlit Cloud usa Secrets, esto no la afecta.
os.environ["DB_HOST"] = "db.qiuhnugcvouffmrzclln.supabase.co"
os.environ["DB_PORT"] = "6543"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASS"] = "6789juanpatito."
os.environ["DB_NAME"] = "postgres"

from app.repos.users_repo import create_user


def main():
    print("=== Crear usuario administrador ===")

    print("DEBUG DB_HOST:", os.getenv("DB_HOST"))
    print("DEBUG DB_PORT:", os.getenv("DB_PORT"))

    username = input("Usuario: ").strip()
    pwd1 = input("Contraseña: ")
    pwd2 = input("Repite la contraseña: ")

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
