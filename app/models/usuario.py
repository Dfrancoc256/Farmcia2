# app/models/usuario.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .base import BaseModel


@dataclass
class Usuario(BaseModel):
    """
    Modelo de usuario del sistema Farmacia 2.0.
    Compatible con repos y servicios actuales.
    """

    id: int
    username: str
    password_hash: str
    rol: Optional[str]
    activo: bool
    creado_en: datetime

    @property
    def esta_activo(self) -> bool:
        """Retorna True si el usuario está activo."""
        return bool(self.activo)

    def tiene_rol(self, rol: str) -> bool:
        """Compara el rol del usuario con el solicitado (case-insensitive)."""
        return (self.rol or "").lower() == rol.lower()
