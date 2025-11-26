# app/core/database.py
import os
import psycopg2


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) usando variables de entorno.

    En la nube (Streamlit Cloud):
      - Las variables vienen de Secrets.
    En local:
      - Las puede poner el script (os.environ) o un .env cargado a mano.
    """

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    # Esto se verá en los logs de Streamlit Cloud (Manage app -> View logs)
    print(f"DEBUG DB_HOST={host}, DB_PORT={port}, DB_NAME={dbname}, DB_USER={user}", flush=True)

    try:
        conexion = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",  # Supabase exige SSL
        )
        print("✅ Conexión exitosa a PostgreSQL (Supabase)", flush=True)
        return conexion

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e, flush=True)
        return None


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
