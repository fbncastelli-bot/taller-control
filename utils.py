import csv
import os
import tempfile
import webbrowser

def exportar_tabla_a_csv(db_instance, nombre_tabla, ruta_destino):
    """Exporta cualquier tabla de la base de datos a un archivo CSV (Excel)"""
    try:
        registros = db_instance.obtener_datos(f"SELECT * FROM {nombre_tabla}")
        if not registros:
            return False, "No hay datos para exportar."

        # Obtener nombres de columnas
        with db_instance.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {nombre_tabla} LIMIT 1")
            columnas = [description[0] for description in cursor.description]

        with open(ruta_destino, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(columnas)
            
            # Convertir registros (objetos Row) a listas para escribir en el CSV
            for fila in registros:
                writer.writerow([fila[col] for col in columnas])

        return True, f"Datos exportados correctamente a {os.path.basename(ruta_destino)}"
    except Exception as e:
        return False, f"Error al exportar: {str(e)}"

def generar_e_imprimir_html(titulo, contenido_html):
    """Renderiza el documento de impresión en el navegador"""
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Segoe UI, Arial, sans-serif; margin: 20px; color: #111; }}
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