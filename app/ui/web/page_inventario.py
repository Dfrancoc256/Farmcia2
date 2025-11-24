import datetime as dt
from datetime import date, datetime

import pandas as pd
import streamlit as st

from app.services.inventario_service import InventarioService
from app.services.fiados_service import FiadosService
from app.services.gastos_service import GastosService

# Paleta
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SURFACE = "#0B1120"
CARD = "#020617"
BORDER = "#1f2937"
TEXT = "#E5E7EB"
MUTED = "#64748B"

# Services
inv_service = InventarioService()
fiados_service = FiadosService()
gastos_service = GastosService()


def _fecha_a_str(valor) -> str:
    """Normaliza distintos tipos de fecha a string YYYY-MM-DD."""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%Y-%m-%d")
    if valor is None:
        return ""
    return str(valor)


def page_inventario():
    # --------- Estilos ---------
    st.markdown(
        f"""
        <style>
        .inv-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 0.1rem;
        }}
        .inv-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}
        .inv-card {{
            background-color: {CARD};
            padding: 1.1rem 1.3rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.8rem;
        }}
        .inv-card-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.25rem;
        }}
        .inv-card-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    hoy = dt.date.today()

    # ===========================================================
    #   INICIALIZAR session_state SOLO SI NO EXISTEN
    # ===========================================================
    if "inv_desde" not in st.session_state:
        st.session_state["inv_desde"] = hoy.replace(day=1)
    if "inv_hasta" not in st.session_state:
        st.session_state["inv_hasta"] = hoy

    # ===========================================================
    #   TÍTULO
    # ===========================================================
    st.markdown("## Director del panel")

    col_title, _ = st.columns([3, 2])
    with col_title:
        st.markdown(
            '<div class="inv-title">📊 Inventario general</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="inv-sub">Movimientos de ventas, egresos y fiados.</div>',
            unsafe_allow_html=True,
        )

    # ===========================================================
    #   FILTROS — NO TOCAR session_state DEL WIDGET DIRECTO
    # ===========================================================
    st.markdown("#### Filtro por fechas")

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 0.9, 0.9])

    with c1:
        desde = st.date_input(
            "Desde",
            value=st.session_state["inv_desde"],
            key="inv_from_widget",
        )

    with c2:
        hasta = st.date_input(
            "Hasta",
            value=st.session_state["inv_hasta"],
            key="inv_to_widget",
        )

    def _set_rango_hoy():
        today = dt.date.today()
        st.session_state["inv_from_widget"] = today
        st.session_state["inv_to_widget"] = today

    def _set_rango_mes():
        today = dt.date.today()
        st.session_state["inv_from_widget"] = today.replace(day=1)
        st.session_state["inv_to_widget"] = today

    with c3:
        st.button("Hoy", key="btn_inv_hoy", on_click=_set_rango_hoy)

    with c4:
        st.button("Este mes", key="btn_inv_mes", on_click=_set_rango_mes)

    st.write("")

    # ===========================================================
    #   MAIN LAYOUT: TABLA & TOTALS
    # ===========================================================
    col_tabla, col_totales = st.columns([3, 2])

    with col_tabla:
        tabla_container = st.container()

    with col_totales:
        metric_container = st.container()
        st.write("")
        # Encabezado tipo tarjeta para las acciones rápidas
        st.markdown(
            """
            <div class="inv-card">
                <div class="inv-card-title">⚙️ Acciones rápidas</div>
                <p class="inv-card-sub">
                    Registra gastos, fiados y pagos directamente desde el inventario.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("➕ Agregar gasto"):
            _form_agregar_gasto()

        with st.expander("📝 Agregar fiado"):
            _form_agregar_fiado()

        with st.expander("✅ Marcar fiado como pagado"):
            _form_marcar_fiado_pagado()

    # ===========================================================
    #   LÓGICA: OBTENER MOVIMIENTOS Y TOTALES (POR RANGO)
    # ===========================================================
    try:
        df_mov, totales = inv_service.get_movimientos_y_totales(
            desde,
            hasta,
        )
    except Exception as e:
        st.error(f"❌ Error al cargar datos del inventario: {e}")
        return

    # ===========================================================
    #   TABLA
    # ===========================================================
    with tabla_container:
        st.markdown(
            """
            <div class="inv-card">
                <div class="inv-card-title">📑 Movimientos (Ventas / Fiados / Egresos)</div>
                <p class="inv-card-sub">
                    Registros consolidados del rango de fechas seleccionado.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if df_mov.empty:
            st.info("No hay movimientos en este rango.")
        else:
            df_show = df_mov.copy()

            # Normalizar fecha (quitar tz si existiera)
            try:
                df_show["fecha"] = (
                    pd.to_datetime(df_show["fecha"], errors="coerce", utc=True)
                    .dt.tz_convert(None)
                )
            except Exception as e:
                st.error(f"Error procesando fecha: {e}")

            df_show = df_show.sort_values("fecha").reset_index(drop=True)

            st.dataframe(
                df_show,
                hide_index=True,
                use_container_width=True,
            )

    # ===========================================================
    #   MÉTRICAS
    # ===========================================================
    with metric_container:
        st.markdown(
            """
            <div class="inv-card">
                <div class="inv-card-title">📌 Totales</div>
                <p class="inv-card-sub">
                    Resumen financiero calculado con base en los movimientos del período.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.metric("Vendido", f"Q {totales.get('vendido', 0):,.2f}")
        st.metric("Gastos", f"Q {totales.get('gastos', 0):,.2f}")
        st.metric("Fiado pendiente", f"Q {totales.get('fiado_pendiente', 0):,.2f}")
        st.metric("Balance", f"Q {totales.get('balance', 0):,.2f}")
        st.metric("Caja (efectivo)", f"Q {totales.get('caja_efectivo', 0):,.2f}")


# =====================================================
#   FORMULARIOS
# =====================================================

def _form_agregar_gasto():
    desc = st.text_input("Descripción", key="gasto_desc")
    monto = st.number_input("Monto (Q)", min_value=0.0, step=1.0, key="gasto_monto")
    fecha = st.date_input("Fecha", dt.date.today(), key="gasto_fecha")
    categoria = st.text_input("Categoría (opcional)", key="gasto_categoria")

    if st.button("Guardar gasto", key="btn_guardar_gasto"):
        if not desc.strip():
            st.warning("⚠ Ingresa una descripción válida.")
            return
        if monto <= 0:
            st.warning("⚠ El monto debe ser mayor que cero.")
            return

        try:
            gastos_service.crear_gasto(
                desc.strip(),
                float(monto),
                fecha,
                categoria or None,
            )
        except Exception as e:
            st.error(f"❌ Error al registrar gasto: {e}")
        else:
            st.rerun()


def _form_agregar_fiado():
    cli = st.text_input("Cliente", key="fiado_cliente")
    tel = st.text_input("Teléfono (opcional)", key="fiado_tel")

    try:
        productos = fiados_service.listar_productos_para_combo()
    except Exception as e:
        st.error(f"❌ Error al cargar productos: {e}")
        productos = []

    if not productos:
        st.info("No hay productos activos para fiar. Registra productos primero.")
        return

    opciones = [f"{pid} - {nom}" for pid, nom in productos]

    prod_sel = st.selectbox("Producto", opciones, key="fiado_producto")

    cant = st.number_input("Cantidad", min_value=1, step=1, key="fiado_cantidad")
    monto = st.number_input("Monto (Q)", min_value=0.0, step=1.0, key="fiado_monto")
    fecha = st.date_input("Fecha", dt.date.today(), key="fiado_fecha")

    if st.button("Guardar fiado", key="btn_guardar_fiado"):
        if not cli:
            st.warning("Ingresa el nombre del cliente.")
            return

        if not prod_sel:
            st.warning("Selecciona un producto.")
            return

        if monto <= 0:
            st.warning("El monto debe ser mayor que 0.")
            return

        try:
            pid = int(prod_sel.split(" - ")[0])
        except Exception:
            st.error("Producto inválido.")
            return

        try:
            fiados_service.crear_fiado(
                id_producto=pid,
                cliente=cli.strip(),
                telefono=(tel.strip() or None),
                cantidad=int(cant),
                monto=float(monto),
                fecha=fecha,
            )
        except Exception as e:
            st.error(f"❌ Error al registrar fiado: {e}")
        else:
            st.rerun()


def _form_marcar_fiado_pagado():
    try:
        fiados_pend = fiados_service.listar_pendientes()
    except Exception as e:
        st.error(f"❌ Error al cargar fiados pendientes: {e}")
        return

    if not fiados_pend:
        st.info("No hay fiados pendientes.")
        return

    opciones = []
    for (fid, cli, prod, monto, fecha) in fiados_pend:
        fecha_str = _fecha_a_str(fecha)
        opciones.append(
            f"{fid} - {cli} - {prod} - Q{monto:.2f} ({fecha_str})"
        )

    sel = st.selectbox("Seleccionar fiado", opciones, key="fiado_pend_sel")

    if st.button("Marcar como pagado", key="btn_pagar_fiado"):
        try:
            fid = int(sel.split(" - ", 1)[0])
        except Exception:
            st.error("ID de fiado inválido.")
            return

        try:
            fiados_service.marcar_fiado_pagado(fid)
        except Exception as e:
            st.error(f"❌ Error al marcar fiado: {e}")
        else:
            st.rerun()
