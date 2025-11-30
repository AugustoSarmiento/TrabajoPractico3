import matplotlib.pyplot as plt
import os
import io # Para manejar imágenes en memoria si fuera necesario, pero lo guardaremos en disco

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
            # No hay datos para graficar, se puede generar una imagen de placeholder o simplemente no guardar nada.
            # Por simplicidad, retornamos si el total es 0.
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
        # Guardar como PNG en la ruta especificada
        try:
            plt.savefig(ruta_guardado_completa, bbox_inches='tight', dpi=100)
        except Exception as e:
            print(f"Error al guardar gráfico: {e}")
        finally:
            plt.close(fig1) # Cerrar la figura para liberar memoria
        
        return ruta_guardado_completa