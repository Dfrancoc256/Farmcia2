cat > scripts/crear_usuario_admin.py << 'EOF'
import os
from app.repos.users_repo import create_user


def main():
    print("=== Crear usuario administrador ===")
    # Solo mostramos lo que YA está en el entorno, no lo cambiamos
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
EOF
