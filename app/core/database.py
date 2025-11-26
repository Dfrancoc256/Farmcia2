# app/core/database.py
import os
import socket
import psycopg2


def _get_env(nombre: str, defecto: str | None = None, requerido: bool = False) -> str:
    """Obtiene una variable de entorno y valida si es requerida."""
    valor = os.getenv(nombre, defecto)
    if requerido and not valor:
        raise RuntimeError(f"⚠️ Variable de entorno {nombre} no definida.")
    return valor


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) usando variables de entorno.

    En Streamlit Cloud las variables vienen de Secrets.
    Localmente puedes usar .env o lo que ya tienes configurado.
    Además, forzamos IPv4 para evitar el error de IPv6 (`Cannot assign requested address`).
    """
    # --- leer variables ---
    host = _get_env("DB_HOST", requerido=True)
    port = int(_get_env("DB_PORT", "5432"))
    dbname = _get_env("DB_NAME", "postgres")
    user = _get_env("DB_USER", requerido=True)
    password = _get_env("DB_PASS", requerido=True)

    # Debug muy ligero (se puede dejar, no imprime password)
    print(f"[DB] HOST={host} PORT={port} DB={dbname} USER={user}")

    # --- forzar IPv4 ---
    try:
        ipv4 = socket.gethostbyname(host)   # resuelve solo A (IPv4)
        print(f"[DB] Resuelto IPv4: {ipv4}")
    except Exception as e:
        print(f"[DB] No se pudo resolver IPv4, uso host tal cual: {e}")
        ipv4 = host

    try:
        conn = psycopg2.connect(
            host=ipv4,            # usamos la IP v4
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",   # Supabase exige SSL
        )
        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return conn

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        # Propagamos un error amigable (lo que ve Streamlit)
        raise RuntimeError(f"No se pudo conectar con la BD: {e}")
