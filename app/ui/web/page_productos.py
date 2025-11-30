import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from app.services.productos_service import ProductosService

# Opciones de presentación (lista fija)
PRESENTACION_OPCIONES = [
    "Capsula",
    "Frasco",
    "Ampolla",
    "Bebible",
    "Bolsa",
    "Jarabe",
    "Gotero",
    "Tableta",
    "Otro",  # cuando es "Otro" se usa el campo de texto
]


def render_listado_productos(df_prods: pd.DataFrame) -> None:
    """
    Renderiza el listado de productos en la columna izquierda (AgGrid)
    y deja en st.session_state["prod_selected_full"] el producto seleccionado.
    """
    st.markdown(
        """
        <div class="carrito-card">
            <div class="carrito-card-title">📑 Listado de productos</div>
            <p class="carrito-card-sub">
                Busca y selecciona un producto para editarlo o añadirlo al carrito.
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

    # Aseguramos que la columna Presentacion tenga lo que viene de la BD
    if "Presentacion" not in df_view.columns:
        if "presentacion" in df_view.columns:
            df_view["Presentacion"] = df_view["presentacion"]
        else:
            df_view["Presentacion"] = ""

    # ----- BÚSQUEDA: nombre + detalle + categoría + presentación -----
    if q:
        terms = [t.strip() for t in q.split() if t.strip()]
        if terms:
            mask = pd.Series(False, index=df_view.index)

            for term in terms:
                term_mask = (
                    df_view["Nombre"]
                    .astype(str)
                    .str.contains(term, case=False, na=False)
                    | df_view.get("Detalle", pd.Series("", index=df_view.index))
                    .astype(str)
                    .str.contains(term, case=False, na=False)
                    | df_view.get("Categoria", pd.Series("", index=df_view.index))
                    .astype(str)
                    .str.contains(term, case=False, na=False)
                    | df_view.get("Presentacion", pd.Series("", index=df_view.index))
                    .astype(str)
                    .str.contains(term, case=False, na=False)
                )
                mask = mask | term_mask

            df_view = df_view[mask]

    prod_sel_dict = None

    if not df_view.empty:
        columnas_grid = [
            "Nombre",
            "Presentacion",  # <-- entre Nombre y Detalle
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

        # Altura un poco mayor para aprovechar el espacio vertical
        grid_response = AgGrid(
            df_view[columnas_grid],
            gridOptions=grid_options,
            height=460,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
            theme="alpine",
        )

        selected_rows = grid_response["selected_rows"]

        if isinstance(selected_rows, list) and selected_rows:
            selected_name = selected_rows[0].get("Nombre")
            if selected_name:
                matches = df_view[df_view["Nombre"] == selected_name]
                if not matches.empty:
                    prod_sel_dict = matches.iloc[0].to_dict()
        elif isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
            selected_name = selected_rows.iloc[0].get("Nombre")
            matches = df_view[df_view["Nombre"] == selected_name]
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


def _presentacion_selector(prefix: str, valor_inicial: str | None = None) -> str:
    """
    Helper para manejar la presentación con:
    - Lista fija de opciones
    - Opción 'Otro' que permite escribir en un campo de texto.

    prefix: 'reg' o 'edit' para diferenciar las keys.
    valor_inicial: valor que viene de la BD para preseleccionar.
    """
    # Si el valor inicial está en la lista, lo usamos tal cual; si no, se trata como "Otro"
    if valor_inicial and valor_inicial in PRESENTACION_OPCIONES and valor_inicial != "Otro":
        opcion_default = valor_inicial
        texto_default = ""
    elif valor_inicial and valor_inicial not in (None, "", "Otro"):
        opcion_default = "Otro"
        texto_default = valor_inicial
    else:
        opcion_default = PRESENTACION_OPCIONES[0]
        texto_default = ""

    opcion = st.selectbox(
        "Presentación",
        PRESENTACION_OPCIONES,
        index=PRESENTACION_OPCIONES.index(opcion_default),
        key=f"{prefix}_presentacion_opcion",
    )

    if opcion == "Otro":
        texto = st.text_input(
            "Escribe la presentación",
            value=texto_default,
            key=f"{prefix}_presentacion_otro",
        )
        return texto.strip()
    else:
        # Limpiamos cualquier valor anterior del texto libre, solo por orden
        st.session_state[f"{prefix}_presentacion_otro"] = ""
        return opcion


def render_registrar_producto_tab(productos_service: ProductosService) -> None:
    """
    Renderiza la pestaña de registro de producto.
    """
    with st.form("form_reg_producto"):
        nombre_reg = st.text_input("Nombre del producto", key="reg_nombre")

        # Presentación con lista + 'Otro' editable
        presentacion_final_reg = _presentacion_selector(prefix="reg")

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
        precios_venta = [
            precio_unidad_reg,
            precio_blister_reg,
            precio_caja_reg,
        ]
        precios_venta_positivos = [p for p in precios_venta if p > 0]

        if precio_compra_reg > 0 and not precios_venta_positivos:
            st.error(
                "Si existe un precio de compra, debe haber al menos un "
                "precio de venta (unidad, blister o caja) mayor que 0."
            )
        else:
            try:
                nuevo_id = productos_service.crear_producto(
                    nombre=nombre_reg,
                    detalle=detalle_reg or None,
                    presentacion=presentacion_final_reg or None,
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


def render_editar_producto_tab(
    df_prods: pd.DataFrame,
    productos_service: ProductosService,
) -> None:
    """
    Renderiza la pestaña de edición / eliminación.
    Usa el producto seleccionado en st.session_state["prod_selected_full"].
    """
    prod_sel = st.session_state.get("prod_selected_full")

    # Sincronizamos SOLO cuando cambia el producto seleccionado
    if prod_sel:
        current_id = int(prod_sel.get("id"))
        last_id = st.session_state.get("edit_id")

        if current_id != last_id:
            st.session_state["edit_id"] = current_id

            # Tomamos la fila actualizada desde df_prods usando el id
            row_df = df_prods[df_prods["id"] == current_id]
            if not row_df.empty:
                row = row_df.iloc[0]
            else:
                row = pd.Series(prod_sel)

            st.session_state["edit_nombre"] = row.get("Nombre", "") or ""
            st.session_state["edit_detalle"] = row.get("Detalle", "") or ""
            st.session_state["edit_categoria"] = row.get("Categoria", "") or ""

            # Presentación (valor inicial para el helper)
            st.session_state["edit_presentacion_valor"] = (
                row.get("Presentacion", "") or ""
            )

            st.session_state["edit_precio_compra"] = float(
                row.get("Compra", 0.0) or 0.0
            )
            st.session_state["edit_precio_unidad"] = float(
                row.get("Unidad", 0.0) or 0.0
            )
            st.session_state["edit_precio_blister"] = float(
                row.get("Blister", 0.0) or 0.0
            )
            st.session_state["edit_precio_caja"] = float(row.get("Caja", 0.0) or 0.0)

            # Unidades por blister
            unidades_val = row.get("UnidadesBlister", 0)
            if unidades_val is None or pd.isna(unidades_val):
                unidades_val = 0
            st.session_state["edit_unidades_blister"] = int(unidades_val)

            # Stock actual
            stock_val = row.get("StockUnidades", 0)
            if stock_val is None or pd.isna(stock_val):
                stock_val = 0
            stock_actual = int(stock_val)

            st.session_state["edit_stock_unidades"] = stock_actual
            st.session_state["edit_stock_original"] = stock_actual

    with st.form("form_edit_producto"):
        nombre_edit = st.text_input("Nombre del producto", key="edit_nombre")

        presentacion_valor_inicial = st.session_state.get(
            "edit_presentacion_valor", ""
        )
        presentacion_final_edit = _presentacion_selector(
            prefix="edit", valor_inicial=presentacion_valor_inicial
        )

        detalle_edit = st.text_input("Detalle / descripción", key="edit_detalle")
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
                productos_service.update_producto_completo(
                    pid=pid_edicion,
                    nombre=nombre_edit,
                    detalle=detalle_edit or None,
                    presentacion=presentacion_final_edit or None,
                    categoria=categoria_edit or None,
                    precio_compra=precio_compra_edit,
                    precio_unidad=precio_unidad_edit,
                    precio_blister=(
                        precio_blister_edit if precio_blister_edit > 0 else None
                    ),
                    unidades_blister=(
                        unidades_blister_edit if unidades_blister_edit > 0 else None
                    ),
                    precio_caja=precio_caja_edit,
                )

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
                st.session_state["edit_stock_original"] = int(stock_actual_edit)

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
