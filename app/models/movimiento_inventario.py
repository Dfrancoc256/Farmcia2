# app/models/movimiento_inventario.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseModel


@dataclass
class MovimientoInventario(BaseModel):
    """
    Representa un movimiento en el inventario.
    Cada movimiento refleja una modificación al stock:

    - tipo: 'entrada', 'salida', 'venta', 'fiado', 'ajuste', etc.
    - cantidad: unidades afectadas (siempre en unidades)
    - referencia: texto como "V-10", "F-3" para enlazar con ventas/fiados
    - motivo: descripción más detallada del movimiento
    - fecha: fecha del movimiento (GETDATE() / NOW())
    - stock_resultante: stock final luego del movimiento
    """

    id: int
    id_producto: int
    tipo: str
    cantidad: int
    referencia: Optional[str]
    motivo: Optional[str]
    fecha: Optional[datetime]
    stock_resultante: Optional[int]
