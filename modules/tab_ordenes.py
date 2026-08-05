import customtkinter as ctk
from tkinter import ttk, messagebox
import utils

class TabOrdenes(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        
        # Estructura del módulo
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Panel de Búsqueda y Control
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.lbl_buscar = ctk.CTkLabel(self.frame_top, text="Buscar Orden:")
        self.lbl_buscar.pack(side="left", padx=5)

        self.entry_buscar = ctk.CTkEntry(self.frame_top, placeholder_text="Cliente, equipo u ID...")
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_ordenes)

        self.btn_nueva = ctk.CTkButton(self.frame_top, text="Nueva Orden", command=self.abrir_dialogo_nueva_orden)
        self.btn_nueva.pack(side="right", padx=5)

        # Tabla de Órdenes
        self.tree = ttk.Treeview(self, columns=("ID", "Cliente", "Equipo", "Falla", "Estado", "Presupuesto", "Fecha"), show="headings")
        
        headers = ["ID", "Cliente", "Equipo", "Falla", "Estado", "Presupuesto", "Fecha"]
        for col in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=50)
        self.tree.column("Falla", width=200)
        
        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        self.cargar_ordenes()

    def cargar_ordenes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        registros = self.db.obtener_datos("SELECT id, cliente, equipo, falla, estado, presupuesto, fecha_ingreso FROM ordenes ORDER BY id DESC")
        for reg in registros:
            self.tree.insert("", "end", values=(
                reg["id"], reg["cliente"], reg["equipo"], reg["falla"], 
                reg["estado"], f"${reg['presupuesto']:.2f}", reg["fecha_ingreso"]
            ))

    def filtrar_ordenes(self, event=None):
        query = self.entry_buscar.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        sql = """SELECT id, cliente, equipo, falla, estado, presupuesto, fecha_ingreso 
                 FROM ordenes 
                 WHERE cliente LIKE ? OR equipo LIKE ? OR id LIKE ? 
                 ORDER BY id DESC"""
        param = f"%{query}%"
        registros = self.db.obtener_datos(sql, (param, param, param))
        
        for reg in registros:
            self.tree.insert("", "end", values=(
                reg["id"], reg["cliente"], reg["equipo"], reg["falla"], 
                reg["estado"], f"${reg['presupuesto']:.2f}", reg["fecha_ingreso"]
            ))

    def abrir_dialogo_nueva_orden(self):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Ingresar Nueva Orden")
        dialogo.geometry("400x400")
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="Cliente:").pack(pady=2)
        ent_cliente = ctk.CTkEntry(dialogo, width=300)
        ent_cliente.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Equipo / Modelo:").pack(pady=2)
        ent_equipo = ctk.CTkEntry(dialogo, width=300)
        ent_equipo.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Falla Declarada:").pack(pady=2)
        ent_falla = ctk.CTkEntry(dialogo, width=300)
        ent_falla.pack(pady=2)

        def guardar():
            cli = ent_cliente.get().strip()
            eq = ent_equipo.get().strip()
            fa = ent_falla.get().strip()
            
            if not cli or not eq:
                messagebox.showerror("Error", "Cliente y Equipo son obligatorios", parent=dialogo)
                return

            orden_id = self.db.ejecutar_consulta(
                "INSERT INTO ordenes (cliente, equipo, falla) VALUES (?, ?, ?)",
                (cli, eq, fa)
            )
            
            # Generar comprobante HTML
            html = f"""
            <div class="header">
                <div class="title">ORDEN DE INGRESO #{orden_id}</div>
                <div class="subtitle">Taller de Electrónica</div>
            </div>
            <div class="box">
                <p><span class="field">Cliente:</span> {cli}</p>
                <p><span class="field">Equipo:</span> {eq}</p>
                <p><span class="field">Falla:</span> {fa}</p>
            </div>
            """
            utils.generar_e_imprimir_html(f"Orden_{orden_id}", html)
            
            dialogo.destroy()
            self.cargar_ordenes()

        ctk.CTkButton(dialogo, text="Guardar e Imprimir Comprobante", command=guardar).pack(pady=20)