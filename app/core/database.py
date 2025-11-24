# app/core/database.py
import psycopg2


def conectar_bd():
    """
    Devuelve una conexión a PostgreSQL (Supabase) o None si falla.
    Ajusta host, puerto, user y password según tu proyecto.
    """
    try:
        conexion = psycopg2.connect(
            host="db.qiuhnugcvouffmrzclln.supabase.co",  # host de tu Supabase
            port=6543,                                   # puerto del Session Pooler
            dbname="postgres",                           # nombre de la BD (por defecto)
            user="postgres",                             # usuario por defecto
            password="6789juanpatito.",                 # ⚠ pon aquí tu password real
            sslmode="require",                           # Supabase exige SSL
        )
        print("✅ Conexión exitosa a PostgreSQL (Supabase)")
        return conexion
    except Exception as e:
        print("❌ Error al conectar a PostgreSQL:", e)
        return None


# Test rápido
if __name__ == "__main__":
    cn = conectar_bd()
    if cn:
        cur = cn.cursor()
        # equivalente a "SELECT TOP 5 name FROM sys.tables" en SQL Server
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            LIMIT 5;
        """)
        print("Tablas:", [r[0] for r in cur.fetchall()])
        cur.close()
        cn.close()
