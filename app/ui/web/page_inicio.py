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

    # ====== Estilos propios del dashboard (tipo Admin / UI cookies) ======
    st.markdown(
        """
        <style>
        /* Contenedor principal del contenido (no sidebar) */
        .main.block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        /* Título y subtítulo del panel */
        .panel-header-title {
            font-size: 1.4rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.1rem;
            color: #0f172a;
        }

        .panel-header-sub {
            font-size: 0.88rem;
            text-align: center;
            color: #6b7280;
            margin-bottom: 1.0rem;
        }

        /* Fila de KPIs principales */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 1rem;
            margin-bottom: 1.4rem;
        }

        .kpi-card {
            border-radius: 1rem;
            padding: 0.9rem 1rem;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            box-shadow: 0 14px 30px rgba(15,23,42,0.04);
        }

        .kpi-card.kpi-blue {
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 55%);
            border-color: #bfdbfe;
        }
        .kpi-card.kpi-emerald {
            background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 55%);
            border-color: #bbf7d0;
        }
        .kpi-card.kpi-purple {
            background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 55%);
            border-color: #ddd6fe;
        }
        .kpi-card.kpi-amber {
            background: linear-gradient(135deg, #fffbeb 0%, #ffffff 55%);
            border-color: #facc15;
        }

        .kpi-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #6b7280;
            margin-bottom: 0.25rem;
        }

        .kpi-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.15rem;
        }

        .kpi-foot {
            font-size: 0.78rem;
            color: #6b7280;
        }

        /* Tarjeta oscura usada para análisis financiero / stock / top vendidos */
        .dash-card {
            background-color: #020617;
            padding: 1.3rem 1.4rem;
            border-radius: 1rem;
            border: 1px solid #1f2937;
            margin-bottom: 1.1rem;
        }
        .dash-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #E5E7EB;
            margin-bottom: 0.15rem;
        }
        .dash-sub {
            font-size: 0.9rem;
            color: #9ca3af;
            margin-bottom: 0.7rem;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

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

    total_vendido = float(resumen.get("total_vendido", 0.0) or 0.0)
    ganancia = float(resumen.get("ganancia", 0.0) or 0.0)

    try:
        _df_gastos, total_gastos_rango = gastos_service.get_gastos_y_total(desde, hasta)
        total_gastos_rango = float(total_gastos_rango or 0.0)
    except Exception:
        total_gastos_rango = 0.0

    # ====== ENCABEZADO DEL PANEL + KPIs (estilo dashboard pro) ======
    st.markdown('<div class="panel-header-title">Panel general</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="panel-header-sub">'
        "Resumen rápido de tus productos, ventas, gastos y punto de equilibrio para el rango seleccionado."
        "</div>",
        unsafe_allow_html=True,
    )

    total_productos = resumen.get("total_productos", 0) or 0
    stock_total_unidades = resumen.get("stock_total_unidades", 0) or 0

    kpi_html = f"""
    <div class="kpi-row">
        <div class="kpi-card kpi-blue">
            <div class="kpi-label">Productos activos</div>
            <div class="kpi-value">{total_productos:,}</div>
            <div class="kpi-foot">Productos actualmente disponibles en catálogo.</div>
        </div>
        <div class="kpi-card kpi-emerald">
            <div class="kpi-label">Existencias totales</div>
            <div class="kpi-value">{stock_total_unidades:,}</div>
            <div class="kpi-foot">Unidades en inventario (todas las presentaciones).</div>
        </div>
        <div class="kpi-card kpi-purple">
            <div class="kpi-label">Vendido (rango)</div>
            <div class="kpi-value">Q {total_vendido:,.2f}</div>
            <div class="kpi-foot">Ventas totales del {desde} al {hasta}.</div>
        </div>
        <div class="kpi-card kpi-amber">
            <div class="kpi-label">Ganancia bruta (rango)</div>
            <div class="kpi-value">Q {ganancia:,.2f}</div>
            <div class="kpi-foot">Diferencia entre precio de venta y costo de compra.</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    # =====================================================
    #   TARJETA: Análisis financiero – Punto de equilibrio
    # =====================================================
    st.markdown(
        """
        <div class="dash-card">
            <div class="dash-title">📈 Análisis financiero · Punto de equilibrio</div>
            <div class="dash-sub">
                Estima qué nivel mínimo de ventas necesitas para no perder dinero en el rango seleccionado,
                combinando tus ventas reales, gastos y ganancia.
            </div>
        """,
        unsafe_allow_html=True,
    )

    # ----- Cálculos base -----
    ganancia_por_q = 0.0
    if total_vendido > 0:
        ganancia_por_q = ganancia / total_vendido

    margen_contrib = 0.0
    if total_vendido > 0:
        margen_contrib = ganancia / total_vendido

    datos_suficientes = (
        total_vendido > 0 and total_gastos_rango > 0 and margen_contrib > 0
    )

    if datos_suficientes:
        punto_equilibrio = total_gastos_rango / margen_contrib
    else:
        punto_equilibrio = 0.0

    # Utilidad neta simple del rango (ganancia bruta – gastos)
    utilidad_neta = ganancia - total_gastos_rango
    # “Presupuesto seguro” adicional que podrías gastar sin perder dinero en este rango
    presupuesto_extra = max(0.0, utilidad_neta)

    # ====== Métricas principales ======
    c_ve, c_ga, c_pe, c_pres = st.columns(4)
    with c_ve:
        st.metric("Ventas (rango)", f"Q {total_vendido:,.2f}")
    with c_ga:
        st.metric("Gastos (rango)", f"Q {total_gastos_rango:,.2f}")
    with c_pe:
        st.metric(
            "Punto de equilibrio",
            f"Q {punto_equilibrio:,.2f}" if datos_suficientes else "N/A",
            help="Nivel mínimo de ventas para no perder dinero en este rango de fechas.",
        )
    with c_pres:
        st.metric(
            "Monto que puedes gastar",
            f"Q {presupuesto_extra:,.2f}" if presupuesto_extra > 0 else "Q 0.00",
            help="Cantidad adicional que podrías gastar en este rango sin caer en pérdidas.",
        )

    # ====== Semáforo financiero ======
    if not datos_suficientes:
        st.info(
            "Aún no es posible calcular un punto de equilibrio confiable. "
            "Verifica que existan ventas, ganancia y gastos en el rango seleccionado."
        )
    else:
        ratio_ventas_pe = total_vendido / punto_equilibrio if punto_equilibrio > 0 else 0

        # Estados del semáforo según cómo estás frente al punto de equilibrio
        if ratio_ventas_pe < 0.95:
            estado = "rojo"
            titulo = "🔴 Zona de pérdida"
            resumen_estado = (
                "Las ventas están por **debajo** del punto de equilibrio en este rango."
            )
            detalle = (
                f"Faltan aproximadamente **Q {punto_equilibrio - total_vendido:,.2f}** "
                "para cubrir completamente los gastos."
            )
        elif ratio_ventas_pe <= 1.10:
            estado = "amarillo"
            titulo = "🟡 Zona de equilibrio ajustado"
            resumen_estado = (
                "Estás **muy cerca** del punto de equilibrio. Cualquier baja en ventas o subida en gastos "
                "puede llevarte a pérdida."
            )
            detalle = "Controla de cerca gastos y promociones para no salirte del equilibrio."
        else:
            estado = "verde"
            titulo = "🟢 Zona saludable"
            resumen_estado = (
                "Las ventas están **por encima** del punto de equilibrio en este rango."
            )
            if presupuesto_extra > 0:
                detalle = (
                    f"Con lo que vendiste en este rango puedes gastar hasta **Q {presupuesto_extra:,.2f}** "
                    "adicionales y seguir sin pérdidas."
                )
            else:
                detalle = (
                    "Aunque estás sobre el equilibrio, es recomendable mantener controlados los gastos."
                )

        # Colores para el semáforo
        if estado == "rojo":
            bg = "#fee2e2"
            border = "#b91c1c"
            text_color = "#7f1d1d"
        elif estado == "amarillo":
            bg = "#fffbeb"
            border = "#b45309"
            text_color = "#92400e"
        else:  # verde
            bg = "#dcfce7"
            border = "#15803d"
            text_color = "#166534"

        st.markdown(
            f"""
            <div style="
                margin-top:0.9rem;
                margin-bottom:0.4rem;
                padding:0.9rem 1rem;
                border-radius:0.75rem;
                border:1px solid {border};
                background-color:{bg};
                color:{text_color};
                font-size:0.92rem;">
                <div style="font-weight:600; margin-bottom:0.2rem;">{titulo}</div>
                <div style="margin-bottom:0.3rem;">{resumen_estado}</div>
                <div>{detalle}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ====== Gráfica simple de línea: Gastos – Punto equilibrio – Ventas ======
        df_pe = (
            pd.DataFrame(
                {
                    "Concepto": [
                        "Gastos (rango)",
                        "Punto de equilibrio",
                        "Ventas (rango)",
                    ],
                    "Monto": [total_gastos_rango, punto_equilibrio, total_vendido],
                }
            )
            .set_index("Concepto")
        )

        st.line_chart(df_pe)

    # Cierre de tarjeta de análisis financiero
    st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    #   TARJETA: Stock crítico y Más vendidos
    # =====================================================
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
