# app/models/fiado.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseModel


@dataclass
class Fiado(BaseModel):
    id: int
    nombre_cliente: str
    telefono: Optional[str]
    producto: str
    cantidad: int
    monto: float
    fecha: Optional[datetime]
    estado: Optional[str]
    fecha_pago: Optional[datetime]
    id_venta: Optional[int]

    @property
    def esta_pagado(self) -> bool:
        return (self.estado or "").lower() == "pagado"

    @property
    def esta_pendiente(self) -> bool:
        return not self.esta_pagado
