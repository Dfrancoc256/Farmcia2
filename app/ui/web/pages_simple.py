# app/ui/web/pages_simple.py
import streamlit as st
import pandas as pd

from app.core.database import conectar_bd
from app.repos.users_repo import create_user

PRIMARY = "#2563EB"
CARD_BG = "#020617"
BORDER = "#1f2937"
TEXT = "#E5E7EB"
MUTED = "#64748B"


def _card_styles():
    """Inyecta SOLO estilos CSS reutilizables (no abre divs)."""
    st.markdown(
        f"""
        <style>
        .config-card {{
            background-color: {CARD_BG};
            padding: 1.3rem 1.4rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.75rem;
        }}
        .config-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.3rem;
        }}
        .config-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
#   GASTOS (placeholder sencillo)
# =========================
def page_gastos():
    """Vista simple de Gastos (placeholder)."""
    _card_styles()

    st.markdown("## Director del panel")
    st.markdown("### 🧾 Gastos")

    st.info(
        "La gestión detallada de gastos se encuentra en el módulo de **Inventario** "
        "y en la pestaña **Gastos** específica. "
        "Más adelante podemos conectar esta vista a la tabla de gastos."
    )


# =========================
#   CONFIGURACIÓN → USUARIOS
# =========================
def page_config():
    """Panel de configuración: gestión básica de usuarios."""
    _card_styles()

    # ====== ENCABEZADO ======
    st.markdown("## Director del panel")
    st.markdown("### ⚙️ Configuración · Usuarios")

    st.info(
        "Desde aquí puedes **registrar nuevos usuarios** para el sistema y "
        "ver los ya existentes. Más adelante se pueden agregar funciones de "
        "edición de roles, bloqueo, etc."
    )

    # ====== CONEXIÓN BD ======
    cn = conectar_bd()
    if not cn:
        st.error("❌ No hay conexión a la base de datos.")
        return

    # ====== LAYOUT: FORMULARIO + LISTADO ======
    col_form, col_tabla = st.columns([2, 3])

    # ---------- FORMULARIO CREAR USUARIO ----------
    with col_form:
        # Solo encabezado estilo “card” (texto, sin envolver widgets)
        st.markdown(
            """
            <div class="config-card">
                <div class="config-title">Crear nuevo usuario</div>
                <div class="config-sub">
                    Define credenciales y rol para un nuevo usuario.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_nuevo_usuario"):
            username = st.text_input("Usuario", max_chars=50)
            password = st.text_input("Contraseña", type="password")
            password2 = st.text_input("Confirmar contraseña", type="password")

            rol = st.selectbox(
                "Rol",
                ["Administrador", "Cajero", "Invitado"],
                index=1,
            )

            activo = st.checkbox("Usuario activo", value=True)

            submitted = st.form_submit_button("Guardar usuario")

        if submitted:
            if not username or not password or not password2:
                st.error("Completa usuario y las dos contraseñas.")
            elif password != password2:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    # 1) Crear usuario usando el repositorio
                    user_id = create_user(
                        username=username,
                        password=password,
                        rol=rol,
                    )

                    # 2) Si el checkbox indica inactivo, actualizar campo activo
                    if not activo:
                        with cn.cursor() as cur:
                            cur.execute(
                                """
                                UPDATE public.usuarios
                                SET activo = FALSE
                                WHERE id = %s;
                                """,
                                (user_id,),
                            )
                        cn.commit()

                    st.success(f"✅ Usuario '{username}' creado correctamente.")
                except Exception as e:
                    cn.rollback()
                    st.error(f"❌ Error al crear usuario: {e}")

    # ---------- LISTADO DE USUARIOS ----------
    with col_tabla:
        st.markdown(
            """
            <div class="config-card">
                <div class="config-title">Usuarios registrados</div>
                <div class="config-sub">Vista rápida de los usuarios del sistema.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            with cn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, username, rol, activo, creado_en
                    FROM public.usuarios
                    ORDER BY creado_en DESC;
                    """
                )
                rows_db = cur.fetchall()

            rows = [tuple(r) for r in rows_db]
            cols = ["Id", "Usuario", "Rol", "Activo", "Creado"]

            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

            if df.empty:
                st.info("No hay usuarios registrados aún.")
            else:
                # Mostrar Activo como Sí/No
                df["Activo"] = df["Activo"].map(
                    lambda x: "Sí" if x in (1, True, "t", "true", "True") else "No"
                )
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                )
        except Exception as e:
            st.error(f"❌ Error al cargar usuarios: {e}")

    cn.close()
