# app/services/inventario_service.py
from __future__ import annotations

from datetime import date
from typing import Tuple, Dict, List, Any

import pandas as pd

from app.repos.inventario_repo import InventarioRepo
from app.repos.fiados_repo import FiadosRepo
from app.repos.gastos_repo import GastosRepo


class InventarioService:
    """
    Lógica de negocio para el panel de Inventario.
    Arma el DataFrame de movimientos y calcula totales.
    """

    def __init__(self) -> None:
        self.inv_repo = InventarioRepo()
        self.fiados_repo = FiadosRepo()
        self.gastos_repo = GastosRepo()

    def get_movimientos_y_totales(
        self,
        desde: date,
        hasta: date,
    ) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """
        Devuelve:
        - df_mov: DataFrame con columnas [fecha, tipo, concepto, entrada, salida]
        - totales: dict con claves vendido, gastos, fiado_pendiente, balance, caja_efectivo
        """

        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        # --- Datos base desde los repos ---
        ventas_rows = self.inv_repo.listar_ventas_resumen(d1, d2)
        gastos_rows = self.inv_repo.listar_gastos(d1, d2)
        fiados_rows = self.fiados_repo.listar_en_rango(d1, d2)

        movimientos: List[Dict[str, Any]] = []

        # Ventas -> entrada
        for fecha, detalle, cantidad, monto in ventas_rows:
            movimientos.append(
                {
                    "fecha": fecha,
                    "tipo": "Venta",
                    "concepto": detalle,
                    "entrada": float(monto or 0.0),
                    "salida": 0.0,
                }
            )

        # Gastos -> salida
        for fecha, desc, monto in gastos_rows:
            movimientos.append(
                {
                    "fecha": fecha,
                    "tipo": "Gasto",
                    "concepto": desc,
                    "entrada": 0.0,
                    "salida": float(monto or 0.0),
                }
            )

        # Fiados -> salida (dinero que no entró)
        # fiados_repo.listar_en_rango devuelve:
        # (id, fecha_str, cliente, producto, cantidad, monto, estado)
        for fid, fecha, cliente, producto, cantidad, monto, estado in fiados_rows:
            movimientos.append(
                {
                    "fecha": fecha,
                    "tipo": "Fiado",
                    "concepto": f"{cliente} - {producto}",
                    "entrada": 0.0,
                    "salida": float(monto or 0.0),
                }
            )

        # --- DataFrame de movimientos ---
        if movimientos:
            df_mov = pd.DataFrame(
                movimientos,
                columns=["fecha", "tipo", "concepto", "entrada", "salida"],
            )

            # 🔑 Normalizar fechas:
            # 1) Convertir todo a datetime en UTC (evita mezcla tz-aware/naive)
            # 2) Quitar la zona horaria para que queden tz-naive
            fechas = pd.to_datetime(df_mov["fecha"], errors="coerce", utc=True)
            df_mov["fecha"] = fechas.dt.tz_convert(None)

        else:
            df_mov = pd.DataFrame(
                columns=["fecha", "tipo", "concepto", "entrada", "salida"]
            )

        # --- Totales ---
        total_vendido = float(df_mov["entrada"].sum()) if not df_mov.empty else 0.0
        total_gastos = (
            float(sum(float(r[2] or 0.0) for r in gastos_rows)) if gastos_rows else 0.0
        )
        total_fiado_pend = (
            float(
                sum(
                    float(r[5] or 0.0)
                    for r in fiados_rows
                    if (r[6] or "Pendiente") != "Pagado"
                )
            )
            if fiados_rows
            else 0.0
        )

        balance = total_vendido - (total_gastos + total_fiado_pend)

        # Total de ventas en efectivo desde el repo dedicado
        caja_bruta = self.inv_repo.get_total_ventas_efectivo(d1, d2)
        caja_efectivo = caja_bruta - total_gastos - total_fiado_pend

        totales = {
            "vendido": total_vendido,
            "gastos": total_gastos,
            "fiado_pendiente": total_fiado_pend,
            "balance": balance,
            "caja_efectivo": caja_efectivo,
        }

        return df_mov, totales
