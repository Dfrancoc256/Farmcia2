# app/services/ventas_service.py
from typing import List, Dict

import pandas as pd

from app.models.venta import CarritoItem
from app.repos.productos_repo import ProductosRepo
from app.repos.ventas_repo import VentasRepo


class VentasService:
    """
    Capa de negocio para el flujo de:
    - Productos / Carrito
    - Registro de ventas
    """

    def __init__(self) -> None:
        self.productos_repo = ProductosRepo()
        self.ventas_repo = VentasRepo()

    # =====================================================
    #   PRODUCTOS → DataFrame para la UI (ventas)
    # =====================================================
    def get_productos_activos_df(self) -> pd.DataFrame:
        productos = self.productos_repo.listar_activos()
        if not productos:
            return pd.DataFrame(
                columns=[
                    "id",
                    "Nombre",
                    "Detalle",
                    "Compra",
                    "Unidad",
                    "Blister",
                    "Caja",
                    "UnidadesBlister",
                    "StockUnidades",
                    "Categoria",
                ]
            )

        rows = []
        for p in productos:
            rows.append(
                {
                    "id": p.id,
                    "Nombre": p.nombre,
                    "Detalle": getattr(p, "detalle", None),
                    "Compra": p.precio_compra,
                    "Unidad": p.precio_venta_unidad,
                    "Blister": p.precio_venta_blister,
                    "Caja": getattr(p, "precio_venta_caja", 0.0),
                    "UnidadesBlister": p.unidades_por_blister,
                    "StockUnidades": p.stock_unidades,
                    "Categoria": getattr(p, "categoria", None),
                }
            )

        return pd.DataFrame(rows)

    # =====================================================
    #   REGISTRO DE VENTAS (CARRITO COMPLETO)
    # =====================================================
    def registrar_ventas_desde_carrito(
        self,
        carrito_raw: List[Dict],
        id_usuario: int,
    ) -> None:
        """
        Convierte los dicts del carrito (UI Streamlit)
        en CarritoItem y los envía al Repo.

        Validaciones:
        - producto válido
        - cantidad > 0
        - tipo válido
        - stock suficiente
        - monto > 0
        """

        # Obtener productos activos (para validaciones)
        productos = {p.id: p for p in self.productos_repo.listar_activos()}

        items: List[CarritoItem] = []

        for it in carrito_raw:

            pid = int(it["producto_id"])
            if pid not in productos:
                raise ValueError(f"Producto ID={pid} no existe o no está activo.")

            prod = productos[pid]

            cantidad = int(it["cantidad"])
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor que cero.")

            tipo = str(it["tipo"]).lower()
            if tipo not in ("unidad", "blister", "caja"):
                raise ValueError("Tipo de venta inválido (unidad/blister/caja).")

            # ===============================
            #   VALIDACIÓN DE STOCK
            # ===============================
            if tipo == "unidad":
                unidades_requeridas = cantidad
            elif tipo == "blister":
                unidades_requeridas = cantidad * prod.unidades_por_blister
            else:  # tipo == "caja"
                # Caja equivale a una unidad en stock_unidades
                unidades_requeridas = cantidad

            if unidades_requeridas > prod.stock_unidades:
                raise ValueError(
                    f"Stock insuficiente para {prod.nombre}. "
                    f"Disponible: {prod.stock_unidades}, requerido: {unidades_requeridas}"
                )

            monto = float(it["monto"])
            if monto <= 0:
                raise ValueError("El monto debe ser mayor que cero.")

            fecha = pd.to_datetime(it["fecha"]).date()

            # ===============================
            #   CREAR ITEM SEGURO
            # ===============================
            items.append(
                CarritoItem(
                    producto_id=pid,
                    nombre=prod.nombre,
                    tipo=tipo,
                    cantidad=cantidad,
                    monto=monto,
                    fecha=fecha,
                )
            )

        # ===============================
        #   Enviar al repo (transacción SQL)
        # ===============================
        self.ventas_repo.registrar_ventas_desde_carrito(items, id_usuario)
