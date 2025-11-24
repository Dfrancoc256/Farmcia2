# app/models/venta.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from .base import BaseModel


@dataclass
class CarritoItem(BaseModel):
    """
    Item que viene desde la UI del carrito.

    IMPORTANTE:
    Las claves del dict guardado en st.session_state["carrito"]
    deben coincidir *exactamente* con estos nombres de atributos,
    porque los services hacen CarritoItem(**item).
    """
    producto_id: int          # ID del producto en la BD
    nombre: str               # Nombre del producto (solo para mostrar)
    tipo: str                 # 'unidad' o 'blister'
    cantidad: int             # Cantidad vendida
    monto: float              # Monto total de ese ítem (cantidad * precio)
    fecha: date               # Fecha de la venta (yyyy-mm-dd)


@dataclass
class Venta(BaseModel):
    """
    Representa la cabecera de una venta (tabla ventas en la BD).
    """
    id: Optional[int]
    fecha: datetime
    total: float
    tipo_pago: str = "efectivo"
    observacion: Optional[str] = None
