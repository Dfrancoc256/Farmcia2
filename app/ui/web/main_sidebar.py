# app/ui/web/main_sidebar.py
import streamlit as st

from app.ui.web.page_carrito import page_productos_carrito
from app.ui.web.page_inventario import page_inventario
from app.ui.web.page_gastos import page_gastos
from app.ui.web.pages_simple import page_config
from app.ui.web.page_fiados import page_fiados
from app.ui.web.page_inicio import page_inicio

# Paleta
PRIMARY = "#2563EB"
SIDEBAR_BG = "#020617"
TEXT = "#F9FAFB"
MUTED = "#6b7280"


def _inject_sidebar_css():
    st.markdown(
        f"""
        <style>
        /* ===== Sidebar general ===== */
        [data-testid="stSidebar"] {{
            background: {SIDEBAR_BG};
            color: {TEXT} !important;
            padding-top: 1.3rem;
        }}

        .main.block-container {{
            padding-top: 1.2rem;
        }}

        /* ===== Header ===== */
        [data-testid="stSidebar"] h3 {{
            margin-bottom: 0.1rem;
            font-weight: 700;
            color: {TEXT} !important;
        }}

        [data-testid="stSidebar"] .sidebar-caption {{
            font-size: 0.8rem;
            color: #CBD5E1 !important;
            margin-bottom: 1.2rem;
        }}

        /* Texto "NAVEGACIÓN" */
        [data-testid="stSidebar"] .nav-label {{
            font-size: 0.68rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #CBD5E1 !important;
            margin-bottom: 0.4rem;
        }}

        /* ===== Radio como menú ===== */
        [data-testid="stSidebar"] div[role="radiogroup"] {{
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }}

        /* Ocultar círculos originales */
        [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {{
            display: none !important;
        }}

        /* Estilo base de cada opción */
        [data-testid="stSidebar"] div[role="radiogroup"] > label {{
            border-radius: 999px;
            padding: 0.55rem 0.9rem;
            cursor: pointer;
            color: {TEXT} !important;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            transition:
                background-color 0.18s ease,
                box-shadow 0.18s ease,
                transform 0.12s ease,
                color 0.18s ease;
        }}

        /* FORZAR texto e iconos en blanco dentro de cada opción */
        [data-testid="stSidebar"] div[role="radiogroup"] > label * {{
            color: {TEXT} !important;
        }}

        /* Hover (no seleccionada) */
        [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            background: rgba(37, 99, 235, 0.25);
            box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.55);
        }}

        /* Opción seleccionada */
        [data-testid="stSidebar"] div[role="radiogroup"] > label[aria-checked="true"] {{
            background: #0b1a3d;
            box-shadow: 0 0 0 1px {PRIMARY};
            transform: translateX(2px);
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] > label[aria-checked="true"] * {{
            font-weight: 700 !important;
            color: {TEXT} !important;
        }}

        /* Separador */
        [data-testid="stSidebar"] .sidebar-separator {{
            border-top: 1px solid rgba(255, 255, 255, 0.18);
            margin: 1.4rem 0 1.1rem 0;
        }}

        /* Botón Cerrar sesión */
        [data-testid="stSidebar"] .logout-btn button {{
            width: 100%;
            border-radius: 999px;
            border: none;
            background: #f9fafb;
            color: #111827;
            font-size: 0.9rem;
            padding: 0.55rem 0.9rem;
            box-shadow: 0 7px 14px rgba(15, 23, 42, 0.35);
            transition:
                background-color 0.18s ease,
                transform 0.1s ease,
                box-shadow 0.18s ease;
        }}

        [data-testid="stSidebar"] .logout-btn button:hover {{
            background: #e5e7eb;
            transform: translateY(-1px);
            box-shadow: 0 10px 18px rgba(15, 23, 42, 0.5);
        }}

        [data-testid="stSidebar"] .logout-btn button:active {{
            transform: translateY(0px);
            box-shadow: 0 4px 8px rgba(15, 23, 42, 0.4);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_main_app():
    """Pantalla principal después del login."""

    _inject_sidebar_css()

    user = st.session_state.get("user", {})
    username = user.get("username", "usuario")

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.markdown(
            f"""
            <h3>💊 Farmacia la Pablo VI</h3>
            <div class="sidebar-caption">Sesión: <b>{username}</b></div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-label">NAVEGACIÓN</div>', unsafe_allow_html=True)

        menu = st.radio(
            "Navegación",
            (
                "🏠 Inicio",
                "📦 Productos / Carrito",
                "📈 Inventario",
                "🧾 Gastos",
                "📘 Fiados",
                "⚙️ Configuración",
            ),
            index=0,
            label_visibility="collapsed",
        )

        st.markdown('<div class="sidebar-separator"></div>', unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
            if st.button("Cerrar sesión", key="btn_logout"):
                st.session_state.clear()
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------- CONTENIDO PRINCIPAL ----------
    if menu.startswith("🏠"):
        page_inicio()
    elif menu.startswith("📦"):
        page_productos_carrito()
    elif menu.startswith("📈"):
        page_inventario()
    elif menu.startswith("🧾"):
        page_gastos()
    elif menu.startswith("📘"):
        page_fiados()
    else:
        page_config()
