import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.estadisticas import GeneradorEstadisticas
from unittest.mock import MagicMock

#MOCK DE DEPENDENCIA (Reclamo)  (Mock: objeto simulado que reemplaza una dependencia real, sirve para aislar y probar de manera unitaria una sección específica de código)
class MockReclamo:
    def __init__(self, estado, contenido, tiempo_resolucion_asignado=None):
        self.estado = estado
        self.contenido = contenido
        self.tiempo_resolucion_asignado = tiempo_resolucion_asignado

class TestGeneradorEstadisticas(unittest.TestCase):

    #Pruebas para calcular_porcentajes_estado

    def test_porcentajes_estados_normal(self):
        """Prueba el cálculo correcto de porcentajes de estado."""
        reclamos = [
            MockReclamo("pendiente", "c1"), MockReclamo("en proceso", "c2"),
            MockReclamo("resuelto", "c3"), MockReclamo("en proceso", "c4"),
        ] #Se crean reclamos mock
        generador = GeneradorEstadisticas(reclamos)
        reporte = generador.calcular_porcentajes_estado() #Se generan los porcentajes 
        
        self.assertEqual(reporte["total"], 4) #Se prueba que el total de reportes es correcto
        self.assertEqual(reporte["pendientes"], 25.0)
        self.assertEqual(reporte["en_proceso"], 50.0)
        self.assertEqual(reporte["resueltos"], 25.0) #26 - 28: Se prueba que el porcentaje para cada estado de reclamo es correcto 
        
    def test_porcentajes_estados_vacio_cubre_linea_27(self):
        """Cubre la rama 'if total_reclamos == 0:'. Declarado en la línea 27 del módulo"""
        generador = GeneradorEstadisticas([])
        reporte = generador.calcular_porcentajes_estado()
        self.assertEqual(reporte["total"], 0) #Se prueba si realmente se cumple que el total de reclamos es 0

    def test_porcentajes_estados_no_contados(self):
        """Prueba que ignore estados no definidos en el reporte."""
        reclamos = [
            MockReclamo("resuelto", "c1"),
            MockReclamo("finalizado", "c2"), #No debe contarse este estado (No corresponde a los pedidos en la actividad) pero suma al total de reclamos
            MockReclamo("pendiente", "c3"),
        ]
        generador = GeneradorEstadisticas(reclamos)
        reporte = generador.calcular_porcentajes_estado()
        self.assertEqual(reporte["total"], 3) #El total de reclamos debe ser 3
        self.assertAlmostEqual(reporte["pendientes"], (1/3) * 100) #El porcentaje de pendientes debe representar un tercio de los reclamos totales

    # Pruebas para calcular_palabras_frecuentes

    def test_palabras_frecuentes_limpieza_completa(self):
        """Prueba remoción de puntuación, mayúsculas, stopwords y palabras cortas."""
        reclamos = [
            MockReclamo("p", "¡La lámpara está rota. Por favor, arreglala!"),
            MockReclamo("p", "La lámpara del aula tiene una avería. ¿El foco está bien?"),
        ] #Se crean reclamos mock
        generador = GeneradorEstadisticas(reclamos) #Se crea el generador de estadísticas
        frecuencias = generador.calcular_palabras_frecuentes(cantidad=3) #Se llama al método
        
        #Palabras esperadas: lampara (2), rota (1), arreglala (1), aula (1), averia (1), foco (1), bien (1)
        # Excluidas: ¡, ., !, ¿, ?, La (SW), está (SW), Por (SW), El (SW), una (SW)
        self.assertEqual(frecuencias[0], ('lámpara', 2)) #Se prueba que la cantidad sea correcta para lámpara
        self.assertIn(('rota', 1), frecuencias) #Se prueba que esta recurrencia exista en la lista frecuencias
        self.assertNotIn(('la', 1), frecuencias) #Se prueba que esta recurrencia NO exista en la lista frecuencias (por ser stopword)
        self.assertNotIn(('por', 1), frecuencias) #Se prueba que esta recurrencia NO exista en la lista frecuencias (por ser stopword)
        self.assertNotIn(('el', 1), frecuencias) #Se prueba que esta recurrencia NO exista en la lista frecuencias (por ser stopword)
        
    def test_palabras_frecuentes_acentos_y_eñes(self):
        """Asegura que los caracteres especiales se conserven."""
        reclamos = [
            MockReclamo("p", "La señalización no funciona. La compañía es ágil y rápida."),
        ] #Se crean reclamos mock
        generador = GeneradorEstadisticas(reclamos)
        frecuencias = generador.calcular_palabras_frecuentes(cantidad=10)
        
        palabras_obtenidas = [p[0] for p in frecuencias] #Por cada palabra en la lista frecuencias
        
        #Se prueba que las palabras guardadas conservan los caracteres del español
        self.assertIn("señalización", palabras_obtenidas) #
        self.assertIn("compañía", palabras_obtenidas)
        self.assertIn("ágil", palabras_obtenidas)
        self.assertIn("rápida", palabras_obtenidas)

        #No debería haber caracteres normalizados (ñ = n, á = a, etc.)
        self.assertNotIn("senalizacion", palabras_obtenidas)
        self.assertNotIn("compania", palabras_obtenidas)
        self.assertNotIn("agil", palabras_obtenidas)
        self.assertNotIn("rapida", palabras_obtenidas)


    def test_palabras_frecuentes_solo_palabras_cortas_o_stopwords(self):
        """Prueba que si solo hay ruido, el resultado es vacío (Line 60)."""
        reclamos = [
            MockReclamo("p", "de la un a y el si no ya"),
        ] #Reclamo de tipo mock con solo stopwords
        generador = GeneradorEstadisticas(reclamos)
        frecuencias = generador.calcular_palabras_frecuentes(cantidad=10)
        self.assertEqual(frecuencias, [])

    #Pruebas para calcular_mediana_tiempos_resolucion

    def test_mediana_tiempos_normal_par(self):
        """Prueba el cálculo de la mediana de tiempos con conteo par."""
        reclamos = [
            MockReclamo("resuelto", "c1", 10), MockReclamo("pendiente", "c2", 5), 
            MockReclamo("en proceso", "c3", 20), MockReclamo("resuelto", "c4", 15),
            MockReclamo("en proceso", "c5", 5),
        ] #Deberían ignorarse los de estado "pendiente" por no ser relevantes en la situación
        # Válidos: 5, 10, 15, 20. Mediana: (10+15)/2 = 12.5
        generador = GeneradorEstadisticas(reclamos)
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 12.5) #Se prueba si la mediana es la esperada
        
    def test_mediana_tiempos_normal_impar(self):
        """Prueba el cálculo de la mediana de tiempos con conteo impar."""
        reclamos = [
            MockReclamo("resuelto", "c1", 10), MockReclamo("en proceso", "c2", 30),
            MockReclamo("resuelto", "c3", 20),
        ]
        # Válidos: 10, 20, 30. Mediana: 20.0
        generador = GeneradorEstadisticas(reclamos)
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 20.0)

    def test_mediana_tiempos_sin_tiempos_asignados_cubre_linea_73(self):
        """Cubre la rama 'if tiempo_asignado is not None' (Line 73)."""
        reclamos = [
            MockReclamo("resuelto", "c1", None), MockReclamo("en proceso", "c2", None),
        ]
        generador = GeneradorEstadisticas(reclamos)
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 0.0) #Prueba que la mediana se comporta como es esperado

    def test_mediana_tiempos_solo_estados_excluidos_cubre_linea_70(self):
        """Cubre la rama 'if reclamo.estado in ["en proceso", "resuelto"]'."""
        reclamos = [
            MockReclamo("pendiente", "c1", 10), MockReclamo("otro", "c2", 20),
        ] #Ninguno de estos dos reclamos debería considerarse para el cálculo de la meidana
        generador = GeneradorEstadisticas(reclamos)
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 0.0) #Se prueba que la mediana es 0

    def test_mediana_tiempos_lista_vacia_cubre_linea_76(self):
        """Cubre la rama 'if reclamos_validos_contados == 0:' (Line 76)."""
        generador = GeneradorEstadisticas([])
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 0.0) #Se prueba que la mediana es 0

    def test_mediana_tiempos_cero(self):
        """Prueba el cálculo de la mediana cuando el tiempo de resolución es 0."""
        reclamos = [
            MockReclamo("resuelto", "c1", 0), MockReclamo("en proceso", "c2", 10),
        ]
        generador = GeneradorEstadisticas(reclamos)
        mediana = generador.calcular_mediana_tiempos_resolucion()
        self.assertEqual(mediana, 5.0)

    def test_stopwords_lista_completa(self):
        """Prueba que todas las stopwords se filtren."""
        test_stopwords = " ".join(["de", "la", "el", "en", "y", "a", "los", "del", "con", "por", "un", "para"])
        reclamos = [MockReclamo("resuelto", f"palabra {test_stopwords} clave")]
        generador = GeneradorEstadisticas(reclamos)
        frecuencias = generador.calcular_palabras_frecuentes(cantidad=1)
        self.assertEqual(frecuencias, [('palabra', 1)])
        self.assertEqual(len(frecuencias), 1)