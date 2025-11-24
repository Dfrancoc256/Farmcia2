# app/models/base.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class BaseModel:
    """
    Clase base para los modelos de dominio.

    - Permite convertir cualquier dataclass hijo a dict con .to_dict(),
      útil para debug, logs o serializar a JSON.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dataclass en dict (útil para debug o JSON)."""
        return asdict(self)
