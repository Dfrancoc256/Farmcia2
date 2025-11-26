# app/core/database.py
import os
import psycopg2


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase).
    - Lee credenciales de variables de entorno (local .env o secrets de Streamlit).
    - Si falla, lanza RuntimeError con el mensaje original.
    """

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "6543")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    # DEBUG para ver en logs de Streamlit Cloud
    print(f"DEBUG DB_HOST={host}")
    print(f"DEBUG DB_PORT={port}")
    print(f"DEBUG DB_NAME={dbname}")
    print(f"DEBUG DB_USER={user}")

    try:
        cn = psycopg2.connect(
            host=host,
            port=int(port),
            dbname=dbname,
            user=user,
            password=password,
            sslmode="require",  # Supabase lo exige en el Session Pooler
        )
        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return cn

    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        # Aquí NO devolvemos None: lanzamos error para que se vea en los logs
        raise RuntimeError(f"No se pudo conectar con la BD: {e}")
