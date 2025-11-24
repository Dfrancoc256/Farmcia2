# app/repos/dashboard_repo.py
from datetime import date
from typing import Dict, List, Tuple
from app.core.database import conectar_bd


class DashboardRepo:
    """
    Consultas agregadas para el dashboard de inicio.
    """

    # ==========================================================
    #   RESUMEN GENERAL (KPIs)
    # ==========================================================
    def get_resumen(self, desde: date, hasta: date) -> Dict[str, float]:
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        # Convertir fechas → string aceptado por PostgreSQL
        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        try:
            resumen: Dict[str, float] = {}

            # ------------------------------------------------------
            #   Total productos activos + stock total
            # ------------------------------------------------------
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(*) AS total_productos,
                        COALESCE(SUM(stock_unidades), 0) AS stock_total
                    FROM public.productos
                    WHERE activo = TRUE;
                """)
                total_prod, stock_total = cur.fetchone()
                resumen["total_productos"] = int(total_prod or 0)
                resumen["stock_total_unidades"] = int(stock_total or 0)

            # ------------------------------------------------------
            #   Total vendido (suma de ventas activas en rango)
            # ------------------------------------------------------
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(total), 0)
                    FROM public.ventas
                    WHERE estado = 'Activa'
                      AND fecha >= %s
                      AND fecha < (%s::date + INTERVAL '1 day');
                """, (d1, d2))
                resumen["total_vendido"] = float(cur.fetchone()[0] or 0.0)

            # ------------------------------------------------------
            #   Ganancia = Σ (precio_unitario – costo_unitario_compra) × unidades_descuento
            # ------------------------------------------------------
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(
                       (d.precio_unitario - d.costo_unitario_compra) * d.unidades_descuento
                    ), 0)
                    FROM public.ventas v
                    JOIN public.detalle_ventas d ON d.id_venta = v.id
                    WHERE v.estado = 'Activa'
                      AND v.fecha >= %s
                      AND v.fecha < (%s::date + INTERVAL '1 day');
                """, (d1, d2))
                resumen["ganancia"] = float(cur.fetchone()[0] or 0.0)

            # ------------------------------------------------------
            #   Fiado pendiente total
            # ------------------------------------------------------
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(monto), 0)
                    FROM public.fiados
                    WHERE estado IS DISTINCT FROM 'Pagado';
                """)
                resumen["fiado_pendiente"] = float(cur.fetchone()[0] or 0.0)

            return resumen

        finally:
            cn.close()

    # ==========================================================
    #   INVENTARIO COMPLETO PARA TABLA
    # ==========================================================
    def get_inventario_completo(self) -> List[Tuple]:
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        codigo,
                        nombre,
                        COALESCE(stock_unidades, 0),
                        precio_venta_unidad,
                        precio_venta_blister,
                        COALESCE(unidades_por_blister, 0)
                    FROM public.productos
                    WHERE activo = TRUE
                    ORDER BY nombre;
                """)
                return cur.fetchall()

        finally:
            cn.close()

    # ==========================================================
    #   TOP PRODUCTOS MÁS VENDIDOS
    # ==========================================================
    def get_top_productos_vendidos(
        self, desde: date, hasta: date, top_n: int = 5
    ) -> List[Tuple]:

        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        sql = f"""
            SELECT
                p.id,
                p.codigo,
                p.nombre,
                COALESCE(SUM(d.unidades_descuento), 0) AS unidades_vendidas
            FROM public.detalle_ventas d
            JOIN public.ventas v ON v.id = d.id_venta
            JOIN public.productos p ON p.id = d.id_producto
            WHERE v.estado = 'Activa'
              AND v.fecha >= %s
              AND v.fecha < (%s::date + INTERVAL '1 day')
            GROUP BY p.id, p.codigo, p.nombre
            ORDER BY unidades_vendidas DESC, p.nombre
            LIMIT {int(top_n)};
        """

        try:
            with cn.cursor() as cur:
                cur.execute(sql, (d1, d2))
                return cur.fetchall()

        finally:
            cn.close()

    # ==========================================================
    #   STOCK CRÍTICO
    # ==========================================================
    def get_productos_stock_critico(self, threshold: int = 1) -> List[Tuple]:
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        codigo,
                        nombre,
                        COALESCE(stock_unidades, 0),
                        precio_venta_unidad,
                        precio_venta_blister,
                        COALESCE(unidades_por_blister, 0)
                    FROM public.productos
                    WHERE activo = TRUE
                      AND COALESCE(stock_unidades, 0) <= %s
                    ORDER BY stock_unidades ASC, nombre;
                """, (threshold,))
                return cur.fetchall()

        finally:
            cn.close()
