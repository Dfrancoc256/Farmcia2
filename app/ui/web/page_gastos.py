# app/ui/web/page_gastos.py
import datetime as dt

import pandas as pd
import streamlit as st

from app.services.gastos_service import GastosService

# Paleta (alineada con inventario / config)
PRIMARY = "#2563EB"
TEXT = "#E5E7EB"
MUTED = "#64748B"
CARD_BG = "#020617"
BORDER = "#1f2937"

service = GastosService()


def _fecha_a_str(valor) -> str:
    """Normaliza distintos tipos de fecha a string YYYY-MM-DD."""
    from datetime import date, datetime as dt_

    if isinstance(valor, (date, dt_)):
        return valor.strftime("%Y-%m-%d")
    if valor is None:
        return ""
    return str(valor)


def page_gastos():
    """Vista completa de gastos con rango de fechas + total del rango."""

    hoy = dt.date.today()

    # --------- Estilos (igual estilo que inventario / config) ---------
    st.markdown(
        f"""
        <style>
        .gastos-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 0.1rem;
        }}
        .gastos-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}
        .gastos-card {{
            background-color: {CARD_BG};
            padding: 1.1rem 1.3rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.8rem;
        }}
        .gastos-card-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.25rem;
        }}
        .gastos-card-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===========================================================
    #   INICIALIZAR session_state SOLO SI NO EXISTEN
    # ===========================================================
    if "gastos_desde" not in st.session_state:
        st.session_state["gastos_desde"] = hoy.replace(day=1)
    if "gastos_hasta" not in st.session_state:
        st.session_state["gastos_hasta"] = hoy

    # ===========================================================
    #   ENCABEZADO
    # ===========================================================
    st.markdown("## Director del panel")

    col_title, _ = st.columns([3, 2])
    with col_title:
        st.markdown(
            '<div class="gastos-title">💸 Gastos</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="gastos-sub">Detalle de gastos y registro de nuevos movimientos.</div>',
            unsafe_allow_html=True,
        )

    # ===========================================================
    #   FILTROS — MISMO PATRÓN QUE INVENTARIO
    # ===========================================================
    st.markdown("#### Filtro por fechas")
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 0.9, 0.9])

    with c1:
        desde = st.date_input(
            "Desde",
            value=st.session_state["gastos_desde"],
            key="gastos_from_widget",
        )

    with c2:
        hasta = st.date_input(
            "Hasta",
            value=st.session_state["gastos_hasta"],
            key="gastos_to_widget",
        )

    def _set_rango_hoy():
        today = dt.date.today()
        st.session_state["gastos_from_widget"] = today
        st.session_state["gastos_to_widget"] = today

    def _set_rango_mes():
        today = dt.date.today()
        st.session_state["gastos_from_widget"] = today.replace(day=1)
        st.session_state["gastos_to_widget"] = today

    with c3:
        st.button("Hoy", key="btn_gastos_hoy", on_click=_set_rango_hoy)

    with c4:
        st.button("Este mes", key="btn_gastos_mes", on_click=_set_rango_mes)

    st.write("")

    # ===========================================================
    #   MAIN LAYOUT: TABLA & FORM
    # ===========================================================
    col_tabla, col_form = st.columns([3, 2])

    # ---------- DATOS DESDE SERVICE ----------
    try:
        df_gastos, total_rango = service.get_gastos_y_total(desde, hasta)
    except Exception as e:
        st.error(f"❌ Error al cargar datos de gastos: {e}")
        return

    # ===========================================================
    #   TABLA (lado izquierdo)
    # ===========================================================
    with col_tabla:
        # Card oscura SOLO para el encabezado (no envuelve widgets)
        st.markdown(
            """
            <div class="gastos-card">
                <div class="gastos-card-title">📒 Detalle de gastos</div>
                <p class="gastos-card-sub">Gastos registrados en el rango seleccionado.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if df_gastos is not None and not df_gastos.empty:
            df_show = df_gastos.copy()

            # Normalizar fecha si existe
            if "fecha" in df_show.columns:
                try:
                    df_show["fecha"] = pd.to_datetime(
                        df_show["fecha"], errors="coerce", utc=True
                    ).dt.tz_convert(None)
                except Exception:
                    df_show["fecha"] = df_show["fecha"].apply(_fecha_a_str)

                df_show = df_show.sort_values("fecha").reset_index(drop=True)

            st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay gastos en el rango seleccionado.")

        st.write("---")
        st.metric("Total de gastos (rango)", f"Q {total_rango:,.2f}")

    # ===========================================================
    #   FORMULARIO: NUEVO GASTO (lado derecho)
    # ===========================================================
    with col_form:
        # Card oscura para el encabezado del formulario
        st.markdown(
            """
            <div class="gastos-card">
                <div class="gastos-card-title">➕ Registrar nuevo gasto</div>
                <p class="gastos-card-sub">Agrega un nuevo movimiento de egreso.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        with st.form("form_nuevo_gasto"):
            desc = st.text_input("Descripción", key="g2_desc")
            monto = st.number_input(
                "Monto (Q)", min_value=0.0, step=1.0, key="g2_monto"
            )
            fecha = st.date_input("Fecha", value=hoy, key="g2_fecha")
            categoria = st.text_input(
                "Categoría (opcional)", key="g2_categoria"
            )

            submitted = st.form_submit_button("Guardar gasto")

        if submitted:
            if not desc.strip():
                st.warning("⚠ Ingresa una descripción.")
            elif monto <= 0:
                st.warning("⚠ El monto debe ser mayor que cero.")
            else:
                try:
                    service.crear_gasto(
                        descripcion=desc.strip(),
                        monto=float(monto),
                        fecha=fecha,
                        categoria=categoria or None,
                    )
                except Exception as e:
                    st.error(f"❌ Error al registrar gasto: {e}")
                else:
                    st.success("✅ Gasto registrado correctamente.")
                    st.rerun()
