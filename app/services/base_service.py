from __future__ import annotations
from contextlib import contextmanager
from typing import Optional, Tuple, Iterable, Dict, Any
from app.core.database import conectar_bd


class BaseService:
    """
    Utilidades comunes para services:
    - conexión, commit/rollback
    - detección de columnas de precio en productos
    - helpers varios
    """

    PRICE_UNIT_CANDIDATES = ["precio_venta_unidad", "precio_unidad", "precio_unitario"]
    PRICE_BLISTER_CANDIDATES = ["precio_venta_blister", "precio_blister"]

    def __init__(self, cn=None):
        self._close_after = False
        if cn is None:
            cn = conectar_bd()
            self._close_after = True
        if not cn:
            raise RuntimeError("No hay conexión a SQL Server.")
        self.cn = cn

    def close(self):
        if self._close_after and self.cn:
            self.cn.close()
            self.cn = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    # -------------------------------
    # DB helpers
    # -------------------------------
    @contextmanager
    def tx(self):
        """
        Contexto de transacción:
        with service.tx():
            ...
        """
        try:
            yield
            self.cn.commit()
        except Exception:
            self.cn.rollback()
            raise

    def price_columns(self) -> Tuple[str, Optional[str]]:
        """
        Detecta nombres de columnas de precios en dbo.productos.
        Devuelve: (col_unidad, col_blister|None)
        """
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='productos'
            """)
            cols = {r[0].lower() for r in cur.fetchall()}

        pu = next((c for c in self.PRICE_UNIT_CANDIDATES if c in cols), None)
        pb = next((c for c in self.PRICE_BLISTER_CANDIDATES if c in cols), None)

        if not pu:
            raise RuntimeError(
                "No se encontró columna de precio por unidad en dbo.productos. "
                "Crea 'precio_venta_unidad' (o 'precio_unidad'/'precio_unitario')."
            )
        return pu, pb

    # -------------------------------
    # Misceláneos
    # -------------------------------
    @staticmethod
    def as_dict_row(row: Iterable[Any], cols: Iterable[str]) -> Dict[str, Any]:
        return dict(zip(cols, row))
