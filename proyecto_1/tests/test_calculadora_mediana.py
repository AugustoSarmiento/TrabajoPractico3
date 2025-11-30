import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.calculadora_mediana import MonticuloMediana

class TestMonticuloMediana(unittest.TestCase):

    def test_mediana_estado_inicial_none(self):
        """La mediana debe ser None antes de agregar cualquier número."""
        calc = MonticuloMediana()
        self.assertIsNone(calc.obtener_mediana()) #Se prueba si realmente es None
        
    def test_mediana_con_un_solo_elemento_impar_max_heap(self):
        """Cubre mediana impar donde tam_inf > tam_sup."""
        calc = MonticuloMediana()
        calc.agregar_numero(100)
        self.assertEqual(calc.obtener_mediana(), 100.0) #Se prueba que la mediana es correcta
        
    def test_mediana_con_cantidad_par_promedio(self):
        """Cubre el caso de la mediana par."""
        calc = MonticuloMediana()
        # 1, 7 -> Mediana: (1+7)/2 = 4.0
        calc.agregar_numero(1)
        calc.agregar_numero(7)
        self.assertEqual(calc.obtener_mediana(), 4.0) #Se prueba si la mediana es correcta
        
    def test_mediana_con_cantidad_impar_min_heap_raiz(self):
        """Fuerza el caso de mediana impar donde tam_sup > tam_inf (Line 42)."""
        calc = MonticuloMediana()
        calc.agregar_numero(10)
        calc.agregar_numero(20)
        calc.agregar_numero(30)
        calc.agregar_numero(40)
        calc.agregar_numero(50) 
        calc.agregar_numero(60)
        calc.agregar_numero(70)
        #Los montículos finales son: max:[40, 30, 20, 10], min:[70, 60, 50]. M=40.0
        self.assertEqual(calc.obtener_mediana(), 40.0) #Se prueba que la mediana es correcta.
        
    def test_balanceo_mueve_de_max_a_min(self):
        """Cubre la rama 'if tam_inf > tam_sup:' del balanceo."""
        calc = MonticuloMediana()
        calc.agregar_numero(10) 
        calc.agregar_numero(20)
        calc.agregar_numero(5)  
        #Montículos finales: max:[5], min:[20, 10]. M=10.0
        self.assertEqual(calc.obtener_mediana(), 10.0) #Se prueba que la mediana es correcta

    def test_balanceo_mueve_de_min_a_max(self):
        """Cubre la rama 'else' del balanceo."""
        calc = MonticuloMediana()
        calc.agregar_numero(100) 
        calc.agregar_numero(10)  
        calc.agregar_numero(200) 
        calc.agregar_numero(300) 
        calc.agregar_numero(400)
        # Montículos finales: max:[200, 100, 10], min:[400, 300]. M=200.0
        self.assertEqual(calc.obtener_mediana(), 200.0) #Se prueba que la mediana es correcta.

    def test_agregar_numero_al_max_heap_directamente(self):
        """Cubre la rama 'if' de agregar_numero (el número va al max-heap)."""
        calc = MonticuloMediana()
        calc.agregar_numero(50) 
        calc.agregar_numero(10) # 10 < 50, va directo al max-heap
        self.assertEqual(calc.obtener_mediana(), 30.0) #Se prueba que la mediana es correcta (debe ser 30 pues es la media entre las raíces de los montículos)

    def test_agregar_numero_al_min_heap_directamente(self):
        """Cubre la rama 'else' de agregar_numero (el número va al min-heap) (Line 51)."""
        calc = MonticuloMediana()
        calc.agregar_numero(10) 
        calc.agregar_numero(20) 
        # 30 > 10 (raíz del max-heap), va directo al min-heap (else)
        calc.agregar_numero(30)
        self.assertEqual(calc.obtener_mediana(), 20.0) #Se prueba que la mediana es correcta (raíz del montículo de máximos)
        