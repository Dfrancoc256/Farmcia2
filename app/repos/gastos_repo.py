# app/repos/gastos_repo.py
from datetime import date
from typing import List, Tuple

from app.core.database import conectar_bd


class GastosRepo:
    """
    Acceso a datos para gastos (PostgreSQL).
    """

    # ==========================================================
    #   CREAR GASTO
    # ==========================================================
    def crear_gasto(self, descripcion: str, monto: float, fecha: date, categoria: str | None):
        """
        Inserta un gasto en PostgreSQL.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.gastos (descripcion, monto, fecha, categoria)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (
                        descripcion.strip(),
                        float(monto),
                        fecha,
                        categoria.strip() if categoria else None,
                    ),
                )

            cn.commit()

        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #   LISTAR GASTOS POR RANGO
    # ==========================================================
    def listar_en_rango(self, d1: str, d2: str) -> List[Tuple]:
        """
        Devuelve tuplas en formato:
        (fecha_str, descripcion, monto_float)

        d1 y d2 deben venir como 'YYYY-MM-DD'
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        to_char(g.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        g.descripcion,
                        g.monto::double precision AS monto
                    FROM public.gastos g
                    WHERE g.fecha >= %s
                      AND g.fecha < %s::date + INTERVAL '1 day'
                    ORDER BY g.fecha;
                    """,
                    (d1, d2),
                )
                return cur.fetchall()
        finally:
            cn.close()
