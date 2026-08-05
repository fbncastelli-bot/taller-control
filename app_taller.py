import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import webbrowser
import os
import tempfile
import requests
from datetime import datetime
from modules.tab_firmwares import TabFirmwares
from modules.auth_store import guardar_session, cargar_session, borrar_session

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ==================== MÓDULO DE LOGIN ====================
class LoginDialog(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Acceso al Sistema - Gestión de Taller")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.eval('tk::PlaceWindow . center')
        self.autenticado = False
        self.usuario_actual = ""
        self.token_acceso = ""
        self.can_download = True

        ctk.CTkLabel(self, text="🔒 CONTROL DE ACCESO", font=("Segoe UI", 16, "bold"), text_color="#38bdf8").pack(pady=(25, 10))
        ctk.CTkLabel(self, text="Ingrese sus credenciales de taller", font=("Segoe UI", 11), text_color="#94a3b8").pack(pady=(0, 20))

        self.ent_user = ctk.CTkEntry(self, width=260, placeholder_text="Usuario")
        self.ent_user.pack(pady=8)
        self.ent_user.insert(0, "admin")

        self.ent_pass = ctk.CTkEntry(self, width=260, placeholder_text="Contraseña", show="*")
        self.ent_pass.pack(pady=8)
        self.ent_pass.insert(0, "1234")
        self.ent_pass.bind("<Return>", lambda e: self.validar())

        ctk.CTkButton(self, text="Iniciar Sesión", width=260, fg_color="#1d4ed8", font=("Segoe UI", 12, "bold"), command=self.validar).pack(pady=20)

    def validar(self):
        user = self.ent_user.get().strip()
        pwd = self.ent_pass.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Atención", "Ingrese usuario y contraseña.")
            return

        try:
            url = "http://127.0.0.1:8000/api/login"
            res = requests.post(url, json={"username": user, "password": pwd}, timeout=3)
            
            if res.status_code == 200:
                data = res.json()
                self.autenticado = True
                self.usuario_actual = data.get("usuario", user)
                self.token_acceso = data.get("token", "")
                self.can_download = data.get("can_download", True)
                
                guardar_session(self.usuario_actual, self.token_acceso, self.can_download)
                
                self.withdraw()
                self.destroy()
                return
            else:
                det = res.json().get("detail", "Credenciales incorrectas.")
                messagebox.showerror("Error de Acceso", det)
                return
        except Exception:
            if user == "admin" and (pwd == "1234" or pwd == "admin1234"):
                self.autenticado = True
                self.usuario_actual = "Administrador (Offline)"
                self.token_acceso = "TOKEN_LOCAL_OFFLINE"
                self.can_download = False
                self.withdraw()
                self.destroy()
            else:
                messagebox.showerror("Error de Acceso", "Usuario o contraseña incorrectos.")

# ==================== APLICACIÓN PRINCIPAL ====================
class TallerApp(ctk.CTk):
    def __init__(self, usuario_actual, token_acceso, can_download=True):
        super().__init__()
        self.usuario_activo = usuario_actual
        self.token_acceso = token_acceso
        self.can_download = can_download

        self.title("Sistema Profesional de Gestión de Taller v4.2")
        self.geometry("1240x860")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        if os.path.exists("icono.ico"):
            try:
                self.iconbitmap("icono.ico")
            except Exception:
                pass

        self.setup_treeview_styles()
        self.init_db()

        self.setup_top_bar()

        self.tabview = ctk.CTkTabview(self, width=1210, height=730)
        self.tabview.pack(padx=15, pady=(5, 10), fill="both", expand=True)

        self.tab_ordenes = self.tabview.add("📋 Órdenes de Trabajo")
        self.tab_placas = self.tabview.add("📺 Banco de Placas (Stock)")
        self.tab_componentes = self.tabview.add("🧱 Stock Componentes")
        self.tab_ventas = self.tabview.add("💰 Ventas y Usados")
        self.tab_caja = self.tabview.add("💵 Caja y Finanzas")
        self.tab_nube = self.tabview.add("☁️ Firmware Nube")

        self.setup_ordenes()
        self.setup_placas()
        self.setup_componentes()
        self.setup_ventas()
        self.setup_caja()

        self.tab_firmwares = TabFirmwares(
            self.tab_nube, 
            user_token=self.token_acceso, 
            can_download=self.can_download
        )

    def _on_closing(self):
        try:
            if hasattr(self, 'tab_firmwares') and hasattr(self.tab_firmwares, 'cancelar_descargas'):
                self.tab_firmwares.cancelar_descargas()
        except Exception:
            pass
        
        try:
            self.after_cancel(self)
        except Exception:
            pass

        try:
            self.withdraw()
            self.quit()
            self.destroy()
        except Exception:
            pass

    def cerrar_sesion_local(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión actual y borrar el token guardado?"):
            borrar_session()
            messagebox.showinfo("Sesión Cerrada", "La sesión fue cerrada. Vuelva a iniciar la aplicación.")
            self._on_closing()

    def setup_top_bar(self):
        frame_top = ctk.CTkFrame(self, height=45, fg_color="#0f172a", corner_radius=6, border_width=1, border_color="#1e293b")
        frame_top.pack(fill="x", padx=15, pady=(10, 0))

        lbl_titulo = ctk.CTkLabel(frame_top, text="🛠️ SERVICIO TÉCNICO & FIRMWARES", font=("Segoe UI", 13, "bold"), text_color="#38bdf8")
        lbl_titulo.pack(side="left", padx=15, pady=8)

        lbl_db = ctk.CTkLabel(frame_top, text="● BBDD: ONLINE", font=("Segoe UI", 11, "bold"), text_color="#4ade80")
        lbl_db.pack(side="left", padx=15)

        btn_logout = ctk.CTkButton(frame_top, text="🚪 Cerrar Sesión", width=110, fg_color="#991b1b", hover_color="#7f1d1d", command=self.cerrar_sesion_local)
        btn_logout.pack(side="right", padx=10, pady=5)

        fecha_actual = datetime.now().strftime("%d/%m/%Y - %H:%M hs")
        lbl_date = ctk.CTkLabel(frame_top, text=f"📅 FECHA: {fecha_actual}", font=("Consolas", 12, "bold"), text_color="#facc15")
        lbl_date.pack(side="right", padx=15)

        lbl_user = ctk.CTkLabel(frame_top, text=f"👤 USER: {str(self.usuario_activo).upper()}", font=("Segoe UI", 11, "bold"), text_color="#94a3b8")
        lbl_user.pack(side="right", padx=15)

    def setup_treeview_styles(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#1e222b",
            foreground="#e2e8f0",
            fieldbackground="#1e222b",
            rowheight=30,
            font=("Consolas", 10),
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background="#0f172a",
            foreground="#38bdf8",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading", background=[("active", "#1e293b")])

    def init_db(self):
        self.conn = sqlite3.connect("taller.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT, equipo TEXT, falla TEXT, estado TEXT, presupuesto REAL, notas TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS placas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_main TEXT, tv_modelo TEXT, chasis TEXT, panel TEXT, ubicacion TEXT, estado TEXT, notas TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT, codigo TEXT, ubicacion TEXT, cantidad INTEGER, notas TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT, precio REAL, estado TEXT, notas TEXT
        )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT, tipo TEXT, concepto TEXT, monto REAL
        )''')

        self.conn.commit()

    def configurar_tags_tabla(self, tree):
        tree.tag_configure("st_ok", foreground="#4ade80", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("st_warn", foreground="#fbbf24", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("st_bad", foreground="#f87171", font=("Segoe UI", 10, "bold"))
        tree.tag_configure("st_info", foreground="#60a5fa", font=("Segoe UI", 10, "bold"))

    def generar_e_imprimir_html(self, titulo, contenido_html):
        html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{titulo}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; color: #111; }}
                .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px; }}
                .title {{ font-size: 18px; font-weight: bold; }}
                .subtitle {{ font-size: 12px; color: #555; }}
                .box {{ border: 1px solid #ccc; padding: 12px; margin-bottom: 12px; border-radius: 4px; }}
                .field {{ font-weight: bold; color: #333; }}
                @media print {{ .no-print {{ display: none; }} }}
            </style>
        </head>
        <body onload="window.print()">
            <div class="no-print" style="margin-bottom: 15px; background: #e2e8f0; padding: 8px; text-align: center; font-size: 12px;">
                <b>Consola de Impresión:</b> Presione <b>Ctrl + P</b> si no abre automáticamente.
            </div>
            {contenido_html}
        </body>
        </html>
        """
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, "impresion_taller.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
        webbrowser.open(f"file://{file_path}")

    # ==================== 📋 ÓRDENES DE TRABAJO ====================
    def setup_ordenes(self):
        frame_in = ctk.CTkFrame(self.tab_ordenes)
        frame_in.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_in, text="Cliente:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_ord_cliente = ctk.CTkEntry(frame_in, width=180)
        self.ent_ord_cliente.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Equipo/Modelo:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_ord_equipo = ctk.CTkEntry(frame_in, width=180)
        self.ent_ord_equipo.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Estado:").grid(row=0, column=4, padx=5, pady=5)
        self.cmb_ord_estado = ctk.CTkComboBox(frame_in, values=["Ingresado", "En Revision", "Presupuestado", "Reparado", "Entregado", "Sin Arreglo"])
        self.cmb_ord_estado.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Falla Reportada:").grid(row=1, column=0, padx=5, pady=5)
        self.ent_ord_falla = ctk.CTkEntry(frame_in, width=180)
        self.ent_ord_falla.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Presupuesto $:").grid(row=1, column=2, padx=5, pady=5)
        self.ent_ord_presupuesto = ctk.CTkEntry(frame_in, width=180)
        self.ent_ord_presupuesto.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkButton(frame_in, text="Guardar Orden", command=self.guardar_orden).grid(row=1, column=4, columnspan=2, padx=5, pady=5)

        frame_busqueda = ctk.CTkFrame(self.tab_ordenes)
        frame_busqueda.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda, text="🔎 Buscar Orden:").pack(side="left", padx=5)
        self.ent_ord_buscar = ctk.CTkEntry(frame_busqueda, width=280, placeholder_text="Cliente, Equipo o N° de Orden...")
        self.ent_ord_buscar.pack(side="left", padx=5)

        ctk.CTkButton(frame_busqueda, text="Filtrar", command=self.filtrar_ordenes).pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="Ver Todas", fg_color="gray", command=self.cargar_ordenes).pack(side="left", padx=5)
        self.ent_ord_buscar.bind("<Return>", lambda event: self.filtrar_ordenes())

        self.tree_ord = ttk.Treeview(self.tab_ordenes, columns=("ID", "Cliente", "Equipo", "Falla", "Estado", "Presupuesto"), show="headings")
        self.tree_ord.heading("ID", text="N°")
        self.tree_ord.heading("Cliente", text="Cliente")
        self.tree_ord.heading("Equipo", text="Equipo / Modelo")
        self.tree_ord.heading("Falla", text="Falla Reportada")
        self.tree_ord.heading("Estado", text="Estado Trabajo")
        self.tree_ord.heading("Presupuesto", text="Presupuesto ($)")

        self.tree_ord.column("ID", width=50, anchor="center")
        self.tree_ord.column("Cliente", width=150)
        self.tree_ord.column("Equipo", width=160)
        self.tree_ord.column("Falla", width=220)
        self.tree_ord.column("Estado", width=110, anchor="center")
        self.tree_ord.column("Presupuesto", width=110, anchor="e")

        self.tree_ord.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabla(self.tree_ord)
        self.tree_ord.bind("<Double-1>", self.abrir_informe_orden)

        frame_btn = ctk.CTkFrame(self.tab_ordenes)
        frame_btn.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_btn, text="📝 Ver Ficha / Informe", fg_color="#2B5B84", command=self.abrir_informe_orden).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="🖨️ Imprimir Comprobante Cliente", fg_color="#15803d", command=self.imprimir_orden).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="🏷️ Ticket para Tapa TV", fg_color="#1d4ed8", command=self.imprimir_ticket_tapa).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="Eliminar Orden Seleccionada", fg_color="#A12A2A", command=self.eliminar_orden).pack(side="right", padx=10)

        self.cargar_ordenes()

    def guardar_orden(self):
        cliente = self.ent_ord_cliente.get().strip()
        equipo = self.ent_ord_equipo.get().strip()
        falla = self.ent_ord_falla.get().strip()
        estado = self.cmb_ord_estado.get()
        presupuesto_str = self.ent_ord_presupuesto.get().strip() or "0"

        if not cliente or not equipo:
            messagebox.showwarning("Atención", "Complete Cliente y Equipo")
            return

        try:
            presupuesto = float(presupuesto_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El presupuesto ingresado no es válido")
            return

        self.cursor.execute("INSERT INTO ordenes (cliente, equipo, falla, estado, presupuesto, notas) VALUES (?, ?, ?, ?, ?, ?)",
                            (cliente, equipo, falla, estado, presupuesto, ""))
        self.conn.commit()
        self.cargar_ordenes()
        self.ent_ord_cliente.delete(0, 'end')
        self.ent_ord_equipo.delete(0, 'end')
        self.ent_ord_falla.delete(0, 'end')
        self.ent_ord_presupuesto.delete(0, 'end')

    def cargar_ordenes(self):
        for i in self.tree_ord.get_children():
            self.tree_ord.delete(i)
        self.cursor.execute("SELECT id, cliente, equipo, falla, estado, presupuesto FROM ordenes ORDER BY id DESC")
        for row in self.cursor.fetchall():
            row_list = list(row)
            row_list[5] = f"$ {row_list[5]:,.2f}"
            st = row_list[4]
            tag_st = "st_info"
            if st in ["Reparado", "Entregado"]: tag_st = "st_ok"
            elif st in ["Presupuestado", "En Revision"]: tag_st = "st_warn"
            elif st == "Sin Arreglo": tag_st = "st_bad"

            self.tree_ord.insert("", "end", values=row_list, tags=(tag_st,))

    def filtrar_ordenes(self):
        criterio = self.ent_ord_buscar.get().strip()
        if not criterio:
            self.cargar_ordenes()
            return
        for i in self.tree_ord.get_children():
            self.tree_ord.delete(i)
        query = "%" + criterio.lower() + "%"
        self.cursor.execute("""
            SELECT id, cliente, equipo, falla, estado, presupuesto 
            FROM ordenes 
            WHERE LOWER(cliente) LIKE ? OR LOWER(equipo) LIKE ? OR CAST(id AS TEXT) LIKE ?
            ORDER BY id DESC
        """, (query, query, query))
        for row in self.cursor.fetchall():
            row_list = list(row)
            row_list[5] = f"$ {row_list[5]:,.2f}"
            self.tree_ord.insert("", "end", values=row_list, tags=("st_info",))

    def abrir_informe_orden(self, event=None):
        sel = self.tree_ord.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una orden de la lista")
            return
        vals = self.tree_ord.item(sel[0])["values"]
        item_id, cliente, equipo = vals[0], vals[1], vals[2]

        self.cursor.execute("SELECT notas FROM ordenes WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        notas_actuales = res[0] if res and res[0] else ""

        top = ctk.CTkToplevel(self)
        top.title(f"Ficha de Trabajo - Orden N° {item_id} | {cliente}")
        top.geometry("600x520")
        top.grab_set()

        ctk.CTkLabel(top, text=f"Historial y Notas de Reparación - Orden N° {item_id}\nCliente: {cliente} | Equipo: {equipo}", font=("Segoe UI", 13, "bold")).pack(padx=10, pady=10)

        txt_notas = ctk.CTkTextbox(top, width=560, height=360)
        txt_notas.pack(padx=10, pady=5)
        txt_notas.insert("1.0", notas_actuales)

        def guardar_informe():
            texto = txt_notas.get("1.0", "end-strip")
            self.cursor.execute("UPDATE ordenes SET notas=? WHERE id=?", (texto, item_id))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Informe de la orden guardado.", parent=top)
            top.destroy()

        ctk.CTkButton(top, text="💾 Guardar Notas de Trabajo", fg_color="green", command=guardar_informe).pack(pady=10)

    def imprimir_orden(self):
        sel = self.tree_ord.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una orden para imprimir")
            return
        vals = self.tree_ord.item(sel[0])["values"]
        item_id = vals[0]

        self.cursor.execute("SELECT cliente, equipo, falla, estado, presupuesto, notas FROM ordenes WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        if not res: return

        cliente, equipo, falla, estado, presupuesto, notas = res

        html = f"""
        <div class="header">
            <div class="title">REMITO DE INGRESO / ORDEN DE TRABAJO N° {item_id:05d}</div>
            <div class="subtitle">Servicio Técnico Especializado - Gestión de Taller</div>
        </div>
        <div class="box">
            <p><span class="field">Cliente:</span> {cliente}</p>
            <p><span class="field">Equipo / Modelo:</span> {equipo}</p>
            <p><span class="field">Falla Reportada:</span> {falla}</p>
            <p><span class="field">Estado Actual:</span> {estado}</p>
            <p><span class="field">Presupuesto Estimado:</span> $ {presupuesto:,.2f}</p>
        </div>
        <div class="box">
            <p class="field">Observaciones Técnicas / Trabajo Realizado:</p>
            <p>{notas if notas else 'Sin observaciones adicionales.'}</p>
        </div>
        """
        self.generar_e_imprimir_html(f"Orden_{item_id}", html)

    def imprimir_ticket_tapa(self):
        sel = self.tree_ord.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una orden de la lista")
            return
        vals = self.tree_ord.item(sel[0])["values"]
        item_id = vals[0]

        self.cursor.execute("SELECT cliente, equipo, falla FROM ordenes WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        if not res: return

        cliente, equipo, falla = res

        html = f"""
        <div style="width: 280px; border: 2px dashed #000; padding: 10px; font-size: 12px;">
            <div style="font-size: 16px; font-weight: bold; text-align: center;">ORDEN N° {item_id:05d}</div>
            <hr>
            <p><b>Cliente:</b> {cliente}</p>
            <p><b>Equipo:</b> {equipo}</p>
            <p><b>Falla:</b> {falla}</p>
        </div>
        """
        self.generar_e_imprimir_html(f"Ticket_Tapa_{item_id}", html)

    def eliminar_orden(self):
        sel = self.tree_ord.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una orden de la lista")
            return
        item_id = self.tree_ord.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Desea borrar la orden N° {item_id}?"):
            self.cursor.execute("DELETE FROM ordenes WHERE id=?", (item_id,))
            self.conn.commit()
            self.cargar_ordenes()

    # ==================== 📺 BANCO DE PLACAS ====================
    def setup_placas(self):
        frame_in = ctk.CTkFrame(self.tab_placas)
        frame_in.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_in, text="Código Main/Placa:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_plc_codigo = ctk.CTkEntry(frame_in, width=180)
        self.ent_plc_codigo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Modelo TV:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_plc_modelo = ctk.CTkEntry(frame_in, width=180)
        self.ent_plc_modelo.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Panel/Display:").grid(row=0, column=4, padx=5, pady=5)
        self.ent_plc_panel = ctk.CTkEntry(frame_in, width=180)
        self.ent_plc_panel.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Ubicación/Gavetero:").grid(row=1, column=0, padx=5, pady=5)
        self.ent_plc_ubicacion = ctk.CTkEntry(frame_in, width=180)
        self.ent_plc_ubicacion.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Estado Placa:").grid(row=1, column=2, padx=5, pady=5)
        self.cmb_plc_estado = ctk.CTkComboBox(frame_in, values=["Probada OK", "Para Repuesto", "A Reparar", "Desconocido"])
        self.cmb_plc_estado.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkButton(frame_in, text="Guardar Placa", command=self.guardar_placa).grid(row=1, column=4, columnspan=2, padx=5, pady=5)

        frame_busqueda = ctk.CTkFrame(self.tab_placas)
        frame_busqueda.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda, text="🔎 Buscar en Stock:").pack(side="left", padx=5)
        self.ent_plc_buscar = ctk.CTkEntry(frame_busqueda, width=250, placeholder_text="Código main, TV o marca...")
        self.ent_plc_buscar.pack(side="left", padx=5)

        ctk.CTkButton(frame_busqueda, text="Filtrar Stock", command=self.filtrar_placas_locales).pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="Ver Todo", fg_color="gray", command=self.cargar_placas).pack(side="left", padx=5)
        self.ent_plc_buscar.bind("<Return>", lambda event: self.filtrar_placas_locales())

        self.tree_plc = ttk.Treeview(self.tab_placas, columns=("ID", "Codigo", "Modelo", "Panel", "Ubicacion", "Estado"), show="headings")
        self.tree_plc.heading("ID", text="N°")
        self.tree_plc.heading("Codigo", text="Código Main")
        self.tree_plc.heading("Modelo", text="Modelo TV")
        self.tree_plc.heading("Panel", text="Panel / Display")
        self.tree_plc.heading("Ubicacion", text="Ubicación / Gaveta")
        self.tree_plc.heading("Estado", text="Estado Placa")

        self.tree_plc.column("ID", width=50, anchor="center")
        self.tree_plc.column("Codigo", width=180)
        self.tree_plc.column("Modelo", width=160)
        self.tree_plc.column("Panel", width=160)
        self.tree_plc.column("Ubicacion", width=130, anchor="center")
        self.tree_plc.column("Estado", width=120, anchor="center")

        self.tree_plc.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabla(self.tree_plc)
        self.tree_plc.bind("<Double-1>", self.abrir_informe_placa)

        frame_web = ctk.CTkFrame(self.tab_placas)
        frame_web.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_web, text="📝 Ficha Técnica/Informe", fg_color="#2B5B84", command=self.abrir_informe_placa).pack(side="left", padx=5)
        ctk.CTkButton(frame_web, text="🖨️ Imprimir Ficha", fg_color="#15803d", command=self.imprimir_placa).pack(side="left", padx=5)
        ctk.CTkButton(frame_web, text="🔍 Info Main/TV", command=self.buscar_web_info).pack(side="left", padx=5)
        ctk.CTkButton(frame_web, text="⚡ Reforma LEDs", command=self.buscar_web_reforma).pack(side="left", padx=5)
        ctk.CTkButton(frame_web, text="Eliminar Placa Seleccionada", fg_color="#A12A2A", command=self.eliminar_placa).pack(side="right", padx=10)

        self.cargar_placas()

    def guardar_placa(self):
        codigo = self.ent_plc_codigo.get().strip()
        modelo = self.ent_plc_modelo.get().strip()
        panel = self.ent_plc_panel.get().strip()
        ubicacion = self.ent_plc_ubicacion.get().strip()
        estado = self.cmb_plc_estado.get()

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese el código de la placa")
            return

        self.cursor.execute("INSERT INTO placas (codigo_main, tv_modelo, chasis, panel, ubicacion, estado, notas) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (codigo, modelo, "", panel, ubicacion, estado, ""))
        self.conn.commit()
        self.cargar_placas()
        self.ent_plc_codigo.delete(0, 'end')
        self.ent_plc_modelo.delete(0, 'end')
        self.ent_plc_panel.delete(0, 'end')
        self.ent_plc_ubicacion.delete(0, 'end')

    def cargar_placas(self):
        for i in self.tree_plc.get_children():
            self.tree_plc.delete(i)
        self.cursor.execute("SELECT id, codigo_main, tv_modelo, panel, ubicacion, estado FROM placas ORDER BY id DESC")
        for row in self.cursor.fetchall():
            st = row[5]
            tag_st = "st_info"
            if st == "Probada OK": tag_st = "st_ok"
            elif st == "Para Repuesto": tag_st = "st_warn"
            elif st == "A Reparar": tag_st = "st_bad"

            self.tree_plc.insert("", "end", values=row, tags=(tag_st,))

    def filtrar_placas_locales(self):
        criterio = self.ent_plc_buscar.get().strip()
        if not criterio:
            self.cargar_placas()
            return
        for i in self.tree_plc.get_children():
            self.tree_plc.delete(i)
        query = "%" + criterio.lower() + "%"
        self.cursor.execute("SELECT id, codigo_main, tv_modelo, panel, ubicacion, estado FROM placas WHERE LOWER(codigo_main) LIKE ? OR LOWER(tv_modelo) LIKE ? ORDER BY id DESC", (query, query))
        for row in self.cursor.fetchall():
            self.tree_plc.insert("", "end", values=row, tags=("st_info",))

    def eliminar_placa(self):
        sel = self.tree_plc.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una placa de la lista")
            return
        item_id = self.tree_plc.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Desea borrar la placa N° {item_id}?"):
            self.cursor.execute("DELETE FROM placas WHERE id=?", (item_id,))
            self.conn.commit()
            self.cargar_placas()

    def abrir_informe_placa(self, event=None):
        sel = self.tree_plc.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una placa de la lista")
            return
        vals = self.tree_plc.item(sel[0])["values"]
        item_id, codigo_main, modelo_tv = vals[0], vals[1], vals[2]

        self.cursor.execute("SELECT notas FROM placas WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        notas_actuales = res[0] if res and res[0] else ""

        top = ctk.CTkToplevel(self)
        top.title(f"Informe Técnico - Main: {codigo_main} | TV: {modelo_tv}")
        top.geometry("600x520")
        top.grab_set()

        ctk.CTkLabel(top, text=f"Historial y Notas de Servicio - {codigo_main}", font=("Segoe UI", 14, "bold")).pack(padx=10, pady=10)

        txt_notas = ctk.CTkTextbox(top, width=560, height=380)
        txt_notas.pack(padx=10, pady=5)
        txt_notas.insert("1.0", notas_actuales)

        def guardar_informe():
            texto = txt_notas.get("1.0", "end-strip")
            self.cursor.execute("UPDATE placas SET notas=? WHERE id=?", (texto, item_id))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Informe técnico guardado.", parent=top)
            top.destroy()

        ctk.CTkButton(top, text="💾 Guardar Informe", fg_color="green", command=guardar_informe).pack(pady=10)

    def imprimir_placa(self):
        sel = self.tree_plc.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una placa para imprimir su ficha")
            return
        vals = self.tree_plc.item(sel[0])["values"]
        item_id = vals[0]

        self.cursor.execute("SELECT codigo_main, tv_modelo, panel, ubicacion, estado, notas FROM placas WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        if not res: return

        codigo, modelo, panel, ubicacion, estado, notas = res

        html = f"""
        <div class="header">
            <div class="title">FICHA TÉCNICA DE BANCO DE PLACAS N° {item_id:04d}</div>
            <div class="subtitle">Módulo de Control de Stock y Repuestos de Taller</div>
        </div>
        <div class="box">
            <p><span class="field">Código Main/Placa:</span> {codigo}</p>
            <p><span class="field">Modelo de TV Asociado:</span> {modelo}</p>
            <p><span class="field">Panel / Display Compatibilidad:</span> {panel}</p>
            <p><span class="field">Ubicación / Gavetero:</span> {ubicacion}</p>
            <p><span class="field">Estado Operativo:</span> {estado}</p>
        </div>
        <div class="box">
            <p class="field">Bitácora Técnica / Reformas / Modificaciones:</p>
            <p>{notas if notas else 'Sin observaciones de taller registradas.'}</p>
        </div>
        """
        self.generar_e_imprimir_html(f"Ficha_Placa_{codigo}", html)

    def buscar_web_info(self):
        sel = self.tree_plc.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una placa de la lista")
            return
        vals = self.tree_plc.item(sel[0])["values"]
        codigo, modelo = vals[1], vals[2]
        query = f'"{codigo}" OR "{modelo}" diagrama fallas -comprar -mercadolibre -precio -tienda'
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    def buscar_web_reforma(self):
        sel = self.tree_plc.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione una placa de la lista")
            return
        vals = self.tree_plc.item(sel[0])["values"]
        codigo = vals[1]
        query = f'"{codigo}" bajar corriente leds reforma backlight -comprar -mercadolibre -precio -tienda'
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    # ==================== 🧱 STOCK COMPONENTES ====================
    def setup_componentes(self):
        frame_in = ctk.CTkFrame(self.tab_componentes)
        frame_in.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_in, text="Categoría:").grid(row=0, column=0, padx=5, pady=5)
        self.cmb_cmp_cat = ctk.CTkComboBox(frame_in, values=["Transistores Bipolares", "MOSFETs", "Integrados PWM/Fuente", "Diodos/Schottky", "Capacitores", "Resistencias SMD", "Otros"])
        self.cmb_cmp_cat.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Código/Descripción:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_cmp_codigo = ctk.CTkEntry(frame_in, width=180)
        self.ent_cmp_codigo.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Ubicación/Gaveta:").grid(row=0, column=4, padx=5, pady=5)
        self.ent_cmp_ubicacion = ctk.CTkEntry(frame_in, width=150)
        self.ent_cmp_ubicacion.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5)
        self.ent_cmp_cantidad = ctk.CTkEntry(frame_in, width=100)
        self.ent_cmp_cantidad.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkButton(frame_in, text="Guardar Componente Nuevo", command=self.guardar_componente).grid(row=1, column=2, columnspan=2, padx=5, pady=5)

        frame_busqueda = ctk.CTkFrame(self.tab_componentes)
        frame_busqueda.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda, text="🔎 Buscar Componente:").pack(side="left", padx=5)
        self.ent_cmp_buscar = ctk.CTkEntry(frame_busqueda, width=280, placeholder_text="Escriba código (ej: 1N4148, MOSFET)...")
        self.ent_cmp_buscar.pack(side="left", padx=5)

        ctk.CTkButton(frame_busqueda, text="Filtrar", command=self.filtrar_componentes).pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="Ver Todos", fg_color="gray", command=self.cargar_componentes).pack(side="left", padx=5)
        self.ent_cmp_buscar.bind("<Return>", lambda event: self.filtrar_componentes())

        self.tree_cmp = ttk.Treeview(self.tab_componentes, columns=("ID", "Categoria", "Codigo", "Ubicacion", "Cantidad"), show="headings")
        self.tree_cmp.heading("ID", text="N°")
        self.tree_cmp.heading("Categoria", text="Categoría")
        self.tree_cmp.heading("Codigo", text="Código / Nombre Componente")
        self.tree_cmp.heading("Ubicacion", text="Gavetero / Ubicación")
        self.tree_cmp.heading("Cantidad", text="Stock Disponible")

        self.tree_cmp.column("ID", width=50, anchor="center")
        self.tree_cmp.column("Categoria", width=180)
        self.tree_cmp.column("Codigo", width=220)
        self.tree_cmp.column("Ubicacion", width=160, anchor="center")
        self.tree_cmp.column("Cantidad", width=110, anchor="center")

        self.tree_cmp.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabla(self.tree_cmp)
        self.tree_cmp.bind("<Double-1>", self.editar_componente_directo)

        frame_btn = ctk.CTkFrame(self.tab_componentes)
        frame_btn.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_btn, text="➕ Sumar 1", width=80, fg_color="green", command=lambda: self.modificar_cantidad(1)).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="➖ Restar 1", width=80, fg_color="orange", command=lambda: self.modificar_cantidad(-1)).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="✏️ Cambiar Cantidad", command=self.cambiar_cantidad_exacta).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="📍 Cambiar Ubicación", command=self.cambiar_ubicacion).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="📄 Datasheet PDF", fg_color="blue", command=self.buscar_datasheet).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="🖨️ Imprimir Etiqueta", fg_color="#15803d", command=self.imprimir_componente).pack(side="left", padx=5)
        ctk.CTkButton(frame_btn, text="Borrar Componente", fg_color="#A12A2A", command=self.eliminar_componente).pack(side="right", padx=10)

        self.cargar_componentes()

    def editar_componente_directo(self, event):
        sel = self.tree_cmp.selection()
        if not sel: return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id, codigo, cant_actual = vals[0], vals[2], vals[4]

        nueva_cant = simpledialog.askinteger("Edición Rápida", f"Modificar cantidad para {codigo}:", initialvalue=cant_actual)
        if nueva_cant is not None:
            self.cursor.execute("UPDATE componentes SET cantidad=? WHERE id=?", (nueva_cant, item_id))
            self.conn.commit()
            self.cargar_componentes()

    def guardar_componente(self):
        cat = self.cmb_cmp_cat.get()
        codigo = self.ent_cmp_codigo.get().strip()
        ubicacion = self.ent_cmp_ubicacion.get().strip()
        cant_str = self.ent_cmp_cantidad.get().strip() or "1"

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese el código del componente")
            return

        try:
            cant = int(cant_str)
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un número entero")
            return

        self.cursor.execute("INSERT INTO componentes (categoria, codigo, ubicacion, cantidad, notas) VALUES (?, ?, ?, ?, ?)",
                            (cat, codigo, ubicacion, cant, ""))
        self.conn.commit()
        self.cargar_componentes()
        self.ent_cmp_codigo.delete(0, 'end')
        self.ent_cmp_ubicacion.delete(0, 'end')
        self.ent_cmp_cantidad.delete(0, 'end')

    def cargar_componentes(self):
        for i in self.tree_cmp.get_children():
            self.tree_cmp.delete(i)
        self.cursor.execute("SELECT id, categoria, codigo, ubicacion, cantidad FROM componentes ORDER BY id DESC")
        for row in self.cursor.fetchall():
            cant = row[4]
            tag_st = "st_ok" if cant > 3 else ("st_warn" if cant > 0 else "st_bad")
            self.tree_cmp.insert("", "end", values=row, tags=(tag_st,))

    def filtrar_componentes(self):
        criterio = self.ent_cmp_buscar.get().strip()
        if not criterio:
            self.cargar_componentes()
            return
        for i in self.tree_cmp.get_children():
            self.tree_cmp.delete(i)
        query = "%" + criterio.lower() + "%"
        self.cursor.execute("SELECT id, categoria, codigo, ubicacion, cantidad FROM componentes WHERE LOWER(codigo) LIKE ? OR LOWER(categoria) LIKE ? OR LOWER(ubicacion) LIKE ? ORDER BY id DESC", (query, query, query))
        for row in self.cursor.fetchall():
            cant = row[4]
            tag_st = "st_ok" if cant > 3 else ("st_warn" if cant > 0 else "st_bad")
            self.tree_cmp.insert("", "end", values=row, tags=(tag_st,))

    def modificar_cantidad(self, delta):
        sel = self.tree_cmp.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un componente de la lista")
            return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id, cant_actual = vals[0], int(vals[4])
        nueva_cant = max(0, cant_actual + delta)

        self.cursor.execute("UPDATE componentes SET cantidad=? WHERE id=?", (nueva_cant, item_id))
        self.conn.commit()
        self.cargar_componentes()

    def cambiar_cantidad_exacta(self):
        sel = self.tree_cmp.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un componente de la lista")
            return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id, codigo, cant_actual = vals[0], vals[2], vals[4]

        nueva_cant = simpledialog.askinteger("Modificar Stock", f"Ingrese el nuevo stock para {codigo}:", initialvalue=cant_actual)
        if nueva_cant is not None:
            self.cursor.execute("UPDATE componentes SET cantidad=? WHERE id=?", (nueva_cant, item_id))
            self.conn.commit()
            self.cargar_componentes()

    def cambiar_ubicacion(self):
        sel = self.tree_cmp.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un componente de la lista")
            return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id, codigo, ubicacion_actual = vals[0], vals[2], vals[3]

        nueva_ubicacion = simpledialog.askstring("Cambiar Gavetero", f"Ingrese la nueva ubicación para {codigo}:", initialvalue=ubicacion_actual)
        if nueva_ubicacion is not None:
            self.cursor.execute("UPDATE componentes SET ubicacion=? WHERE id=?", (nueva_ubicacion, item_id))
            self.conn.commit()
            self.cargar_componentes()

    def buscar_datasheet(self):
        sel = self.tree_cmp.selection()
        codigo = self.ent_cmp_codigo.get().strip()
        if not codigo and sel:
            codigo = self.tree_cmp.item(sel[0])["values"][2]

        if not codigo:
            messagebox.showwarning("Atención", "Ingrese o seleccione un componente de la lista")
            return

        query = f'"{codigo}" datasheet pdf'
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    def imprimir_componente(self):
        sel = self.tree_cmp.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un componente para imprimir")
            return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id = vals[0]

        self.cursor.execute("SELECT categoria, codigo, ubicacion, cantidad FROM componentes WHERE id=?", (item_id,))
        res = self.cursor.fetchone()
        if not res: return

        cat, codigo, ubicacion, cantidad = res

        html = f"""
        <div class="header">
            <div class="title">ETIQUETA DE STOCK / COMPONENTE N° {item_id:04d}</div>
            <div class="subtitle">Organización de Gaveteros y Repuestos de Taller</div>
        </div>
        <div class="box">
            <p><span class="field">Componente:</span> {codigo}</p>
            <p><span class="field">Categoría:</span> {cat}</p>
            <p><span class="field">Ubicación / Gavetero:</span> {ubicacion}</p>
            <p><span class="field">Cantidad Disponible:</span> {cantidad} unidades</p>
        </div>
        """
        self.generar_e_imprimir_html(f"Componente_{codigo}", html)

    def eliminar_componente(self):
        sel = self.tree_cmp.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un componente de la lista")
            return
        vals = self.tree_cmp.item(sel[0])["values"]
        item_id, codigo = vals[0], vals[2]

        if messagebox.askyesno("Confirmar Borrado", f"¿Desea borrar el componente '{codigo}' (N° {item_id})?"):
            self.cursor.execute("DELETE FROM componentes WHERE id=?", (item_id,))
            self.conn.commit()
            self.cargar_componentes()

    # ==================== 💰 VENTAS Y USADOS ====================
    def setup_ventas(self):
        frame_in = ctk.CTkFrame(self.tab_ventas)
        frame_in.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_in, text="Producto/Equipo:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_vta_prod = ctk.CTkEntry(frame_in, width=200)
        self.ent_vta_prod.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Precio $:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_vta_precio = ctk.CTkEntry(frame_in, width=120)
        self.ent_vta_precio.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Estado:").grid(row=0, column=4, padx=5, pady=5)
        self.cmb_vta_estado = ctk.CTkComboBox(frame_in, values=["En Venta", "Reservado", "Vendido"])
        self.cmb_vta_estado.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkButton(frame_in, text="Guardar en Publicaciones", command=self.guardar_venta).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        ctk.CTkButton(frame_in, text="🔍 Consultar Valor Usado (MercadoLibre)", command=self.buscar_mercadolibre).grid(row=1, column=2, columnspan=4, padx=5, pady=5)

        self.tree_vta = ttk.Treeview(self.tab_ventas, columns=("ID", "Producto", "Precio", "Estado"), show="headings")
        self.tree_vta.heading("ID", text="N°")
        self.tree_vta.heading("Producto", text="Producto / Equipo")
        self.tree_vta.heading("Precio", text="Precio Publicado ($)")
        self.tree_vta.heading("Estado", text="Estado Venta")

        self.tree_vta.column("ID", width=50, anchor="center")
        self.tree_vta.column("Producto", width=320)
        self.tree_vta.column("Precio", width=130, anchor="e")
        self.tree_vta.column("Estado", width=120, anchor="center")

        self.tree_vta.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabla(self.tree_vta)

        frame_btn = ctk.CTkFrame(self.tab_ventas)
        frame_btn.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_btn, text="Eliminar Registro Seleccionado", fg_color="#A12A2A", command=self.eliminar_venta).pack(side="right", padx=10)

        self.cargar_ventas()

    def guardar_venta(self):
        prod = self.ent_vta_prod.get().strip()
        precio_str = self.ent_vta_precio.get().strip() or "0"
        estado = self.cmb_vta_estado.get()

        if not prod:
            messagebox.showwarning("Atención", "Ingrese la descripción del producto")
            return

        try:
            precio = float(precio_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El precio ingresado no es válido")
            return

        self.cursor.execute("INSERT INTO ventas (producto, precio, estado, notas) VALUES (?, ?, ?, ?)", (prod, precio, estado, ""))
        self.conn.commit()
        self.cargar_ventas()
        self.ent_vta_prod.delete(0, 'end')
        self.ent_vta_precio.delete(0, 'end')

    def cargar_ventas(self):
        for i in self.tree_vta.get_children():
            self.tree_vta.delete(i)
        self.cursor.execute("SELECT id, producto, precio, estado FROM ventas ORDER BY id DESC")
        for row in self.cursor.fetchall():
            row_list = list(row)
            row_list[2] = f"$ {row_list[2]:,.2f}"
            st = row_list[3]
            tag_st = "st_ok" if st == "Vendido" else ("st_warn" if st == "Reservado" else "st_info")
            self.tree_vta.insert("", "end", values=row_list, tags=(tag_st,))

    def eliminar_venta(self):
        sel = self.tree_vta.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un registro de la lista")
            return
        item_id = self.tree_vta.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Desea borrar el registro N° {item_id}?"):
            self.cursor.execute("DELETE FROM ventas WHERE id=?", (item_id,))
            self.conn.commit()
            self.cargar_ventas()

    def buscar_mercadolibre(self):
        prod = self.ent_vta_prod.get().strip()
        if not prod:
            sel = self.tree_vta.selection()
            if sel: prod = self.tree_vta.item(sel[0])["values"][1]

        if not prod:
            messagebox.showwarning("Atención", "Escriba un producto o seleccione uno de la lista")
            return

        query = f"{prod} usado"
        webbrowser.open(f"https://listado.mercadolibre.com.ar/{query.replace(' ', '-')}")

    # ==================== 💵 CAJA Y FINANZAS ====================
    def setup_caja(self):
        frame_top = ctk.CTkFrame(self.tab_caja)
        frame_top.pack(fill="x", padx=10, pady=5)

        self.lbl_caja_ingresos = ctk.CTkLabel(frame_top, text="Ingresos: $ 0.00", font=("Segoe UI", 12, "bold"), text_color="#4ade80")
        self.lbl_caja_ingresos.pack(side="left", padx=15, pady=10)

        self.lbl_caja_egresos = ctk.CTkLabel(frame_top, text="Egresos: $ 0.00", font=("Segoe UI", 12, "bold"), text_color="#f87171")
        self.lbl_caja_egresos.pack(side="left", padx=15, pady=10)

        self.lbl_caja_balance = ctk.CTkLabel(frame_top, text="Balance Neto: $ 0.00", font=("Segoe UI", 13, "bold"), text_color="#38bdf8")
        self.lbl_caja_balance.pack(side="right", padx=15, pady=10)

        frame_in = ctk.CTkFrame(self.tab_caja)
        frame_in.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_in, text="Tipo Movimiento:").grid(row=0, column=0, padx=5, pady=5)
        self.cmb_caja_tipo = ctk.CTkComboBox(frame_in, values=["Ingreso", "Egreso"])
        self.cmb_caja_tipo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Concepto / Detalle:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_caja_concepto = ctk.CTkEntry(frame_in, width=280)
        self.ent_caja_concepto.grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkLabel(frame_in, text="Monto $:").grid(row=0, column=4, padx=5, pady=5)
        self.ent_caja_monto = ctk.CTkEntry(frame_in, width=120)
        self.ent_caja_monto.grid(row=0, column=5, padx=5, pady=5)

        ctk.CTkButton(frame_in, text="Registrar Movimiento", fg_color="#15803d", command=self.guardar_movimiento_caja).grid(row=0, column=6, padx=10, pady=5)

        frame_busqueda = ctk.CTkFrame(self.tab_caja)
        frame_busqueda.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_busqueda, text="🔎 Buscar en Caja:").pack(side="left", padx=5)
        self.ent_caja_buscar = ctk.CTkEntry(frame_busqueda, width=320, placeholder_text="Concepto, fecha (AAAA-MM-DD), monto o tipo...")
        self.ent_caja_buscar.pack(side="left", padx=5)

        ctk.CTkButton(frame_busqueda, text="Filtrar", command=self.filtrar_caja).pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="Ver Todo", fg_color="gray", command=self.cargar_caja).pack(side="left", padx=5)
        self.ent_caja_buscar.bind("<Return>", lambda event: self.filtrar_caja())

        self.tree_caja = ttk.Treeview(self.tab_caja, columns=("ID", "Fecha", "Tipo", "Concepto", "Monto"), show="headings")
        self.tree_caja.heading("ID", text="N°")
        self.tree_caja.heading("Fecha", text="Fecha y Hora")
        self.tree_caja.heading("Tipo", text="Tipo")
        self.tree_caja.heading("Concepto", text="Concepto / Detalle")
        self.tree_caja.heading("Monto", text="Monto ($)")

        self.tree_caja.column("ID", width=50, anchor="center")
        self.tree_caja.column("Fecha", width=140, anchor="center")
        self.tree_caja.column("Tipo", width=100, anchor="center")
        self.tree_caja.column("Concepto", width=400)
        self.tree_caja.column("Monto", width=120, anchor="e")

        self.tree_caja.pack(fill="both", expand=True, padx=10, pady=5)
        self.configurar_tags_tabla(self.tree_caja)

        frame_btn = ctk.CTkFrame(self.tab_caja)
        frame_btn.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(frame_btn, text="Eliminar Movimiento", fg_color="#A12A2A", command=self.eliminar_movimiento_caja).pack(side="right", padx=10)

        self.cargar_caja()

    def guardar_movimiento_caja(self):
        tipo = self.cmb_caja_tipo.get()
        concepto = self.ent_caja_concepto.get().strip()
        monto_str = self.ent_caja_monto.get().strip()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not concepto or not monto_str:
            messagebox.showwarning("Atención", "Ingrese el concepto y el monto")
            return

        try:
            monto = float(monto_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "El monto ingresado no es válido")
            return

        self.cursor.execute("INSERT INTO caja (fecha, tipo, concepto, monto) VALUES (?, ?, ?, ?)", (fecha_actual, tipo, concepto, monto))
        self.conn.commit()
        self.cargar_caja()
        self.ent_caja_concepto.delete(0, 'end')
        self.ent_caja_monto.delete(0, 'end')

    def cargar_caja(self):
        if hasattr(self, 'ent_caja_buscar'):
            self.ent_caja_buscar.delete(0, 'end')

        for i in self.tree_caja.get_children():
            self.tree_caja.delete(i)

        total_ingresos = 0.0
        total_egresos = 0.0

        self.cursor.execute("SELECT id, fecha, tipo, concepto, monto FROM caja ORDER BY id DESC")
        for row in self.cursor.fetchall():
            row_list = list(row)
            monto_val, tipo = row_list[4], row_list[2]

            if tipo == "Ingreso":
                total_ingresos += monto_val
                tag_st = "st_ok"
            else:
                total_egresos += monto_val
                tag_st = "st_bad"

            row_list[4] = f"$ {monto_val:,.2f}"
            self.tree_caja.insert("", "end", values=row_list, tags=(tag_st,))

        balance = total_ingresos - total_egresos

        self.lbl_caja_ingresos.configure(text=f"Ingresos: $ {total_ingresos:,.2f}")
        self.lbl_caja_egresos.configure(text=f"Egresos: $ {total_egresos:,.2f}")
        self.lbl_caja_balance.configure(text=f"Balance Neto: $ {balance:,.2f}")

    def filtrar_caja(self):
        criterio = self.ent_caja_buscar.get().strip()
        if not criterio:
            self.cargar_caja()
            return

        for i in self.tree_caja.get_children():
            self.tree_caja.delete(i)

        total_ingresos = 0.0
        total_egresos = 0.0

        query = "%" + criterio.lower() + "%"
        
        self.cursor.execute("""
            SELECT id, fecha, tipo, concepto, monto 
            FROM caja 
            WHERE LOWER(concepto) LIKE ? 
               OR fecha LIKE ? 
               OR LOWER(tipo) LIKE ? 
               OR CAST(monto AS TEXT) LIKE ?
            ORDER BY id DESC
        """, (query, query, query, query))

        for row in self.cursor.fetchall():
            row_list = list(row)
            monto_val, tipo = row_list[4], row_list[2]

            if tipo == "Ingreso":
                total_ingresos += monto_val
                tag_st = "st_ok"
            else:
                total_egresos += monto_val
                tag_st = "st_bad"

            row_list[4] = f"$ {monto_val:,.2f}"
            self.tree_caja.insert("", "end", values=row_list, tags=(tag_st,))

        balance = total_ingresos - total_egresos
        self.lbl_caja_ingresos.configure(text=f"Ingresos: $ {total_ingresos:,.2f}")
        self.lbl_caja_egresos.configure(text=f"Egresos: $ {total_egresos:,.2f}")
        self.lbl_caja_balance.configure(text=f"Balance Neto (Filtrado): $ {balance:,.2f}")

    def eliminar_movimiento_caja(self):
        sel = self.tree_caja.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un movimiento de la lista")
            return
        item_id = self.tree_caja.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"¿Desea eliminar el movimiento N° {item_id}?"):
            self.cursor.execute("DELETE FROM caja WHERE id=?", (item_id,))
            self.conn.commit()
            self.cargar_caja()

# ==================== PUNTO DE ENTRADA ====================
if __name__ == "__main__":
    session = cargar_session()
    autenticado = False
    usuario_actual = ""
    token_acceso = ""
    can_download = False

    if session:
        token_candidato = session.get("token")
        try:
            url = "http://127.0.0.1:8000/api/v1/verify-token"
            headers = {"Authorization": f"Bearer {token_candidato}"}
            res = requests.get(url, headers=headers, timeout=3)
            
            if res.status_code == 200:
                data = res.json()
                autenticado = True
                usuario_actual = data.get("usuario")
                token_acceso = token_candidato
                can_download = data.get("can_download", True)
            else:
                borrar_session()
        except Exception:
            autenticado = True
            usuario_actual = session.get("username")
            token_acceso = token_candidato
            can_download = session.get("can_download", True)

    if not autenticado:
        login = LoginDialog()
        login.mainloop()
        autenticado = login.autenticado
        usuario_actual = login.usuario_actual
        token_acceso = login.token_acceso
        can_download = login.can_download

    if autenticado:
        app = TallerApp(
            usuario_actual=usuario_actual,
            token_acceso=token_acceso,
            can_download=can_download
        )
        try:
            app.mainloop()
        except Exception:
            pass