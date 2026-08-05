import customtkinter as ctk
from tkinter import ttk, messagebox
import webbrowser

class TabPlacas(ctk.CTkFrame):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Panel Superior de Búsqueda y Acciones
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.lbl_buscar = ctk.CTkLabel(self.frame_top, text="Buscar Placa:")
        self.lbl_buscar.pack(side="left", padx=5)

        self.entry_buscar = ctk.CTkEntry(self.frame_top, placeholder_text="Código Main, Modelo TV, Chasis...")
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_placas)

        self.btn_buscar_web = ctk.CTkButton(self.frame_top, text="Buscar Reformas LED", fg_color="#1f538d", command=self.buscar_reforma_web)
        self.btn_buscar_web.pack(side="right", padx=5)

        self.btn_nueva = ctk.CTkButton(self.frame_top, text="Nueva Placa", command=self.abrir_dialogo_nueva_placa)
        self.btn_nueva.pack(side="right", padx=5)

        # Tabla de Placas
        self.tree = ttk.Treeview(self, columns=("ID", "Codigo Main", "TV Modelo", "Chasis", "Panel", "Ubicacion", "Estado"), show="headings")
        
        headers = ["ID", "Codigo Main", "TV Modelo", "Chasis", "Panel", "Ubicacion", "Estado"]
        for col in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.column("ID", width=40)
        self.tree.column("Codigo Main", width=150)
        
        self.tree.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        self.cargar_placas()

    def cargar_placas(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        registros = self.db.obtener_datos("SELECT id, codigo_main, tv_modelo, chasis, panel, ubicacion, estado FROM placas ORDER BY id DESC")
        for reg in registros:
            self.tree.insert("", "end", values=(
                reg["id"], reg["codigo_main"], reg["tv_modelo"], reg["chasis"], 
                reg["panel"], reg["ubicacion"], reg["estado"]
            ))

    def filtrar_placas(self, event=None):
        query = self.entry_buscar.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        sql = """SELECT id, codigo_main, tv_modelo, chasis, panel, ubicacion, estado 
                 FROM placas 
                 WHERE codigo_main LIKE ? OR tv_modelo LIKE ? OR chasis LIKE ? OR panel LIKE ?
                 ORDER BY id DESC"""
        param = f"%{query}%"
        registros = self.db.obtener_datos(sql, (param, param, param, param))
        
        for reg in registros:
            self.tree.insert("", "end", values=(
                reg["id"], reg["codigo_main"], reg["tv_modelo"], reg["chasis"], 
                reg["panel"], reg["ubicacion"], reg["estado"]
            ))

    def buscar_reforma_web(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione una placa de la lista para buscar reformas de corriente LED.")
            return
        
        valores = self.tree.item(selected[0])['values']
        codigo_main = valores[1]
        
        # Abre búsqueda automatizada en Google para bajada de corriente LED
        url = f"https://www.google.com/search?q=reforma+bajar+corriente+led+{codigo_main}"
        webbrowser.open(url)

    def abrir_dialogo_nueva_placa(self):
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Registrar Placa / Repuesto")
        dialogo.geometry("400x480")
        dialogo.grab_set()

        ctk.CTkLabel(dialogo, text="Código Main / Fuente:").pack(pady=2)
        ent_cod = ctk.CTkEntry(dialogo, width=300)
        ent_cod.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Modelo TV Asociado:").pack(pady=2)
        ent_mod = ctk.CTkEntry(dialogo, width=300)
        ent_mod.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Chasis:").pack(pady=2)
        ent_cha = ctk.CTkEntry(dialogo, width=300)
        ent_cha.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Panel (Display):").pack(pady=2)
        ent_pan = ctk.CTkEntry(dialogo, width=300)
        ent_pan.pack(pady=2)

        ctk.CTkLabel(dialogo, text="Ubicación en Estante/Caja:").pack(pady=2)
        ent_ubi = ctk.CTkEntry(dialogo, width=300)
        ent_ubi.pack(pady=2)

        def guardar():
            cod = ent_cod.get().strip()
            if not cod:
                messagebox.showerror("Error", "El Código Main es obligatorio", parent=dialogo)
                return

            self.db.ejecutar_consulta(
                "INSERT INTO placas (codigo_main, tv_modelo, chasis, panel, ubicacion) VALUES (?, ?, ?, ?, ?)",
                (cod, ent_mod.get().strip(), ent_cha.get().strip(), ent_pan.get().strip(), ent_ubi.get().strip())
            )
            
            dialogo.destroy()
            self.cargar_placas()

        ctk.CTkButton(dialogo, text="Guardar Placa", command=guardar).pack(pady=15)