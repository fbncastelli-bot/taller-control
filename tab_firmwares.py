import customtkinter as ctk
from tkinter import ttk, messagebox
import requests
import threading
import os

class TabFirmwares:
    def __init__(self, parent_frame, user_token="", can_download=True):
        self.parent = parent_frame
        self.user_token = user_token
        self.can_download = can_download
        self.download_thread = None
        self.cancel_flag = False

        self.setup_ui()
        self.cargar_firmwares_nube()

    def setup_ui(self):
        frame_top = ctk.CTkFrame(self.parent)
        frame_top.pack(fill="x", padx=10, pady=5)

        self.lbl_estado_plan = ctk.CTkLabel(
            frame_top, 
            text="ESTADO: Activo | Plan Premium Taller", 
            font=("Segoe UI", 11, "bold"), 
            text_color="#4ade80"
        )
        self.lbl_estado_plan.pack(side="left", padx=10, pady=10)

        btn_refresh = ctk.CTkButton(
            frame_top, 
            text="🔄 Actualizar Lista", 
            width=130, 
            command=self.cargar_firmwares_nube
        )
        btn_refresh.pack(side="right", padx=5, pady=5)

        btn_clear = ctk.CTkButton(
            frame_top, 
            text="✖ Limpiar Selección", 
            width=140, 
            fg_color="#475569", 
            hover_color="#334155", 
            command=self.deseleccionar_todo
        )
        btn_clear.pack(side="right", padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.parent, 
            columns=("ID", "Modelo", "Chasis", "Archivo"), 
            show="headings"
        )
        self.tree.heading("ID", text="N°")
        self.tree.heading("Modelo", text="Modelo de Smart TV")
        self.tree.heading("Chasis", text="Chasis / Mainboard")
        self.tree.heading("Archivo", text="Nombre de Archivo")

        self.tree.column("ID", width=60, anchor="center")
        self.tree.column("Modelo", width=250)
        self.tree.column("Chasis", width=200)
        self.tree.column("Archivo", width=350)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Button-1>", self.on_click_tabla)

        frame_bottom = ctk.CTkFrame(self.parent)
        frame_bottom.pack(fill="x", padx=10, pady=5)

        self.lbl_seleccion = ctk.CTkLabel(
            frame_bottom, 
            text="Seleccione un firmware de la lista para descargar...", 
            font=("Segoe UI", 11, "italic"),
            text_color="#94a3b8"
        )
        self.lbl_seleccion.pack(side="left", padx=10)

        self.btn_download = ctk.CTkButton(
            frame_bottom, 
            text="⬇️ Descargar Firmware", 
            fg_color="#15803d", 
            hover_color="#166534",
            state="disabled", 
            command=self.iniciar_descarga
        )
        self.btn_download.pack(side="right", padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(frame_bottom, width=200)
        self.progress_bar.set(0)

    def cargar_firmwares_nube(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.deseleccionar_todo()

        def fetch():
            try:
                url = "http://127.0.0.1:8000/api/v1/firmwares"
                headers = {"Authorization": f"Bearer {self.user_token}"}
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.parent.after(0, lambda: self._poblar_tabla(data))
                elif response.status_code in (401, 403):
                    self.parent.after(0, lambda: messagebox.showerror("Acceso Denegado", "Suscripción expirada o Token inválido."))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error", f"Error servidor: {response.status_code}"))
            except Exception as e:
                msg = str(e)
                self.parent.after(0, lambda: messagebox.showerror("Error de Conexión", f"No se pudo conectar con el servidor de firmwares:\n{msg}"))

        threading.Thread(target=fetch, daemon=True).start()

    def _poblar_tabla(self, data):
        for item in data:
            self.tree.insert("", "end", values=(item["id"], item["modelo"], item["chasis"], item["filename"]))

    def on_click_tabla(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.deseleccionar_todo()

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            vals = self.tree.item(selected[0])["values"]
            self.lbl_seleccion.configure(
                text=f"Seleccionado: ID {vals[0]} - {vals[1]} ({vals[3]})", 
                text_color="#38bdf8"
            )
            if self.can_download:
                self.btn_download.configure(state="normal", fg_color="#15803d")
        else:
            self.deseleccionar_todo()

    def deseleccionar_todo(self):
        selected = self.tree.selection()
        if selected:
            self.tree.selection_remove(selected)
        
        self.lbl_seleccion.configure(
            text="Seleccione un firmware de la lista para descargar...", 
            text_color="#94a3b8"
        )
        self.btn_download.configure(state="disabled", fg_color="gray")
        self.progress_bar.pack_forget()

    def iniciar_descarga(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un firmware de la lista")
            return

        vals = self.tree.item(selected[0])["values"]
        fw_id = vals[0]
        filename = vals[3]

        self.btn_download.configure(state="disabled")
        self.progress_bar.pack(side="right", padx=10)
        self.progress_bar.set(0)

        def download():
            try:
                url = f"http://127.0.0.1:8000/api/v1/firmwares/download/{fw_id}"
                headers = {"Authorization": f"Bearer {self.user_token}"}
                
                with requests.get(url, headers=headers, stream=True, timeout=10) as r:
                    r.raise_for_status()
                    total_length = int(r.headers.get('content-length', 0))
                    
                    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
                    save_path = os.path.join(downloads_dir, filename)

                    dl = 0
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if self.cancel_flag:
                                break
                            if chunk:
                                dl += len(chunk)
                                f.write(chunk)
                                if total_length:
                                    percent = dl / total_length
                                    self.parent.after(0, lambda p=percent: self.progress_bar.set(p))

                if not self.cancel_flag:
                    self.parent.after(0, lambda: messagebox.showinfo("Éxito", f"Firmware descargado en:\n{save_path}"))
            except requests.exceptions.HTTPError as http_err:
                status_c = http_err.response.status_code if http_err.response else "desconocido"
                if status_c in (401, 403):
                    self.parent.after(0, lambda: messagebox.showerror("Error de Autorización", "Su suscripción no le permite realizar descargas."))
                else:
                    self.parent.after(0, lambda: messagebox.showerror("Error HTTP", f"Error de servidor ({status_c}): {http_err}"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Fallo al descargar: {e}"))
            finally:
                self.parent.after(0, self.deseleccionar_todo)

        self.cancel_flag = False
        threading.Thread(target=download, daemon=True).start()

    def cancelar_descargas(self):
        self.cancel_flag = True