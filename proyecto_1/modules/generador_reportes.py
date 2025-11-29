from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
import datetime

# Importamos las bibliotecas que SÍ necesitamos (y que causaron el error)
import os         # Para crear carpetas y unir rutas de archivos
import datetime   # Para crear nombres de archivo únicos con fecha/hora

# Importamos la biblioteca para crear PDF (asegúrate de instalarla: pip install fpdf2)
from fpdf import FPDF 

# Importamos las clases de nuestro dominio
from modules.reclamo import Reclamo 
from modules.usuario import Usuario # Necesario para los datos del reclamo


# Carpeta donde se guardarán los reportes (relativa a la raíz del proyecto)
CARPETA_REPORTES = "reportes"


# --- 2. INTERFAZ ABSTRACTA (Estrategia) ---
# (La incluimos aquí para que el archivo esté completo)

class ReporteEstrategiaAbstracta(ABC):
    """
    Interfaz abstracta (Patrón Estrategia) para definir cómo se genera un reporte.
    """
    
    @abstractmethod
    def generar(self, lista_reclamos: List[Reclamo], estadisticas: Dict[str, Any], departamento: str) -> str:
        """
        Método abstracto para generar el reporte.
        Devolverá la ruta (string) al archivo generado.
        """
        raise NotImplementedError

# --- 3. CLASE "CONTEXTO" (La que usa la estrategia) ---
# (La incluimos aquí para que el archivo esté completo)

class GeneradorReportes:
    """
    Clase principal que genera un reporte utilizando una estrategia específica.
    """
    
    def __init__(self, estrategia: ReporteEstrategiaAbstracta):
        self.__estrategia = estrategia

    def set_estrategia(self, estrategia: ReporteEstrategiaAbstracta):
        self.__estrategia = estrategia

    def generar_reporte(self, lista_reclamos: List[Reclamo], estadisticas: Dict[str, Any], departamento: str) -> str:
        # Delega la creación del reporte a la estrategia seleccionada
        return self.__estrategia.generar(lista_reclamos, estadisticas, departamento)


# --- 4. IMPLEMENTACIONES CONCRETAS (HTML y PDF) ---

class ReporteHTML(ReporteEstrategiaAbstracta):
    """
    Implementación concreta para generar el reporte en formato HTML.
   
    """
    
    def generar(self, lista_reclamos: List[Reclamo], estadisticas: Dict[str, Any], departamento: str) -> str:
        
        # Usamos 'os' para asegurarnos de que la carpeta de reportes exista
        os.makedirs(CARPETA_REPORTES, exist_ok=True)
        
        # Usamos 'datetime' para generar un nombre de archivo único
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_{departamento.replace(' ', '_')}_{timestamp}.html"
        # Usamos 'os.path.join' para crear la ruta de forma segura
        ruta_completa = os.path.join(CARPETA_REPORTES, nombre_archivo)

        # Construir el contenido del HTML
        html = "<html><head><title>Reporte de Reclamos</title>"
        html += """
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1 { color: #333; }
            h2 { color: #555; border-bottom: 1px solid #ccc; padding-bottom: 5px;}
            ul { background-color: #f4f4f4; border: 1px solid #ddd; padding: 15px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f0f0f0; }
        </style>
        """
        html += f"</head><body>"
        html += f"<h1>Reporte de Reclamos - Departamento: {departamento}</h1>"
        
        # --- Sección de Estadísticas ---
        html += "<h2>Estadísticas Generales</h2>"
        html += "<ul>"
        html += f"<li><b>Total de Reclamos:</b> {estadisticas.get('total', 0)}</li>"
        html += f"<li><b>Pendientes:</b> {estadisticas.get('pendientes', 0):.2f}%</li>"
        html += f"<li><b>En Proceso:</b> {estadisticas.get('en_proceso', 0):.2f}%</li>"
        html += f"<li><b>Resueltos:</b> {estadisticas.get('resueltos', 0):.2f}%</li>"
        html += f"<li><b>Mediana Tiempos Resolución:</b> {estadisticas.get('mediana_tiempos', 0)} días</li>"
        # (Aquí podríamos añadir el gráfico de palabras clave si lo pasamos a 'estadisticas')
        html += "</ul>"

        # --- Sección de Lista de Reclamos ---
        html += "<h2>Detalle de Reclamos</h2>"
        html += "<table>"
        html += "<tr><th>ID</th><th>Estado</th><th>Contenido</th><th>Creador (Usuario)</th><th>Fecha</th><th>Adherentes</th></tr>"
        
        for reclamo in lista_reclamos:
            html += "<tr>"
            html += f"<td>{reclamo.id_reclamo}</td>"
            html += f"<td>{reclamo.estado}</td>"
            html += f"<td>{reclamo.contenido}</td>"
            html += f"<td>{reclamo.usuario_creador.nombre_usuario}</td>"
            # Formateamos el timestamp (que es un objeto datetime)
            fecha_str = reclamo.timestamp.strftime('%Y-%m-%d %H:%M') if reclamo.timestamp else 'N/A'
            html += f"<td>{fecha_str}</td>"
            html += f"<td>{reclamo.numero_adherentes}</td>"
            html += "</tr>"
            
        html += "</table>"
        html += "</body></html>"
        
        # Escribir el string HTML en un archivo
        try:
            with open(ruta_completa, "w", encoding="utf-8") as f:
                f.write(html)
            return ruta_completa # Devolvemos la ruta al archivo creado
        except Exception as e:
            return f"Error al crear HTML: {e}"


class ReportePDF(ReporteEstrategiaAbstracta):
    """
    Implementación concreta para generar el reporte en formato PDF.
   
    """
    
    def generar(self, lista_reclamos: List[Reclamo], estadisticas: Dict[str, Any], departamento: str) -> str:
        
        os.makedirs(CARPETA_REPORTES, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_{departamento.replace(' ', '_')}_{timestamp}.pdf"
        ruta_completa = os.path.join(CARPETA_REPORTES, nombre_archivo)

        # Configuración básica del PDF
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- Título ---
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, f"Reporte de Reclamos - Depto: {departamento}", ln=True, align='C')
        pdf.ln(5) # Salto de línea

        # --- Estadísticas ---
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Estadisticas Generales", ln=True)
        
        pdf.set_font("Helvetica", '', 10)
        ancho_celda = 190 # Ancho A4 menos márgenes
        alto_celda = 6
        
        stats_texto = f"""
        - Total de Reclamos: {estadisticas.get('total', 0)}
        - Pendientes: {estadisticas.get('pendientes', 0):.2f}%
        - En Proceso: {estadisticas.get('en_proceso', 0):.2f}%
        - Resueltos: {estadisticas.get('resueltos', 0):.2f}%
        - Mediana Tiempos Resolucion: {estadisticas.get('mediana_tiempos', 0)} dias
        """
        # Usamos multi_cell para texto que puede ser largo
        pdf.multi_cell(ancho_celda, alto_celda, stats_texto, border=1)
        pdf.ln(5)

        # --- Detalle de Reclamos ---
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Detalle de Reclamos", ln=True)
        pdf.set_font("Helvetica", '', 9)
        
        # Encabezado de la "tabla"
        pdf.set_fill_color(240, 240, 240)
        ancho_id = 10
        ancho_estado = 25
        ancho_contenido = 95 # Más pequeño para que quepa todo
        ancho_creador = 30
        ancho_fecha = 20
        ancho_adh = 10
        
        pdf.cell(ancho_id, alto_celda, "ID", border=1, fill=True)
        pdf.cell(ancho_estado, alto_celda, "Estado", border=1, fill=True)
        pdf.cell(ancho_contenido, alto_celda, "Contenido", border=1, fill=True)
        pdf.cell(ancho_creador, alto_celda, "Creador", border=1, fill=True)
        pdf.cell(ancho_fecha, alto_celda, "Fecha", border=1, fill=True)
        pdf.cell(ancho_adh, alto_celda, "Adh.", border=1, fill=True, ln=True)
        
        # Filas de reclamos
        pdf.set_font("Helvetica", '', 8) # Letra más chica para los datos
        
        for reclamo in lista_reclamos:
            # Codificar texto a 'latin-1' para fpdf
            contenido = reclamo.contenido.encode('latin-1', 'replace').decode('latin-1')
            creador = reclamo.usuario_creador.nombre_usuario.encode('latin-1', 'replace').decode('latin-1')
            estado = reclamo.estado.encode('latin-1', 'replace').decode('latin-1')
            fecha = reclamo.timestamp.strftime('%Y-%m-%d') if reclamo.timestamp else 'N/A'
            
            # Guardamos la posición Y actual
            y_inicial_fila = pdf.get_y()
            
            # Celda ID (altura fija)
            pdf.cell(ancho_id, alto_celda, str(reclamo.id_reclamo), border='LR')
            
            # Celda Estado (altura fija)
            x_actual = pdf.get_x()
            pdf.cell(ancho_estado, alto_celda, estado, border='R')
            
            # Celda Contenido (altura variable)
            x_actual += ancho_estado
            pdf.multi_cell(ancho_contenido, alto_celda, contenido, border='R')
            
            # Guardamos la altura máxima que alcanzó la celda de contenido
            y_final_fila = pdf.get_y()
            altura_fila_real = y_final_fila - y_inicial_fila
            
            # Volvemos al inicio de la fila (en Y) y dibujamos las celdas restantes
            # con la altura calculada
            pdf.set_xy(x_actual + ancho_contenido, y_inicial_fila)
            
            pdf.cell(ancho_creador, altura_fila_real, creador, border='R')
            pdf.cell(ancho_fecha, altura_fila_real, fecha, border='R')
            pdf.cell(ancho_adh, altura_fila_real, str(reclamo.numero_adherentes), border='R', ln=True)
            
            # Dibujar la línea inferior de la fila
            pdf.cell(ancho_celda, 0, '', border='T', ln=True)
            
        # Guardar el archivo PDF
        try:
            pdf.output(ruta_completa)
            return ruta_completa # Devolvemos la ruta al archivo creado
        except Exception as e:
            return f"Error al crear PDF: {e}"