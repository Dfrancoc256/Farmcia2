from __future__ import annotations

from datetime import date, datetime
from typing import List, Tuple, Optional

from app.repos.fiados_repo import FiadosRepo
from app.core.database import conectar_bd
from app.models.fiado import Fiado


class FiadosService:
    """
    Service para la lógica de fiados.
    Alineado con:
    - app/ui/web/page_fiados.py
    - app/ui/web/page_inventario.py
    """

    def __init__(self) -> None:
        self.repo = FiadosRepo()

    # ==========================================================
    #   CONVERSIÓN ROW → OBJETO
    # ==========================================================
    @staticmethod
    def _row_to_fiado(row: Tuple) -> Fiado:
        """
        Convierte una tupla:
        (id, fecha, cliente, producto, cantidad, monto, estado)
        en un objeto Fiado.

        Si tu FiadosRepo devuelve más columnas, ajusta el desempaquetado.
        """
        fid, fecha_raw, cliente, producto, cantidad, monto, estado = row

        # Manejo seguro de fecha
        fecha_dt: Optional[datetime] = None

        if isinstance(fecha_raw, (date, datetime)):
            # Ya viene como tipo fecha/fecha-hora
            fecha_dt = datetime.combine(fecha_raw, datetime.min.time()) if isinstance(fecha_raw, date) and not isinstance(fecha_raw, datetime) else fecha_raw
        elif isinstance(fecha_raw, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    fecha_dt = datetime.strptime(fecha_raw, fmt)
                    break
                except Exception:
                    continue

        return Fiado(
            id=int(fid),
            nombre_cliente=cliente,
            telefono=None,
            producto=producto,
            cantidad=int(cantidad or 0),
            monto=float(monto or 0.0),
            fecha=fecha_dt,
            estado=estado or "Pendiente",
            fecha_pago=None,
            id_venta=None,
        )

    # ==========================================================
    #   CREAR FIADO (USADA POR FIADOS E INVENTARIO)
    # ==========================================================
    def crear_fiado(
        self,
        id_producto: int,
        cliente: str,
        telefono: Optional[str],
        cantidad: int,
        monto: float,
        fecha: date,
    ) -> int:
        """
        Firma compatible con:
        - page_fiados._form_agregar_fiado_ui
        - page_inventario._form_agregar_fiado

        Parámetros nombrados esperados:
        - id_producto=...
        - cliente=...
        - telefono=...
        - cantidad=...
        - monto=...
        - fecha=...
        """
        if not cliente or not cliente.strip():
            raise ValueError("El nombre del cliente es obligatorio.")

        return self.repo.crear_fiado(
            nombre_cliente=cliente.strip(),
            telefono=(telefono or "").strip() or None,
            id_producto=int(id_producto),
            cantidad=int(cantidad),
            monto=float(monto),
            fecha=fecha,
        )

    # ==========================================================
    #   LISTAR RANGO (USADA POR VISTA FIADOS)
    # ==========================================================
    def listar_rango(self, desde: date, hasta: date):
        """
        Vista FIADOS usa esta función.
        Devuelve una lista de diccionarios con keys:
        id, fecha, nombre_cliente, telefono, producto, cantidad, monto, estado
        """
        d1 = desde.strftime("%Y-%m-%d")
        d2 = hasta.strftime("%Y-%m-%d")

        rows = self.repo.listar_en_rango(d1, d2)
        fiados = [self._row_to_fiado(r) for r in rows]

        salida = []
        for f in fiados:
            fecha_str = f.fecha.strftime("%Y-%m-%d") if f.fecha else ""

            salida.append(
                {
                    "id": f.id,
                    "fecha": fecha_str,
                    "nombre_cliente": f.nombre_cliente,
                    "telefono": f.telefono,
                    "producto": f.producto,
                    "cantidad": f.cantidad,
                    "monto": float(f.monto),
                    "estado": f.estado,
                }
            )
        return salida

    # ==========================================================
    #   LISTAR PENDIENTES (USADA POR FIADOS E INVENTARIO)
    # ==========================================================
    def listar_pendientes(self) -> List[Tuple[int, str, str, float, date]]:
        """
        Devuelve tuplas: (id, cliente, producto, monto, fecha)
        Formato esperado por:
        - page_inventario._form_marcar_fiado_pagado
        (page_fiados también soporta dicts, pero con tuplas basta)
        """
        return self.repo.listar_pendientes()

    # ==========================================================
    #   PAGAR FIADO (USADA POR FIADOS)
    # ==========================================================
    def pagar_fiado(self, fiado_id: int) -> Optional[int]:
        """
        Marca fiado como pagado y, si aplica, genera una venta.
        Retorna id_venta si se creó, o None si solo se actualizó el fiado.
        Usada en page_fiados._form_marcar_fiado_pagado_ui
        """
        return self.repo.pagar_fiado(fiado_id)

    # ==========================================================
    #   MARCAR FIADO PAGADO (USADA POR INVENTARIO)
    # ==========================================================
    def marcar_fiado_pagado(self, fiado_id: int) -> Optional[int]:
        """
        Wrapper para ser compatible con page_inventario._form_marcar_fiado_pagado.
        Internamente reutiliza pagar_fiado.
        """
        return self.pagar_fiado(fiado_id)

    # ==========================================================
    #   PRODUCTOS PARA COMBO (VISTA FIADOS)
    # ==========================================================
    def listar_productos_activos(self):
        """
        Devuelve lista de diccionarios {id, nombre} para el select.
        Usada en page_fiados._form_agregar_fiado_ui
        """
        cn = conectar_bd()
        if not cn:
            raise RuntimeError("No se pudo conectar a la base de datos.")

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, nombre
                    FROM public.productos
                    WHERE activo = TRUE
                    ORDER BY nombre;
                    """
                )
                return [{"id": int(r[0]), "nombre": r[1]} for r in cur.fetchall()]
        finally:
            cn.close()

    # ==========================================================
    #   PRODUCTOS PARA COMBO (VISTA INVENTARIO)
    # ==========================================================
    def listar_productos_para_combo(self) -> List[Tuple[int, str]]:
        """
        Wrapper para page_inventario._form_agregar_fiado, que espera
        una lista de tuplas (id, nombre).
        """
        productos = self.listar_productos_activos()
        return [(p["id"], p["nombre"]) for p in productos]
