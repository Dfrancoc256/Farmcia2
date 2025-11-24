# app/interfaz/app_sidebar.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from tkcalendar import DateEntry
from app.interfaz.productos_carrito import ProductosCarritoView
from app.core.database import conectar_bd

# ---- Paleta ----
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SURFACE = "#F8FAFC"
CARD = "#FFFFFF"
BORDER = "#E5E7EB"
TEXT = "#0F172A"
MUTED = "#64748B"


# =========================
#   APLICACIÓN PRINCIPAL
# =========================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Farmacia 2.0")
        self.geometry("1280x800")
        self.configure(bg=SURFACE)

        # grid base: [sidebar | content]
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # contenido
        self.grid_rowconfigure(0, weight=1)

        self._styles()
        self._sidebar()
        self._content_area()

        # vistas
        self.views = {}
        self._show_view("inventario")  # vista inicial

    def _styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Sidebar.TFrame", background="#0B1220")
        s.configure(
            "Sidebar.TButton",
            background="#0B1220",
            foreground="#E5E7EB",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padding=(14, 12),
        )
        s.map(
            "Sidebar.TButton",
            background=[("active", "#111827")],
            foreground=[("active", "#FFFFFF")],
        )

        s.configure("Header.TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 22, "bold"))
        s.configure("TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 10))
        s.configure("Card.TLabel", background=CARD, foreground=TEXT, font=("Segoe UI", 10))

        s.configure("Primary.TButton", background=PRIMARY, foreground="#FFFFFF",
                    font=("Segoe UI", 10, "bold"), padding=(12, 8))
        s.map("Primary.TButton", background=[("active", PRIMARY_HOVER)])
        s.configure("Secondary.TButton", background="#E5E7EB", foreground="#111827",
                    font=("Segoe UI", 10, "bold"), padding=(12, 8))
        s.map("Secondary.TButton", background=[("active", "#D1D5DB")])

        s.configure("m.Treeview", background="#FFFFFF", fieldbackground="#FFFFFF",
                    foreground=TEXT, bordercolor=BORDER, borderwidth=1,
                    rowheight=28, font=("Segoe UI", 10))
        s.configure("m.Treeview.Heading", background="#F1F5F9", foreground=TEXT,
                    relief="flat", font=("Segoe UI", 10, "bold"))

    def _sidebar(self):
        sidebar = ttk.Frame(self, style="Sidebar.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_rowconfigure(10, weight=1)  # empujar botones abajo

        # Logo / título
        tk.Label(sidebar, text="💊  Farmacia 2.0", bg="#0B1220", fg="#FFFFFF",
                 font=("Segoe UI", 14, "bold"), pady=16).grid(row=0, column=0, sticky="we", padx=14)

        # Botones del menú
        def btn(text, key, row):
            ttk.Button(sidebar, text=text, style="Sidebar.TButton",
                       command=lambda: self._show_view(key))\
                .grid(row=row, column=0, sticky="we", padx=6, pady=4)

        btn("📦  Productos / Carrito", "productos", 1)
        btn("📈  Inventario", "inventario", 2)
        btn("🧾  Gastos", "gastos", 3)
        btn("📘  Fiados", "fiados", 4)
        ttk.Separator(sidebar, orient="horizontal").grid(row=8, column=0, sticky="we", padx=8, pady=8)
        btn("⚙️  Configuración", "config", 9)

        # Footer
        tk.Label(sidebar, text="v2.0", bg="#0B1220", fg="#64748B", font=("Segoe UI", 9))\
            .grid(row=11, column=0, sticky="swe", padx=12, pady=12)

    def _content_area(self):
        self.content = tk.Frame(self, bg=SURFACE)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _show_view(self, key: str):
        # destruir vista anterior
        for child in self.content.winfo_children():
            child.destroy()

        if key == "inventario":
            view = InventarioUnificadoView(self.content)
        elif key == "productos":
            view = ProductosCarritoView(self.content)  # <<—— aquí llamas la vista nueva
        elif key in ("gastos", "fiados", "config"):
            view = PlaceholderView(self.content, title={
                "gastos": "Gastos",
                "fiados": "Fiados",
                "config": "Configuración"
            }[key], note="(Próximamente)")
        else:
            view = PlaceholderView(self.content, title="Pantalla", note="(Próximamente)")

        view.grid(row=0, column=0, sticky="nsew")
        self.views[key] = view


# ===================================
#   VISTA: INVENTARIO UNIFICADO
# ===================================
class InventarioUnificadoView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self.cn = conectar_bd()
        if not self.cn:
            messagebox.showerror("BD", "No hay conexión a SQL Server."); return

        self._build()

        hoy = date.today()
        self.var_desde.set(hoy.strftime("%Y-%m-%d"))
        self.var_hasta.set(hoy.strftime("%Y-%m-%d"))
        self._cargar()

    def _aplicar(self):
        self.var_desde.set(self.de_desde.get_date().strftime("%Y-%m-%d"))
        self.var_hasta.set(self.de_hasta.get_date().strftime("%Y-%m-%d"))
        self._cargar()

    # ---- UI Inventario ----
    def _build(self):
        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(header, text="Inventario General", style="Header.TLabel").pack(side="left")

        # Filtros
        filtros = tk.Frame(self, bg=SURFACE)
        filtros.pack(fill="x", padx=16, pady=(0, 8))
        self.var_desde, self.var_hasta = tk.StringVar(), tk.StringVar()
        ttk.Label(filtros, text="Desde:").pack(side="left")
        self.de_desde = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_desde.pack(side="left", padx=(6, 12))
        ttk.Label(filtros, text="Hasta:").pack(side="left")
        self.de_hasta = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_hasta.pack(side="left", padx=(6, 12))
        ttk.Button(filtros, text="Aplicar", style="Primary.TButton",
                   command=self._aplicar).pack(side="left")
        ttk.Button(filtros, text="Hoy", style="Secondary.TButton",
                   command=self._set_hoy).pack(side="left", padx=(8, 0))
        ttk.Button(filtros, text="Este mes", style="Secondary.TButton",
                   command=self._set_mes).pack(side="left", padx=(8, 0))

        # Body layout (más ancho a la izquierda / derecho angosto)
        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=6)  # listado
        body.grid_columnconfigure(1, weight=3)  # panel totales
        body.grid_rowconfigure(0, weight=1)

        # --- Tabla izquierda ---
        card = tk.Frame(body, bg=CARD, bd=1, relief="solid",
                        highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        card.grid_rowconfigure(1, weight=1)

        ttk.Label(card, text="Movimientos (Ventas / Fiados / Egresos)",
                  style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=12, pady=12)

        cols = ("Fecha", "Tipo", "Persona", "Producto / Detalle", "Cantidad", "Monto (Q)", "Estado")
        self.tv = ttk.Treeview(card, columns=cols, show="headings",
                               style="m.Treeview", height=26)
        for c in cols:
            self.tv.heading(c, text=c)

        # anchos más equilibrados
        self.tv.column("Fecha", width=150, anchor="center")
        self.tv.column("Tipo", width=90, anchor="center")
        self.tv.column("Persona", width=160, anchor="w")
        self.tv.column("Producto / Detalle", width=480, anchor="w")
        self.tv.column("Cantidad", width=90, anchor="e")
        self.tv.column("Monto (Q)", width=120, anchor="e")
        self.tv.column("Estado", width=110, anchor="center")

        self.tv.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        vs = ttk.Scrollbar(card, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=vs.set)
        vs.grid(row=1, column=0, sticky="nse", padx=(0, 12))

        # tags de filas
        self.tv.tag_configure("even", background="#F8FAFC")
        self.tv.tag_configure("odd", background="#FFFFFF")
        self.tv.tag_configure("venta", foreground="#16A34A")
        self.tv.tag_configure("egreso", foreground="#DC2626")
        self.tv.tag_configure("fiado", foreground="#0EA5E9")

        self.row_meta = {}

        # --- Panel derecho (ancho fijo y limpio) ---
        right = tk.Frame(body, bg=CARD, bd=1, relief="solid",
                         highlightthickness=1, highlightbackground=BORDER,
                         width=360)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_propagate(False)

        ttk.Label(right, text="Totales", style="Card.TLabel") \
            .pack(anchor="w", padx=12, pady=(12, 4))

        self.lbl_ven = ttk.Label(right, text="Vendido: Q 0.00", style="Card.TLabel")
        self.lbl_gas = ttk.Label(right, text="Gastos: Q 0.00", style="Card.TLabel")
        self.lbl_fia = ttk.Label(right, text="Fiado (pend.): Q 0.00", style="Card.TLabel")
        self.lbl_bal = ttk.Label(right, text="Balance: Q 0.00", style="Card.TLabel")
        self.lbl_caj = ttk.Label(right, text="Caja (efectivo): Q 0.00", style="Card.TLabel")
        for w in (self.lbl_ven, self.lbl_gas, self.lbl_fia, self.lbl_bal, self.lbl_caj):
            w.pack(anchor="w", padx=16, pady=3)

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=12, pady=10)

        btns = tk.Frame(right, bg=CARD)
        btns.pack(fill="x", padx=12, pady=(2, 12))
        ttk.Button(btns, text="Agregar Gasto", style="Primary.TButton",
                   command=self._modal_gasto).pack(fill="x", pady=6)
        ttk.Button(btns, text="Agregar Fiado", style="Secondary.TButton",
                   command=self._modal_fiado).pack(fill="x", pady=6)
        ttk.Button(btns, text="Marcar Pagado (Fiado)", style="Primary.TButton",
                   command=self._marcar_pagado).pack(fill="x", pady=6)

    def _set_hoy(self):
        h = date.today()
        self.de_desde.set_date(h); self.de_hasta.set_date(h); self._aplicar()

    def _set_mes(self):
        h = date.today()
        self.de_desde.set_date(h.replace(day=1)); self.de_hasta.set_date(h); self._aplicar()

    # --- Carga de datos y totales ---
    def _cargar(self):
        d1, d2 = self.var_desde.get(), self.var_hasta.get()
        for iid in self.tv.get_children(): self.tv.delete(iid)
        self.row_meta.clear()

        # Ventas
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CONVERT(varchar(16), v.fecha, 120) AS fecha,
                       STRING_AGG(p.nombre + ' x' + CAST(d.cantidad AS varchar(10)), ', ')
                           WITHIN GROUP (ORDER BY d.id) AS detalle,
                       SUM(d.cantidad) AS cantidad,
                       CAST(SUM(d.cantidad * d.precio_unitario) AS float) AS monto
                FROM dbo.ventas v
                JOIN dbo.detalle_ventas d ON d.id_venta = v.id
                JOIN dbo.productos p ON p.id = d.id_producto
                WHERE v.fecha >= ? AND v.fecha < DATEADD(DAY,1,?)
                GROUP BY v.fecha
                ORDER BY v.fecha
            """, (d1, d2))
            ventas = cur.fetchall()

        # Gastos
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CONVERT(varchar(16), g.fecha, 120) AS fecha,
                       g.descripcion,
                       CAST(g.monto AS float) AS monto
                FROM dbo.gastos g
                WHERE g.fecha >= ? AND g.fecha < DATEADD(DAY,1,?)
                ORDER BY g.fecha
            """, (d1, d2))
            gastos = cur.fetchall()

        # Fiados
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT f.id, CONVERT(varchar(16), f.fecha, 120) AS fecha, ISNULL(f.estado,'Pendiente') AS estado,
                       f.nombre_cliente, f.producto, f.cantidad, CAST(f.monto AS float) AS monto
                FROM dbo.fiados f
                WHERE f.fecha >= ? AND f.fecha < DATEADD(DAY,1,?)
                ORDER BY f.fecha
            """, (d1, d2))
            fiados = cur.fetchall()

        # Poblar tabla
        n = 0
        for (fecha, det, cant, mon) in ventas:
            self.tv.insert("", "end",
                           values=(fecha, "Venta", "", det or "", int(cant or 0), f"{float(mon or 0):.2f}", ""),
                           tags=("venta", "even" if n % 2 == 0 else "odd")); n += 1
        for (fecha, desc, mon) in gastos:
            self.tv.insert("", "end",
                           values=(fecha, "Egreso", "", desc or "", "-", f"{float(mon or 0):.2f}", ""),
                           tags=("egreso", "even" if n % 2 == 0 else "odd")); n += 1
        for (fid, fecha, est, cli, prod, cant, mon) in fiados:
            iid = self.tv.insert("", "end",
                                 values=(fecha, "Fiado", cli or "", prod or "", int(cant or 0), f"{float(mon or 0):.2f}",
                                         est or "Pendiente"),
                                 tags=("fiado", "even" if n % 2 == 0 else "odd")); n += 1
            self.row_meta[iid] = {"tipo": "fiado", "id": int(fid)}

        # Totales
        total_v = sum(float(r[3] or 0) for r in ventas)
        total_g = sum(float(r[2] or 0) for r in gastos)  # gastos: (fecha, desc, monto) -> idx 2
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CAST(ISNULL(SUM(monto),0) AS float)
                FROM dbo.fiados
                WHERE (estado IS NULL OR estado <> 'Pagado')
                  AND fecha >= ? AND fecha < DATEADD(DAY,1,?)
            """, (d1, d2))
            fiado_pend = float(cur.fetchone()[0] or 0)
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CAST(ISNULL(SUM(total),0) AS float)
                FROM dbo.ventas
                WHERE fecha >= ? AND fecha < DATEADD(DAY,1,?)
                  AND (LOWER(ISNULL(tipo_pago,'efectivo'))='efectivo')
            """, (d1, d2))
            ventas_ef = float(cur.fetchone()[0] or 0)

        balance = total_v - total_g - fiado_pend
        caja = ventas_ef - total_g

        self.lbl_ven.config(text=f"Vendido: Q {total_v:,.2f}")
        self.lbl_gas.config(text=f"Gastos: Q {total_g:,.2f}")
        self.lbl_fia.config(text=f"Fiado (pend.): Q {fiado_pend:,.2f}")
        self.lbl_bal.config(text=f"Balance: Q {balance:,.2f}")
        self.lbl_caj.config(text=f"Caja (efectivo): Q {caja:,.2f}")

    # --- Acciones (modales resumidos) ---
    def _modal_gasto(self):
        win = tk.Toplevel(self); win.title("Agregar Gasto"); win.configure(bg=CARD); win.grab_set(); win.resizable(False, False)
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)
        ttk.Label(frm, text="Descripción:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_desc = ttk.Entry(frm, width=36); e_desc.grid(row=0, column=1, padx=8, pady=4)
        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=16); e_monto.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        de_f = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd"); de_f.set_date(date.today()); de_f.grid(row=2, column=1, padx=8, pady=4, sticky="w")
        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def save():
            try: monto = float((e_monto.get() or "0").replace(",", "."))
            except: messagebox.showwarning("Gasto", "Monto inválido."); return
            try:
                with self.cn.cursor() as cur:
                    cur.execute("INSERT INTO dbo.gastos(descripcion,monto,fecha) VALUES(?,?,?)",
                                (e_desc.get().strip(), monto, de_f.get_date().strftime("%Y-%m-%d")))
                    self.cn.commit()
                win.destroy(); self._cargar()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Gasto", str(e))
        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=save).pack(side="right")

    def _modal_fiado(self):
        win = tk.Toplevel(self); win.title("Agregar Fiado"); win.configure(bg=CARD); win.grab_set(); win.resizable(False, False)
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)
        ttk.Label(frm, text="Cliente:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_cli = ttk.Entry(frm, width=30); e_cli.grid(row=0, column=1, padx=8, pady=4)
        ttk.Label(frm, text="Producto:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        cb = ttk.Combobox(frm, width=34, state="readonly")
        with self.cn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM dbo.productos WHERE activo=1 ORDER BY nombre")
            prods = cur.fetchall()
        cb["values"] = [f"{i} - {n}" for i, n in prods]
        if cb["values"]: cb.current(0)
        cb.grid(row=1, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(frm, text="Cantidad:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        e_c = ttk.Entry(frm, width=12); e_c.insert(0, "1"); e_c.grid(row=2, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_m = ttk.Entry(frm, width=12); e_m.grid(row=3, column=1, padx=8, pady=4, sticky="w")
        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        de_f = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd"); de_f.set_date(date.today()); de_f.grid(row=4, column=1, padx=8, pady=4, sticky="w")
        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def save():
            if not cb.get(): messagebox.showwarning("Fiado", "Seleccione producto."); return
            try:
                pid = int(cb.get().split(" - ", 1)[0]); cant = int(e_c.get()); assert cant > 0
                monto = float((e_m.get() or "0").replace(",", "."))
            except Exception:
                messagebox.showwarning("Fiado", "Verifica cantidad y monto."); return
            try:
                with self.cn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dbo.fiados(nombre_cliente, producto, cantidad, monto, fecha, estado)
                        SELECT ?, p.nombre, ?, ?, ?, 'Pendiente' FROM dbo.productos p WHERE p.id=?
                    """, (e_cli.get().strip(), cant, monto, de_f.get_date().strftime("%Y-%m-%d"), pid))
                    cur.execute("UPDATE dbo.productos SET stock=stock-? WHERE id=?", (cant, pid))
                    self.cn.commit()
                win.destroy(); self._cargar()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Fiado", str(e))
        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=save).pack(side="right")

    def _marcar_pagado(self):
        sel = self.tv.selection()
        if not sel: messagebox.showinfo("Fiado", "Selecciona un fiado."); return
        iid = sel[0]; meta = self.row_meta.get(iid, {})
        if meta.get("tipo") != "fiado": messagebox.showinfo("Fiado", "La fila no es fiado."); return
        fid = meta.get("id")

        with self.cn.cursor() as cur:
            cur.execute("SELECT id,nombre_cliente,producto,cantidad,CAST(monto AS float),fecha,id_venta FROM dbo.fiados WHERE id=?", (fid,))
            row = cur.fetchone()
        if not row: messagebox.showerror("Fiado", "No encontrado."); return
        _id, cliente, producto, cant, monto, fecha_fiado, idv = row
        if idv: messagebox.showinfo("Fiado", f"Ya pagado (venta #{idv})."); return

        with self.cn.cursor() as cur:
            cur.execute("SELECT TOP 1 id FROM dbo.productos WHERE nombre=?", (producto,))
            prod = cur.fetchone()
        if not prod: messagebox.showerror("Fiado", "Producto no existe."); return
        id_producto = int(prod[0])

        if not messagebox.askyesno("Confirmar",
                                   f"Registrar pago Q{monto:.2f} de {cliente}.\n"
                                   f"Se creará venta con fecha {fecha_fiado.strftime('%Y-%m-%d')}."):
            return

        try:
            with self.cn.cursor() as cur:
                cur.execute("""INSERT INTO dbo.ventas (fecha,total,tipo_pago,observacion)
                               OUTPUT INSERTED.id VALUES (?,?, 'efectivo', ?)""",
                            (fecha_fiado, float(monto), f"Pago fiado {cliente}"))
                idv = int(cur.fetchone()[0])
                precio_u = float(monto) / max(int(cant), 1)
                cur.execute("""INSERT INTO dbo.detalle_ventas(id_venta,id_producto,tipo,cantidad,precio_unitario)
                               VALUES(?,?,'unidad',?,?)""",
                            (idv, id_producto, int(cant), float(precio_u)))
                cur.execute("""UPDATE dbo.fiados SET estado='Pagado', fecha_pago=GETDATE(), id_venta=? WHERE id=?""",
                            (idv, fid))
                self.cn.commit()
            self._cargar()
        except Exception as e:
            self.cn.rollback(); messagebox.showerror("Fiado", str(e))


# ===================================
#   VISTA: PRODUCTOS / CARRITO
# ===================================
class ProductosCarritoView(tk.Frame):

    def _editar_producto_fila(self, iid: str):
        """Selecciona la fila y abre el modal de edición."""
        if iid:
            self.tv_prod.selection_set(iid)
        self._editar_producto()

    def _agregar_producto_fila(self, iid: str):
        """Selecciona la fila y abre el modal para añadir al carrito."""
        if iid:
            self.tv_prod.selection_set(iid)
        self._modal_add_carrito()

    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self.cn = conectar_bd()
        if not self.cn:
            messagebox.showerror("BD", "No hay conexión a SQL Server."); return

        self.carrito = []  # [{'id':..,'nombre':..,'tipo':'unidad'|'blister','cantidad':int,'monto':float,'fecha':'YYYY-MM-DD'}]
        self._build()
        self._cargar_productos()
        self._refrescar_carrito()

    def _get_price_columns(self, cur):
        """
        Devuelve (pu_col, pb_col) con los nombres de columnas a usar para
        precio unidad y precio blister según lo que exista en dbo.productos.
        Solo elige de esta whitelist para evitar inyección.
        """
        candidates_u = ["precio_unidad", "precio_venta_unidad", "precio_unitario"]
        candidates_b = ["precio_blister", "precio_venta_blister"]

        cur.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='productos'
        """)
        cols = {r[0].lower() for r in cur.fetchall()}

        pu = next((c for c in candidates_u if c in cols), None)
        pb = next((c for c in candidates_b if c in cols), None)

        if not pu:
            raise RuntimeError(
                "No se encontró una columna de precio por unidad. "
                "Crea 'precio_unidad' o usa 'precio_venta_unidad' / 'precio_unitario'."
            )
        if not pb:
            pb = None  # si no hay blister, usamos 0

        return pu, pb

    # ---------- UI Productos / Carrito ----------
    def _cargar_productos(self):
        self.products = []
        self.tv_prod.delete(*self.tv_prod.get_children())
        with self.cn.cursor() as cur:
            pu_col, pb_col = self._get_price_columns(cur)
            if pb_col:
                sql = f"""
                    SELECT id, nombre,
                           CAST(precio_compra AS float) AS pc,
                           CAST({pu_col} AS float)     AS pu,
                           CAST({pb_col} AS float)     AS pb
                    FROM dbo.productos
                    WHERE activo = 1
                    ORDER BY nombre
                """
            else:
                sql = f"""
                    SELECT id, nombre,
                           CAST(precio_compra AS float) AS pc,
                           CAST({pu_col} AS float)      AS pu,
                           CAST(0 AS float)             AS pb
                    FROM dbo.productos
                    WHERE activo = 1
                    ORDER BY nombre
                """
            cur.execute(sql)
            self.products = cur.fetchall()

        for (pid, nom, pc, pu, pb) in self.products:
            self.tv_prod.insert(
                "", "end", iid=f"P{pid}",
                values=(nom, f"{pc:.2f}", f"{pu:.2f}", f"{pb:.2f}", "Editar", "Añadir")
            )

    # ---------- Data ----------
    def _build(self):
        # ===== Header =====
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(header, text="Productos / Carrito", style="Header.TLabel").pack(anchor="w")

        # ===== Layout =====
        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=7)  # productos
        body.grid_columnconfigure(1, weight=3)  # carrito
        body.grid_rowconfigure(0, weight=1)

        # ==========================
        #   IZQUIERDA: PRODUCTOS
        # ==========================
        left = tk.Frame(body, bg=CARD, bd=1, relief="solid",
                        highlightthickness=1, highlightbackground=BORDER)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(3, weight=1)

        # Búsqueda
        top = tk.Frame(left, bg=CARD)
        top.grid(row=0, column=0, sticky="we", padx=12, pady=10)
        ttk.Label(top, text="Buscar:", style="Card.TLabel").pack(side="left")
        self.var_buscar = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.var_buscar, width=48)
        ent.pack(side="left", padx=(8, 0))
        ent.bind("<KeyRelease>", lambda e: self._filtrar())

        ttk.Label(left, text="Listado", style="Card.TLabel",
                  font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", padx=12)

        # Contenedor tabla + scrollbar
        prod_container = tk.Frame(left, bg=CARD)
        prod_container.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        prod_container.grid_rowconfigure(0, weight=1)
        prod_container.grid_columnconfigure(0, weight=1)

        # Tabla de productos con columnas de acción
        cols = ("Nombre", "Compra", "Unidad", "Blister", "Editar", "Añadir")
        self.tv_prod = ttk.Treeview(prod_container, columns=cols, show="headings",
                                    style="m.Treeview", height=20)
        for c in cols:
            self.tv_prod.heading(c, text=c)

        # anchos (primera columna estira)
        self.tv_prod.column("Nombre", width=420, anchor="w", stretch=True)
        self.tv_prod.column("Compra", width=80, anchor="e", stretch=False)
        self.tv_prod.column("Unidad", width=80, anchor="e", stretch=False)
        self.tv_prod.column("Blister", width=80, anchor="e", stretch=False)
        self.tv_prod.column("Editar", width=80, anchor="center", stretch=False)
        self.tv_prod.column("Añadir", width=80, anchor="center", stretch=False)

        self.tv_prod.grid(row=0, column=0, sticky="nsew")
        vs_prod = ttk.Scrollbar(prod_container, orient="vertical", command=self.tv_prod.yview)
        self.tv_prod.configure(yscrollcommand=vs_prod.set)
        vs_prod.grid(row=0, column=1, sticky="ns")

        # Eventos para acciones
        self.tv_prod.bind("<Button-1>", self._on_prod_click)
        self.tv_prod.bind("<Motion>", self._on_prod_motion)

        # ==========================
        #   DERECHA: CARRITO
        # ==========================
        right = tk.Frame(body, bg=CARD, bd=1, relief="solid",
                         highlightthickness=1, highlightbackground=BORDER)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)  # <- importante para que estire a lo ancho

        ttk.Label(right, text="Carrito", style="Card.TLabel",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=10)

        cart_container = tk.Frame(right, bg=CARD)
        cart_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        cart_container.grid_rowconfigure(0, weight=1)
        cart_container.grid_columnconfigure(0, weight=1)

        cols_c = ("Producto", "Tipo", "Cant", "Monto", "Fecha")
        self.tv_cart = ttk.Treeview(cart_container, columns=cols_c, show="headings",
                                    style="m.Treeview", height=16)
        for c in cols_c: self.tv_cart.heading(c, text=c)
        self.tv_cart.column("Producto", width=220, anchor="w", stretch=True)
        self.tv_cart.column("Tipo", width=70, anchor="center", stretch=False)
        self.tv_cart.column("Cant", width=60, anchor="e", stretch=False)
        self.tv_cart.column("Monto", width=90, anchor="e", stretch=False)
        self.tv_cart.column("Fecha", width=110, anchor="center", stretch=False)
        self.tv_cart.grid(row=0, column=0, sticky="nsew")

        vs_cart = ttk.Scrollbar(cart_container, orient="vertical", command=self.tv_cart.yview)
        self.tv_cart.configure(yscrollcommand=vs_cart.set)
        vs_cart.grid(row=0, column=1, sticky="ns")

        bottom = tk.Frame(right, bg=CARD)
        bottom.grid(row=2, column=0, sticky="we", padx=12, pady=(0, 12))
        self.lbl_total = ttk.Label(bottom, text="Total: Q 0.00",
                                   style="Card.TLabel", font=("Segoe UI", 11, "bold"))
        self.lbl_total.pack(side="left")
        ttk.Button(bottom, text="Eliminar selección", style="Secondary.TButton",
                   command=self._cart_eliminar).pack(side="right")
        ttk.Button(bottom, text="Finalizar venta", style="Primary.TButton",
                   command=self._finalizar_venta).pack(side="right", padx=(0, 8))

    def _filtrar(self):
        q = (self.var_buscar.get() or "").lower()
        self.tv_prod.delete(*self.tv_prod.get_children())
        for (pid, nom, pc, pu, pb) in self.products:
            if q in nom.lower():
                self.tv_prod.insert(
                    "", "end", iid=f"P{pid}",
                    values=(nom, f"{pc:.2f}", f"{pu:.2f}", f"{pb:.2f}", "Editar", "Añadir")
                )

    # ---------- Acciones producto ----------
    def _on_prod_click(self, event):
        col = self.tv_prod.identify_column(event.x)  # '#1'..'#6'
        row = self.tv_prod.identify_row(event.y)
        if not row:
            return
        if col == "#5":  # Editar
            self.tv_prod.selection_set(row)
            self._editar_producto()
        elif col == "#6":  # Añadir
            self.tv_prod.selection_set(row)
            self._modal_add_carrito()

    def _on_prod_motion(self, event):
        col = self.tv_prod.identify_column(event.x)
        # mano solo sobre columnas de acción
        if col in ("#5", "#6"):
            self.tv_prod.configure(cursor="hand2")
        else:
            self.tv_prod.configure(cursor="")

    def _get_selected_product(self):
        sel = self.tv_prod.selection()
        if not sel:
            messagebox.showinfo("Productos", "Selecciona un producto."); return None
        iid = sel[0]
        pid = int(iid[1:])
        for row in self.products:
            if row[0] == pid:
                return {"id": row[0], "nombre": row[1], "pc": float(row[2]), "pu": float(row[3]), "pb": float(row[4])}
        return None

    def _editar_producto(self):
        prod = self._get_selected_product()
        if not prod: return

        win = tk.Toplevel(self); win.title("Editar precios"); win.configure(bg=CARD); win.grab_set(); win.resizable(False, False)
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)
        ttk.Label(frm, text=prod["nombre"], style="Card.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        ttk.Label(frm, text="Precio compra:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_pc = ttk.Entry(frm, width=12); e_pc.insert(0, f"{prod['pc']:.2f}"); e_pc.grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(frm, text="Precio unidad:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        e_pu = ttk.Entry(frm, width=12); e_pu.insert(0, f"{prod['pu']:.2f}"); e_pu.grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(frm, text="Precio blister:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_pb = ttk.Entry(frm, width=12); e_pb.insert(0, f"{prod['pb']:.2f}"); e_pb.grid(row=3, column=1, sticky="w", padx=8)

        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def guardar():
            try:
                pc = float((e_pc.get() or "0").replace(",", "."))
                pu = float((e_pu.get() or "0").replace(",", "."))
                pb = float((e_pb.get() or "0").replace(",", "."))
            except:
                messagebox.showwarning("Precios", "Valores inválidos."); return
            try:
                with self.cn.cursor() as cur:
                    cur.execute("""
                        UPDATE dbo.productos
                           SET precio_compra=?, precio_unidad=?, precio_blister=?
                         WHERE id=?
                    """, (pc, pu, pb, prod["id"]))
                    self.cn.commit()
                messagebox.showinfo("Precios", "Actualizado.")
                win.destroy()
                self._cargar_productos()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("BD", str(e))

        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=guardar).pack(side="right")

    def _modal_add_carrito(self):
        prod = self._get_selected_product()
        if not prod: return

        win = tk.Toplevel(self); win.title("Añadir al carrito"); win.configure(bg=CARD); win.grab_set(); win.resizable(False, False)
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)
        ttk.Label(frm, text=prod["nombre"], style="Card.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

        ttk.Label(frm, text="Tipo:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        tipo = tk.StringVar(value="unidad")
        cb_tipo = ttk.Combobox(frm, textvariable=tipo, values=["unidad","blister"], state="readonly", width=12)
        cb_tipo.grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(frm, text="Cantidad:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        e_cant = ttk.Entry(frm, width=12); e_cant.insert(0, "1"); e_cant.grid(row=2, column=1, sticky="w", padx=8)

        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=12); e_monto.grid(row=3, column=1, sticky="w", padx=8)

        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        de_fecha = DateEntry(frm, width=12, date_pattern="yyyy-mm-dd"); de_fecha.set_date(date.today())
        de_fecha.grid(row=4, column=1, sticky="w", padx=8)

        # autocalcular monto según tipo * precio
        def _autocalc(*_):
            try:
                q = int(e_cant.get() or "1")
                price = prod["pu"] if tipo.get()=="unidad" else prod["pb"]
                e_monto.delete(0, "end")
                e_monto.insert(0, f"{q*price:.2f}")
            except:
                pass
        tipo.trace_add("write", _autocalc)
        e_cant.bind("<KeyRelease>", _autocalc)
        _autocalc()

        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def add():
            try:
                q = int(e_cant.get()); assert q>0
                m = float((e_monto.get() or "0").replace(",", "."))
            except:
                messagebox.showwarning("Carrito","Cantidad o monto inválidos."); return
            self.carrito.append({
                "id": prod["id"], "nombre": prod["nombre"],
                "tipo": tipo.get(), "cantidad": q, "monto": m,
                "fecha": de_fecha.get_date().strftime("%Y-%m-%d")
            })
            win.destroy()
            self._refrescar_carrito()

        ttk.Button(btns, text="Añadir", style="Primary.TButton", command=add).pack(side="right")

    # ---------- Carrito ----------
    def _refrescar_carrito(self):
        self.tv_cart.delete(*self.tv_cart.get_children())
        total = 0.0
        for i, it in enumerate(self.carrito, start=1):
            total += float(it["monto"] or 0.0)
            self.tv_cart.insert("", "end", iid=f"C{i}",
                                values=(it["nombre"], it["tipo"], it["cantidad"], f"{it['monto']:.2f}", it["fecha"]))
        self.lbl_total.config(text=f"Total: Q {total:,.2f}")

    def _cart_eliminar(self):
        sel = self.tv_cart.selection()
        if not sel: return
        idxs = sorted([int(iid[1:])-1 for iid in sel], reverse=True)
        for i in idxs:
            if 0 <= i < len(self.carrito):
                self.carrito.pop(i)
        self._refrescar_carrito()

    def _finalizar_venta(self):
        if not self.carrito:
            messagebox.showinfo("Venta","El carrito está vacío."); return
        if not messagebox.askyesno("Confirmar", "¿Registrar la(s) venta(s) del carrito? Se generará una venta por cada fecha de ítem."):
            return
        try:
            with self.cn.cursor() as cur:
                # agrupamos por fecha para crear una venta por fecha
                by_date = {}
                for it in self.carrito:
                    by_date.setdefault(it["fecha"], []).append(it)

                for fecha, items in by_date.items():
                    total = sum(float(i["monto"]) for i in items)
                    cur.execute("""
                        INSERT INTO dbo.ventas(fecha,total,tipo_pago,observacion)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, 'efectivo', 'Venta app carrito')
                    """, (fecha, float(total)))
                    idv = int(cur.fetchone()[0])
                    for i in items:
                        punit = float(i["monto"]) / max(1, int(i["cantidad"]))
                        cur.execute("""
                            INSERT INTO dbo.detalle_ventas(id_venta,id_producto,tipo,cantidad,precio_unitario)
                            VALUES (?, ?, ?, ?, ?)
                        """, (idv, int(i["id"]), i["tipo"], int(i["cantidad"]), float(punit)))
                        # descontar stock
                        cur.execute("UPDATE dbo.productos SET stock = stock - ? WHERE id=?", (int(i["cantidad"]), int(i["id"])))
            self.cn.commit()

            self.carrito.clear()
            self._refrescar_carrito()
            messagebox.showinfo("Venta", "Venta(s) registrada(s) correctamente.")
        except Exception as e:
            self.cn.rollback()
            messagebox.showerror("Venta", f"Ocurrió un error:\n{e}")


# ===================================
#   PLACEHOLDER
# ===================================
class PlaceholderView(tk.Frame):
    def __init__(self, parent, title="Pantalla", note=""):
        super().__init__(parent, bg=SURFACE)
        header = tk.Frame(self, bg=SURFACE); header.pack(fill="x", padx=16, pady=(18, 10))
        ttk.Label(header, text=title, style="Header.TLabel").pack(anchor="w")
        card = tk.Frame(self, bg=CARD, bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=12)
        ttk.Label(card, text=f"{note}", style="Card.TLabel").pack(padx=16, pady=16, anchor="w")


if __name__ == "__main__":
    MainApp().mainloop()
