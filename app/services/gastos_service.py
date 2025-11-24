# app/services/gastos_service.py
from __future__ import annotations

from datetime import date
from typing import List, Any, Tuple

import pandas as pd

from app.repos.gastos_repo import GastosRepo
from app.core.database import conectar_bd


class GastosService:
    """
    Lógica de negocio para gastos.
    No ejecuta SQL directo: delega a GastosRepo o usa conexiones controladas.
    """

    def __init__(self) -> None:
        self.repo = GastosRepo()

    # ==========================================================
    #   CREAR GASTO
    # ==========================================================
    def crear_gasto(
        self,
        descripcion: str,
        monto: float,
        fecha: date,
        categoria: str | None,
    ) -> None:
        """
        Valida los datos y delega al repositorio.

        Firma usada desde la UI:
            gastos_service.crear_gasto(desc, monto, fecha, categoria)
        """
        desc = (descripcion or "").strip()

        if not desc:
            raise ValueError("La descripción del gasto es obligatoria.")

        # monto → float válido
        try:
            monto_float = float(monto)
        except (TypeError, ValueError):
            raise ValueError("El monto del gasto no es válido.")

        if monto_float <= 0:
            raise ValueError("El monto del gasto debe ser mayor que cero.")

        # fecha debe ser un date
        if not isinstance(fecha, date):
            raise ValueError("La fecha del gasto no es válida.")

        # Categoría NO obligatoria
        cat = (categoria or "").strip() or None

        # Delegamos al repo (SQL)
        self.repo.crear_gasto(desc, monto_float, fecha, cat)

    # ==========================================================
    #   LISTAR EN RANGO (crudo, desde la BD)
    # ==========================================================
    def listar_en_rango(self, d1: str, d2: str) -> List[Tuple[Any, ...]]:
        """
        Devuelve tuplas:
        (fecha, descripcion, monto)
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la BD.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        fecha,
                        descripcion,
                        monto::double precision
                    FROM public.gastos
                    WHERE fecha >= %s
                      AND fecha < %s::date + INTERVAL '1 day'
                    ORDER BY fecha;
                    """,
                    (d1, d2),
                )
                return cur.fetchall()
        finally:
            cn.close()

    # ==========================================================
    #   RESUMEN PARA LA VISTA: DF + TOTAL
    # ==========================================================
    def get_gastos_y_total(
        self,
        desde: date,
        hasta: date,
    ) -> Tuple[pd.DataFrame, float]:
        """
        Devuelve:
        - df_gastos: DataFrame con columnas [Fecha, Descripción, Monto (Q)]
        - total_rango: float con la suma del monto en el rango
        """

        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        filas = self.listar_en_rango(d1, d2)

        if not filas:
            df = pd.DataFrame(columns=["Fecha", "Descripción", "Monto (Q)"])
            return df, 0.0

        df = pd.DataFrame(filas, columns=["fecha", "descripcion", "monto"])

        # Normalizar fecha (por si vienen datetime)
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").dt.strftime(
            "%Y-%m-%d"
        )

        total = float(df["monto"].sum())

        df_show = df.rename(
            columns={
                "fecha": "Fecha",
                "descripcion": "Descripción",
                "monto": "Monto (Q)",
            }
        )

        return df_show, total
