# app/ui/web/page_productos_carrito.py
from datetime import date

import pandas as pd
import streamlit as st

from app.services.ventas_service import VentasService
from app.services.productos_service import ProductosService
from app.ui.web.page_productos import (
    render_listado_productos,
    render_registrar_producto_tab,
    render_editar_producto_tab,
)
from app.ui.web.page_carrito import render_carrito_tab

# Servicios (una sola instancia aquí)
ventas_service = VentasService()
productos_service = ProductosService()

# Paleta coherente con el resto del sistema
PRIMARY = "#2563EB"
CARD_BG = "#020617"
BORDER = "#1f2937"
TEXT = "#E5E7EB"
MUTED = "#64748B"


def page_productos_carrito():
    # =========================
    #   ESTILOS GENERALES
    # =========================
    st.markdown(
        f"""
        <style>
        .carrito-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 0.1rem;
        }}
        .carrito-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}
        .carrito-card {{
            background-color: {CARD_BG};
            padding: 1.1rem 1.3rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.8rem;
        }}
        .carrito-card-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.25rem;
        }}
        .carrito-card-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    #   TÍTULO
    # =========================
    st.markdown("## Director del panel")

    col_title, _ = st.columns([3, 2])
    with col_title:
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:10px; margin-top:0.4rem; margin-bottom:0.6rem;">
                <div style="
                    width:18px; height:18px;
                    border-radius:3px;
                    background: linear-gradient(135deg, #22c55e, #4ade80);
                "></div>
                <span class="carrito-title">📦 Productos / Carrito</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="carrito-card" style="margin-top:0;">
                <div class="carrito-card-sub">
                    Desde aquí puedes registrar productos, editar / desactivar existentes
                    y gestionar el carrito de venta.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =========================
    #   MENSAJES POST-RERUN
    # =========================
    for key in ["msg_producto_creado", "msg_producto_editado"]:
        msg = st.session_state.pop(key, None)
        if msg:
            st.success(msg)

    # =========================
    #   SESSION STATE BÁSICO
    # =========================
    if "carrito" not in st.session_state:
        st.session_state["carrito"] = []

    user = st.session_state.get("user") or {}
    id_usuario = user.get("id", 1)

    # =========================
    #   CARGA PRODUCTOS
    # =========================
    try:
        df_prods = ventas_service.get_productos_activos_df()
    except Exception as e:
        st.error(f"❌ No se pudieron cargar los productos: {e}")
        return

    if df_prods.empty:
        st.info("No hay productos activos en este momento.")
        df_prods = pd.DataFrame(
            columns=[
                "id",
                "Nombre",
                "Presentacion",
                "Detalle",
                "Compra",
                "Unidad",
                "Blister",
                "Caja",
                "UnidadesBlister",
                "StockUnidades",
                "Categoria",
            ]
        )

    # Aseguramos la columna Presentacion aunque el backend aún no la tenga
    if "Presentacion" not in df_prods.columns:
        df_prods["Presentacion"] = ""

    # =========================
    #   LAYOUT PRINCIPAL
    # =========================
    col_left, col_right = st.columns([2, 1])

    # -------- IZQUIERDA: TABLA DE PRODUCTOS --------
    with col_left:
        render_listado_productos(df_prods)

    # -------- DERECHA: TABS (CARRITO + REGISTRO + EDICIÓN) --------
    with col_right:
        st.markdown(
            """
            <div class="carrito-card">
                <div class="carrito-card-title">Producto / Carrito</div>
                <p class="carrito-card-sub">
                    Usa las pestañas para gestionar el carrito y administrar los productos.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_carrito, tab_reg, tab_edit = st.tabs(
            ["🛒 Añadir al carrito", "➕ Registrar producto", "✏️ Editar / eliminar"]
        )

        # TAB 1: CARRITO
        with tab_carrito:
            render_carrito_tab(ventas_service, id_usuario, date.today())

        # TAB 2: REGISTRAR PRODUCTO
        with tab_reg:
            render_registrar_producto_tab(productos_service)

        # TAB 3: EDITAR / ELIMINAR
        with tab_edit:
            render_editar_producto_tab(df_prods, productos_service)
