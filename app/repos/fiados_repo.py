# app/repos/fiados_repo.py
from datetime import date
from typing import List, Tuple, Optional

from app.core.database import conectar_bd


class FiadosRepo:
    """
    Acceso a datos de fiados en PostgreSQL.

    Aquí solo hay SQL “puro”. Toda la lógica de validaciones y reglas
    de negocio debe ir en FiadosService.
    """

    # ==========================================================
    #  LISTAR EN RANGO
    # ==========================================================
    def listar_en_rango(self, d1: str, d2: str) -> List[Tuple]:
        """
        Devuelve fiados dentro del rango [d1, d2] (ambos inclusive).

        Parámetros:
            d1: fecha inicial en formato 'YYYY-MM-DD'
            d2: fecha final  en formato 'YYYY-MM-DD'

        Retorna una lista de tuplas:
            (id, fecha_str, cliente, producto, cantidad, monto, estado)
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        f.id,
                        to_char(f.fecha, 'YYYY-MM-DD HH24:MI') AS fecha,
                        f.nombre_cliente,
                        f.producto,
                        f.cantidad,
                        f.monto::double precision            AS monto,
                        COALESCE(f.estado, 'Pendiente')      AS estado
                    FROM public.fiados f
                    WHERE f.fecha >= %s
                      AND f.fecha < %s::date + INTERVAL '1 day'
                    ORDER BY f.fecha;
                    """,
                    (d1, d2),
                )
                return cur.fetchall()
        finally:
            cn.close()

    def listar_rango(self, d1: date, d2: date) -> List[Tuple]:
        """
        Alias usado por algunos servicios que envían objetos date.

        Convierte d1 y d2 a 'YYYY-MM-DD' y delega en listar_en_rango.
        """
        d1_str = d1.strftime("%Y-%m-%d")
        d2_str = d2.strftime("%Y-%m-%d")
        return self.listar_en_rango(d1_str, d2_str)

    # ==========================================================
    #  LISTAR PENDIENTES
    # ==========================================================
    def listar_pendientes(self) -> List[Tuple]:
        """
        Devuelve fiados que aún no están pagados.

        Tuplas:
            (id, cliente, producto, monto, fecha)
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        f.id,
                        f.nombre_cliente,
                        f.producto,
                        f.monto::double precision AS monto,
                        f.fecha
                    FROM public.fiados f
                    WHERE f.estado IS DISTINCT FROM 'Pagado'
                    ORDER BY f.fecha;
                    """
                )
                return cur.fetchall()
        finally:
            cn.close()

    # ==========================================================
    #  CREAR FIADO
    # ==========================================================
    def crear_fiado(
        self,
        nombre_cliente: str,
        telefono: Optional[str],
        id_producto: int,
        cantidad: int,
        monto: float,
        fecha: date,
    ) -> int:
        """
        Inserta un nuevo fiado, descuenta stock y registra movimiento.

        Devuelve:
            id_fiado (int) generado por la BD.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                # 1) Obtener datos del producto
                cur.execute(
                    """
                    SELECT
                        nombre,
                        COALESCE(stock_unidades, 0)
                    FROM public.productos
                    WHERE id = %s;
                    """,
                    (id_producto,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(f"Producto id={id_producto} no encontrado.")

                nombre_producto, stock_actual = row
                stock_actual = int(stock_actual or 0)

                if cantidad > stock_actual:
                    raise RuntimeError(
                        f"Stock insuficiente para producto id={id_producto}. "
                        f"Stock={stock_actual}, requerido={cantidad}"
                    )

                # 2) Insertar fiado
                cur.execute(
                    """
                    INSERT INTO public.fiados(
                        id_producto,
                        nombre_cliente,
                        telefono,
                        producto,
                        cantidad,
                        monto,
                        fecha,
                        estado
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pendiente')
                    RETURNING id;
                    """,
                    (
                        id_producto,
                        nombre_cliente,
                        telefono,
                        nombre_producto,
                        cantidad,
                        float(monto),
                        fecha,
                    ),
                )
                id_fiado = int(cur.fetchone()[0])

                # 3) Descontar stock del producto
                cur.execute(
                    """
                    UPDATE public.productos
                    SET stock_unidades = COALESCE(stock_unidades, 0) - %s
                    WHERE id = %s;
                    """,
                    (cantidad, id_producto),
                )

                # 4) Registrar movimiento en inventario
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
                        'fiado',
                        %s,
                        %s,
                        'Fiado registrado',
                        p.stock_unidades
                    FROM public.productos p
                    WHERE p.id = %s;
                    """,
                    (
                        cantidad,
                        f"F-{id_fiado}",
                        id_producto,
                    ),
                )

            cn.commit()
            return id_fiado

        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #  PAGAR FIADO
    # ==========================================================
    def pagar_fiado(self, fiado_id: int) -> None:
        """
        Marca un fiado como pagado y registra la fecha de pago.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.fiados
                    SET estado = 'Pagado',
                        fecha_pago = NOW()
                    WHERE id = %s;
                    """,
                    (fiado_id,),
                )
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()
