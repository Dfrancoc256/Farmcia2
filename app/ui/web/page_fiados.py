# app/ui/web/page_fiados.py
import datetime as dt
from datetime import date, datetime
import pandas as pd
import streamlit as st

from app.services.fiados_service import FiadosService

# Colores (alineados con Gastos / Configuración)
PRIMARY = "#2563EB"
TEXT = "#E5E7EB"
MUTED = "#64748B"
CARD_BG = "#020617"
BORDER = "#1f2937"

service = FiadosService()


def _fecha_a_str(valor) -> str:
    """Normaliza diferentes formatos de fecha a YYYY-MM-DD."""
    if isinstance(valor, (date, datetime)):
        return valor.strftime("%Y-%m-%d")
    if valor is None:
        return ""
    return str(valor)


def page_fiados():
    hoy = dt.date.today()

    # --------------------------- ESTILOS ---------------------------
    st.markdown(
        f"""
        <style>
        .fiados-title {{
            font-size: 1.4rem;
            font-weight: 700;
            color: {TEXT};
            margin-bottom: 0.1rem;
        }}
        .fiados-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0.7rem;
        }}
        .fiados-card {{
            background-color: {CARD_BG};
            padding: 1.1rem 1.3rem;
            border-radius: 1rem;
            border: 1px solid {BORDER};
            margin-bottom: 0.8rem;
        }}
        .fiados-card-title {{
            font-size: 1.05rem;
            font-weight: 600;
            color: {TEXT};
            margin-bottom: 0.25rem;
        }}
        .fiados-card-sub {{
            font-size: 0.9rem;
            color: {MUTED};
            margin-bottom: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------- SESSION STATE --------------------------
    if "fiados_desde" not in st.session_state:
        st.session_state["fiados_desde"] = hoy.replace(day=1)
    if "fiados_hasta" not in st.session_state:
        st.session_state["fiados_hasta"] = hoy

    # ---------------------- TÍTULO --------------------------
    st.markdown("## Director del panel")

    col_title, _ = st.columns([3, 2])
    with col_title:
        st.markdown('<div class="fiados-title">🤝 Fiados</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="fiados-sub">Resumen de fiados, registro y pagos.</div>',
            unsafe_allow_html=True,
        )

    # ---------------------- FILTROS --------------------------
    st.markdown("#### Filtro por fechas")

    c1, c2, c3, c4 = st.columns([1.2, 1.2, 0.9, 0.9])

    with c1:
        desde = st.date_input(
            "Desde",
            value=st.session_state["fiados_desde"],
            key="fiados_from_widget",
        )

    with c2:
        hasta = st.date_input(
            "Hasta",
            value=st.session_state["fiados_hasta"],
            key="fiados_to_widget",
        )

    def _set_hoy():
        today = dt.date.today()
        st.session_state["fiados_from_widget"] = today
        st.session_state["fiados_to_widget"] = today

    def _set_mes():
        today = dt.date.today()
        st.session_state["fiados_from_widget"] = today.replace(day=1)
        st.session_state["fiados_to_widget"] = today

    with c3:
        st.button("Hoy", on_click=_set_hoy, key="btn_fiados_hoy")

    with c4:
        st.button("Este mes", on_click=_set_mes, key="btn_fiados_mes")

    st.write("")

    # ---------------------- CARGA DE DATOS --------------------------
    try:
        fiados = service.listar_rango(desde, hasta)
    except Exception as e:
        st.error(f"❌ Error al cargar fiados: {e}")
        return

    columnas = [
        "Id",
        "Fecha",
        "Cliente",
        "Teléfono",
        "Producto",
        "Cantidad",
        "Monto (Q)",
        "Estado",
    ]

    if fiados:
        df = pd.DataFrame(fiados)
        df = df.rename(
            columns={
                "id": "Id",
                "fecha": "Fecha",
                "nombre_cliente": "Cliente",
                "cliente": "Cliente",
                "telefono": "Teléfono",
                "producto": "Producto",
                "cantidad": "Cantidad",
                "monto": "Monto (Q)",
                "estado": "Estado",
            }
        )

        if "Fecha" in df.columns:
            df["Fecha"] = df["Fecha"].apply(_fecha_a_str)

        for col in columnas:
            if col not in df.columns:
                df[col] = None

        df = df[columnas]
    else:
        df = pd.DataFrame(columns=columnas)

    # ---------------------- LAYOUT: TABLA + FORM --------------------------
    col_tabla, col_forms = st.columns([3, 2])

    # ---------------------- TABLA --------------------------
    with col_tabla:

        st.markdown(
            """
            <div class="fiados-card">
                <div class="fiados-card-title">📋 Listado de fiados</div>
                <p class="fiados-card-sub">Movimientos registrados en el rango seleccionado.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if df.empty:
            st.info("No hay fiados en el rango seleccionado.")
        else:
            st.dataframe(
                df.drop(columns=["Id"], errors="ignore"),
                hide_index=True,
                use_container_width=True,
            )

            total_pend = df.loc[df["Estado"] != "Pagado", "Monto (Q)"].sum()
            total_pag = df.loc[df["Estado"] == "Pagado", "Monto (Q)"].sum()

            st.write("---")
            m1, m2 = st.columns(2)
            m1.metric("Fiado pendiente", f"Q {total_pend:,.2f}")
            m2.metric("Fiado pagado", f"Q {total_pag:,.2f}")

    # ---------------------- FORMULARIOS -----------------------
    with col_forms:

        # ------- CARD: NUEVO FIADO -------
        st.markdown(
            """
            <div class="fiados-card">
                <div class="fiados-card-title">➕ Agregar fiado</div>
                <p class="fiados-card-sub">Registrar un nuevo fiado para un cliente.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        cli = st.text_input("Cliente", key="f_cli")
        tel = st.text_input("Teléfono (opcional)", key="f_tel")

        try:
            productos = service.listar_productos_activos()
        except Exception as e:
            st.error(f"Error al cargar productos: {e}")
            productos = []

        prod_sel = None
        if productos:
            opciones = [f"{p['id']} - {p['nombre']}" for p in productos]
            prod_sel = st.selectbox("Producto", opciones, key="f_prod")
        else:
            st.warning("No hay productos activos. Registra productos primero.")

        cant = st.number_input("Cantidad", min_value=1, value=1, key="f_cant")
        monto = st.number_input("Monto (Q)", min_value=0.0, key="f_monto")
        fecha = st.date_input("Fecha", hoy, key="f_fecha")

        if st.button("Guardar fiado", key="btn_fiado_guardar"):
            if not cli.strip():
                st.warning("Ingresa el nombre del cliente.")
            elif prod_sel is None:
                st.warning("No hay productos disponibles para fiar.")
            elif monto <= 0:
                st.warning("Monto debe ser mayor a 0.")
            else:
                try:
                    pid = int(prod_sel.split(" - ")[0])
                    service.crear_fiado(
                        nombre_cliente=cli.strip(),
                        telefono=tel.strip() or None,
                        id_producto=pid,
                        cantidad=int(cant),
                        monto=float(monto),
                        fecha=fecha,
                    )
                    st.success("Fiado registrado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar fiado: {e}")

        st.write("---")

        # ------- CARD: MARCAR PAGO -------
        st.markdown(
            """
            <div class="fiados-card">
                <div class="fiados-card-title">💰 Marcar fiado como pagado</div>
                <p class="fiados-card-sub">Actualiza el estado del fiado seleccionado.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            pendientes = service.listar_pendientes()
        except Exception as e:
            st.error(f"Error al cargar fiados pendientes: {e}")
            pendientes = []

        if not pendientes:
            st.info("No hay fiados pendientes.")
        else:
            opciones_pend = []
            for item in pendientes:
                try:
                    fid, cli_p, prod_p, monto_p, fch = item
                except Exception:
                    continue
                opciones_pend.append(
                    f"{fid} - {cli_p} - {prod_p} - Q{monto_p:.2f} ({_fecha_a_str(fch)})"
                )

            sel = st.selectbox("Selecciona fiado", opciones_pend, key="f_pend")

            if st.button("Marcar como pagado", key="btn_fiado_pagar"):
                try:
                    fid = int(sel.split(" - ")[0])
                    service.pagar_fiado(fid)
                    st.success("Fiado pagado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al pagar fiado: {e}")
