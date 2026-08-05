import tkinter as tk
from tkinter import ttk, messagebox

class TabVentas(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        
        self.id_seleccionado = None
        
        self.crear_interface()
        self.cargar_datos()

    def crear_interface(self):
        # Panel Izquierdo: Formularios (Ventas y Movimiento de Caja)
        left_frame = ttk.LabelFrame(self, text=" Registro / Entrada ", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Campos de Venta
        ttk.Label(left_frame, text="Producto / Servicio:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ent_producto = ttk.Entry(left_frame, width=25)
        self.ent_producto.grid(row=0, column=1, pady=2, padx=5)

        ttk.Label(left_frame, text="Precio ($):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ent_precio = ttk.Entry(left_frame, width=25)
        self.ent_precio.grid(row=1, column=1, pady=2, padx=5)

        ttk.Label(left_frame, text="Estado:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.cmb_estado = ttk.Combobox(left_frame, values=["En Venta", "Vendida", "Reservada"], width=23, state="readonly")
        self.cmb_estado.set("En Venta")
        self.cmb_estado.grid(row=2, column=1, pady=2, padx=5)

        ttk.Label(left_frame, text="Notas:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.ent_notas = ttk.Entry(left_frame, width=25)
        self.ent_notas.grid(row=3, column=1, pady=2, padx=5)

        # Botones de Ventas
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Agregar Venta", command=self.agregar_venta).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Actualizar", command=self.actualizar_venta).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Eliminar", command=self.eliminar_venta).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Limpiar", command=self.limpiar_campos).pack(side=tk.LEFT, padx=2)

        # Separador visual
        ttk.Separator(left_frame, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

        # Sección Registrar Movimiento de Caja directo
        ttk.Label(left_frame, text="Movimiento Directo de Caja", font=('Helvetica', 9, 'bold')).grid(row=6, column=0, columnspan=2, pady=5)
        
        ttk.Label(left_frame, text="Tipo:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.cmb_caja_tipo = ttk.Combobox(left_frame, values=["Ingreso", "Egreso"], width=23, state="readonly")
        self.cmb_caja_tipo.set("Ingreso")
        self.cmb_caja_tipo.grid(row=7, column=1, pady=2, padx=5)

        ttk.Label(left_frame, text="Monto ($):").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.ent_caja_monto = ttk.Entry(left_frame, width=25)
        self.ent_caja_monto.grid(row=8, column=1, pady=2, padx=5)

        ttk.Button(left_frame, text="Registrar en Caja", command=self.registrar_caja_directo).grid(row=9, column=0, columnspan=2, pady=10)

        # Panel Derecho: Grilla de datos (Treeview)
        right_frame = ttk.LabelFrame(self, text=" Listado de Ventas ", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "producto", "precio", "estado", "notas")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("producto", text="Producto / Servicio")
        self.tree.heading("precio", text="Precio ($)")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("notas", text="Notas")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("producto", width=180)
        self.tree.column("precio", width=80, anchor=tk.E)
        self.tree.column("estado", width=100, anchor=tk.CENTER)
        self.tree.column("notas", width=200)

        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_registro)

    def cargar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = "SELECT id, producto, precio, estado, notas FROM ventas ORDER BY id DESC"
        filas = self.db.obtener_datos(query)
        for fila in filas:
            self.tree.insert("", tk.END, values=(fila["id"], fila["producto"], fila["precio"], fila["estado"], fila["notas"]))

    def agregar_venta(self):
        producto = self.ent_producto.get().strip()
        precio_str = self.ent_precio.get().strip()
        estado = self.cmb_estado.get()
        notas = self.ent_notas.get().strip()

        if not producto:
            messagebox.showwarning("Atención", "El campo Producto es obligatorio.")
            return

        try:
            precio = float(precio_str) if precio_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido.")
            return

        query_venta = "INSERT INTO ventas (producto, precio, estado, notas) VALUES (?, ?, ?, ?)"
        self.db.ejecutar_consulta(query_venta, (producto, precio, estado, notas))

        # Si el estado se marca directamente como "Vendida", impacta el ingreso en la tabla caja
        if estado == "Vendida" and precio > 0:
            query_caja = "INSERT INTO caja (tipo, concepto, monto) VALUES ('Ingreso', ?, ?)"
            self.db.ejecutar_consulta(query_caja, (f"Venta: {producto}", precio))

        self.limpiar_campos()
        self.cargar_datos()

    def actualizar_venta(self):
        if not self.id_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un registro para actualizar.")
            return

        producto = self.ent_producto.get().strip()
        precio_str = self.ent_precio.get().strip()
        estado = self.cmb_estado.get()
        notas = self.ent_notas.get().strip()

        try:
            precio = float(precio_str) if precio_str else 0.0
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido.")
            return

        query = "UPDATE ventas SET producto=?, precio=?, estado=?, notas=? WHERE id=?"
        self.db.ejecutar_consulta(query, (producto, precio, estado, notas, self.id_seleccionado))

        self.limpiar_campos()
        self.cargar_datos()

    def eliminar_venta(self):
        if not self.id_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un registro para eliminar.")
            return

        if messagebox.askyesno("Confirmar", "¿Desea eliminar la venta seleccionada?"):
            query = "DELETE FROM ventas WHERE id=?"
            self.db.ejecutar_consulta(query, (self.id_seleccionado,))
            self.limpiar_campos()
            self.cargar_datos()

    def registrar_caja_directo(self):
        tipo = self.cmb_caja_tipo.get()
        monto_str = self.ent_caja_monto.get().strip()
        producto = self.ent_producto.get().strip() or "Movimiento vario"

        try:
            monto = float(monto_str)
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido para la caja.")
            return

        query = "INSERT INTO caja (tipo, concepto, monto) VALUES (?, ?, ?)"
        self.db.ejecutar_consulta(query, (tipo, f"{tipo}: {producto}", monto))
        
        messagebox.showinfo("Éxito", f"{tipo} de ${monto:.2f} registrado en Caja.")
        self.ent_caja_monto.delete(0, tk.END)

    def seleccionar_registro(self, event):
        item = self.tree.selection()
        if not item:
            return
            
        valores = self.tree.item(item[0], "values")
        self.id_seleccionado = valores[0]

        self.ent_producto.delete(0, tk.END)
        self.ent_producto.insert(0, valores[1])

        self.ent_precio.delete(0, tk.END)
        self.ent_precio.insert(0, valores[2])

        self.cmb_estado.set(valores[3])

        self.ent_notas.delete(0, tk.END)
        self.ent_notas.insert(0, valores[4])

    def limpiar_campos(self):
        self.id_seleccionado = None
        self.ent_producto.delete(0, tk.END)
        self.ent_precio.delete(0, tk.END)
        self.cmb_estado.set("En Venta")
        self.ent_notas.delete(0, tk.END)