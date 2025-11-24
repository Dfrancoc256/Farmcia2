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
    ) -> int:
        """
        Valida datos y delega al repo la creación del producto.
        Se alinea con la tabla 'productos' en PostgreSQL:
        - nombre
        - detalle
        - precio_compra
        - precio_venta_unidad
        - precio_venta_blister
        - unidades_por_blister
        - stock_unidades
        - categoria
        """

        nombre = (nombre or "").strip()
        detalle = (detalle or "").strip() or None
        categoria = (categoria or "").strip() or None

        # ---------- Validaciones básicas ----------
        if not nombre:
            raise ValueError("El nombre del producto no puede estar vacío.")

        if precio_compra < 0:
            raise ValueError("El precio de compra no puede ser negativo.")

        if precio_venta_unidad <= 0:
            raise ValueError("El precio de venta por unidad debe ser mayor a 0.")

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
    ) -> None:
        """
        Valida y delega a repo.update_precios().
        Se asume que el repositorio actualiza:
        - precio_compra
        - precio_venta_unidad
        - precio_venta_blister
        """
        if precio_compra < 0:
            raise ValueError("Precio de compra inválido (no puede ser negativo).")

        if precio_unidad <= 0:
            raise ValueError("Precio por unidad inválido (debe ser > 0).")

        if precio_blister is not None and precio_blister <= 0:
            raise ValueError("Precio por blister inválido (si se usa, debe ser > 0).")

        self.repo.update_precios(pid, precio_compra, precio_unidad, precio_blister)

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
        """
        Lógica para ajustar inventario (entrada/salida) y registrar
        el movimiento en movimientos_inventario.

        - delta > 0  -> entrada
        - delta < 0  -> salida
        """
        if delta == 0:
            raise ValueError("El ajuste de stock no puede ser 0.")

        motivo = (motivo or "").strip() or "Ajuste manual"
        referencia = (referencia or "").strip() or None

        self.repo.update_stock(pid, delta, motivo, referencia)
