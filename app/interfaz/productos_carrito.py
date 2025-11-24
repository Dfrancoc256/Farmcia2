# app/interfaz/productos_carrito_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from app.core.database import conectar_bd

PRIMARY = "#1E63FF"
SURFACE = "#F5F7FB"
CARD_BG = "#FFFFFF"
TEXT = "#0F172A"
MUTED = "#64748B"

class ProductosCarritoView(tk.Frame):
    """
    Vista embebible para Productos / Carrito.
    Úsala en tu MainApp con sidebar: view = ProductosCarritoView(parent)
    """
    def __init__(self, parent):
        super().__init__(parent, bg=SURFACE)
        self._styles()

        self.cn = conectar_bd()
        if not self.cn:
            messagebox.showerror("BD", "No hay conexión a SQL Server.")
            return

        self.carrito = []
        self.botones_overlay = {}
        self._ui()
        self._cargar_productos()

    # -------- estilos --------
    def _styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TLabel", background=SURFACE, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Muted.TLabel", background=SURFACE, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=("Segoe UI", 11))

        style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor="#E2E8F0",
                        lightcolor="#E2E8F0", darkcolor="#E2E8F0", borderwidth=1, padding=6)

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
        style.map("m.Treeview.Heading", background=[("active", "#EEF2F7")])

    # -------- UI --------
    def _ui(self):
        header = tk.Frame(self, bg=SURFACE)
        header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="Productos", bg=SURFACE, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left")

        # Búsqueda
        search = tk.Frame(self, bg=SURFACE); search.pack(fill="x", padx=16, pady=(0, 10))
        ttk.Label(search, text="Buscar:", style="TLabel").pack(side="left")
        self.entry_buscar = ttk.Entry(search, width=42)
        self.entry_buscar.pack(side="left", padx=8)
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_en_linea)

        # Split
        body = tk.Frame(self, bg=SURFACE); body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # LEFT: listado
        left_card = tk.Frame(body, bg=CARD_BG, bd=1, relief="solid")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_card.grid_rowconfigure(1, weight=1)
        ttk.Label(left_card, text="Listado", style="Card.TLabel",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=10)

        cols = ("Nombre", "Precio Compra", "Precio Unidad", "Precio Blister", "Acciones")
        self.tv = ttk.Treeview(left_card, columns=cols, show="headings", style="m.Treeview", height=18)
        for c in cols:
            self.tv.heading(c, text=c, anchor="center")
        self.tv.column("Nombre", width=320, anchor=10)
        self.tv.column("Precio Compra", width=130, anchor="center")
        self.tv.column("Precio Unidad", width=130, anchor="center")
        self.tv.column("Precio Blister", width=130, anchor="center")
        self.tv.column("Acciones", width=200, anchor="center")
        self.tv.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        vs = ttk.Scrollbar(left_card, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=vs.set)
        vs.grid(row=1, column=0, sticky="nse", padx=(0, 12))

        # overlay botones en la columna "Acciones"
        self.tv.bind("<Expose>", self._refrescar_botones_overlay)
        self.tv.bind("<Configure>", self._refrescar_botones_overlay)
        self.tv.bind("<Motion>", self._refrescar_botones_overlay)
        self.tv.bind("<Double-1>", self._editar_inline_precio)

        # RIGHT: carrito + cambio
        right = tk.Frame(body, bg=CARD_BG, bd=1, relief="solid")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=0)
        right.grid_rowconfigure(1, weight=0)
        right.grid_rowconfigure(2, weight=0)
        right.grid_rowconfigure(3, weight=1)

        ttk.Label(right, text="Carrito", style="Card.TLabel",
                  font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        cols_c = ("Producto", "Tipo", "Cant", "Monto", "Fecha")
        self.tv_carrito = ttk.Treeview(right, columns=cols_c, show="headings", style="m.Treeview", height=9)
        for c in cols_c:
            self.tv_carrito.heading(c, text=c)
        self.tv_carrito.column("Producto", width=220, anchor="w")
        self.tv_carrito.column("Tipo", width=70, anchor="center")
        self.tv_carrito.column("Cant", width=70, anchor="e")
        self.tv_carrito.column("Monto", width=100, anchor="e")
        self.tv_carrito.column("Fecha", width=110, anchor="center")
        self.tv_carrito.grid(row=1, column=0, sticky="ew", padx=12)

        bottom_r = tk.Frame(right, bg=CARD_BG); bottom_r.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 6))
        bottom_r.grid_columnconfigure(0, weight=1)
        self.lbl_total = tk.Label(bottom_r, text="Total: Q 0.00", bg=CARD_BG, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.lbl_total.grid(row=0, column=0, sticky="w")
        ttk.Button(bottom_r, text="Eliminar selección", style="Secondary.TButton",
                   command=self._eliminar_item_carrito).grid(row=0, column=1, padx=6)
        ttk.Button(bottom_r, text="Finalizar venta", style="Primary.TButton",
                   command=self._finalizar_venta).grid(row=0, column=2)

        pago = tk.Frame(right, bg=CARD_BG)
        pago.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 12))
        pago.grid_columnconfigure(1, weight=1)

        ttk.Label(pago, text="Pagado (Q):", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.var_pagado = tk.StringVar(value="")
        self.entry_pagado = ttk.Entry(pago, textvariable=self.var_pagado, width=16)
        self.entry_pagado.grid(row=0, column=1, sticky="w", padx=(8, 12), pady=4)

        ttk.Button(pago, text="Calcular cambio", style="Primary.TButton",
                   command=self._calcular_cambio).grid(row=0, column=2, padx=(0, 6), pady=4)
        self.lbl_cambio = ttk.Label(pago, text="Cambio: Q 0.00", style="Card.TLabel")
        self.lbl_cambio.grid(row=0, column=3, sticky="w", padx=(8, 0), pady=4)

    # -------- datos --------
    def _cargar_productos(self, where_text=""):
        for fr in self.botones_overlay.values():
            fr.destroy()
        self.botones_overlay.clear()

        self.tv.delete(*self.tv.get_children())
        cur = self.cn.cursor()
        if where_text:
            q = f"%{where_text.lower()}%"
            cur.execute("""
                SELECT id, nombre, precio_compra, precio_venta_unidad, ISNULL(precio_venta_blister,0)
                FROM dbo.productos
                WHERE LOWER(nombre) LIKE ? OR LOWER(categoria) LIKE ?
                ORDER BY nombre
            """, (q, q))
        else:
            cur.execute("""
                SELECT id, nombre, precio_compra, precio_venta_unidad, ISNULL(precio_venta_blister,0)
                FROM dbo.productos
                WHERE activo=1
                ORDER BY nombre
            """)
        for (pid, nombre, pc, pu, pb) in cur.fetchall():
            self.tv.insert("", "end",
                           values=(nombre, f"{pc:.2f}", f"{pu:.2f}", f"{pb:.2f}", ""),
                           tags=(str(pid),))
        cur.close()
        self.after(50, self._refrescar_botones_overlay)

    def _filtrar_en_linea(self, _):
        self._cargar_productos(self.entry_buscar.get().strip())

    # -------- overlay de botones --------
    def _refrescar_botones_overlay(self, _=None):
        col_index = 4  # Acciones
        for iid in self.tv.get_children():
            bbox = self.tv.bbox(iid, column=col_index)
            if not bbox:
                if iid in self.botones_overlay:
                    self.botones_overlay[iid].place_forget()
                continue
            x, y, w, h = bbox
            if iid not in self.botones_overlay:
                fr = tk.Frame(self.tv, bg="#FFFFFF")
                ttk.Button(fr, text="Editar", style="Secondary.TButton",
                           command=lambda a=iid: self._abrir_modal_editar(a)).pack(side="left", padx=(0, 6))
                ttk.Button(fr, text="Añadir", style="Primary.TButton",
                           command=lambda a=iid: self._abrir_modal_add(a)).pack(side="left")
                self.botones_overlay[iid] = fr
            self.botones_overlay[iid].place(x=x + 8, y=y + 2, width=w - 16, height=h - 4)

    def _get_producto_by_iid(self, iid):
        vals = self.tv.item(iid, "values")
        pid = int(self.tv.item(iid, "tags")[0])
        return {
            "id": pid,
            "nombre": vals[0],
            "precio_compra": float(vals[1]),
            "precio_unidad": float(vals[2]),
            "precio_blister": float(vals[3]),
        }

    # -------- editar precios --------
    def _abrir_modal_editar(self, iid):
        p = self._get_producto_by_iid(iid)
        win = tk.Toplevel(self); win.title(f"Editar — {p['nombre']}"); win.grab_set()
        win.configure(bg=CARD_BG); win.resizable(False, False)

        def fila(lbl, var):
            fr = tk.Frame(win, bg=CARD_BG); fr.pack(fill="x", padx=16, pady=8)
            ttk.Label(fr, text=lbl, style="Card.TLabel").pack(side="left", padx=(0, 10))
            e = ttk.Entry(fr, textvariable=var, width=18); e.pack(side="left")
            return e

        v_pc = tk.StringVar(value=f"{p['precio_compra']:.2f}")
        v_pu = tk.StringVar(value=f"{p['precio_unidad']:.2f}")
        v_pb = tk.StringVar(value=f"{p['precio_blister']:.2f}")

        fila("Precio compra (Q):", v_pc)
        fila("Precio unidad (Q):", v_pu)
        fila("Precio blister (Q):", v_pb)

        btns = tk.Frame(win, bg=CARD_BG); btns.pack(fill="x", padx=16, pady=14)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=win.destroy).pack(side="right", padx=6)

        def guardar():
            try:
                pc = float(v_pc.get()); pu = float(v_pu.get()); pb = float(v_pb.get())
            except:
                messagebox.showwarning("Validación", "Valores numéricos inválidos."); return
            cur = self.cn.cursor()
            cur.execute("""
                UPDATE dbo.productos
                   SET precio_compra=?, precio_venta_unidad=?, precio_venta_blister=?
                 WHERE id=?""", (pc, pu, pb, p["id"]))
            self.cn.commit(); cur.close()
            self._cargar_productos(self.entry_buscar.get().strip())
            messagebox.showinfo("OK", "Producto actualizado.")
            win.destroy()

        ttk.Button(btns, text="Guardar", style="Primary.TButton",
                   command=guardar).pack(side="right")

    # -------- añadir al carrito --------
    def _abrir_modal_add(self, iid):
        p = self._get_producto_by_iid(iid)
        win = tk.Toplevel(self); win.title(f"Añadir — {p['nombre']}"); win.grab_set()
        win.configure(bg=CARD_BG); win.resizable(False, False)

        fr = tk.Frame(win, bg=CARD_BG); fr.pack(padx=16, pady=12)

        ttk.Label(fr, text="Tipo:", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        cb_tipo = ttk.Combobox(fr, values=["unidad","blister"], state="readonly", width=14)
        cb_tipo.current(0); cb_tipo.grid(row=0, column=1, padx=10, pady=4, sticky="w")

        ttk.Label(fr, text="Cantidad:", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        e_cant = ttk.Entry(fr, width=16); e_cant.insert(0, "1")
        e_cant.grid(row=1, column=1, padx=10, pady=4, sticky="w")

        ttk.Label(fr, text="Monto (Q):", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        e_monto = ttk.Entry(fr, width=16); e_monto.insert(0, f"{p['precio_unidad']:.2f}")
        e_monto.grid(row=2, column=1, padx=10, pady=4, sticky="w")

        ttk.Label(fr, text="Fecha (YYYY-MM-DD):", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        e_fecha = ttk.Entry(fr, width=16); e_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        e_fecha.grid(row=3, column=1, padx=10, pady=4, sticky="w")

        btns = tk.Frame(win, bg=CARD_BG); btns.pack(fill="x", padx=16, pady=12)
        ttk.Button(btns, text="Cancelar", style="Secondary.TButton",
                   command=win.destroy).pack(side="right", padx=6)

        def agregar():
            try:
                cantidad = int(e_cant.get())
                monto = float(e_monto.get())
                datetime.strptime(e_fecha.get(), "%Y-%m-%d")
            except Exception:
                messagebox.showwarning("Validación", "Revisa cantidad, monto y fecha (YYYY-MM-DD)."); return

            item = {"id_producto": p["id"], "nombre": p["nombre"],
                    "tipo": cb_tipo.get(), "cantidad": cantidad,
                    "monto": monto, "fecha": e_fecha.get()}
            self.carrito.append(item)
            self.tv_carrito.insert("", "end", values=(
                item["nombre"], item["tipo"], item["cantidad"],
                f"{item['monto']:.2f}", item["fecha"]))
            self._recalcular_total()
            win.destroy()

        ttk.Button(btns, text="Añadir", style="Primary.TButton",
                   command=agregar).pack(side="right")

    # -------- helpers carrito --------
    def _recalcular_total(self):
        total = sum(i["monto"] for i in self.carrito)
        self.lbl_total.config(text=f"Total: Q {total:,.2f}")

    def _eliminar_item_carrito(self):
        sel = self.tv_carrito.selection()
        if not sel: return
        idx = self.tv_carrito.index(sel[0])
        self.tv_carrito.delete(sel[0])
        del self.carrito[idx]
        self._recalcular_total()

    def _calcular_cambio(self):
        try:
            pagado = float(self.var_pagado.get().strip().replace(",", "."))
        except Exception:
            messagebox.showwarning("Pago", "Ingrese un monto pagado válido (número).")
            return
        total = sum(i["monto"] for i in self.carrito)
        cambio = pagado - total
        self.lbl_cambio.config(text=f"Cambio: Q {cambio:,.2f}")

    # -------- persistir venta --------
    def _finalizar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Carrito", "No hay productos en el carrito."); return
        total = round(sum(i["monto"] for i in self.carrito), 2)
        try:
            pagado = float(self.var_pagado.get().strip().replace(",", ".")) if self.var_pagado.get().strip() else 0.0
        except Exception:
            pagado = 0.0
        if pagado and pagado < total:
            messagebox.showwarning("Pago", f"El pagado (Q {pagado:.2f}) es menor al total (Q {total:.2f}).")
            return

        try:
            cur = self.cn.cursor()
            cur.execute("INSERT INTO dbo.ventas(total, tipo_pago, observacion) VALUES (?, ?, ?);",
                        (total, "efectivo", "Venta desde Tkinter"))
            cur.execute("SELECT SCOPE_IDENTITY();")
            idv = int(cur.fetchone()[0])

            for it in self.carrito:
                punit = round(it["monto"] / it["cantidad"], 2)
                cur.execute("""
                    INSERT INTO dbo.detalle_ventas(id_venta, id_producto, tipo, cantidad, precio_unitario)
                    VALUES (?, ?, ?, ?, ?)""",
                    (idv, it["id_producto"], it["tipo"], it["cantidad"], punit))
            self.cn.commit()

            # limpiar UI
            self.carrito.clear()
            for i in self.tv_carrito.get_children(): self.tv_carrito.delete(i)
            self._recalcular_total()
            self.var_pagado.set("")
            self.lbl_cambio.config(text="Cambio: Q 0.00")
            messagebox.showinfo("Venta", f"Venta #{idv} registrada.")
        except Exception as e:
            self.cn.rollback()
            messagebox.showerror("Venta", f"Ocurrió un error:\n{e}")

    # -------- edición inline de precios --------
    def _editar_inline_precio(self, event):
        region = self.tv.identify("region", event.x, event.y)
        if region != "cell": return
        col = self.tv.identify_column(event.x)
        if col not in ("#2", "#3", "#4"):  # solo columnas de precio
            return
        iid = self.tv.identify_row(event.y)
        bbox = self.tv.bbox(iid, col)
        if not bbox: return
        x, y, w, h = bbox
        valor = self.tv.set(iid, col)

        e = ttk.Entry(self.tv); e.insert(0, valor); e.place(x=x, y=y, width=w, height=h)
        e.focus()

        def guardar(_=None):
            try:
                nuevo = float(e.get())
            except:
                e.destroy(); return
            self.tv.set(iid, col, f"{nuevo:.2f}")
            e.destroy()
            p = self._get_producto_by_iid(iid)
            pc = float(self.tv.set(iid, "#2"))
            pu = float(self.tv.set(iid, "#3"))
            pb = float(self.tv.set(iid, "#4"))
            cur = self.cn.cursor()
            cur.execute("""
                UPDATE dbo.productos
                   SET precio_compra=?, precio_venta_unidad=?, precio_venta_blister=?
                 WHERE id=?""", (pc, pu, pb, p["id"]))
            self.cn.commit(); cur.close()

        e.bind("<Return>", guardar)
        e.bind("<FocusOut>", lambda _=None: e.destroy())
