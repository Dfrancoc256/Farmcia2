# app/ui/web/main_sidebar.py
import streamlit as st

from app.ui.web.page_carrito import page_productos_carrito
from app.ui.web.page_inventario import page_inventario
from app.ui.web.page_gastos import page_gastos      # 👈 NUEVO
from app.ui.web.pages_simple import page_config     # solo queda config aquí
from app.ui.web.page_fiados import page_fiados
from app.ui.web.page_inicio import page_inicio



# ---- Paleta (similar a la de Tkinter / login) ----
PRIMARY = "#2563EB"
BACKGROUND = "#020617"
CARD = "#020617"       # usamos tarjetas oscuras para integrarse al tema dark
TEXT = "#E5E7EB"
MUTED = "#64748B"


# =========================
#   MAIN LAYOUT
# =========================
def render_main_app():
    """Pantalla principal después del login."""

    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
        }
        .card {
            background-color: #020617;
            border-radius: 16px;
            padding: 1.25rem 1.4rem;
            border: 1px solid #1f2937;
        }
        .card h3 {
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user = st.session_state.get("user", {})
    username = user.get("username", "usuario")

    # ----- SIDEBAR -----
    with st.sidebar:
        st.markdown("### 💊 Farmacia 2.0")
        st.caption(f"Sesión: **{username}**")

        menu = st.radio(
            "Navegación",
            [
                "🏠 Inicio",                # 👈 NUEVO
                "📦 Productos / Carrito",
                "📈 Inventario",
                "🧾 Gastos",
                "📘 Fiados",
                "⚙️ Configuración",
            ],
            index=0,
            label_visibility="collapsed",
        )

        st.markdown("---")
        if st.button("Cerrar sesión", type="secondary", key="btn_logout"):
            st.session_state.clear()
            st.experimental_rerun()

    # ----- CONTENIDO -----
    st.markdown("### Panel principal")

    if menu.startswith("🏠"):
        page_inicio()                    # 👈 NUEVO
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
