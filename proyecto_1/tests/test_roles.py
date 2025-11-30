import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.roles import JefeDepartamento, SecretarioTecnico


class TestRoles(unittest.TestCase):

    #Prueba para JefeDepartamento
    
    def test_jefe_departamento_inicializacion_completa(self):
        """Prueba que JefeDepartamento se inicialice correctamente y asigne el rol y departamento.
        Notar que NO ES PRUEBA DE PROPERTY, probamos si la clase hija inicializa de manera correcta"""
        depto = "Soporte Informático"
        jefe = JefeDepartamento(
            "Juan", "Perez", "jp@f.com", "jperez", "123", depto, id_bd=1
        )
        # Verificación del atributo propio
        self.assertEqual(jefe.departamento_asignado, depto)
        

    #Pruebas para SecretarioTecnico

    def test_secretario_tecnico_inicializacion_y_rol_fijo(self):
        """Prueba que SecretarioTecnico se inicialice y asigne su rol fijo ("PAyS").
        De nuevo, no es prueba de property, es prueba de inicialización"""
        secretario = SecretarioTecnico(
            nombre="Ana", apellido="Gomez", email="ag@f.com", nombre_usuario="agomez", contrasena="456"
        )
        self.assertEqual(secretario.claustro, "PAyS")

    def test_secretario_tecnico_con_id_bd(self):
        """Prueba que el id_bd opcional se maneje correctamente y se asigne."""
        secretario = SecretarioTecnico("A", "B", "c@d.com", "user", "pass", id_bd=50)
        # Verificamos que se haya pasado el valor a la propiedad de la clase base.
        self.assertEqual(secretario.id_bd, 50)
        
    def test_secretario_tecnico_sin_id_bd(self):
        """Prueba que el id_bd opcional sea None por defecto."""
        secretario = SecretarioTecnico("A", "B", "c@d.com", "user", "pass")
        # Verificamos que el valor por defecto sea None.
        self.assertIsNone(secretario.id_bd)