# app/ui/web/page_inicio.py
import datetime as dt

import pandas as pd
import streamlit as st

from app.services.dashboard_service import DashboardService
from app.services.gastos_service import GastosService

# Paleta
PRIMARY = "#2563EB"
CARD_BG = "#020617"
BORDER = "#1f2937"
TEXT = "#E5E7EB"
MUTED = "#64748B"

# Servicios
service = DashboardService()
gastos_service = GastosService()


def page_inicio():
    """Dashboard inicial: resumen de productos, ventas, alertas y análisis de equilibrio."""

    hoy = dt.date.today()
    primer_dia_mes = hoy.replace(day=1)

    # ====== Estilos (tarjetas y gráficos) ======
    st.markdown(
        f"""
        <style>
        .dash-card {{
            background-color: {CARD_BG};
            padding: 1.3rem 1.4rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 1.1rem;
        }}
        .dash-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.1rem;
        }}
        .dash-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}

        /* ==== Hacer que las GRÁFICAS se vean como tarjetas oscuras ==== */
        div[data-testid="stChart"] {{
            background-color: {CARD_BG};
            padding: 1.0rem 1.2rem 1.4rem 1.2rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ====== Título principal ======
    st.markdown("## Inicio / Panel de control")

    # ====== Inicializar filtros en session_state ======
    if "dash_desde" not in st.session_state:
        st.session_state["dash_desde"] = primer_dia_mes
    if "dash_hasta" not in st.session_state:
        st.session_state["dash_hasta"] = hoy

    st.markdown("#### Filtros del tablero")

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 0.8, 0.8])

    # Valores que vienen de los widgets (patrón igual a inventario/gastos/fiados)
    with c1:
        desde = st.date_input(
            "Desde",
            value=st.session_state["dash_desde"],
            key="dash_from_widget",
        )

    with c2:
        hasta = st.date_input(
            "Hasta",
            value=st.session_state["dash_hasta"],
            key="dash_to_widget",
        )

    def _set_rango_hoy():
        today = dt.date.today()
        st.session_state["dash_from_widget"] = today
        st.session_state["dash_to_widget"] = today

    def _set_rango_mes():
        today = dt.date.today()
        st.session_state["dash_from_widget"] = today.replace(day=1)
        st.session_state["dash_to_widget"] = today

    with c3:
        st.button("Hoy", use_container_width=True, on_click=_set_rango_hoy)

    with c4:
        st.button("Este mes", use_container_width=True, on_click=_set_rango_mes)

    st.write("")

    # Valores efectivos para consultas
    desde = st.session_state.get("dash_from_widget", st.session_state["dash_desde"])
    hasta = st.session_state.get("dash_to_widget", st.session_state["dash_hasta"])

    # ====== Consultar datos principales ======
    try:
        resumen = service.get_resumen(desde, hasta)
        df_bajos = service.get_productos_bajo_stock_df(threshold=1)
        df_top = service.get_top_mas_vendidos_df(desde, hasta, top_n=5)
    except Exception as e:
        st.error(f"❌ Error al cargar datos del dashboard: {e}")
        return

    # Extra para el análisis financiero
    total_vendido = float(resumen.get("total_vendido", 0.0) or 0.0)
    ganancia = float(resumen.get("ganancia", 0.0) or 0.0)

    try:
        df_gastos, total_gastos_rango = gastos_service.get_gastos_y_total(desde, hasta)
        total_gastos_rango = float(total_gastos_rango or 0.0)
    except Exception:
        total_gastos_rango = 0.0

    # ====== TARJETA: Indicadores generales ======
    st.markdown(
        """
        <div class="dash-card">
            <div class="dash-title">📊 Indicadores generales</div>
            <div class="dash-sub">
                Resumen general del sistema: productos activos, existencias totales, ventas,
                ganancia y fiado pendiente.
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Productos activos", f"{resumen.get('total_productos', 0):,}")
    with col_m2:
        st.metric(
            "Total de existencias (unidades)",
            f"{resumen.get('stock_total_unidades', 0):,}",
        )
    with col_m3:
        st.metric("Vendido (rango)", f"Q {total_vendido:,.2f}")
    with col_m4:
        st.metric("Ganancia (rango)", f"Q {ganancia:,.2f}")

    col_m5, _, _, _ = st.columns(4)
    with col_m5:
        st.metric(
            "Fiado pendiente (global)",
            f"Q {resumen.get('fiado_pendiente', 0.0):,.2f}",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ====== TARJETA: Análisis financiero – Punto de equilibrio ======
    st.markdown(
        """
        <div class="dash-card">
            <div class="dash-title">📈 Análisis financiero · Punto de equilibrio</div>
            <div class="dash-sub">
                Calcula qué nivel de ventas necesitas, como mínimo, para no perder dinero
                en el rango seleccionado, usando tus ventas reales, tus gastos y tu ganancia.
            </div>
        """,
        unsafe_allow_html=True,
    )

    # ----- Cálculo del margen de contribución y punto de equilibrio -----
    margen_contrib = 0.0
    punto_equilibrio = 0.0

    if total_vendido > 0:
        margen_contrib = ganancia / total_vendido if total_vendido != 0 else 0.0

    datos_suficientes = (
        total_vendido > 0 and total_gastos_rango > 0 and margen_contrib > 0
    )

    if datos_suficientes:
        punto_equilibrio = total_gastos_rango / margen_contrib
    else:
        punto_equilibrio = 0.0

    # Métricas de la tarjeta
    c_ve, c_ga, c_mc, c_pe = st.columns(4)
    with c_ve:
        st.metric("Ventas (rango)", f"Q {total_vendido:,.2f}")
    with c_ga:
        st.metric("Gastos (rango)", f"Q {total_gastos_rango:,.2f}")
    with c_mc:
        st.metric(
            "Margen de contribución",
            f"{(margen_contrib * 100):,.1f} %" if margen_contrib > 0 else "N/A",
        )
    with c_pe:
        st.metric(
            "Punto de equilibrio",
            f"Q {punto_equilibrio:,.2f}" if datos_suficientes else "N/A",
        )

    if not datos_suficientes:
        st.info(
            "Aún no es posible calcular un punto de equilibrio confiable. "
            "Verifica que existan ventas, ganancia y gastos en el rango seleccionado."
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Si hay datos suficientes, mostramos la gráfica (ya con estilo oscuro por CSS)
    if datos_suficientes:
        df_pe = pd.DataFrame(
            {
                "Concepto": ["Gastos (rango)", "Punto de equilibrio", "Ventas (rango)"],
                "Monto": [total_gastos_rango, punto_equilibrio, total_vendido],
            }
        ).set_index("Concepto")

        st.markdown("#### Gráfica de ventas, gastos y punto de equilibrio")
        st.line_chart(df_pe)

        st.markdown(
            """
            <div class="dash-sub" style="margin-top:0.8rem;">
                • Si las ventas reales están <b>por encima</b> del punto de equilibrio,
                el negocio está generando utilidad en el rango.<br>
                • Si las ventas caen <b>por debajo</b> del punto de equilibrio,
                empezarías a tener pérdidas en ese rango de fechas.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ====== TARJETA: Stock crítico y Más vendidos ======
    col_left, col_right = st.columns([1.4, 1])

    # --- Productos con stock crítico ---
    with col_left:
        st.markdown(
            """
            <div class="dash-card">
                <div class="dash-title">📉 Stock crítico</div>
                <div class="dash-sub">
                    Productos con menos de 1 unidad disponible.
                </div>
            """,
            unsafe_allow_html=True,
        )

        if df_bajos.empty:
            st.success("✔ No hay productos con stock crítico en este momento.")
        else:
            df_view = df_bajos.copy()
            if "Id" in df_view.columns:
                df_view = df_view.drop(columns=["Id"])
            st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # --- Top productos más vendidos ---
    with col_right:
        st.markdown(
            """
            <div class="dash-card">
                <div class="dash-title">🔥 Más vendidos</div>
                <div class="dash-sub">
                    Top 5 productos más vendidos según el rango.
                </div>
            """,
            unsafe_allow_html=True,
        )

        if df_top.empty:
            st.info("No hay ventas registradas en el rango seleccionado.")
        else:
            df_view = df_top.copy()
            if "Id" in df_view.columns:
                df_view = df_view.drop(columns=["Id"])
            st.dataframe(df_view, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)
