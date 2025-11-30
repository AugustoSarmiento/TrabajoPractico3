import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.monticulo import MonticuloMinimos, MonticuloMaximos

class TestMonticulo(unittest.TestCase):
    
    #Test para probar MonticuloMinimos    
    def test_minimos_infiltracion_arriba_camino_largo(self):
        """Prueba que un elemento pequeño insertado al final infiltrarse hasta la raíz."""
        min_heap = MonticuloMinimos()
        for val in [50, 40, 30, 20, 10]:
            min_heap.insertar(val)
        min_heap.insertar(1) #Debe subir 5 niveles
        self.assertEqual(min_heap.obtener_raiz(), 1) #Se prueba que la raíz sea 1
        self.assertEqual(min_heap.tamano(), 6) #Se prueba que el montículo tenga 6 elementos

    def test_minimos_infiltracion_arriba_se_detiene(self):
        """Prueba que __infiltrar_arriba se detenga cuando el padre es menor (cumpliendo con la
        característica de Monticulo de Minimos)."""
        min_heap = MonticuloMinimos()
        min_heap.insertar(10)
        min_heap.insertar(50)
        min_heap.insertar(20)
        min_heap.insertar(60)
        min_heap.insertar(70) #En ningún caso la raíz debería cambiar
        self.assertEqual(min_heap.obtener_raiz(), 10) #Se prueba que la raíz es 10

    def test_minimos_eliminacion_y_reorganizacion(self):
        """Prueba la eliminación y el reajuste del monticulo con varios niveles."""
        min_heap = MonticuloMinimos()
        for val in [10, 5, 20, 15, 2, 8]:
            min_heap.insertar(val) #Notar que la raíz debe 2
        
        self.assertEqual(min_heap.eliminar_raiz(), 2) #La nueva raíz debe ser 5. Se prueba que realmente se elimina la raíz
        self.assertEqual(min_heap.obtener_raiz(), 5) #Se prueba que la nueva raíz sea 5
        self.assertEqual(min_heap.tamano(), 5) #Se prueba que el tamaño del montículo sea 5

    def test_minimos_infiltrar_abajo_prioridad_izquierda(self):
        """Prueba que la lógica de __obtener_hijo_prioritario elija al hijo correcto."""
        min_heap = MonticuloMinimos()
        for val in [10, 5, 15, 2, 8]:
            min_heap.insertar(val) #La raíz ez 2. Sus hijos deben ser 5 y 10
        
        self.assertEqual(min_heap.eliminar_raiz(), 2)
        #La nueva raíz es 15 de manera temporal. Sus hijos son 5 y 10. El 15 debe bajar, el 5 debe subir hasta ser la raíz.
        self.assertEqual(min_heap.obtener_raiz(), 5)  #Se prueba que la raíz sea 5

    def test_minimos_con_valores_duplicados(self):
        """Prueba la correcta gestión de valores duplicados."""
        min_heap = MonticuloMinimos()
        min_heap.insertar(5)
        min_heap.insertar(5)
        min_heap.insertar(1)
        
        self.assertEqual(min_heap.eliminar_raiz(), 1)
        self.assertEqual(min_heap.eliminar_raiz(), 5)
        self.assertEqual(min_heap.eliminar_raiz(), 5) #44 - 46: Se prueba que se ha eliminado el elemento correcto.
        self.assertTrue(min_heap.esta_vacio()) #Se prueba si realmente el montículo quedó vacío
        
    def test_minimos_eliminar_vacio_y_obtener_raiz_vacia(self):
        """Prueba las operaciones en un montículo vacío."""
        min_heap = MonticuloMinimos()
        self.assertTrue(min_heap.esta_vacio()) #Prueba si realmente está vacío
        self.assertIsNone(min_heap.obtener_raiz()) #Si está vacío, la raíz debe ser None
        self.assertIsNone(min_heap.eliminar_raiz()) #Al eliminar la raíz, el valor devuelto debe ser None

    #Pruebas para el MonticuloMaximos
    
    def test_maximos_infiltracion_arriba_camino_largo(self):
        """Prueba que un elemento grande insertado al final se infiltre hasta la raíz."""
        max_heap = MonticuloMaximos()
        for val in [1, 2, 3, 4, 5]:
            max_heap.insertar(val)
        max_heap.insertar(100) #Se debe infiltrar hasta la raíz
        self.assertEqual(max_heap.obtener_raiz(), 100) #Se prueba que la raíz se actualizó correctamente
        self.assertEqual(max_heap.tamano(), 6) #Se prueba que el tamaño se actualizó correctamente

    def test_maximos_eliminacion_y_reorganizacion(self):
        """Prueba la eliminación y el reajuste del Montículo."""
        max_heap = MonticuloMaximos()
        for val in [10, 50, 5, 15, 20]:
            max_heap.insertar(val) #La raíz debe ser 50
        
        self.assertEqual(max_heap.eliminar_raiz(), 50) #Se prueba que eliminar la raíz devuelve el valor correcto
        #La nueva raíz debe ser 20
        self.assertEqual(max_heap.obtener_raiz(), 20) #Se prueba que la raíz se actualizó de manera correcta
        
    def test_maximos_infiltrar_abajo_prioridad_derecha(self):
        """Prueba que la lógica de __obtener_hijo_prioritario elija el hijo con mayor valor."""
        max_heap = MonticuloMaximos()
        for val in [5, 10, 20, 15, 8]:
            max_heap.insertar(val) #La raíz es 20. Sus hijos son 15 y 10
        
        self.assertEqual(max_heap.eliminar_raiz(), 20) #Se prueba que el método devuelve el valor correspondiente
        #La nueva raíz es 8 de manera temporal. Sus hijos son 15 y 10. El 8 debe bajar, el 15 debe subir.
        self.assertEqual(max_heap.obtener_raiz(), 15) #Se prueba que la raíz se actualizó de manera correcta

    def test_maximos_con_valores_duplicados(self):
        """Prueba la correcta gestión de valores duplicados en el MontículoMaximos."""
        max_heap = MonticuloMaximos()
        max_heap.insertar(10)
        max_heap.insertar(10)
        max_heap.insertar(15)
        
        self.assertEqual(max_heap.eliminar_raiz(), 15)
        self.assertEqual(max_heap.eliminar_raiz(), 10)
        self.assertEqual(max_heap.eliminar_raiz(), 10) #93 - 95: se prueba que el valor de la raíz fue actualizado de manera correcta

    def test_minimos_comparador_retorna_false(self):
        """Prueba explícita del comparador en MonticuloMinimos (a < b)."""
        min_heap = MonticuloMinimos()
        # 10 < 5 -> Falso (No es un MontículoMinimos)
        self.assertFalse(min_heap._comparar(10, 5)) #Se prueba que devuelve el booleano correcto
        # 5 < 10 -> Verdadero
        self.assertTrue(min_heap._comparar(5, 10)) #Se prueba que devuelve el booleano correcto

    def test_maximos_comparador_retorna_true(self):
        """Prueba explícita del comparador en MonticuloMaximos (a > b)."""
        max_heap = MonticuloMaximos()
        # 10 > 5 -> Verdadero
        self.assertTrue(max_heap._comparar(10, 5)) #Se prueba que devuelve el booleano correcto
        # 5 > 10 -> False (No es un MontículoMaximos)
        self.assertFalse(max_heap._comparar(5, 10)) #Se prueba que devuelve el booleano correcto