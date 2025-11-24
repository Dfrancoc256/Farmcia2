# app/interfaz/inventario_unificado.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from tkcalendar import DateEntry

from app.core.database import conectar_bd

# ======== Paleta / Tokens de diseño ========
PRIMARY = "#2563EB"   # azul moderno
PRIMARY_HOVER = "#1D4ED8"
SURFACE = "#F8FAFC"   # fondo gris muy claro
CARD = "#FFFFFF"      # tarjetas
BORDER = "#E5E7EB"
TEXT = "#0F172A"      # slate-900
MUTED = "#64748B"     # slate-500
SUCCESS = "#16A34A"   # verde
DANGER = "#DC2626"    # rojo
INFO = "#0EA5E9"      # cyan
WARNING = "#D97706"   # amber

FONT_BASE = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 22, "bold")

class InventarioUnificadoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Farmacia 2.0 — Inventario unificado")
        self.geometry("1200x760")
        self.configure(bg=SURFACE)

        self.cn = conectar_bd()
        if not self.cn:
            messagebox.showerror("BD", "No hay conexión a SQL Server.")
            self.destroy(); return

        self._styles()
        self._ui()

        hoy = date.today()
        self.var_desde.set(hoy.strftime("%Y-%m-%d"))
        self.var_hasta.set(hoy.strftime("%Y-%m-%d"))
        self._cargar()

    # ---------- Estilos ----------
    def _styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Labels / Cards
        self.style.configure("TLabel", background=SURFACE, foreground=TEXT, font=FONT_BASE)
        self.style.configure("Title.TLabel", background=SURFACE, foreground=TEXT, font=FONT_TITLE)
        self.style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=FONT_BASE)
        self.style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=FONT_BASE)

        # Entries
        self.style.configure(
            "TEntry",
            padding=6, borderwidth=1, relief="flat",
            fieldbackground="#FFFFFF",
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER
        )

        # Buttons
        self.style.configure("Primary.TButton", background=PRIMARY, foreground="#FFFFFF",
                             padding=(14, 8), font=FONT_BOLD, relief="flat")
        self.style.map("Primary.TButton", background=[("active", PRIMARY_HOVER)])

        self.style.configure("Secondary.TButton", background="#E5E7EB", foreground="#111827",
                             padding=(14, 8), font=FONT_BOLD, relief="flat")
        self.style.map("Secondary.TButton", background=[("active", "#D1D5DB")])

        # Treeview
        self.style.configure("m.Treeview",
                             background="#FFFFFF", fieldbackground="#FFFFFF",
                             foreground=TEXT, bordercolor=BORDER, borderwidth=1,
                             rowheight=30, font=FONT_BASE)
        self.style.configure("m.Treeview.Heading",
                             background="#F1F5F9", foreground=TEXT,
                             relief="flat", font=("Segoe UI", 10, "bold"))
        self.style.map("m.Treeview.Heading", background=[("active", "#E2E8F0")])

    # ---------- UI ----------
    def _ui(self):
        # Vars
        self.var_desde = tk.StringVar()
        self.var_hasta = tk.StringVar()

        # Header
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=16, pady=(14, 6))
        ttk.Label(header, text="Inventario General", style="Title.TLabel").pack(side="left")

        # Filtros
        filtros = tk.Frame(self, bg=SURFACE)
        filtros.pack(fill="x", padx=16, pady=(0, 8))

        ttk.Label(filtros, text="Desde:").pack(side="left")
        self.de_desde = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_desde.pack(side="left", padx=(6, 12))

        ttk.Label(filtros, text="Hasta:").pack(side="left")
        self.de_hasta = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_hasta.pack(side="left", padx=(6, 12))

        ttk.Button(filtros, text="Aplicar", style="Primary.TButton",
                   command=self._aplicar_filtro).pack(side="left")
        ttk.Button(filtros, text="Hoy", style="Secondary.TButton",
                   command=self._set_hoy).pack(side="left", padx=(8, 0))
        ttk.Button(filtros, text="Este mes", style="Secondary.TButton",
                   command=self._set_mes).pack(side="left", padx=(8, 0))

        # Layout principal
        body = tk.Frame(self, bg=SURFACE)
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Card centro
        center = tk.Frame(body, bg=CARD, bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER)
        center.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        center.grid_rowconfigure(1, weight=1)

        ttk.Label(center, text="Movimientos (Ventas / Fiados / Egresos)", style="Card.TLabel") \
            .grid(row=0, column=0, sticky="w", padx=12, pady=12)

        cols = ("Fecha", "Tipo", "Persona", "Producto / Detalle", "Cantidad", "Monto (Q)", "Estado")
        self.tv = ttk.Treeview(center, columns=cols, show="headings", style="m.Treeview", height=24)
        for c in cols:
            self.tv.heading(c, text=c)
        self.tv.column("Fecha", width=150, anchor="center")
        self.tv.column("Tipo", width=90, anchor="center")
        self.tv.column("Persona", width=170, anchor="w")
        self.tv.column("Producto / Detalle", width=410, anchor="w")
        self.tv.column("Cantidad", width=90, anchor="e")
        self.tv.column("Monto (Q)", width=120, anchor="e")
        self.tv.column("Estado", width=110, anchor="center")
        self.tv.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        sv = ttk.Scrollbar(center, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sv.set)
        sv.grid(row=1, column=0, sticky="nse", padx=(0, 12))

        # Zebra rows + tags tipo
        self.tv.tag_configure("even", background="#F8FAFC")
        self.tv.tag_configure("odd", background="#FFFFFF")
        self.tv.tag_configure("venta", foreground="#16A34A")  # verde
        self.tv.tag_configure("egreso", foreground="#DC2626")  # rojo
        self.tv.tag_configure("fiado", foreground="#0EA5E9")  # azul
        self.tv.tag_configure("badge-pagado", foreground="#0EA5E9")
        self.tv.tag_configure("badge-pendiente", foreground="#D97706")

        # meta por fila
        self.row_meta = {}

        # Card derecha
        right = tk.Frame(body, bg=CARD, bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER)
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Totales", style="Card.TLabel").pack(anchor="w", padx=12, pady=(12, 4))
        self.lbl_vendido = ttk.Label(right, text="Vendido: Q 0.00", style="Card.TLabel")
        self.lbl_gastos = ttk.Label(right, text="Gastos: Q 0.00", style="Card.TLabel")
        self.lbl_fiado = ttk.Label(right, text="Fiado (pend.): Q 0.00", style="Card.TLabel")
        self.lbl_balance = ttk.Label(right, text="Balance: Q 0.00", style="Card.TLabel")
        self.lbl_caja = ttk.Label(right, text="Caja (efectivo): Q 0.00", style="Card.TLabel")  # << NUEVA

        for w in (self.lbl_vendido, self.lbl_gastos, self.lbl_fiado, self.lbl_balance, self.lbl_caja):
            w.pack(anchor="w", padx=16, pady=3)

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=12, pady=10)

        actions = tk.Frame(right, bg=CARD)
        actions.pack(fill="x", padx=12, pady=(2, 12))
        ttk.Button(actions, text="Agregar Gasto", style="Primary.TButton",
                   command=self._modal_gasto).pack(fill="x", pady=6)
        ttk.Button(actions, text="Agregar Fiado", style="Secondary.TButton",
                   command=self._modal_fiado).pack(fill="x", pady=6)
        ttk.Button(actions, text="Marcar Pagado (Fiado)", style="Primary.TButton",
                   command=self._marcar_fiado_pagado).pack(fill="x", pady=6)

    # ---------- Filtros ----------
    def _aplicar_filtro(self):
        self.var_desde.set(self.de_desde.get_date().strftime("%Y-%m-%d"))
        self.var_hasta.set(self.de_hasta.get_date().strftime("%Y-%m-%d"))
        self._cargar()

    def _set_hoy(self):
        h = date.today()
        self.de_desde.set_date(h); self.de_hasta.set_date(h)
        self._aplicar_filtro()

    def _set_mes(self):
        h = date.today()
        self.de_desde.set_date(h.replace(day=1)); self.de_hasta.set_date(h)
        self._aplicar_filtro()

    # ---------- Carga de datos ----------
    def _marcar_fiado_pagado(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showinfo("Fiado", "Selecciona un fiado para marcar pagado."); return
        iid = sel[0]
        meta = self.row_meta.get(iid, {})
        if meta.get("tipo") != "fiado":
            messagebox.showinfo("Fiado", "La fila seleccionada no es un fiado."); return

        # ya pagado?
        estado = (self.tv.item(iid, "values")[6] or "").lower()
        if estado == "pagado":
            messagebox.showinfo("Fiado", "Ese fiado ya está pagado."); return

        fid = meta.get("id_fiado")
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT id, nombre_cliente, producto, cantidad, CAST(monto AS float) AS monto, fecha, id_venta
                FROM dbo.fiados WHERE id=?
            """, (fid,))
            row = cur.fetchone()
        if not row:
            messagebox.showerror("Fiado", "No se encontró el fiado."); return
        _id, cliente, producto, cantidad, monto, fecha_fiado, idv_ex = row
        if idv_ex:
            messagebox.showinfo("Fiado", f"Ya tiene venta asociada #{idv_ex}."); return

        # obtener id_producto por nombre
        with self.cn.cursor() as cur:
            cur.execute("SELECT TOP 1 id FROM dbo.productos WHERE nombre = ?", (producto,))
            r = cur.fetchone()
        if not r:
            messagebox.showerror("Fiado", f"No existe producto '{producto}' en productos."); return
        id_producto = int(r[0])

        if not messagebox.askyesno("Confirmar pago",
                                   f"Marcar pagado Q {monto:.2f} de {cliente}.\n"
                                   f"Se creará una venta con fecha {fecha_fiado.strftime('%Y-%m-%d')}.\n¿Continuar?"):
            return

        try:
            with self.cn.cursor() as cur:
                # Crear venta con fecha original del fiado
                cur.execute("""
                    INSERT INTO dbo.ventas (fecha, total, tipo_pago, observacion)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, 'efectivo', ?)
                """, (fecha_fiado, float(monto), f"Pago fiado {cliente}"))
                idv = int(cur.fetchone()[0])

                precio_unit = float(monto) / max(int(cantidad), 1)
                cur.execute("""
                    INSERT INTO dbo.detalle_ventas (id_venta, id_producto, tipo, cantidad, precio_unitario)
                    VALUES (?, ?, 'unidad', ?, ?)
                """, (idv, id_producto, int(cantidad), float(precio_unit)))

                cur.execute("""
                    UPDATE dbo.fiados
                       SET estado='Pagado',
                           fecha_pago=GETDATE(),
                           id_venta=?
                     WHERE id=?
                """, (idv, fid))

                self.cn.commit()

            messagebox.showinfo("Fiado", f"Fiado pagado. Venta #{idv} creada.")
            self._cargar()
        except Exception as e:
            self.cn.rollback()
            messagebox.showerror("Fiado", f"Ocurrió un error:\n{e}")

    # ---------- Acciones ----------
    def _modal_gasto(self):
        win = tk.Toplevel(self); win.title("Agregar Gasto"); win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)

        ttk.Label(frm, text="Descripción:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_desc = ttk.Entry(frm, width=34); e_desc.grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=16); e_monto.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        de_fecha = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd"); de_fecha.set_date(date.today())
        de_fecha.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Categoría:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_cat = ttk.Entry(frm, width=20); e_cat.grid(row=3, column=1, padx=8, pady=4, sticky="w")

        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def guardar():
            try: monto = float((e_monto.get() or "0").replace(",", "."))
            except: messagebox.showwarning("Gasto", "Monto inválido."); return
            try:
                with self.cn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dbo.gastos(descripcion, monto, fecha, categoria)
                        VALUES (?, ?, ?, ?)
                    """, (e_desc.get().strip(), monto, de_fecha.get_date().strftime("%Y-%m-%d"), e_cat.get().strip() or None))
                    self.cn.commit()
                messagebox.showinfo("Gasto", "Gasto registrado.")
                win.destroy(); self._cargar()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Gasto", f"Ocurrió un error:\n{e}")

        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=guardar).pack(side="right")

    def _cargar(self):
        d1, d2 = self.var_desde.get(), self.var_hasta.get()
        # limpiar tabla y meta
        for iid in self.tv.get_children():
            self.tv.delete(iid)
        self.row_meta.clear()

        # 1) Ventas (agregadas por documento)
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

        # 2) Gastos (egresos)
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

        # 3) Fiados del rango (para mostrar y para total de fiado pendiente)
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT f.id,
                       CONVERT(varchar(16), f.fecha, 120) AS fecha,
                       ISNULL(f.estado,'Pendiente') AS estado,
                       f.nombre_cliente,
                       f.producto,
                       f.cantidad,
                       CAST(f.monto AS float) AS monto
                FROM dbo.fiados f
                WHERE f.fecha >= ? AND f.fecha < DATEADD(DAY,1,?)
                ORDER BY f.fecha
            """, (d1, d2))
            fiados = cur.fetchall()

        # Poblar grilla con zebra + tags
        rownum = 0
        for (fecha, detalle, cant, monto) in ventas:
            tags = ("venta", "even" if rownum % 2 == 0 else "odd")
            iid = self.tv.insert("", "end",
                                 values=(fecha, "Venta", "", detalle or "", int(cant or 0), f"{float(monto or 0):.2f}",
                                         ""),
                                 tags=tags)
            self.row_meta[iid] = {"tipo": "venta"}
            rownum += 1

        for (fecha, desc, monto) in gastos:
            tags = ("egreso", "even" if rownum % 2 == 0 else "odd")
            iid = self.tv.insert("", "end",
                                 values=(fecha, "Egreso", "", desc or "", "-", f"{float(monto or 0):.2f}", ""),
                                 tags=tags)
            self.row_meta[iid] = {"tipo": "egreso"}
            rownum += 1

        for (fid, fecha, estado, cliente, producto, cant, monto) in fiados:
            tags = ("fiado", "even" if rownum % 2 == 0 else "odd",
                    "badge-pagado" if (estado or "").lower() == "pagado" else "badge-pendiente")
            iid = self.tv.insert("", "end",
                                 values=(fecha, "Fiado", cliente or "", producto or "",
                                         int(cant or 0), f"{float(monto or 0):.2f}", estado or "Pendiente"),
                                 tags=tags)
            self.row_meta[iid] = {"tipo": "fiado", "id_fiado": int(fid)}
            rownum += 1

        # -------- Totales --------
        total_vendido = sum((float(r[3] or 0) for r in ventas), 0.0)
        # en gastos r = (fecha, desc, monto) -> índice 2 = monto
        total_gastos = sum((float(r[2] or 0) for r in gastos), 0.0)

        # Fiado pendiente del rango
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CAST(ISNULL(SUM(monto),0) AS float)
                FROM dbo.fiados
                WHERE (estado IS NULL OR estado <> 'Pagado')
                  AND fecha >= ? AND fecha < DATEADD(DAY,1,?)
            """, (d1, d2))
            fiado_pend = float(cur.fetchone()[0] or 0)

        # Caja (efectivo): ventas en efectivo del rango - gastos
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CAST(ISNULL(SUM(total),0) AS float)
                FROM dbo.ventas
                WHERE fecha >= ? AND fecha < DATEADD(DAY,1,?)
                  AND (LOWER(ISNULL(tipo_pago,'efectivo')) = 'efectivo')
            """, (d1, d2))
            ventas_efectivo = float(cur.fetchone()[0] or 0)

        caja_efectivo = ventas_efectivo - total_gastos
        balance = total_vendido - total_gastos - fiado_pend

        # Pintar totales
        self.lbl_vendido.config(text=f"Vendido: Q {total_vendido:,.2f}")
        self.lbl_gastos.config(text=f"Gastos: Q {total_gastos:,.2f}")
        self.lbl_fiado.config(text=f"Fiado (pend.): Q {fiado_pend:,.2f}")
        self.lbl_balance.config(text=f"Balance: Q {balance:,.2f}")
        self.lbl_caja.config(text=f"Caja (efectivo): Q {caja_efectivo:,.2f}")

    # --------- Modales ---------

    def _modal_fiado(self):
        win = tk.Toplevel(self); win.title("Agregar Fiado"); win.configure(bg=CARD); win.resizable(False, False); win.grab_set()
        frm = tk.Frame(win, bg=CARD); frm.pack(padx=16, pady=12)

        ttk.Label(frm, text="Cliente:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_cli = ttk.Entry(frm, width=30); e_cli.grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frm, text="Teléfono:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_tel = ttk.Entry(frm, width=20); e_tel.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Producto:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        cb_prod = ttk.Combobox(frm, width=34, state="readonly")
        with self.cn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM dbo.productos WHERE activo=1 ORDER BY nombre")
            prods = cur.fetchall()
        options = [f"{pid} - {nom}" for pid, nom in prods]
        cb_prod["values"] = options
        if options: cb_prod.current(0)
        cb_prod.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Cantidad:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_cant = ttk.Entry(frm, width=14); e_cant.insert(0, "1"); e_cant.grid(row=3, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=14); e_monto.grid(row=4, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=4)
        de_fecha = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd"); de_fecha.set_date(date.today())
        de_fecha.grid(row=5, column=1, padx=8, pady=4, sticky="w")

        btns = tk.Frame(win, bg=CARD); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton", command=win.destroy).pack(side="right", padx=6)

        def guardar():
            if not cb_prod.get():
                messagebox.showwarning("Fiado", "Seleccione un producto."); return
            try:
                pid = int(cb_prod.get().split(" - ", 1)[0])
                cantidad = int(e_cant.get()); assert cantidad > 0
                monto = float((e_monto.get() or "0").replace(",", "."))
            except Exception:
                messagebox.showwarning("Fiado", "Verifica producto, cantidad y monto."); return

            try:
                with self.cn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dbo.fiados(nombre_cliente, telefono, producto, cantidad, monto, fecha, estado)
                        SELECT ?, ?, p.nombre, ?, ?, ?, 'Pendiente'
                        FROM dbo.productos p WHERE p.id=?
                    """, (e_cli.get().strip(), e_tel.get().strip() or None, cantidad, monto,
                          de_fecha.get_date().strftime("%Y-%m-%d"), pid))
                    # descontar stock: la mercadería sale
                    cur.execute("UPDATE dbo.productos SET stock = stock - ? WHERE id=?", (cantidad, pid))
                    self.cn.commit()
                messagebox.showinfo("Fiado", "Fiado registrado y stock actualizado.")
                win.destroy(); self._cargar()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Fiado", f"Ocurrió un error:\n{e}")

        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=guardar).pack(side="right")


if __name__ == "__main__":
    app = InventarioUnificadoApp()
    app.mainloop()
