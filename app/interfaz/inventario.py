# app/interfaz/inventario.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

from tkcalendar import DateEntry
from app.core.database import conectar_bd

PRIMARY = "#1E63FF"
SURFACE = "#F5F7FB"
CARD_BG = "#FFFFFF"
TEXT = "#0F172A"
MUTED = "#64748B"

class InventarioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Farmacia 2.0 — Inventario")
        self.geometry("1200x760")
        self.configure(bg=SURFACE)

        self._styles()

        self.cn = conectar_bd()
        if not self.cn:
            messagebox.showerror("BD", "No hay conexión a SQL Server.")
            self.destroy(); return

        hoy = date.today()
        self.var_desde = tk.StringVar(value=hoy.strftime("%Y-%m-%d"))
        self.var_hasta = tk.StringVar(value=hoy.strftime("%Y-%m-%d"))

        self._ui()
        self._cargar_todo()

    # ---------- estilos ----------
    def _styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 10))

        style.configure("TEntry",
                        fieldbackground="#FFFFFF", bordercolor="#E2E8F0",
                        lightcolor="#E2E8F0", darkcolor="#E2E8F0",
                        borderwidth=1, padding=6)

        style.configure("Primary.TButton", background=PRIMARY, foreground="#FFFFFF",
                        font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.map("Primary.TButton", background=[("active", "#2A6BFF")])

        style.configure("Secondary.TButton", background="#E5E7EB", foreground="#111827",
                        font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.map("Secondary.TButton", background=[("active", "#D1D5DB")])

        style.configure("m.Treeview",
                        background="#FFFFFF", fieldbackground="#FFFFFF",
                        foreground=TEXT, bordercolor="#E5E7EB", borderwidth=1,
                        rowheight=28, font=("Segoe UI", 10))
        style.configure("m.Treeview.Heading",
                        background="#F8FAFC", foreground=TEXT,
                        relief="flat", font=("Segoe UI", 10, "bold"))

    # ---------- UI ----------
    def _ui(self):
        header = tk.Frame(self, bg=SURFACE); header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="Inventario", bg=SURFACE, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left")

        # Filtros por fecha
        filtros = tk.Frame(self, bg=SURFACE); filtros.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Label(filtros, text="Desde:", style="TLabel").pack(side="left")
        self.de_desde = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_desde.set_date(datetime.strptime(self.var_desde.get(), "%Y-%m-%d"))
        self.de_desde.pack(side="left", padx=(6, 12))

        ttk.Label(filtros, text="Hasta:", style="TLabel").pack(side="left")
        self.de_hasta = DateEntry(filtros, width=12, date_pattern="yyyy-mm-dd")
        self.de_hasta.set_date(datetime.strptime(self.var_hasta.get(), "%Y-%m-%d"))
        self.de_hasta.pack(side="left", padx=(6, 12))

        ttk.Button(filtros, text="Aplicar", style="Primary.TButton", command=self._aplicar_filtro).pack(side="left")
        ttk.Button(filtros, text="Hoy", style="Secondary.TButton", command=self._set_hoy).pack(side="left", padx=(8, 0))
        ttk.Button(filtros, text="Este mes", style="Secondary.TButton", command=self._set_mes).pack(side="left", padx=(8, 0))

        # Layout principal
        body = tk.Frame(self, bg=SURFACE); body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Notebook con 2 pestañas: Movimientos y Fiados
        left_card = tk.Frame(body, bg=CARD_BG, bd=1, relief="solid")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_card.grid_rowconfigure(0, weight=1)
        left_card.grid_columnconfigure(0, weight=1)

        self.nb = ttk.Notebook(left_card)
        self.nb.grid(row=0, column=0, sticky="nsew")

        # --- Movimientos (Ventas + Gastos)
        tab_mov = tk.Frame(self.nb, bg=CARD_BG)
        self.nb.add(tab_mov, text="Movimientos")

        ttk.Label(tab_mov, text="Ventas y Egresos del rango", style="Card.TLabel",
                  font=("Segoe UI", 12, "bold"), background=CARD_BG).pack(anchor="w", padx=12, pady=10)

        cols_mov = ("Fecha", "Tipo", "Persona", "Producto/Detalle", "Cantidad", "Monto (Q)")
        self.tv_mov = ttk.Treeview(tab_mov, columns=cols_mov, show="headings", style="m.Treeview", height=20)
        for c in cols_mov:
            self.tv_mov.heading(c, text=c)
        self.tv_mov.column("Fecha", width=140, anchor="center")
        self.tv_mov.column("Tipo", width=100, anchor="center")
        self.tv_mov.column("Persona", width=200, anchor="w")
        self.tv_mov.column("Producto/Detalle", width=360, anchor="w")
        self.tv_mov.column("Cantidad", width=90, anchor="e")
        self.tv_mov.column("Monto (Q)", width=120, anchor="e")
        self.tv_mov.pack(fill="both", expand=True, padx=12, pady=(0,12))

        vs1 = ttk.Scrollbar(tab_mov, orient="vertical", command=self.tv_mov.yview)
        self.tv_mov.configure(yscrollcommand=vs1.set)
        vs1.place(in_=self.tv_mov, relx=1.0, rely=0, relheight=1.0, x=-1)

        # --- Fiados (pendientes y pagados)
        tab_fiado = tk.Frame(self.nb, bg=CARD_BG)
        self.nb.add(tab_fiado, text="Fiados")

        top_f = tk.Frame(tab_fiado, bg=CARD_BG); top_f.pack(fill="x", padx=12, pady=(10, 6))
        ttk.Label(top_f, text="Fiados del rango", style="Card.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(side="left")

        ttk.Button(top_f, text="Marcar pagado", style="Primary.TButton",
                   command=self._marcar_fiado_pagado).pack(side="right", padx=(8,0))

        cols_f = ("ID", "Fecha", "Estado", "Cliente", "Producto", "Cantidad", "Monto (Q)", "Fecha pago", "id_venta")
        self.tv_fiados = ttk.Treeview(tab_fiado, columns=cols_f, show="headings", style="m.Treeview", height=20)
        for c in cols_f:
            self.tv_fiados.heading(c, text=c)
        self.tv_fiados.column("ID", width=70, anchor="center")
        self.tv_fiados.column("Fecha", width=120, anchor="center")
        self.tv_fiados.column("Estado", width=90, anchor="center")
        self.tv_fiados.column("Cliente", width=180, anchor="w")
        self.tv_fiados.column("Producto", width=230, anchor="w")
        self.tv_fiados.column("Cantidad", width=90, anchor="e")
        self.tv_fiados.column("Monto (Q)", width=120, anchor="e")
        self.tv_fiados.column("Fecha pago", width=130, anchor="center")
        self.tv_fiados.column("id_venta", width=90, anchor="center")
        self.tv_fiados.pack(fill="both", expand=True, padx=12, pady=(0,12))

        vs2 = ttk.Scrollbar(tab_fiado, orient="vertical", command=self.tv_fiados.yview)
        self.tv_fiados.configure(yscrollcommand=vs2.set)
        vs2.place(in_=self.tv_fiados, relx=1.0, rely=0, relheight=1.0, x=-1)

        # --- Panel derecho: Totales y acciones rápidas
        right = tk.Frame(body, bg=CARD_BG, bd=1, relief="solid")
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Totales", style="Card.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 6))

        self.lbl_total_vendido = ttk.Label(right, text="Vendido: Q 0.00", style="Card.TLabel")
        self.lbl_total_gastos  = ttk.Label(right, text="Gastos: Q 0.00", style="Card.TLabel")
        self.lbl_total_fiado   = ttk.Label(right, text="Fiado (pend.): Q 0.00", style="Card.TLabel")
        self.lbl_balance       = ttk.Label(right, text="Balance: Q 0.00", style="Card.TLabel")

        for w in (self.lbl_total_vendido, self.lbl_total_gastos, self.lbl_total_fiado, self.lbl_balance):
            w.pack(anchor="w", padx=16, pady=4)

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=12, pady=10)

        acciones = tk.Frame(right, bg=CARD_BG); acciones.pack(fill="x", padx=12, pady=(6,12))
        ttk.Button(acciones, text="Agregar Gasto", style="Primary.TButton",
                   command=self._modal_gasto).pack(fill="x", pady=6)
        ttk.Button(acciones, text="Agregar Fiado", style="Secondary.TButton",
                   command=self._modal_fiado).pack(fill="x", pady=6)

    # ---------- helpers fechas ----------
    def _aplicar_filtro(self):
        self.var_desde.set(self.de_desde.get_date().strftime("%Y-%m-%d"))
        self.var_hasta.set(self.de_hasta.get_date().strftime("%Y-%m-%d"))
        self._cargar_todo()

    def _set_hoy(self):
        hoy = date.today()
        self.de_desde.set_date(hoy); self.de_hasta.set_date(hoy)
        self._aplicar_filtro()

    def _set_mes(self):
        hoy = date.today()
        desde = hoy.replace(day=1)
        self.de_desde.set_date(desde); self.de_hasta.set_date(hoy)
        self._aplicar_filtro()

    # ---------- cargar datos (totales + grillas) ----------
    def _cargar_todo(self):
        d1 = self.var_desde.get()
        d2 = self.var_hasta.get()

        # Limpiar tablas
        self.tv_mov.delete(*self.tv_mov.get_children())
        self.tv_fiados.delete(*self.tv_fiados.get_children())

        # 1) MOVIMIENTOS: Ventas (incluye fiados pagados) y Gastos
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CONVERT(varchar(16), v.fecha, 120) AS fecha,
                       'Venta' AS tipo,
                       '' AS persona,
                       STRING_AGG(p.nombre + ' x' + CAST(d.cantidad AS varchar(10)), ', ') WITHIN GROUP (ORDER BY d.id) AS detalle,
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

        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CONVERT(varchar(16), g.fecha, 120) AS fecha,
                       'Egreso' AS tipo,
                       '' AS persona,
                       g.descripcion AS detalle,
                       NULL AS cantidad,
                       CAST(g.monto AS float) AS monto
                FROM dbo.gastos g
                WHERE g.fecha >= ? AND g.fecha < DATEADD(DAY,1,?)
                ORDER BY g.fecha
            """, (d1, d2))
            gastos = cur.fetchall()

        # poblar tabla movimientos
        for (fecha, tipo, persona, detalle, cantidad, monto) in ventas:
            self.tv_mov.insert("", "end", values=(fecha, tipo, persona, detalle or "", int(cantidad or 0), f"{float(monto or 0):.2f}"))
        for (fecha, tipo, persona, detalle, cantidad, monto) in gastos:
            self.tv_mov.insert("", "end", values=(fecha, tipo, persona, detalle or "", "-", f"{float(monto or 0):.2f}"))

        # 2) FIADOS (pendientes y pagados) del rango por fecha del fiado
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT f.id, CONVERT(varchar(16), f.fecha, 120) AS fecha, f.estado,
                       f.nombre_cliente, f.producto, f.cantidad,
                       CAST(f.monto AS float) AS monto,
                       CONVERT(varchar(16), f.fecha_pago, 120) AS fecha_pago,
                       f.id_venta
                FROM dbo.fiados f
                WHERE f.fecha >= ? AND f.fecha < DATEADD(DAY,1,?)
                ORDER BY f.fecha
            """, (d1, d2))
            fiados = cur.fetchall()

        for (fid, fecha, estado, cliente, producto, cantidad, monto, fecha_pago, idv) in fiados:
            self.tv_fiados.insert("", "end", values=(fid, fecha, estado or "Pendiente", cliente or "", producto or "",
                                                     int(cantidad or 0), f"{float(monto or 0):.2f}", fecha_pago or "-", idv or "-"))

        # 3) Totales y balance
        total_vendido = sum((float(r[5] or 0) for r in ventas), 0.0)
        total_gastos  = sum((float(r[5] or 0) for r in gastos), 0.0)
        # Fiado pendiente del rango (no pagado)
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT CAST(ISNULL(SUM(monto),0) AS float)
                FROM dbo.fiados
                WHERE (estado IS NULL OR estado <> 'Pagado')
                  AND fecha >= ? AND fecha < DATEADD(DAY,1,?)
            """, (d1, d2))
            total_fiado_pend = float(cur.fetchone()[0] or 0)
        balance = total_vendido - total_gastos - total_fiado_pend

        self.lbl_total_vendido.config(text=f"Vendido: Q {total_vendido:,.2f}")
        self.lbl_total_gastos.config(text=f"Gastos: Q {total_gastos:,.2f}")
        self.lbl_total_fiado.config(text=f"Fiado (pend.): Q {total_fiado_pend:,.2f}")
        self.lbl_balance.config(text=f"Balance: Q {balance:,.2f}")

    # ---------- acciones ----------
    def _marcar_fiado_pagado(self):
        sel = self.tv_fiados.selection()
        if not sel:
            messagebox.showinfo("Fiado", "Selecciona un fiado para marcar como pagado."); return
        item = self.tv_fiados.item(sel[0], "values")
        fid = int(item[0])
        estado_actual = item[2]
        if estado_actual == "Pagado":
            messagebox.showinfo("Fiado", "Ese fiado ya está marcado como pagado."); return

        # traemos el fiado completo
        with self.cn.cursor() as cur:
            cur.execute("""
                SELECT id, nombre_cliente, producto, cantidad, CAST(monto AS float) AS monto, fecha, id_venta
                FROM dbo.fiados WHERE id = ?
            """, (fid,))
            row = cur.fetchone()
        if not row:
            messagebox.showerror("Fiado", "No se encontró el fiado seleccionado."); return

        _id, cliente, producto, cantidad, monto, fecha_fiado, idv_exist = row
        if idv_exist:
            messagebox.showinfo("Fiado", f"Ya tiene venta asociada #{idv_exist}."); return

        # Necesitamos el id_producto por nombre (si hay duplicados, escogemos el primero)
        with self.cn.cursor() as cur:
            cur.execute("SELECT TOP 1 id FROM dbo.productos WHERE nombre = ?", (producto,))
            r = cur.fetchone()
        if not r:
            messagebox.showerror("Fiado", f"No existe producto '{producto}' en productos."); return
        id_producto = int(r[0])

        # Confirmar
        if not messagebox.askyesno("Confirmar pago",
                                   f"Marcar como pagado Q {monto:.2f} de {cliente}.\n"
                                   f"Se registrará una VENTA con fecha {fecha_fiado.strftime('%Y-%m-%d')}.\n¿Continuar?"):
            return

        try:
            with self.cn.cursor() as cur:
                # 1) Insertar venta con la FECHA ORIGINAL del fiado
                cur.execute("""
                    DECLARE @idv INT;
                    INSERT INTO dbo.ventas (fecha, total, tipo_pago, observacion)
                    OUTPUT INSERTED.id INTO #tmp(id)
                    SELECT ?, ?, 'efectivo', 'Pago de fiado';

                    -- si no existe #tmp, créala
                """)  # noqa
        except Exception:
            pass  # pyodbc no maneja temp table así; usamos OUTPUT... SELECT truco abajo

        try:
            with self.cn.cursor() as cur:
                # Usamos OUTPUT INSERTED.id para capturar el id
                cur.execute("""
                    INSERT INTO dbo.ventas (fecha, total, tipo_pago, observacion)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?);
                """, (fecha_fiado, float(monto), 'efectivo', f'Pago fiado {cliente}'))
                idv = int(cur.fetchone()[0])

                # 2) detalle_ventas
                precio_unit = float(monto) / max(int(cantidad), 1)
                cur.execute("""
                    INSERT INTO dbo.detalle_ventas (id_venta, id_producto, tipo, cantidad, precio_unitario)
                    VALUES (?, ?, 'unidad', ?, ?)
                """, (idv, id_producto, int(cantidad), float(precio_unit)))

                # 3) actualizar fiado a Pagado (fecha_pago=ahora, id_venta)
                cur.execute("""
                    UPDATE dbo.fiados
                       SET estado='Pagado',
                           fecha_pago=GETDATE(),
                           id_venta=?
                     WHERE id=?
                """, (idv, fid))

                self.cn.commit()

            messagebox.showinfo("Fiado", f"Fiado pagado. Venta #{idv} creada con fecha {fecha_fiado.strftime('%Y-%m-%d')}.")
            self._cargar_todo()
        except Exception as e:
            self.cn.rollback()
            messagebox.showerror("Fiado", f"Ocurrió un error:\n{e}")

    # ---------- modales ----------
    def _modal_gasto(self):
        win = tk.Toplevel(self); win.title("Agregar Gasto"); win.grab_set()
        win.configure(bg=CARD_BG); win.resizable(False, False)

        frm = tk.Frame(win, bg=CARD_BG); frm.pack(padx=16, pady=12)

        ttk.Label(frm, text="Descripción:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_desc = ttk.Entry(frm, width=32); e_desc.grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=16); e_monto.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        de_fecha = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd")
        de_fecha.set_date(date.today()); de_fecha.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Categoría:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_cat = ttk.Entry(frm, width=20); e_cat.grid(row=3, column=1, padx=8, pady=4, sticky="w")

        btns = tk.Frame(win, bg=CARD_BG); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=win.destroy).pack(side="right", padx=6)

        def guardar():
            try:
                monto = float((e_monto.get() or "0").replace(",", "."))
            except:
                messagebox.showwarning("Gasto", "Monto inválido."); return
            try:
                with self.cn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dbo.gastos(descripcion, monto, fecha, categoria)
                        VALUES (?, ?, ?, ?)
                    """, (e_desc.get().strip(), monto,
                          de_fecha.get_date().strftime("%Y-%m-%d"),
                          e_cat.get().strip() or None))
                    self.cn.commit()
                messagebox.showinfo("Gasto", "Gasto registrado.")
                win.destroy(); self._cargar_todo()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Gasto", f"Ocurrió un error:\n{e}")

        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=guardar).pack(side="right")

    def _modal_fiado(self):
        win = tk.Toplevel(self); win.title("Agregar Fiado"); win.grab_set()
        win.configure(bg=CARD_BG); win.resizable(False, False)

        frm = tk.Frame(win, bg=CARD_BG); frm.pack(padx=16, pady=12)

        ttk.Label(frm, text="Cliente:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        e_cli = ttk.Entry(frm, width=30); e_cli.grid(row=0, column=1, padx=8, pady=4)

        ttk.Label(frm, text="Teléfono:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_tel = ttk.Entry(frm, width=20); e_tel.grid(row=1, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Producto:", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        cb_prod = ttk.Combobox(frm, width=34, state="readonly")
        with self.cn.cursor() as cur:
            cur.execute("SELECT id, nombre FROM dbo.productos WHERE activo=1 ORDER BY nombre")
            prods = cur.fetchall()
        opciones = [f"{pid} - {nom}" for pid, nom in prods]
        cb_prod["values"] = opciones
        if opciones: cb_prod.current(0)
        cb_prod.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Cantidad:", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_cant = ttk.Entry(frm, width=14); e_cant.insert(0, "1"); e_cant.grid(row=3, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Monto (Q):", style="Card.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(frm, width=14); e_monto.grid(row=4, column=1, padx=8, pady=4, sticky="w")

        ttk.Label(frm, text="Fecha:", style="Card.TLabel").grid(row=5, column=0, sticky="w", pady=4)
        de_fecha = DateEntry(frm, width=14, date_pattern="yyyy-mm-dd")
        de_fecha.set_date(date.today()); de_fecha.grid(row=5, column=1, padx=8, pady=4, sticky="w")

        btns = tk.Frame(win, bg=CARD_BG); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=win.destroy).pack(side="right", padx=6)

        def guardar():
            if not cb_prod.get():
                messagebox.showwarning("Fiado", "Seleccione un producto."); return
            try:
                pid = int(cb_prod.get().split(" - ", 1)[0])
                cantidad = int(e_cant.get())
                if cantidad <= 0: raise ValueError()
                monto = float((e_monto.get() or "0").replace(",", "."))
            except:
                messagebox.showwarning("Fiado", "Verifica producto, cantidad y monto."); return

            try:
                with self.cn.cursor() as cur:
                    # Insertar fiado (pendiente)
                    cur.execute("""
                        INSERT INTO dbo.fiados(nombre_cliente, telefono, producto, cantidad, monto, fecha, estado)
                        SELECT ?, ?, p.nombre, ?, ?, ?, 'Pendiente'
                        FROM dbo.productos p WHERE p.id = ?
                    """, (e_cli.get().strip(), e_tel.get().strip() or None,
                          cantidad, monto, de_fecha.get_date().strftime("%Y-%m-%d"), pid))

                    # ↓↓↓ Al generar fiado, el producto ya salió: descontamos STOCK
                    cur.execute("""
                        UPDATE dbo.productos
                           SET stock = stock - ?
                         WHERE id = ?
                    """, (cantidad, pid))

                    self.cn.commit()

                messagebox.showinfo("Fiado", "Fiado registrado y stock actualizado.")
                win.destroy(); self._cargar_todo()
            except Exception as e:
                self.cn.rollback(); messagebox.showerror("Fiado", f"Ocurrió un error:\n{e}")

        ttk.Button(btns, text="Guardar", style="Primary.TButton", command=guardar).pack(side="right")


if __name__ == "__main__":
    app = InventarioApp()
    app.mainloop()
