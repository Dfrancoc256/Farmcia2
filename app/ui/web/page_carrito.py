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
                    Desde aquí puedes registrar productos, añadirlos al carrito
                    y editar / desactivar productos existentes.
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

    # =========================
    #   LAYOUT PRINCIPAL
    # =========================
    col_left, col_right = st.columns([2, 1])

    # ======================================================
    #   IZQUIERDA: LISTADO DE PRODUCTOS (AGGRID)
    # ======================================================
    with col_left:
        st.markdown(
            """
            <div class="carrito-card">
                <div class="carrito-card-title">📑 Listado de productos</div>
                <p class="carrito-card-sub">
                    Busca y selecciona un producto para añadirlo al carrito
                    o editarlo.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Buscar + refrescar
        col_buscar, col_refresh = st.columns([3, 1])
        with col_buscar:
            q = st.text_input("Buscar producto", "")
        with col_refresh:
            if st.button("🔄 Actualizar listado"):
                st.rerun()

        df_view = df_prods.copy()

        # ----- BÚSQUEDA INTELIGENTE: nombre + detalle + categoría -----
        if q:
            terms = [t.strip() for t in q.split() if t.strip()]
            if terms:
                mask = pd.Series(False, index=df_prods.index)

                for term in terms:
                    term_mask = (
                        df_prods["Nombre"]
                        .astype(str)
                        .str.contains(term, case=False, na=False)
                        | df_prods.get(
                            "Detalle", pd.Series("", index=df_prods.index)
                        )
                        .astype(str)
                        .str.contains(term, case=False, na=False)
                        | df_prods.get(
                            "Categoria", pd.Series("", index=df_prods.index)
                        )
                        .astype(str)
                        .str.contains(term, case=False, na=False)
                    )
                    mask = mask | term_mask

                df_view = df_prods[mask]
            else:
                df_view = df_prods.copy()

        prod_sel_dict = None

        if not df_view.empty:
            columnas_grid = [
                "Nombre",
                "Detalle",
                "Compra",
                "Unidad",
                "Blister",
                "Caja",
                "StockUnidades",
            ]

            gb = GridOptionsBuilder.from_dataframe(df_view[columnas_grid])
            gb.configure_selection("single", use_checkbox=False)
            gb.configure_grid_options(domLayout="normal")
            grid_options = gb.build()

            grid_response = AgGrid(
                df_view[columnas_grid],
                gridOptions=grid_options,
                height=360,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                allow_unsafe_jscode=True,
                theme="alpine",
            )

            selected_rows = grid_response["selected_rows"]

            if isinstance(selected_rows, list) and selected_rows:
                selected_name = selected_rows[0].get("Nombre")
                if selected_name:
                    matches = df_prods[df_prods["Nombre"] == selected_name]
                    if not matches.empty:
                        prod_sel_dict = matches.iloc[0].to_dict()
            elif isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
                selected_name = selected_rows.iloc[0].get("Nombre")
                matches = df_prods[df_prods["Nombre"] == selected_name]
                if not matches.empty:
                    prod_sel_dict = matches.iloc[0].to_dict()

            if prod_sel_dict is not None:
                st.session_state["prod_selected_full"] = prod_sel_dict
        else:
            st.info(
                "No hay productos para mostrar con el filtro actual. "
                "Limpia el buscador o registra un producto nuevo."
            )
            st.session_state["prod_selected_full"] = None

    # Objeto seleccionado completo (para las pestañas de la derecha)
    prod_sel = st.session_state.get("prod_selected_full")

    # ======================================================
    #   DERECHA: PESTAÑAS (REGISTRAR / CARRITO / EDITAR)
    # ======================================================
    with col_right:
        st.markdown(
            """
            <div class="carrito-card">
                <div class="carrito-card-title">Producto</div>
                <p class="carrito-card-sub">
                    Usa las pestañas para registrar productos, añadir al carrito
                    o editar / desactivar el producto seleccionado.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_reg, tab_cart, tab_edit = st.tabs(
            ["➕ Registrar producto", "🛒 Añadir al carrito", "✏️ Editar / eliminar"]
        )

        # ==================================================
        #   TAB 1: REGISTRAR PRODUCTO
        # ==================================================
        with tab_reg:
            with st.form("form_reg_producto"):
                nombre_reg = st.text_input("Nombre del producto", key="reg_nombre")
                detalle_reg = st.text_input("Detalle / descripción", key="reg_detalle")
                categoria_reg = st.text_input(
                    "Categoría / palabras clave",
                    key="reg_categoria",
                    help="Ej: dolor, fiebre, antibiótico… (sirve para el buscador).",
                )

                precio_compra_reg = st.number_input(
                    "Precio compra (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="reg_precio_compra",
                )
                precio_unidad_reg = st.number_input(
                    "Precio venta unidad (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="reg_precio_unidad",
                )
                precio_blister_reg = st.number_input(
                    "Precio venta blister (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="reg_precio_blister",
                    help="Si el producto no se vende por blister, puedes dejarlo en 0.",
                )
                # NUEVO: precio venta caja
                precio_caja_reg = st.number_input(
                    "Precio venta caja (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="reg_precio_caja",
                    help="Si el producto no se vende por caja, puedes dejarlo en 0.",
                )

                unidades_blister_reg = st.number_input(
                    "Unidades por blister",
                    min_value=0,
                    step=1,
                    key="reg_unidades_blister",
                    help="0 si no aplica blister.",
                )

                stock_inicial_reg = st.number_input(
                    "Stock inicial (unidades)",
                    min_value=0,
                    step=1,
                    key="reg_stock_inicial",
                    help="Cantidad disponible al registrar el producto.",
                )

                submitted_reg = st.form_submit_button("Guardar producto", type="primary")

            if submitted_reg:
                try:
                    nuevo_id = productos_service.crear_producto(
                        nombre=nombre_reg,
                        detalle=detalle_reg or None,
                        precio_compra=precio_compra_reg,
                        precio_venta_unidad=precio_unidad_reg,
                        precio_venta_blister=(
                            precio_blister_reg if precio_blister_reg > 0 else None
                        ),
                        stock_unidades=stock_inicial_reg,
                        categoria=categoria_reg or None,
                        unidades_por_blister=(
                            unidades_blister_reg if unidades_blister_reg > 0 else None
                        ),
                        precio_venta_caja=precio_caja_reg,
                    )
                except Exception as e:
                    st.error(f"❌ Error al crear producto: {e}")
                else:
                    st.session_state["msg_producto_creado"] = (
                        f"✅ Producto '{nombre_reg}' creado con id {nuevo_id}."
                    )
                    st.rerun()

        # ==================================================
        #   TAB 2: AÑADIR AL CARRITO
        # ==================================================
        with tab_cart:
            st.markdown(
                """
                <div class="carrito-card">
                    <div class="carrito-card-title">Añadir al carrito</div>
                    <p class="carrito-card-sub">
                        Selecciona un producto del listado, define tipo de venta y cantidad
                        y agrégalo al carrito actual.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not prod_sel:
                st.info(
                    "Selecciona un producto en la tabla de la izquierda para añadirlo al carrito."
                )
            else:
                st.text_input(
                    "Producto seleccionado",
                    value=prod_sel.get("Nombre", ""),
                    disabled=True,
                )

                # Ahora permitimos unidad / blister / caja
                tipo = st.selectbox("Tipo de venta", ["unidad", "blister", "caja"])
                cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
                fecha = st.date_input("Fecha", value=date.today())

                precio_unidad = float(prod_sel.get("Unidad", 0) or 0)
                precio_blister = float(prod_sel.get("Blister", 0) or 0)
                precio_caja = float(prod_sel.get("Caja", 0) or 0)
                unidades_por_blister = int(prod_sel.get("UnidadesBlister", 1) or 1)

                if tipo == "unidad":
                    price = precio_unidad
                elif tipo == "blister":
                    price = (
                        precio_blister
                        if precio_blister > 0
                        else precio_unidad * unidades_por_blister
                    )
                else:  # tipo == "caja"
                    if precio_caja > 0:
                        price = precio_caja
                    else:
                        st.warning(
                            "Este producto no tiene precio por caja configurado. "
                            "Se usará el precio por unidad."
                        )
                        price = precio_unidad

                monto_default = round(price * cantidad, 2)
                monto = st.number_input(
                    "Monto (Q)",
                    min_value=0.0,
                    value=float(monto_default),
                    step=0.01,
                )

                if st.button("Añadir al carrito", use_container_width=True):
                    st.session_state["carrito"].append(
                        {
                            "producto_id": int(prod_sel["id"]),
                            "nombre": prod_sel["Nombre"],
                            "tipo": tipo,
                            "cantidad": int(cantidad),
                            "monto": float(monto),
                            "fecha": fecha.strftime("%Y-%m-%d"),
                        }
                    )
                    st.success("✅ Producto añadido al carrito.")

        # ==================================================
        #   TAB 3: EDITAR / ELIMINAR (incluye edición de stock)
        # ==================================================
        with tab_edit:
            # Sincronizamos los campos edit_* cada vez que cambia la selección
            if prod_sel:
                current_id = int(prod_sel.get("id"))
                last_id = st.session_state.get("edit_id")
                if current_id != last_id:
                    st.session_state["edit_id"] = current_id
                    st.session_state["edit_nombre"] = prod_sel.get("Nombre", "") or ""
                    st.session_state["edit_detalle"] = prod_sel.get("Detalle", "") or ""
                    st.session_state["edit_categoria"] = (
                        prod_sel.get("Categoria", "") or ""
                    )
                    st.session_state["edit_precio_compra"] = float(
                        prod_sel.get("Compra", 0.0) or 0.0
                    )
                    st.session_state["edit_precio_unidad"] = float(
                        prod_sel.get("Unidad", 0.0) or 0.0
                    )
                    st.session_state["edit_precio_blister"] = float(
                        prod_sel.get("Blister", 0.0) or 0.0
                    )
                    st.session_state["edit_precio_caja"] = float(
                        prod_sel.get("Caja", 0.0) or 0.0
                    )
                    st.session_state["edit_unidades_blister"] = int(
                        prod_sel.get("UnidadesBlister", 0) or 0
                    )
                    stock_actual = int(prod_sel.get("StockUnidades", 0) or 0)
                    st.session_state["edit_stock_unidades"] = stock_actual
                    # guardamos el stock original para calcular delta
                    st.session_state["edit_stock_original"] = stock_actual

            with st.form("form_edit_producto"):
                nombre_edit = st.text_input(
                    "Nombre del producto", key="edit_nombre"
                )
                detalle_edit = st.text_input(
                    "Detalle / descripción", key="edit_detalle"
                )
                categoria_edit = st.text_input(
                    "Categoría / palabras clave",
                    key="edit_categoria",
                    help="Ej: dolor, fiebre, antibiótico… (sirve para el buscador).",
                )

                precio_compra_edit = st.number_input(
                    "Precio de compra (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="edit_precio_compra",
                )
                precio_unidad_edit = st.number_input(
                    "Precio venta unidad (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="edit_precio_unidad",
                )
                precio_blister_edit = st.number_input(
                    "Precio de venta blister (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="edit_precio_blister",
                    help="Si el producto no se vende por blister, puedes dejarlo en 0.",
                )
                precio_caja_edit = st.number_input(
                    "Precio venta caja (Q)",
                    min_value=0.0,
                    step=0.01,
                    key="edit_precio_caja",
                    help="Si el producto no se vende por caja, puedes dejarlo en 0.",
                )

                unidades_blister_edit = st.number_input(
                    "Unidades por blister",
                    min_value=0,
                    step=1,
                    key="edit_unidades_blister",
                    help="0 si no aplica blister.",
                )

                # AHORA SÍ editable
                stock_actual_edit = st.number_input(
                    "Stock actual (unidades)",
                    min_value=0,
                    step=1,
                    key="edit_stock_unidades",
                    help="Puedes ajustar el stock manualmente (se registra un movimiento).",
                )

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    submitted_edit = st.form_submit_button(
                        "Guardar cambios",
                        type="primary",
                        disabled=not prod_sel,
                    )
                with col_e2:
                    desactivar_click = st.form_submit_button(
                        "Desactivar producto", disabled=not prod_sel
                    )

            pid_edicion = st.session_state.get("edit_id")

            if submitted_edit:
                if not prod_sel or not pid_edicion:
                    st.warning("Selecciona un producto en la tabla para editarlo.")
                else:
                    try:
                        # 1) Actualizamos datos generales del producto (sin stock)
                        productos_service.update_producto_completo(
                            pid=pid_edicion,
                            nombre=nombre_edit,
                            detalle=detalle_edit or None,
                            categoria=categoria_edit or None,
                            precio_compra=precio_compra_edit,
                            precio_unidad=precio_unidad_edit,
                            precio_blister=(
                                precio_blister_edit
                                if precio_blister_edit > 0
                                else None
                            ),
                            unidades_blister=(
                                unidades_blister_edit
                                if unidades_blister_edit > 0
                                else None
                            ),
                            precio_caja=precio_caja_edit,
                        )

                        # 2) Ajustamos stock si cambió
                        stock_original = st.session_state.get(
                            "edit_stock_original", stock_actual_edit
                        )
                        delta = int(stock_actual_edit) - int(stock_original)
                        if delta != 0:
                            productos_service.ajustar_stock(
                                pid=pid_edicion,
                                delta=delta,
                                motivo="Ajuste manual desde edición",
                                referencia="page_carrito",
                            )

                    except Exception as e:
                        st.error(f"❌ Error al guardar producto: {e}")
                    else:
                        st.session_state["msg_producto_editado"] = (
                            f"✅ Producto '{nombre_edit}' actualizado correctamente."
                        )
                        st.rerun()

            if desactivar_click:
                if not prod_sel or not pid_edicion:
                    st.warning("Selecciona un producto en la tabla para desactivarlo.")
                else:
                    try:
                        productos_service.eliminar_producto(pid_edicion)
                    except Exception as e:
                        st.error(f"❌ Error al desactivar producto: {e}")
                    else:
                        st.success("✅ Producto desactivado correctamente.")
                        st.rerun()

    # ==================================================
    #   SECCIÓN CARRITO (CARRITO + VUELTO + RESUMEN)
    # ==================================================
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

        # Total del carrito
        total = sum(i["monto"] for i in carrito)
        st.write(f"**Total:** Q {total:,.2f}")

        # Monto pagado y cálculo de cambio
        monto_pagado = st.number_input(
            "Monto pagado por el cliente (Q)",
            min_value=0.0,
            step=0.01,
            key="monto_pagado",
        )

        cambio = None
        if monto_pagado > 0:
            if monto_pagado >= total:
                cambio = monto_pagado - total
                st.success(f"💵 Cambio a entregar: **Q {cambio:,.2f}**")
            else:
                st.warning(
                    "El monto pagado es menor que el total. "
                    "No se podrá registrar la venta hasta corregirlo."
                )

        col_a, col_b = st.columns(2)

        # Eliminar ítem del carrito
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
                if monto_pagado < total:
                    st.error(
                        "❌ El monto pagado no puede ser menor que el total de la venta."
                    )
                else:
                    try:
                        ventas_service.registrar_ventas_desde_carrito(
                            carrito,
                            id_usuario,
                        )
                    except Exception as e:
                        st.error(f"❌ Ocurrió un error al registrar la venta: {e}")
                    else:
                        st.session_state["carrito"] = []

                        if cambio is None:
                            cambio = max(monto_pagado - total, 0.0)

                        st.success("✅ Venta(s) registrada(s) correctamente.")
                        st.info(
                            f"**Resumen de la venta:**  \n"
                            f"- Total: **Q {total:,.2f}**  \n"
                            f"- Pagó: **Q {monto_pagado:,.2f}**  \n"
                            f"- Cambio entregado: **Q {cambio:,.2f}**"
                        )

                        if st.button("➕ Agregar más productos"):
                            st.rerun()
    else:
        st.info("El carrito está vacío.")
