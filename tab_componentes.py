import customtkinter as ctk
from tkinter import ttk, messagebox
import webbrowser

class TabComponentes(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Panel Superior de Control
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.lbl_buscar = ctk.CTkLabel(self.frame_top, text="Buscar Componente:")
        self.lbl_buscar.pack(side="left", padx=5)

        self.entry_buscar = ctk.CTkEntry(self.frame_top, placeholder_text="Matrícula, Categoría o Ubicación...")
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_componentes)

        self.btn_datasheet = ctk.CTkButton(self.frame_top, text="Buscar Datasheet (PDF)", fg_color="#2b8a3e", command=self.buscar_datasheet)
        self.btn_datasheet.pack(side="right", padx=5)

        self.btn_nuevo = ctk.CTkButton(self.frame_top, text="Nuevo Componente", command=self.abrir_dialogo_nuevo)
        self.btn_nuevo.pack(side="right", padx=5)

        # Tabla de Componentes con Tags de Color para Stock Crítico
        self.tree = ttk.Treeview(self, columns=("ID", "Categoria", "Codigo", "Ubicacion", "Cantidad"), show="headings")
        
        headers = ["ID", "Categoria", "Codigo", "Ubicacion", "Cantidad"]
        for col in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=40)
        self.tree.column("Codigo", width=150)
        
        # Estilos visuales para alerta de Stock Crítico
        self.tree.tag_configure("stock_ok", background="#e6fffa", foreground="#000000")
        self.tree.tag_configure("stock_bajo", background="#fff9db", foreground="#000000")
        self.tree.tag_configure("stock_critico", background="#ffe3e3", foreground="#000000")

        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Botones de ajuste rápido de stock (+1 / -1)
        self.frame_bot = ctk.CTkFrame(self)
        self.frame_bot.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.btn_restar = ctk.CTkButton(self.frame_bot, text="-1 Restar Stock", fg_color="#c92a2a", width=120, command=lambda: self.modificar_stock(-1))
        self.btn_restar.pack(side="left", padx=10, pady=5)

        self.btn_sumar = ctk.CTkButton(self.frame_bot, text="+1 Sumar Stock", fg_color="#2b8a3e", width=120, command=lambda: self.modificar_stock(1))
        self.btn_sumar.pack(side="left", padx=5, pady=5)

        self.cargar_componentes()

    def cargar_componentes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        registros = self.db.obtener_datos("SELECT id, categoria, codigo, ubicacion, cantidad FROM componentes ORDER BY codigo ASC")
        for reg in registros:
            cant = reg["cantidad"]
            tag = "stock_ok" if cant > 3 else ("stock_bajo" if cant > 0 else "stock_critico")
            
            self.tree.insert("", "end", values=(
                reg["id"], reg["categoria"], reg["codigo"], 
                reg["ubicacion"], cant
            ), tags=(tag,))

    def filtrar_componentes(self, event=None):
        query = self.entry_buscar.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        sql = """SELECT id, categoria, codigo, ubicacion, cantidad 
                 FROM componentes 
                 WHERE codigo LIKE ? OR categoria LIKE ? OR ubicacion LIKE ?
                 ORDER BY codigo ASC"""
        param = f"%{query}%"
        registros = self.db.obtener_datos(sql, (param, param, param))
        
        for reg in registros:
            cant = reg["cantidad"]
            tag = "stock_ok" if cant > 3 else ("stock_bajo" if cant > 0 else "stock_critico")
            
            self.tree.insert("", "end", values=(
                reg["id"], reg["categoria"], reg["codigo"], 
                reg["ubicacion"], cant
            ), tags=(tag,))

    def modificar_stock(self, delta):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un componente de la lista.")
            return

        valores = self.tree.item(selected[0])['values']
        comp_id = valores[0]
        cant_actual = valores[4]
        nueva_cant = max(0, cant_actual + delta)

        self.db.ejecutar_consulta("UPDATE componentes SET cantidad = ? WHERE id = ?", (nueva_cant, comp_id))
        self.cargar_componentes()

    def buscar_datasheet(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un componente para buscar su hoja de datos.")
            return

        valores = self.tree.item(selected[0])['values']
        codigo = valores[2]
        
        url = f"https://www.google.com/search?q={codigo}+datasheet+filetype:pdf"
        webbrowser.open(url)

    def abrir_dialogo_nuevo(self):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Agregar Componente Discreto")
        dialogo.geometry("380x380")
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="Matrícula / Código:").pack(pady=2)
        ent_cod = ctk.CTkEntry(dialogo, width=280)
        ent_cod.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Categoría (ej: MOSFET, PWM, Diodo):").pack(pady=2)
        ent_cat = ctk.CTkEntry(dialogo, width=280)
        ent_cat.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Ubicación (ej: Cajón A1):").pack(pady=2)
        ent_ubi = ctk.CTkEntry(dialogo, width=280)
        ent_ubi.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Cantidad Inicial:").pack(pady=2)
        ent_cant = ctk.CTkEntry(dialogo, width=280)
        ent_cant.insert(0, "1")
        ent_cant.pack(pady=2)

        def guardar():
            cod = ent_cod.get().strip()
            if not cod:
                messagebox.showerror("Error", "La matrícula del componente es obligatoria", parent=dialogo)
                return

            try:
                cant = int(ent_cant.get().strip())
            except ValueError:
                cant = 0

            self.db.ejecutar_consulta(
                "INSERT INTO componentes (codigo, categoria, ubicacion, cantidad) VALUES (?, ?, ?, ?)",
                (cod, ent_cat.get().strip(), ent_ubi.get().strip(), cant)
            )
            
            dialogo.destroy()
            self.cargar_componentes()

        ctk.CTkButton(dialogo, text="Guardar Componente", command=guardar).pack(pady=15)