# app/models/detalle_venta.py
from __future__ import annotations

from dataclasses import dataclass

from .base import BaseModel


@dataclass
class DetalleVenta(BaseModel):
    """
    Representa una fila de detalle de venta (dbo.detalle_ventas).
    Compatibilidad total con tu SQL Server y VentasRepo.
    """
    id: int
    id_venta: int
    id_producto: int
    tipo: str                     # 'unidad' o 'blister'
    cantidad: int                 # cantidad de items vendidos
    precio_unitario: float        # precio por unidad o blister
    unidades_descuento: int | None = None   # unidades reales descontadas del stock
    costo_unitario_compra: float | None = None  # costo unitario según precio compra

    @property
    def subtotal(self) -> float:
        """Subtotal calculado (cantidad * precio_unitario)."""
        return float(self.cantidad) * float(self.precio_unitario)
