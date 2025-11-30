from dataclasses import dataclass
from typing import Optional

from .base import BaseModel


@dataclass
class Producto(BaseModel):
    """
    Entidad de dominio para un producto de la farmacia.
    Representa la fila de public.productos.
    """

    id: int
    nombre: str
    precio_compra: float
    precio_venta_unidad: float
    precio_venta_blister: Optional[float]
    unidades_por_blister: int
    stock_unidades: int
    stock_actual: int
    precio_venta_caja: float

    # Nuevos campos opcionales (no rompen llamadas existentes)
    detalle: Optional[str] = None
    categoria: Optional[str] = None
    presentacion: Optional[str] = None  # Jarabe / Gotero / Tableta / Otro, etc.
