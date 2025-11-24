# app/models/gasto.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseModel


@dataclass
class Gasto(BaseModel):
    """
    Representa un gasto registrado en el sistema.
    Compatible con las columnas de dbo.gastos.
    """
    id: int
    descripcion: str
    monto: float
    fecha: Optional[datetime]
    categoria: Optional[str]
