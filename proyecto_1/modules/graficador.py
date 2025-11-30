import matplotlib.pyplot as plt
import os
import io 
from wordcloud import WordCloud # <<--- NUEVA IMPORTACIÓN

class Graficador:
    
    @staticmethod
    def generar_grafico_estados(stats_porcentaje: dict[str, float], ruta_guardado_completa: str):
        """
        Genera un gráfico circular de estados de reclamos y lo guarda.
        stats_porcentaje debe contener 'pendientes', 'en_proceso', 'resueltos' (en porcentaje).
        """
        
        # 1. Preparar datos
        labels = ['Pendientes', 'En Proceso', 'Resueltos']
        # Obtener los porcentajes. Usar 0 si la clave no existe.
        sizes = [
            stats_porcentaje.get('pendientes', 0), 
            stats_porcentaje.get('en_proceso', 0), 
            stats_porcentaje.get('resueltos', 0)
        ]
        
        colors = ['#ffc107', '#17a2b8', '#28a745'] # Colores (Warning/Amarillo, Info/Azul, Success/Verde)
        explode = (0.0, 0.05, 0.05) # Pequeña separación para "En Proceso" y "Resueltos"
        
        # Filtrar elementos con tamaño 0 para no mostrarlos ni en la leyenda ni en el pie
        data = [(labels[i], sizes[i], colors[i], explode[i]) for i in range(len(sizes)) if sizes[i] > 0]
        
        if not data:
            if stats_porcentaje.get('total', 0) == 0:
                return

        labels, sizes, colors, explode = zip(*data) # Desempaquetar los datos filtrados

        # 2. Crear carpetas si no existen
        os.makedirs(os.path.dirname(ruta_guardado_completa), exist_ok=True)

        # 3. Crear el gráfico
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        
        # Crear el gráfico circular (autopct formatea los porcentajes)
        wedges, texts, autotexts = ax1.pie(
            sizes, 
            labels=labels, 
            autopct=lambda p: f'{p:.2f}%' if p >= 1.0 else '', # Mostrar porcentaje solo si es >= 1%
            startangle=90, 
            colors=colors,
            explode=explode,
            textprops={'fontsize': 10}
        )
        
        # Título
        ax1.set_title(f'Distribución de Estados (Total: {stats_porcentaje.get("total", 0)} Reclamos)')
        
        # Asegura que el gráfico sea un círculo (aspecto igual)
        ax1.axis('equal')  

        # 4. Guardar la figura
        try:
            plt.savefig(ruta_guardado_completa, bbox_inches='tight', dpi=100)
            return ruta_guardado_completa # Devolvemos la ruta en caso de éxito
        except Exception as e:
            print(f"Error al guardar gráfico de estados: {e}")
            return None
        finally:
            plt.close(fig1) # Cerrar la figura para liberar memoria
    
    @staticmethod
    def generar_wordcloud(stats_palabras: list[tuple[str, int]], ruta_guardado_completa: str):
        """
        Genera una nube de palabras a partir de las frecuencias y la guarda.
        stats_palabras es una lista de tuplas (palabra, frecuencia).
        """
        if not stats_palabras:
            return None

        # Convertir la lista de tuplas a un diccionario de frecuencias
        frecuencias = dict(stats_palabras) # WordCloud puede generar a partir de frecuencias

        # 1. Crear carpetas si no existen
        os.makedirs(os.path.dirname(ruta_guardado_completa), exist_ok=True)

        # 2. Configurar y generar la nube de palabras
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white', 
            collocations=False, # Evitar agrupar palabras (opcional)
            colormap='viridis',  # Colores más amigables (ej: viridis, cool, tab10)
            max_words=100 
        ).generate_from_frequencies(frecuencias) # Se genera directamente desde el diccionario de frecuencias

        # 3. Visualizar y guardar la imagen (usando Matplotlib)
        plt.figure(figsize=(8, 4), facecolor=None)
        plt.imshow(wordcloud, interpolation='bilinear') # Mostrar la nube generada
        plt.axis("off") # Ocultar ejes
        plt.tight_layout(pad=0)

        try:
            plt.savefig(ruta_guardado_completa, dpi=100)
            return ruta_guardado_completa # Devolvemos la ruta en caso de éxito
        except Exception as e:
            print(f"Error al guardar Word Cloud: {e}")
            return None
        finally:
            plt.close() # Cerrar la figura