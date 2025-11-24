# app/ui/web/page_carrito.py
from datetime import date

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from app.services.ventas_service import VentasService
from app.services.productos_service import ProductosService

# Servicios
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
                    Desde aquí puedes registrar nuevos productos y gestionar ventas rápidas
                    usando el carrito. El total se calcula automáticamente con base en los
                    productos añadidos.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =========================
    #   SESSION STATE
    # =========================
    if "carrito" not in st.session_state:
        st.session_state["carrito"] = []

    user = st.session_state.get("user") or {}
    id_usuario = user.get("id", 1)

    # =========================
    #   CARGA PRODUCTOS (SERVICE)
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
                "Compra",
                "Unidad",
                "Blister",
                "UnidadesBlister",
                "StockUnidades",
            ]
        )

    col_left, col_right = st.columns([2, 1])

    # =========================
    #   LISTADO + SELECCIÓN
    # =========================
    with col_left:
        st.markdown(
            """
            <div class="carrito-card">
                <div class="carrito-card-title">📑 Listado de productos</div>
                <p class="carrito-card-sub">
                    Busca y selecciona un producto para añadirlo al carrito de ventas.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q = st.text_input("Buscar producto", "")

        df_view = df_prods.copy()
        if q:
            df_view = df_view[df_view["Nombre"].str.contains(q, case=False, na=False)]

        if not df_view.empty:
            # Configuración de AGGrid
            gb = GridOptionsBuilder.from_dataframe(
                df_view[["Nombre", "Compra", "Unidad", "Blister", "StockUnidades"]]
            )
            gb.configure_selection("single", use_checkbox=False)
            gb.configure_grid_options(domLayout="normal")
            grid_options = gb.build()

            grid_response = AgGrid(
                df_view[["Nombre", "Compra", "Unidad", "Blister", "StockUnidades"]],
                gridOptions=grid_options,
                height=320,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                theme="alpine",
            )

            selected_rows = grid_response["selected_rows"]

            prod_sel = None
            selected_name = ""

            # Normalizamos la selección
            if isinstance(selected_rows, list):
                if selected_rows:
                    selected_name = selected_rows[0]["Nombre"]
            elif isinstance(selected_rows, pd.DataFrame):
                if not selected_rows.empty:
                    selected_name = selected_rows.iloc[0]["Nombre"]

            if selected_name:
                # Buscamos en df_prods para traer todas las columnas (incluyendo id)
                matches = df_prods[df_prods["Nombre"] == selected_name]
                if not matches.empty:
                    prod_sel = matches.iloc[0]
                else:
                    # Fallback al primer registro del df_view
                    prod_sel = df_view.iloc[0]
                    selected_name = prod_sel["Nombre"]
            else:
                # Si no seleccionó nada, tomamos el primero del df_view (respeta el filtro)
                prod_sel = df_view.iloc[0]
                selected_name = prod_sel["Nombre"]
        else:
            prod_sel = None
            selected_name = ""
            st.info(
                "No hay productos para mostrar con el filtro actual. "
                "Limpia el buscador o registra un producto nuevo."
            )

    # =========================
    #   FORMULARIOS (TABS)
    # =========================
    with col_right:
        tab_reg, tab_cart = st.tabs(["➕ Registrar producto", "🛒 Añadir al carrito"])

        # ---------- TAB 1: REGISTRAR PRODUCTO ----------
        with tab_reg:
            st.markdown(
                """
                <div class="carrito-card">
                    <div class="carrito-card-title">Nuevo producto</div>
                    <p class="carrito-card-sub">
                        Registra un producto nuevo con precios y stock para habilitarlo en ventas.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("form_nuevo_producto"):
                nombre = st.text_input("Nombre del producto")
                detalle = st.text_input("Detalle / descripción", value="")
                categoria = st.text_input(
                    "Categoría / palabras clave",
                    help="Ej: dolor, fiebre, antibiótico… (sirve para el buscador).",
                )

                precio_compra = st.number_input(
                    "Precio compra (Q)", min_value=0.0, step=0.01, value=0.0
                )
                precio_unidad = st.number_input(
                    "Precio venta unidad (Q)", min_value=0.0, step=0.01, value=0.0
                )
                precio_blister = st.number_input(
                    "Precio venta blister (Q)",
                    min_value=0.0,
                    step=0.01,
                    value=0.0,
                    help="Si el producto no se vende por blister, puedes dejarlo en 0.",
                )

                stock_unidades = st.number_input(
                    "Stock inicial (unidades)", min_value=0, step=1, value=0
                )
                unidades_por_blister = st.number_input(
                    "Unidades por blister",
                    min_value=0,
                    step=1,
                    value=0,
                    help="0 si no aplica blister.",
                )

                submitted_prod = st.form_submit_button("Guardar producto")

            if submitted_prod:
                try:
                    nuevo_id = productos_service.crear_producto(
                        nombre=nombre,
                        detalle=detalle or None,
                        precio_compra=precio_compra,
                        precio_venta_unidad=precio_unidad,
                        precio_venta_blister=(
                            precio_blister if precio_blister > 0 else None
                        ),
                        stock_unidades=stock_unidades,
                        categoria=categoria or None,
                        unidades_por_blister=(
                            unidades_por_blister
                            if unidades_por_blister > 0
                            else None
                        ),
                    )
                    st.success(f"✅ Producto creado con id {nuevo_id}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al crear producto: {e}")

        # ---------- TAB 2: AÑADIR AL CARRITO ----------
        with tab_cart:
            st.markdown(
                """
                <div class="carrito-card">
                    <div class="carrito-card-title">Añadir al carrito</div>
                    <p class="carrito-card-sub">
                        Selecciona un producto del listado, define tipo de venta y cantidad,
                        y agrégalo al carrito actual.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if prod_sel is None:
                st.info("Primero registra o selecciona un producto para añadir al carrito.")
            else:
                st.text_input(
                    "Producto seleccionado",
                    value=selected_name,
                    disabled=True,
                )

                tipo = st.selectbox("Tipo de venta", ["unidad", "blister"])
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    value=1,
                    step=1,
                )
                fecha = st.date_input("Fecha", value=date.today())

                precio_unidad = float(prod_sel["Unidad"] or 0)
                precio_blister = (
                    float(prod_sel["Blister"] or 0)
                    if prod_sel["Blister"] is not None
                    else 0.0
                )
                unidades_por_blister = int(prod_sel["UnidadesBlister"] or 1)

                if tipo == "unidad":
                    price = precio_unidad
                else:
                    price = (
                        precio_blister
                        if precio_blister > 0
                        else precio_unidad * unidades_por_blister
                    )

                monto_default = round(price * cantidad, 2)
                monto = st.number_input(
                    "Monto (Q)",
                    min_value=0.0,
                    value=float(monto_default),
                    step=0.01,
                )

                if st.button(
                    "Añadir al carrito",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["carrito"].append(
                        {
                            "producto_id": int(prod_sel["id"]),  # 👈 clave usada por CarritoItem
                            "nombre": prod_sel["Nombre"],
                            "tipo": tipo,
                            "cantidad": int(cantidad),
                            "monto": float(monto),
                            "fecha": fecha.strftime("%Y-%m-%d"),
                        }
                    )
                    st.success("✅ Producto añadido al carrito.")

    # =========================
    #   TABLA CARRITO
    # =========================
    st.markdown("---")
    st.markdown(
        """
        <div class="carrito-card">
            <div class="carrito-card-title">🧾 Carrito actual</div>
            <p class="carrito-card-sub">
                Revisa las líneas añadidas, elimina registros si es necesario y registra la venta.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    carrito = st.session_state["carrito"]

    if carrito:
        df_cart = pd.DataFrame(carrito)

        df_cart_disp = df_cart.copy()
        df_cart_disp["Monto"] = df_cart_disp["monto"]
        df_cart_disp["Cant"] = df_cart_disp["cantidad"]
        df_cart_disp = df_cart_disp[["nombre", "tipo", "Cant", "Monto", "fecha"]]
        df_cart_disp.columns = ["Producto", "Tipo", "Cant", "Monto", "Fecha"]

        st.dataframe(df_cart_disp, use_container_width=True, hide_index=True)

        total = sum(i["monto"] for i in carrito)
        st.write(f"**Total:** Q {total:,.2f}")

        col_a, col_b = st.columns(2)

        # Eliminar línea del carrito
        with col_a:
            idx_del = st.number_input(
                "Índice a eliminar (1..N)",
                min_value=1,
                max_value=len(carrito),
                step=1,
                key="idx_del_cart",
            )
            if st.button("Eliminar del carrito"):
                carrito.pop(idx_del - 1)
                st.session_state["carrito"] = carrito
                st.rerun()

        # Registrar venta(s)
        with col_b:
            if st.button("Registrar venta(s)", type="primary"):
                try:
                    ventas_service.registrar_ventas_desde_carrito(
                        carrito,
                        id_usuario,
                    )
                except Exception as e:
                    st.error(f"❌ Ocurrió un error al registrar la venta: {e}")
                else:
                    st.session_state["carrito"] = []
                    st.success("✅ Venta(s) registrada(s) correctamente.")
                    st.rerun()
    else:
        st.info("El carrito está vacío.")
