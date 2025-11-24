# app/models/__init__.py

from .producto import Producto
from .usuario import Usuario
from .venta import Venta, CarritoItem
from .detalle_venta import DetalleVenta
from .fiado import Fiado
from .gasto import Gasto
from .movimiento_inventario import MovimientoInventario

__all__ = [
    "Producto",
    "Usuario",
    "Venta",
    "CarritoItem",
    "DetalleVenta",
    "Fiado",
    "Gasto",
    "MovimientoInventario",
]
