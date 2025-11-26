# app/core/database.py
import os
import socket
import psycopg2


def _ipv4_only(hostname: str) -> str:
    """
    Resuelve el hostname a una IP IPv4.
    Si algo falla, devuelve el hostname original.
    Esto evita errores cuando el contenedor no soporta IPv6.
    """
    try:
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if infos:
            # infos[0][4] -> (ip, puerto)
            return infos[0][4][0]
    except Exception:
        pass
    return hostname


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) usando variables de entorno.
    En Streamlit Cloud los valores vienen de Secrets; localmente puedes usar .env.
    """

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS")

    if not host or not password:
        raise RuntimeError("Faltan variables de entorno de la BD (DB_HOST/DB_PASS).")

    # 🔧 Forzamos IPv4 para evitar el error "Cannot assign requested address" con IPv6
    host_ipv4 = _ipv4_only(host)

    try:
        print(f"DEBUG conectar_bd host={host} -> {host_ipv4} port={port}")
        conexion = psycopg2.connect(
            host=host_ipv4,
            port=int(port),
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",  # Supabase exige SSL
        )
        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return conexion

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        raise RuntimeError(f"No se pudo conectar con la BD: {e}")
