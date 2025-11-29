# app/services/productos_service.py
from __future__ import annotations

from typing import List, Optional

from app.repos.productos_repo import ProductosRepo
from app.models.producto import Producto


class ProductosService:
    """
    Lógica de negocio para productos.
    No ejecuta SQL directo: delega a ProductosRepo.
    """

    def __init__(self):
        self.repo = ProductosRepo()

    # ==========================================================
    #   LISTAR Y BUSCAR
    # ==========================================================
    def listar_activos(self) -> List[Producto]:
        """Devuelve lista de entidades Producto activas."""
        return self.repo.listar_activos()

    def buscar_activos(self, q: str) -> List[Producto]:
        """Búsqueda simple por nombre (se puede mejorar después)."""
        q = (q or "").strip().lower()
        if not q:
            return self.repo.listar_activos()

        productos = self.repo.listar_activos()
        return [p for p in productos if q in p.nombre.lower()]

    # ==========================================================
    #   OBTENER UNO
    # ==========================================================
    def obtener_por_id(self, pid: int) -> Optional[Producto]:
        productos = self.repo.listar_activos()
        for p in productos:
            if p.id == pid:
                return p
        return None

    # ==========================================================
    #   CREAR PRODUCTO (LÓGICA)
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
        precio_venta_caja: float = 0.0,
    ) -> int:
        """
        Valida datos y delega al repo la creación del producto.
        """

        nombre = (nombre or "").strip()
        detalle = (detalle or "").strip() or None
        categoria = (categoria or "").strip() or None

        # ---------- Validaciones básicas ----------
        if not nombre:
            raise ValueError("El nombre del producto no puede estar vacío.")

        if precio_compra < 0:
            raise ValueError("El precio de compra no puede ser negativo.")

        if stock_unidades < 0:
            raise ValueError("El stock inicial no puede ser negativo.")

        # No permitimos precios negativos
        if precio_venta_unidad < 0:
            raise ValueError("El precio de venta por unidad no puede ser negativo.")
        if precio_venta_blister is not None and precio_venta_blister < 0:
            raise ValueError("El precio de venta por blister no puede ser negativo.")
        if precio_venta_caja < 0:
            raise ValueError("El precio de venta por caja no puede ser negativo.")

        # ---------- Lógica de blister ----------
        if precio_venta_blister is not None:
            if not unidades_por_blister or unidades_por_blister <= 0:
                raise ValueError(
                    "Si defines un precio por blister, debes indicar "
                    "unidades_por_blister mayor a 0."
                )

        if unidades_por_blister is not None and unidades_por_blister < 0:
            raise ValueError("Las unidades por blister no pueden ser negativas.")

        # ---------- Regla de negocio: al menos un precio > compra ----------
        max_precio_venta = max(
            precio_venta_unidad or 0.0,
            precio_venta_blister or 0.0,
            precio_venta_caja or 0.0,
        )
        if max_precio_venta <= precio_compra:
            raise ValueError(
                "Debe existir al menos un precio de venta (unidad, blister o caja) "
                "mayor al precio de compra."
            )

        # Delegar al repositorio
        return self.repo.crear_producto(
            nombre=nombre,
            detalle=detalle,
            precio_compra=precio_compra,
            precio_venta_unidad=precio_venta_unidad,
            precio_venta_blister=precio_venta_blister,
            stock_unidades=stock_unidades,
            categoria=categoria,
            unidades_por_blister=unidades_por_blister,
            precio_venta_caja=precio_venta_caja,
        )

    # ==========================================================
    #   ACTUALIZAR PRECIOS
    # ==========================================================
    def actualizar_precios(
        self,
        pid: int,
        precio_compra: float,
        precio_unidad: float,
        precio_blister: Optional[float] = None,
        precio_caja: float = 0.0,
    ) -> None:
        if precio_compra < 0:
            raise ValueError("Precio de compra inválido (no puede ser negativo).")

        # No permitimos precios negativos
        if precio_unidad < 0:
            raise ValueError("Precio por unidad inválido (no puede ser negativo).")
        if precio_blister is not None and precio_blister < 0:
            raise ValueError("Precio por blister inválido (no puede ser negativo).")
        if precio_caja < 0:
            raise ValueError("Precio por caja inválido (no puede ser negativo).")

        max_precio_venta = max(
            precio_unidad or 0.0,
            precio_blister or 0.0,
            precio_caja or 0.0,
        )
        if max_precio_venta <= precio_compra:
            raise ValueError(
                "Debe existir al menos un precio de venta (unidad, blister o caja) "
                "mayor al precio de compra."
            )

        self.repo.update_precios(
            pid,
            precio_compra,
            precio_unidad,
            precio_blister,
            precio_caja,
        )

    # ==========================================================
    #   AJUSTAR STOCK
    # ==========================================================
    def ajustar_stock(
        self,
        pid: int,
        delta: int,
        motivo: str = "",
        referencia: Optional[str] = None,
    ) -> None:
        if delta == 0:
            raise ValueError("El ajuste de stock no puede ser 0.")

        motivo = (motivo or "").strip() or "Ajuste manual"
        referencia = (referencia or "").strip() or None

        self.repo.update_stock(pid, delta, motivo, referencia)

    # ==========================================================
    #   ACTUALIZAR PRODUCTO COMPLETO (sin stock)
    # ==========================================================
    def actualizar_producto(
        self,
        pid: int,
        nombre: str,
        detalle: Optional[str],
        precio_compra: float,
        precio_venta_unidad: float,
        precio_venta_blister: Optional[float],
        categoria: Optional[str],
        unidades_por_blister: Optional[int],
        precio_venta_caja: float = 0.0,
    ) -> None:
        """
        Actualiza los datos principales de un producto
        (sin tocar stock_unidades).
        """
        nombre = (nombre or "").strip()
        detalle = (detalle or "").strip() or None
        categoria = (categoria or "").strip() or None

        if not nombre:
            raise ValueError("El nombre del producto no puede estar vacío.")

        if precio_compra < 0:
            raise ValueError("El precio de compra no puede ser negativo.")

        # No permitimos precios negativos
        if precio_venta_unidad < 0:
            raise ValueError("El precio de venta por unidad no puede ser negativo.")
        if precio_venta_blister is not None and precio_venta_blister < 0:
            raise ValueError("El precio por blister no puede ser negativo.")
        if precio_venta_caja < 0:
            raise ValueError("El precio de venta por caja no puede ser negativo.")

        if precio_venta_blister is not None:
            if not unidades_por_blister or unidades_por_blister <= 0:
                raise ValueError(
                    "Si defines un precio por blister, debes indicar "
                    "unidades_por_blister mayor a 0."
                )

        if unidades_por_blister is not None and unidades_por_blister < 0:
            raise ValueError("Las unidades por blister no pueden ser negativas.")

        max_precio_venta = max(
            precio_venta_unidad or 0.0,
            precio_venta_blister or 0.0,
            precio_venta_caja or 0.0,
        )
        if max_precio_venta <= precio_compra:
            raise ValueError(
                "Debe existir al menos un precio de venta (unidad, blister o caja) "
                "mayor al precio de compra."
            )

        self.repo.update_producto(
            pid=pid,
            nombre=nombre,
            detalle=detalle,
            precio_compra=precio_compra,
            precio_venta_unidad=precio_venta_unidad,
            precio_venta_blister=precio_venta_blister,
            categoria=categoria,
            unidades_por_blister=unidades_por_blister,
            precio_venta_caja=precio_venta_caja,
        )

    # 👉 ALIAS compatible con page_carrito.py
    def update_producto_completo(
        self,
        pid: int,
        nombre: str,
        detalle: Optional[str],
        precio_compra: float,
        precio_unidad: float,
        precio_blister: Optional[float],
        categoria: Optional[str],
        unidades_blister: Optional[int] = None,
        unidades_por_blister: Optional[int] = None,
        precio_caja: float = 0.0,
    ) -> None:
        """
        Alias para mantener compatibilidad con la llamada que hace page_carrito.py,
        que usa los nombres 'precio_unidad', 'precio_blister' y 'unidades_blister'.
        """
        if unidades_por_blister is None:
            unidades_por_blister = unidades_blister

        self.actualizar_producto(
            pid=pid,
            nombre=nombre,
            detalle=detalle,
            precio_compra=precio_compra,
            precio_venta_unidad=precio_unidad,
            precio_venta_blister=precio_blister,
            categoria=categoria,
            unidades_por_blister=unidades_por_blister,
            precio_venta_caja=precio_caja,
        )

    # ==========================================================
    #   ELIMINAR / DESACTIVAR PRODUCTO
    # ==========================================================
    def eliminar_producto(self, pid: int) -> None:
        """Soft delete: marca activo = FALSE."""
        self.repo.desactivar_producto(pid)

    # Alias para que funcione productos_service.desactivar_producto(...)
    def desactivar_producto(self, pid: int) -> None:
        self.eliminar_producto(pid)
