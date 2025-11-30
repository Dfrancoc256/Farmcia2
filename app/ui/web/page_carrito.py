import pandas as pd
import streamlit as st

from app.services.ventas_service import VentasService


def render_carrito_tab(
    ventas_service: VentasService,
    id_usuario: int,
    today,
) -> None:
    """
    Renderiza la pestaña de carrito:
    - Añadir producto seleccionado al carrito
    - Tabla de carrito
    - Cálculo de total, pago y cambio
    - Registro de venta(s)
    """

    st.markdown(
        """
        <div class="carrito-card">
            <div class="carrito-card-title">🛒 Carrito actual</div>
            <p class="carrito-card-sub">
                Selecciona un producto del listado, define tipo de venta y cantidad
                y agrégalo al carrito. Luego registra la venta.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prod_sel = st.session_state.get("prod_selected_full")
    carrito = st.session_state.get("carrito", [])

    # -------- Añadir al carrito --------
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

        tipo = st.selectbox("Tipo de venta", ["unidad", "blister", "caja"])
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
        fecha = st.date_input("Fecha", value=today)

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
            carrito.append(
                {
                    "producto_id": int(prod_sel["id"]),
                    "nombre": prod_sel["Nombre"],
                    "tipo": tipo,
                    "cantidad": int(cantidad),
                    "monto": float(monto),
                    "fecha": fecha.strftime("%Y-%m-%d"),
                }
            )
            st.session_state["carrito"] = carrito
            st.success("✅ Producto añadido al carrito.")

    # -------- Carrito actual + cobro --------
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

        # Eliminar ítem del carrito SELECCIONANDO PRODUCTO
        with col_a:
            opciones_eliminar = [
                f"{i + 1}. {item['nombre']} ({item['tipo']}) - Q {item['monto']:.2f}"
                for i, item in enumerate(carrito)
            ]

            idx_sel = st.selectbox(
                "Producto a eliminar",
                options=list(range(len(carrito))),
                format_func=lambda i: opciones_eliminar[i],
                key="carrito_item_a_eliminar",
            )

            if st.button("Eliminar del carrito"):
                carrito.pop(idx_sel)
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
