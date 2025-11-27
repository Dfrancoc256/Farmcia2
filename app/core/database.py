# app/core/database.py

import os
import psycopg2


def conectar_bd():
    """
    Conexión universal para VPS y Supabase.
    - VPS: sslmode=disable (PostgreSQL local)
    - Supabase: sslmode=require automáticamente
    """

    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD", "")

    if not host:
        raise RuntimeError("DB_HOST no está definido en las variables de entorno.")

    # SSL automático
    sslmode = os.getenv("DB_SSLMODE")
    if not sslmode:
        if "supabase.co" in host:
            sslmode = "require"
        else:
            sslmode = "disable"

    try:
        print(
            f"[DB DEBUG] Conectando a PostgreSQL: "
            f"host={host}, port={port}, db={dbname}, user={user}, sslmode={sslmode}"
        )

        conexion = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode=sslmode,
        )

        print("✅ Conexión exitosa a PostgreSQL")
        return conexion

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        raise RuntimeError(f"No se pudo conectar con la BD: {e}") from e


# Test manual
if __name__ == "__main__":
    cn = conectar_bd()
    if cn:
        cur = cn.cursor()
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            LIMIT 5;
            """
        )
        print("Tablas:", [r[0] for r in cur.fetchall()])
        cur.close()
        cn.close()
