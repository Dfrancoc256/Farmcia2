# app/core/database.py
import os
import psycopg2


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) usando variables de entorno.

    - En local: puedes usar .env o os.environ.
    - En Streamlit Cloud: se leen desde Secrets.
    """

    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT", "5432"))
    dbname = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "")

    if not host:
        raise RuntimeError("DB_HOST no está definido en las variables de entorno.")

    try:
        print(
            f"[DB DEBUG] Conectando a PostgreSQL: "
            f"host={host}, port={port}, db={dbname}, user={user}"
        )

        conexion = psycopg2.connect(
            host=host,      # 👈 dejamos que psycopg2 resuelva (IPv4/IPv6)
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",   # Supabase exige SSL
        )

        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return conexion

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        raise RuntimeError(f"No se pudo conectar con la BD: {e}") from e


# Test rápido local (opcional)
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
