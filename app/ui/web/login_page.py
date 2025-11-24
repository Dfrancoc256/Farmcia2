# app/ui/web/login_page.py
import streamlit as st

from app.repos.users_repo import get_user_by_username
from app.core.auth import verify_password

# ======== Paleta ========
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SURFACE = "#F8FAFC"
CARD = "#FFFFFF"
TEXT = "#0F172A"
MUTED = "#64748B"
SUCCESS = "#16A34A"
DANGER = "#DC2626"


def render_login_page():
    """
    Pantalla de inicio de sesión con diseño moderno y validación de usuario.

    Nota: el set_page_config lo hace main.py para evitar llamarlo dos veces.
    """

    # ---- Estilos CSS ----
    st.markdown(
        f"""
        <style>
        body {{
            background-color: {SURFACE};
        }}
        div[data-testid="stForm"] {{
            background-color: {CARD};
            padding: 2.5rem;
            border-radius: 1rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            border: 1px solid #E5E7EB;
        }}
        .login-title {{
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
            color: {TEXT};
            font-size: 2rem;
            font-weight: bold;
        }}
        .login-subtitle {{
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
            color: {MUTED};
            margin-bottom: 1.5rem;
        }}
        div.stButton > button:first-child {{
            background-color: {PRIMARY};
            color: white;
            font-weight: 600;
            border-radius: 999px;
            border: none;
        }}
        div.stButton > button:first-child:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Título ---
    st.markdown('<p class="login-title">💊 Farmacia 2.0</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="login-subtitle">Bienvenido, inicia sesión para continuar.</p>',
        unsafe_allow_html=True,
    )

    # --- Formulario ---
    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Ejemplo: diego")
        password = st.text_input("Contraseña", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            # Validaciones básicas
            if not username or not password:
                st.warning("Por favor, completa todos los campos.")
                return

            user = get_user_by_username(username)

            if not user:
                st.error("❌ Usuario no encontrado.")
                return

            if not user.get("activo", True):
                st.error("⚠️ Usuario inactivo.")
                return

            if verify_password(password, user["password_hash"]):
                # Guardamos todo en session_state para usarlo en el dashboard
                st.session_state["user"] = {
                    "id": user["id"],
                    "username": user["username"],
                    "rol": user.get("rol"),
                    "activo": user.get("activo", True),
                }
                st.success(f"✅ Bienvenido, {user['username']} ({user.get('rol', 'sin rol')})")
                # 🔄 recargar app (reemplaza a experimental_rerun)
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")


def logout_button(label: str = "🔒 Cerrar sesión"):
    """Botón de cierre de sesión que puedes usar en cualquier vista."""
    if st.button(label):
        st.session_state.clear()
        # 🔄 recargar app (reemplaza a experimental_rerun)
        st.rerun()


# Alias por si en algún lado lo llamas como login_page()
def login_page():
    render_login_page()
