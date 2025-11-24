from __future__ import annotations
from typing import Optional, Dict, Any

from app.repos.users_repo import get_user_by_username
from app.core.auth import verify_password


class AuthService:
    """
    Servicio de autenticación.
    Encapsula el flujo de login sin exponer SQL.
    """

    @staticmethod
    def login(username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Retorna un diccionario con los datos del usuario
        si las credenciales son correctas; de lo contrario, None.
        """

        # 1. Buscar usuario en la BD
        user = get_user_by_username(username)
        if not user:
            return None

        # 2. Verificar si está activo
        if not user.get("activo", True):
            return None

        # 3. Verificar contraseña hasheada
        if verify_password(password, user["password_hash"]):
            return {
                "id": user["id"],
                "username": user["username"],
                "rol": user.get("rol"),
                "activo": user.get("activo", True),
            }

        return None
