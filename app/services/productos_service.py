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
        """
        Búsqueda simple mejorada:
        - Busca en nombre, detalle, categoría y presentación.
        """
        q = (q or "").strip().lower()
        if not q:
            return self.repo.listar_activos()

        productos = self.repo.listar_activos()
        resultado: List[Producto] = []

        for p in productos:
            texto = " ".join(
                [
                    p.nombre or "",
                    p.detalle or "",
                    p.categoria or "",
                    getattr(p, "presentacion", "") or "",
                ]
            ).lower()
            if q in texto:
                resultado.append(p)

        return resultado

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
        presentacion: Optional[str],
        precio_compra: float,
        precio_venta_unidad: float,
        precio_venta_blister: Optional[float],
        stock_unidades: int,
        categoria: Optional[str],
        unidades_por_blister: Optional[int],
        precio_venta_caja: float,
    ) -> int:
        """
        Valida datos y delega al repo la creación del producto.

        Reglas:
        - Si hay precio de compra (>0), debe existir al menos
          un precio de venta (unidad, blister o caja) > 0.
        - NO se exige que el precio de venta sea mayor al de compra.
        """

        nombre = (nombre or "").strip()
        detalle = (detalle or "").strip() or None
        presentacion = (presentacion or "").strip() or None
        categoria = (categoria or "").strip() or None

        # ---------- Validaciones básicas ----------
        if not nombre:
            raise ValueError("El nombre del producto no puede estar vacío.")

        if precio_compra < 0:
            raise ValueError("El precio de compra no puede ser negativo.")

        # precios de venta no pueden ser negativos
        if precio_venta_unidad < 0:
            raise ValueError("El precio de venta por unidad no puede ser negativo.")

        if precio_venta_blister is not None and precio_venta_blister < 0:
            raise ValueError("El precio de venta por blister no puede ser negativo.")

        if precio_venta_caja < 0:
            raise ValueError("El precio de venta por caja no puede ser negativo.")

        if stock_unidades < 0:
            raise ValueError("El stock inicial no puede ser negativo.")

        # ---------- Lógica de blister ----------
        if precio_venta_blister is not None:
            if precio_venta_blister <= 0:
                raise ValueError("El precio por blister debe ser mayor a 0.")
            if not unidades_por_blister or unidades_por_blister <= 0:
                raise ValueError(
                    "Si defines un precio por blister, debes indicar "
                    "unidades_por_blister mayor a 0."
                )

        if unidades_por_blister is not None and unidades_por_blister < 0:
            raise ValueError("Las unidades por blister no pueden ser negativas.")

        # ---------- REGLA NUEVA (creación) ----------
        # Si hay precio de compra (>0), tiene que haber al menos
        # UN precio de venta > 0 (unidad, blister o caja)
        if precio_compra > 0:
            hay_precio_venta = any(
                [
                    precio_venta_unidad > 0,
                    (precio_venta_blister or 0) > 0,
                    precio_venta_caja > 0,
                ]
            )
            if not hay_precio_venta:
                raise ValueError(
                    "Si existe un precio de compra, debe haber al menos un "
                    "precio de venta (unidad, blister o caja) mayor que 0."
                )

        # Delegar al repositorio
        return self.repo.crear_producto(
            nombre=nombre,
            detalle=detalle,
            presentacion=presentacion,
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

        # ---------- REGLA NUEVA (actualización precios) ----------
        # Si hay precio de compra (>0), debe existir al menos un precio de venta > 0
        if precio_compra > 0:
            hay_precio_venta = any(
                [
                    precio_unidad > 0,
                    (precio_blister or 0) > 0,
                    precio_caja > 0,
                ]
            )
            if not hay_precio_venta:
                raise ValueError(
                    "Si existe un precio de compra, debe haber al menos un "
                    "precio de venta (unidad, blister o caja) mayor que 0."
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
        presentacion: Optional[str],
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
        presentacion = (presentacion or "").strip() or None
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

        # ---------- REGLA NUEVA (actualizar producto completo) ----------
        if precio_compra > 0:
            hay_precio_venta = any(
                [
                    precio_venta_unidad > 0,
                    (precio_venta_blister or 0) > 0,
                    precio_venta_caja > 0,
                ]
            )
            if not hay_precio_venta:
                raise ValueError(
                    "Si existe un precio de compra, debe haber al menos un "
                    "precio de venta (unidad, blister o caja) mayor que 0."
                )

        self.repo.update_producto(
            pid=pid,
            nombre=nombre,
            detalle=detalle,
            presentacion=presentacion,
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
        presentacion: Optional[str],
        categoria: Optional[str],
        precio_compra: float,
        precio_unidad: float,
        precio_blister: Optional[float],
        unidades_blister: Optional[int] = None,
        unidades_por_blister: Optional[int] = None,
        precio_caja: float = 0.0,
    ) -> None:
        """
        Alias para mantener compatibilidad con la llamada que hace page_carrito.py,
        que usa los nombres 'precio_unidad', 'precio_blister' y 'unidades_blister',
        y ahora también maneja 'presentacion'.
        """
        if unidades_por_blister is None:
            unidades_por_blister = unidades_blister

        self.actualizar_producto(
            pid=pid,
            nombre=nombre,
            detalle=detalle,
            presentacion=presentacion,
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
