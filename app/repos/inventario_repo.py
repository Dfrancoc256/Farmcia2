# app/repos/inventario_repo.py
from typing import List, Tuple

from app.core.database import conectar_bd


class InventarioRepo:
    """
    Acceso a datos para el panel de Inventario en PostgreSQL:
    - Ventas resumidas
    - Gastos
    - Totales de ventas en efectivo
    """

    # ==========================================================
    #  LISTAR VENTAS RESUMEN
    # ==========================================================
    def listar_ventas_resumen(self, d1: str, d2: str) -> List[Tuple]:
        """
        Devuelve ventas agrupadas por fecha en formato:
        (fecha, detalle, cantidad, monto)

        d1 y d2 vienen como 'YYYY-MM-DD'
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        to_char(v.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        string_agg(
                            p.nombre || ' x' || d.cantidad::text,
                            ', ' ORDER BY d.id
                        ) AS detalle,
                        SUM(d.cantidad) AS cantidad,
                        SUM(d.cantidad * d.precio_unitario)::double precision AS monto
                    FROM public.ventas v
                    JOIN public.detalle_ventas d ON d.id_venta = v.id
                    JOIN public.productos      p ON p.id = d.id_producto
                    WHERE v.fecha >= %s
                      AND v.fecha < %s::date + INTERVAL '1 day'
                    GROUP BY v.fecha
                    ORDER BY v.fecha;
                    """,
                    (d1, d2),
                )
                return cur.fetchall()
        finally:
            cn.close()

    # ==========================================================
    #  LISTAR GASTOS
    # ==========================================================
    def listar_gastos(self, d1: str, d2: str) -> List[Tuple]:
        """
        Devuelve gastos en el rango:
        (fecha, descripcion, monto)
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

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

    # ==========================================================
    #  TOTAL VENTAS EN EFECTIVO
    # ==========================================================
    def get_total_ventas_efectivo(self, d1: str, d2: str) -> float:
        """
        Total de ventas en efectivo dentro del rango indicado.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        COALESCE(SUM(total), 0)::double precision
                    FROM public.ventas
                    WHERE fecha >= %s
                      AND fecha < %s::date + INTERVAL '1 day'
                      AND lower(COALESCE(tipo_pago, 'efectivo')) = 'efectivo';
                    """,
                    (d1, d2),
                )
                row = cur.fetchone()
                return float(row[0]) if row else 0.0
        finally:
            cn.close()
