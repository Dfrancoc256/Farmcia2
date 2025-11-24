# app/repos/movimientos_repo.py
from datetime import date
from typing import List, Tuple, Union

from app.core.database import conectar_bd


class MovimientosRepo:
    """
    Acceso unificado a movimientos en PostgreSQL:
    - Ventas   -> entrada
    - Gastos   -> salida
    - Fiados   -> salida (dinero no recibido)

    Formato devuelto:
    (fecha:str, tipo:str, concepto:str, entrada:float, salida:float)
    """

    def listar_en_rango(
        self,
        desde: Union[date, str],
        hasta: Union[date, str],
    ) -> List[Tuple]:
        """
        Devuelve ventas, gastos y fiados dentro del rango.
        En PostgreSQL el límite 'hasta' se maneja como:

            fecha >= desde AND fecha < hasta + INTERVAL '1 day'
        """

        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    /* =============================
                       VENTAS → ENTRADA DE DINERO
                       ============================= */
                    SELECT
                        TO_CHAR(v.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        'Venta'                                AS tipo,
                        'Venta #' || v.id                       AS concepto,
                        CAST(v.total AS DOUBLE PRECISION)       AS entrada,
                        0.0                                     AS salida
                    FROM public.ventas v
                    WHERE v.fecha >= %s
                      AND v.fecha < (%s::date + INTERVAL '1 day')

                    UNION ALL

                    /* =============================
                       GASTOS → SALIDA DE DINERO
                       ============================= */
                    SELECT
                        TO_CHAR(g.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        'Gasto'                                AS tipo,
                        g.descripcion                          AS concepto,
                        0.0                                    AS entrada,
                        CAST(g.monto AS DOUBLE PRECISION)      AS salida
                    FROM public.gastos g
                    WHERE g.fecha >= %s
                      AND g.fecha < (%s::date + INTERVAL '1 day')

                    UNION ALL

                    /* =============================
                       FIADOS → SALIDA (NO RECIBIDO)
                       ============================= */
                    SELECT
                        TO_CHAR(f.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        'Fiado'                                AS tipo,
                        f.nombre_cliente                       AS concepto,
                        0.0                                    AS entrada,
                        CAST(f.monto AS DOUBLE PRECISION)      AS salida
                    FROM public.fiados f
                    WHERE f.fecha >= %s
                      AND f.fecha < (%s::date + INTERVAL '1 day')

                    ORDER BY fecha, tipo;
                    """,
                    (
                        desde, hasta,
                        desde, hasta,
                        desde, hasta,
                    ),
                )

                rows = cur.fetchall()

        finally:
            cn.close()

        return rows
