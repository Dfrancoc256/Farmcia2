# app/ui/web/login_page.py
import streamlit as st

from app.repos.users_repo import get_user_by_username
from app.core.auth import verify_password

# ======== Paleta ========
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SURFACE = "#020617"   # fondo oscuro
CARD = "#020617"
TEXT = "#E5E7EB"
MUTED = "#64748B"
ACCENT = "#22c55e"


def render_login_page():
    """
    Pantalla de inicio de sesión con diseño moderno, centrada vertical y horizontalmente.
    """

    # ---- CSS global (quitar padding y centrar visualmente) ----
    st.markdown(
        f"""
        <style>

        /* Fondo general del app */
        html, body, [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at 0% 0%, #0f172a 0, #020617 45%, #020617 100%);
        }}

        /* Contenedor principal de Streamlit:
           - Quitamos padding por defecto
           - Le damos un padding-top moderado para que el login quede visible sin scroll
           - Lo centramos horizontalmente */
        main[data-testid="stAppViewContainer"] > div.block-container {{
            padding-top: 8vh !important;      /* 🔧 Ajusta 6–10 según lo quieras más arriba/abajo */
            padding-bottom: 4vh !important;
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* ⛔ Eliminamos la lógica anterior de .login-wrapper (ya no la usamos)
           Si aún tienes una regla .login-wrapper en tu CSS, bórrala completa. */

        .login-layout {{
            width: 100%;
            max-width: 1100px;
            display: grid;
            grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
            gap: 2.5rem;
        }}

        /* Hero izquierdo */
        .hero-card {{
            background: rgba(15, 23, 42, 0.92);
            border-radius: 1.75rem;
            padding: 2.2rem 2.4rem;
            border: 1px solid rgba(148, 163, 184, 0.28);
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.85);
        }}

        .hero-title {{
            font-size: 2.2rem;
            font-weight: 800;
            color: {TEXT};
            margin-bottom: 0.75rem;
        }}

        .hero-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(22, 163, 74, 0.15);
            color: {ACCENT};
            border-radius: 999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid rgba(22, 163, 74, 0.4);
        }}

        .hero-sub {{
            color: {MUTED};
            font-size: 0.9rem;
            max-width: 460px;
            margin-top: 0.75rem;
            line-height: 1.6;
        }}

        .hero-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1.5rem;
        }}

        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            background: rgba(15,23,42,0.95);
            border: 1px solid rgba(148,163,184,0.28);
            color: {MUTED};
        }}

        .hero-glow {{
            position: absolute;
            inset: -40%;
            background: radial-gradient(circle at 10% 0%, rgba(56,189,248,0.24), transparent 55%),
                        radial-gradient(circle at 100% 0%, rgba(94,234,212,0.2), transparent 50%);
            opacity: 0.9;
            filter: blur(40px);
            z-index: 0;
        }}

        /* Card de login derecha */
        .login-card {{
            position: relative;
            background: rgba(15, 23, 42, 0.96);
            border-radius: 1.5rem;
            padding: 2rem 2.2rem 2.1rem;
            border: 1px solid rgba(148, 163, 184, 0.35);
            box-shadow: 0 18px 40px rgba(15,23,42,0.9);
        }}

        .login-header {{
            font-size: 0.8rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: {MUTED};
            margin-bottom: 0.6rem;
        }}

        .login-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 1.2rem;
        }}

        div[data-testid="stForm"] {{
            background-color: transparent;
            padding: 0;
            border-radius: 0;
            box-shadow: none;
            border: none;
        }}

        .stTextInput > label, .stPassword > label {{
            color: {MUTED};
            font-size: 0.8rem;
        }}

        .stTextInput input, .stPassword input {{
            background-color: #020617;
            border-radius: 999px;
            border: 1px solid #1f2937;
            color: {TEXT};
            font-size: 0.9rem;
        }}

        .stTextInput input:focus, .stPassword input:focus {{
            border-color: {PRIMARY};
            box-shadow: 0 0 0 1px {PRIMARY};
        }}

        div.stButton > button:first-child {{
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_HOVER});
            color: white;
            font-weight: 600;
            border-radius: 999px;
            border: none;
            width: 100%;
            box-shadow: 0 18px 30px rgba(37,99,235,0.55);
        }}

        div.stButton > button:first-child:hover {{
            transform: translateY(-1px);
            box-shadow: 0 22px 35px rgba(37,99,235,0.7);
        }}

        .login-footer {{
            margin-top: 0.65rem;
            font-size: 0.78rem;
            color: {MUTED};
            text-align: center;
        }}

        @media (max-width: 900px) {{
            .login-layout {{
                grid-template-columns: minmax(0, 1fr);
                gap: 1.5rem;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---- Layout principal centrado ----
    st.markdown('<div class="login-wrapper"><div class="login-layout">', unsafe_allow_html=True)

    # ======================================================
    #   COLUMNA IZQUIERDA (hero)
    # ======================================================
    col1, col2 = st.columns([1.4, 1], gap="large")

    with col1:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-glow"></div>
                <div style="position:relative; z-index:1;">
                    <div class="hero-title">
                        Farmacia <span style="color:#60a5fa;">2.0</span>
                        <span class="hero-pill">
                            ● Panel seguro
                        </span>
                    </div>
                    <p class="hero-sub">
                        Controla <span style="color:#93c5fd;">ventas</span>,
                        <span style="color:#93c5fd;">inventario</span>,
                        <span style="color:#93c5fd;">gastos</span> y
                        <span style="color:#93c5fd;">fiados</span> desde un solo lugar,
                        con acceso restringido por usuario.
                    </p>
                    <div class="hero-badges">
                        <span class="hero-badge">🛒 Módulo de ventas con carrito</span>
                        <span class="hero-badge">📦 Inventario en tiempo real</span>
                        <span class="hero-badge">📊 Análisis financiero básico</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ======================================================
    #   COLUMNA DERECHA (login)
    # ======================================================
    with col2:
        st.markdown(
            """
            <div class="login-card">
                <div class="login-header">INICIO DE SESIÓN</div>
                <div class="login-title">Accede al panel</div>
            """,
            unsafe_allow_html=True,
        )

        # Formulario real
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ejemplo: diego")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Iniciar sesión")

            if submitted:
                if not username or not password:
                    st.warning("Por favor, completa todos los campos.")
                else:
                    user = get_user_by_username(username)

                    if not user:
                        st.error("❌ Usuario no encontrado.")
                    elif not user.get("activo", True):
                        st.error("⚠️ Usuario inactivo.")
                    elif verify_password(password, user["password_hash"]):
                        st.session_state["user"] = {
                            "id": user["id"],
                            "username": user["username"],
                            "rol": user.get("rol"),
                            "activo": user.get("activo", True),
                        }
                        st.success(
                            f"✅ Bienvenido, {user['username']} "
                            f"({user.get('rol', 'sin rol')})"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta.")

        st.markdown(
            """
                <div class="login-footer">
                    Farmacia 2.0 · Acceso restringido · Todos los movimientos quedan registrados.
                </div>
            </div>  <!-- login-card -->
            """,
            unsafe_allow_html=True,
        )

    # Cerrar wrappers
    st.markdown("</div></div>", unsafe_allow_html=True)


def logout_button(label: str = "🔒 Cerrar sesión"):
    if st.button(label):
        st.session_state.clear()
        st.rerun()


def login_page():
    render_login_page()