# app/services/dashboard_service.py
from datetime import date
from typing import Dict

import pandas as pd

from app.repos.dashboard_repo import DashboardRepo


class DashboardService:
    """
    Lógica de negocio para el dashboard de inicio.
    Se encarga de preparar DataFrames, validar datos y
    delegar el SQL al DashboardRepo.
    """

    def __init__(self) -> None:
        self.repo = DashboardRepo()

    # ==========================================================
    #   RESUMEN GENERAL (KPIs)
    # ==========================================================
    def get_resumen(self, desde: date, hasta: date) -> Dict[str, float]:
        """
        Devuelve un diccionario con KPIs:
        - productos_activos
        - stock_total
        - vendido_rango
        - ganancia_rango
        - fiado_pendiente
        """
        return self.repo.get_resumen(desde, hasta)

    # ==========================================================
    #   INVENTARIO COMPLETO (PARA TABLA)
    # ==========================================================
    def get_inventario_df(self) -> pd.DataFrame:
        """
        Devuelve el inventario completo como DataFrame.
        Cada fila representa un producto.
        """
        rows = self.repo.get_inventario_completo()
        cols = [
            "Id",
            "Código",
            "Producto",
            "Stock (unidades)",
            "Precio unidad",
            "Precio blister",
            "Unidades por blister",
        ]

        if not rows:
            return pd.DataFrame(columns=cols)

        return pd.DataFrame(rows, columns=cols)

    # ==========================================================
    #   TOP MÁS VENDIDOS
    # ==========================================================
    def get_top_mas_vendidos_df(
        self, desde: date, hasta: date, top_n: int = 5
    ) -> pd.DataFrame:
        """
        Devuelve top_n productos más vendidos dentro del rango.
        """
        rows = self.repo.get_top_productos_vendidos(desde, hasta, top_n)
        cols = ["Id", "Código", "Producto", "Unidades vendidas"]

        if not rows:
            return pd.DataFrame(columns=cols)

        return pd.DataFrame(rows, columns=cols)

    # ==========================================================
    #   PRODUCTOS CON STOCK CRÍTICO
    # ==========================================================
    def get_productos_bajo_stock_df(self, threshold: int = 1) -> pd.DataFrame:
        """
        Devuelve productos cuyo stock es ≤ threshold.
        """
        rows = self.repo.get_productos_stock_critico(threshold)
        cols = [
            "Id",
            "Código",
            "Producto",
            "Stock (unidades)",
            "Precio unidad",
            "Precio blister",
            "Unidades por blister",
        ]

        if not rows:
            return pd.DataFrame(columns=cols)

        return pd.DataFrame(rows, columns=cols)
