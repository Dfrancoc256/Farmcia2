# scripts/crear_usuario_admin.py
import os
import sys

# === Ajuste para rutas ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.repos.users_repo import create_user


def main():
    print("=== Crear usuario administrador ===")

    # Usuario
    username = input("Usuario: ").strip()

    # Contraseñas (visibles para evitar problemas con getpass)
    pwd = input("Contraseña: ").strip()
    pwd2 = input("Repite la contraseña: ").strip()

    if not username or not pwd or not pwd2:
        print("❌ Debes completar usuario y ambas contraseñas.")
        return

    if pwd != pwd2:
        print("❌ Las contraseñas no coinciden.")
        return

    try:
        # 👇 IMPORTANTE: rol que sí acepte tu CHECK constraint
        user_id = create_user(username, pwd, rol="Administrador")
        print(f"✅ Usuario admin '{username}' creado con id {user_id}")
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")


if __name__ == "__main__":
    main()
