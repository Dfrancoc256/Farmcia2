# app/core/database.py
import os
import socket
import psycopg2


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) usando variables de entorno.

    - En local: se leen desde .env (si lo usas) o desde el script que hace os.environ.
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
        # 🔹 Forzar IPv4 para evitar el problema de IPv6 en Streamlit Cloud
        host_ipv4 = socket.gethostbyname(host)

        print(
            f"[DB DEBUG] Conectando a PostgreSQL: "
            f"host={host} -> IPv4={host_ipv4}, port={port}, db={dbname}, user={user}"
        )

        conexion = psycopg2.connect(
            host=host_ipv4,    # 👈 aquí ya va la IP v4, no el hostname
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",  # Supabase exige SSL
        )

        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return conexion

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        # Importante: relanzamos como RuntimeError para que el resto de capas lo vean
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
