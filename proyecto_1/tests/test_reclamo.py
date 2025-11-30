import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
import datetime
from modules.reclamo import Reclamo

#Mock simple para Usuario
class MockUsuario:
    def __init__(self, id_bd=1, nombre="Test"):
        self.id_bd = id_bd
        self.nombre = nombre

class TestReclamo(unittest.TestCase):

    def setUp(self):
        self.creador = MockUsuario(id_bd=1, nombre="Creador")
        self.reclamo = Reclamo(self.creador, "El sistema está caído.", "soporte informático")

    def test_reclamo_inicializacion_por_defecto(self):
        """Verifica los valores iniciales del reclamo."""
        self.assertEqual(self.reclamo.estado, "pendiente") #Eñ estado inicial siempre debe ser "pendiente"
        self.assertEqual(self.reclamo.departamento, "soporte informático") #Se verifica que coincide el departamento
        self.assertEqual(self.reclamo.numero_adherentes, 0) #Un reclamo debería inicializar sin adherentes
        self.assertIsNone(self.reclamo.id_reclamo)

    def test_reclamo_cambio_estado_simple(self):
        """Prueba el cambio de estado a 'resuelto' o 'inválido' (sin días)."""
        self.reclamo.cambiar_estado("resuelto")
        self.assertEqual(self.reclamo.estado, "resuelto") #Se prueba que el estado ha cambiado de manera correcta
        self.assertIsNone(self.reclamo.tiempo_resolucion_asignado) #Como no se asignaron dias, debería ser None

    def test_reclamo_cambio_estado_en_proceso_valido(self):
        """Prueba el cambio de estado a 'en proceso' con días válidos."""
        self.reclamo.cambiar_estado("en proceso", 7)
        self.assertEqual(self.reclamo.estado, "en proceso") #Se prueba que el estado ha cambiado de manera correcta
        self.assertEqual(self.reclamo.tiempo_resolucion_asignado, 7) #Se peuba que se ha asignado una opción válida de días

    def test_reclamo_cambio_estado_en_proceso_dias_invalidos(self):
        """Prueba ValueError si 'en proceso' no tiene cantidad de días válida."""
        with self.assertRaises(ValueError): #Se lanza si es un valor no válido
            self.reclamo.cambiar_estado("en proceso", 0) #Es menor a 1
        with self.assertRaises(ValueError):
            self.reclamo.cambiar_estado("en proceso", 16) #Es mayor a 15
        with self.assertRaises(ValueError):
            self.reclamo.cambiar_estado("en proceso") #Es None

    def test_reclamo_cambio_estado_invalido(self):
        """Prueba que no se pueda cambiar a un estado no permitido."""
        with self.assertRaises(ValueError): #Se lanza al no estar dentro del if (Line 79)
            self.reclamo.cambiar_estado("otro estado") #No es un estado permitido
    

    def test_reclamo_adherir_usuario_unico(self):
        """Prueba agregar un adherente que no está en la lista."""
        adherente1 = MockUsuario(id_bd=2)
        self.reclamo.agregar_adherente(adherente1)
        self.assertEqual(self.reclamo.numero_adherentes, 1) #prueba que se modificó correctamente el número de adherentes
        self.assertIn(adherente1, self.reclamo.adherentes) #Prueba si se ha añadido al adherente a la lista de adherentes del reclamo

    def test_reclamo_adherir_usuario_duplicado(self):
        """Prueba que no se agreguen adherentes duplicados."""
        adherente1 = MockUsuario(id_bd=2)
        self.reclamo.agregar_adherente(adherente1)
        self.reclamo.agregar_adherente(adherente1) #Intento duplicado
        self.assertEqual(self.reclamo.numero_adherentes, 1) #La cantidad de adherentes debe ser 1, pues un mismo usuario no puede adherirse dos veces a un mismo reclamo.