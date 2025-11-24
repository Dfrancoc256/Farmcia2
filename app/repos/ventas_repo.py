# app/repos/ventas_repo.py
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import List, Sequence, Dict

from app.core.database import conectar_bd
from app.models.venta import CarritoItem


class VentasRepo:
    """
    Acceso a datos para registrar y consultar ventas completas
    (cabecera, detalle, stock y movimientos de inventario) en PostgreSQL.
    """

    # ============================================================
    #  LISTAR VENTAS PARA EL MÓDULO INVENTARIO
    # ============================================================
    def listar_en_rango(self, desde: date, hasta: date) -> List[Sequence]:
        """
        Devuelve tuplas (fecha, concepto, monto) para el rango indicado.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        v.fecha                                AS fecha,
                        CONCAT('Venta #', v.id)                AS concepto,
                        v.total::double precision              AS monto
                    FROM public.ventas v
                    WHERE v.fecha >= %s
                      AND v.fecha < %s::date + INTERVAL '1 day'
                      AND v.estado = 'Activa';
                    """,
                    (d1, d2),
                )
                rows = cur.fetchall()
            return list(rows)
        finally:
            cn.close()

    # ============================================================
    #  REGISTRAR VENTAS DESDE EL CARRITO
    # ============================================================
    def registrar_ventas_desde_carrito(
        self,
        items: List[CarritoItem],
        id_usuario: int,
    ) -> None:
        """
        Crea una venta por cada fecha distinta y registra:
        - Cabecera en public.ventas
        - Detalle en public.detalle_ventas
        - Actualización de stock_unidades en public.productos
        - Movimiento en public.movimientos_inventario
        """
        if not items:
            return

        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            by_date: Dict[date, List[CarritoItem]] = defaultdict(list)
            for it in items:
                # CarritoItem.fecha es date (en el modelo), si vino como str ya se convierte antes
                by_date[it.fecha].append(it)

            with cn.cursor() as cur:
                for fecha, lista in by_date.items():
                    total = sum(float(i.monto) for i in lista)

                    # 1) Cabecera de venta
                    cur.execute(
                        """
                        INSERT INTO public.ventas(
                            fecha,
                            total,
                            tipo_pago,
                            observacion,
                            id_usuario,
                            estado
                        )
                        VALUES (%s, %s, 'efectivo', 'Venta app web', %s, 'Activa')
                        RETURNING id;
                        """,
                        (fecha, float(total), int(id_usuario)),
                    )
                    id_venta = int(cur.fetchone()[0])

                    # 2) Detalles + stock + inventario
                    for item in lista:
                        pid = int(item.producto_id)
                        cantidad = int(item.cantidad)
                        monto = float(item.monto)
                        tipo = item.tipo  # 'unidad' o 'blister'

                        # Datos del producto
                        cur.execute(
                            """
                            SELECT
                                precio_compra::double precision,
                                COALESCE(unidades_por_blister, 1),
                                COALESCE(stock_unidades, 0)
                            FROM public.productos
                            WHERE id = %s;
                            """,
                            (pid,),
                        )
                        row_p = cur.fetchone()
                        if not row_p:
                            raise Exception(f"Producto id={pid} no encontrado.")

                        precio_compra, unidades_por_blister, stock_actual = row_p
                        unidades_por_blister = int(unidades_por_blister or 1)
                        stock_actual = int(stock_actual or 0)

                        # Unidades reales a descontar
                        if tipo == "unidad":
                            unidades_desc = cantidad
                        else:
                            unidades_desc = cantidad * unidades_por_blister

                        if unidades_desc > stock_actual:
                            raise Exception(
                                f"Stock insuficiente para producto id={pid}. "
                                f"Stock={stock_actual}, requerido={unidades_desc}"
                            )

                        precio_unitario = monto / max(1, cantidad)
                        costo_unit_unit = precio_compra / unidades_por_blister

                        # 2.1) Detalle
                        cur.execute(
                            """
                            INSERT INTO public.detalle_ventas(
                                id_venta,
                                id_producto,
                                tipo,
                                cantidad,
                                precio_unitario,
                                unidades_descuento,
                                costo_unitario_compra
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """,
                            (
                                id_venta,
                                pid,
                                tipo,
                                cantidad,
                                float(precio_unitario),
                                int(unidades_desc),
                                float(costo_unit_unit),
                            ),
                        )

                        # 2.2) Stock
                        cur.execute(
                            """
                            UPDATE public.productos
                            SET stock_unidades = COALESCE(stock_unidades, 0) - %s
                            WHERE id = %s;
                            """,
                            (int(unidades_desc), pid),
                        )

                        # 2.3) Movimiento inventario
                        cur.execute(
                            """
                            INSERT INTO public.movimientos_inventario(
                                id_producto,
                                tipo,
                                cantidad,
                                referencia,
                                motivo,
                                stock_resultante
                            )
                            SELECT
                                p.id,
                                'venta',
                                %s,
                                %s,
                                'Venta app web',
                                p.stock_unidades
                            FROM public.productos p
                            WHERE p.id = %s;
                            """,
                            (
                                int(unidades_desc),
                                f"V-{id_venta}",
                                pid,
                            ),
                        )

            cn.commit()

        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()
