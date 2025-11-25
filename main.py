# main.py  (RAÍZ DEL PROYECTO)
import streamlit as st

from app.ui.web.login_page import render_login_page
from app.ui.web.main_sidebar import render_main_app


def main():
    # Configuración global de la app
    st.set_page_config(
        page_title="Farmacia la Pablo VI",
        page_icon="💊",
        layout="wide",
    )

    # Si NO hay usuario en sesión -> mostrar LOGIN
    if "user" not in st.session_state:
        render_login_page()
    else:
        # Si ya hay usuario -> mostrar el panel principal (sidebar + páginas)
        render_main_app()


if __name__ == "__main__":
    main()
