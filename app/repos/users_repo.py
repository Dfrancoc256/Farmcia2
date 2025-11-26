# app/repos/users_repo.py
from app.core.database import conectar_bd
from app.core.auth import hash_password


def create_user(username: str, password: str, rol: str = "Administrador") -> int:
    """
    Crea un usuario en public.usuarios y devuelve el ID generado.
    PostgreSQL:
      - Usa RETURNING id.
      - Usa TRUE/FALSE para booleanos.
    """
    cn = None

    try:
        cn = conectar_bd()

        pwd_hash = hash_password(password)

        with cn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.usuarios (
                    username,
                    password_hash,
                    rol,
                    activo
                )
                VALUES (%s, %s, %s, TRUE)
                RETURNING id;
                """,
                (username, pwd_hash, rol),
            )

            row = cur.fetchone()
            if not row:
                raise RuntimeError("No se pudo obtener el ID del nuevo usuario.")

            user_id = int(row[0])

        cn.commit()
        return user_id

    except Exception as e:
        if cn:
            cn.rollback()
        # Propagamos el error con contexto
        raise RuntimeError(f"❌ Error en create_user: {e}")

    finally:
        if cn:
            cn.close()


def get_user_by_username(username: str):
    """
    Devuelve un dict con los datos del usuario o None si no existe.
    """
    cn = None

    try:
        cn = conectar_bd()

        with cn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    username,
                    password_hash,
                    rol,
                    activo
                FROM public.usuarios
                WHERE username = %s;
                """,
                (username,),
            )

            row = cur.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "password_hash": row[2],
            "rol": row[3],
            "activo": bool(row[4]),
        }

    finally:
        if cn:
            cn.close()
