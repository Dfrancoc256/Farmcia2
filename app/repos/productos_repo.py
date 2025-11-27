# app/repos/productos_repo.py
from typing import List, Optional

from app.core.database import conectar_bd
from app.models.producto import Producto


class ProductosRepo:
    """
    Acceso a datos de productos (PostgreSQL).
    Solo hace SQL, TODA la validación está en ProductosService.
    """

    # ==========================================================
    #   LISTAR ACTIVOS
    # ==========================================================
    def listar_activos(self) -> List[Producto]:
        """
        Devuelve todos los productos activos como una lista de entidades Producto.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        nombre,
                        precio_compra::double precision        AS compra,
                        precio_venta_unidad::double precision  AS unidad,
                        precio_venta_blister::double precision AS blister,
                        COALESCE(unidades_por_blister, 1)      AS unidades_por_blister,
                        COALESCE(stock_unidades, 0)            AS stock_unidades,
                        COALESCE(stock_actual, 0)              AS stock_actual
                    FROM public.productos
                    WHERE activo = TRUE
                    ORDER BY nombre;
                    """
                )

                rows = cur.fetchall()
        finally:
            cn.close()

        productos: List[Producto] = []
        for r in rows:
            productos.append(
                Producto(
                    id=int(r[0]),
                    nombre=r[1],
                    precio_compra=float(r[2]),
                    precio_venta_unidad=float(r[3]),
                    precio_venta_blister=float(r[4]) if r[4] is not None else None,
                    unidades_por_blister=int(r[5] or 1),
                    stock_unidades=int(r[6] or 0),
                    stock_actual=int(r[7] or 0),
                )
            )
        return productos

    # ==========================================================
    #   CREAR PRODUCTO
    # ==========================================================
    def crear_producto(
        self,
        nombre: str,
        detalle: Optional[str],
        precio_compra: float,
        precio_venta_unidad: float,
        precio_venta_blister: Optional[float],
        stock_unidades: int,
        categoria: Optional[str],
        unidades_por_blister: Optional[int],
    ) -> int:
        """
        Inserta un nuevo producto en public.productos y devuelve el id generado.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        sql = """
            INSERT INTO public.productos(
                nombre,
                detalle,
                precio_compra,
                precio_venta_unidad,
                precio_venta_blister,
                stock_unidades,
                stock_actual,
                categoria,
                activo,
                fecha_registro,
                unidades_por_blister
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), %s)
            RETURNING id;
        """

        try:
            with cn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        nombre,
                        detalle,
                        float(precio_compra),
                        float(precio_venta_unidad),
                        float(precio_venta_blister)
                        if precio_venta_blister is not None
                        else None,
                        int(stock_unidades),  # stock_unidades
                        int(stock_unidades),  # stock_actual = stock inicial
                        categoria,
                        int(unidades_por_blister)
                        if unidades_por_blister is not None
                        else None,
                    ),
                )
                new_id = int(cur.fetchone()[0])

            cn.commit()
            return new_id
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #   ACTUALIZAR PRECIOS
    # ==========================================================
    def update_precios(
        self,
        pid: int,
        precio_compra: float,
        precio_unidad: float,
        precio_blister: Optional[float],
    ) -> None:
        """
        Actualiza precios de compra / venta para un producto.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.productos
                    SET precio_compra        = %s,
                        precio_venta_unidad  = %s,
                        precio_venta_blister = %s
                    WHERE id = %s;
                    """,
                    (
                        float(precio_compra),
                        float(precio_unidad),
                        float(precio_blister) if precio_blister is not None else None,
                        int(pid),
                    ),
                )
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #   AJUSTAR STOCK + REGISTRAR MOVIMIENTO
    # ==========================================================
    def update_stock(
        self,
        pid: int,
        delta: int,
        motivo: str,
        referencia: Optional[str],
    ) -> None:
        """
        Ajusta el stock_unidades de un producto y registra el movimiento
        en public.movimientos_inventario.

        delta > 0  → entrada
        delta < 0  → salida
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                # 1) Actualizar stock
                cur.execute(
                    """
                    UPDATE public.productos
                    SET stock_unidades = COALESCE(stock_unidades, 0) + %s
                    WHERE id = %s;
                    """,
                    (int(delta), int(pid)),
                )

                # 2) Insertar movimiento de inventario
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
                        CASE WHEN %s > 0 THEN 'entrada' ELSE 'salida' END,
                        %s,
                        %s,
                        %s,
                        p.stock_unidades
                    FROM public.productos p
                    WHERE p.id = %s;
                    """,
                    (
                        int(delta),
                        abs(int(delta)),
                        referencia,
                        motivo,
                        int(pid),
                    ),
                )

            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #   ACTUALIZAR PRODUCTO COMPLETO (sin stock)
    # ==========================================================
    def update_producto(
        self,
        pid: int,
        nombre: str,
        detalle: Optional[str],
        precio_compra: float,
        precio_venta_unidad: float,
        precio_venta_blister: Optional[float],
        categoria: Optional[str],
        unidades_por_blister: Optional[int],
    ) -> None:
        """
        Actualiza los datos principales de un producto en la tabla productos.
        No realiza validaciones, eso lo hace ProductosService.
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        sql = """
            UPDATE public.productos
            SET nombre              = %s,
                detalle             = %s,
                precio_compra       = %s,
                precio_venta_unidad = %s,
                precio_venta_blister= %s,
                categoria           = %s,
                unidades_por_blister = %s
            WHERE id = %s;
        """

        try:
            with cn.cursor() as cur:
                cur.execute(
                    sql,
                    (
                        nombre,
                        detalle,
                        float(precio_compra),
                        float(precio_venta_unidad),
                        float(precio_venta_blister)
                        if precio_venta_blister is not None
                        else None,
                        categoria,
                        int(unidades_por_blister)
                        if unidades_por_blister is not None
                        else None,
                        int(pid),
                    ),
                )
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()

    # ==========================================================
    #   ELIMINAR / DESACTIVAR PRODUCTO
    # ==========================================================
    def desactivar_producto(self, pid: int) -> None:
        """
        Soft delete: marca activo = FALSE (no borra el registro).
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE public.productos
                    SET activo = FALSE
                    WHERE id = %s;
                    """,
                    (int(pid),),
                )
            cn.commit()
        except Exception:
            cn.rollback()
            raise
        finally:
            cn.close()
