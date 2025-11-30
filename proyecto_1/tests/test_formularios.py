import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 
warnings.filterwarnings("ignore", category=ResourceWarning) 
warnings.filterwarnings("ignore", category=UserWarning)
import unittest
from modules.formularios import FormRegistro, FormEditarEstado, FormCrearReclamo
from modules.formularios import EqualTo, NumberRange
from unittest.mock import MagicMock, patch

# --- CAMBIO 1: Importar MultiDict ---
from werkzeug.datastructures import MultiDict

# (No importamos 'app' aquí, lo hacemos en el setUp)

# --- CAMBIO 2: Corregir simular_form ---
def simular_form(form_class, data):
    """
    Simula la creación de un formulario pasándole los datos
    como 'formdata', que es lo que 'validate()' espera.
    """
    # Usamos MultiDict para simular 'formdata' (datos de un POST)
    mock_form = form_class(formdata=MultiDict(data))
    mock_form.validate()
    return mock_form

class TestFormularios(unittest.TestCase):

    def setUp(self):
        """Se ejecuta ANTES de cada test."""
        
        # 1. Parcheamos el Clasificador ANTES de importar 'server'
        self.patcher = patch('modules.sistema.ClasificadorReclamo')
        MockClasificador = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        
        # 2. Ahora es seguro importar 'server' y 'app'
        from server import app
        self.app = app

        # 3. Creamos el contexto de la app
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 4. Configuramos la app para testing (desactiva CSRF)
        self.app.config.update({
            "WTF_CSRF_ENABLED": False,
            "TESTING": True
        })

    def tearDown(self):
        """Se ejecuta DESPUÉS de cada test."""
        self.app_context.pop()

    # --- Tests ---

    def test_form_registro_contrasenas_no_coinciden(self):
        """Prueba la validación EqualTo en FormRegistro (Line 23)."""
        data = {
            'nombre': 'A', 'apellido': 'B', 'email': 'a@b.com', 'nombre_usuario': 'user', 
            'claustro': 'estudiante', 'password': 'pass1', 'confirmacion': 'pass2', 
            'submit': True
        }
        form = simular_form(FormRegistro, data)
        self.assertFalse(form.validate())
        # (Este mensaje SÍ está en español porque seguro lo pusiste en el 'message' del validador)
        self.assertIn("Las contraseñas deben coincidir", form.confirmacion.errors[0])
        
    def test_form_registro_email_invalido(self):
        """Prueba la validación de Email (Line 15)."""
        data = {
            'nombre': 'A', 'apellido': 'B', 'email': 'emailinvalido', 'nombre_usuario': 'user', 
            'claustro': 'estudiante', 'password': 'pass1', 'confirmacion': 'pass1', 
            'submit': True
        }
        form = simular_form(FormRegistro, data)
        self.assertFalse(form.validate())
        
        # --- CAMBIO 3: Mensaje de error en Inglés ---
        self.assertIn("Invalid email address.", form.email.errors[0])
        
    # --- FormCrearReclamo ---
    def test_form_crear_reclamo_longitud_invalida(self):
        """Prueba la validación de longitud del contenido (Line 38)."""
        data = {'contenido': 'corto', 'submit': True}
        form = simular_form(FormCrearReclamo, data)
        self.assertFalse(form.validate())
        
        # --- CAMBIO 4: Mensaje de error en Inglés ---
        self.assertIn("Field must be between 10 and 1000 characters long.", form.contenido.errors[0])
        
    def test_form_crear_reclamo_longitud_valida(self):
        """Prueba la validación de longitud del contenido (Line 38)."""
        data = {'contenido': 'Este es un contenido de prueba más largo que diez.', 'submit': True}
        form = simular_form(FormCrearReclamo, data)
        self.assertTrue(form.validate()) 
        
    # --- FormEditarEstado ---
    def test_form_editar_estado_tiempo_resolucion_invalido(self):
        """Prueba NumberRange para tiempo_resolucion (Line 66)."""
        data = {'estado': 'en proceso', 'tiempo_resolucion': 0, 'submit': True}
        form = simular_form(FormEditarEstado, data)
        
        # (Gracias al CAMBIO 2, esto ahora sí dará False)
        self.assertFalse(form.validate())
        
        # --- CAMBIO 5: Mensaje de error en Inglés ---
        # (El mensaje default de NumberRange)
        self.assertIn("Debe estar entre 1 y 15 días", form.tiempo_resolucion.errors[0])

    def test_form_editar_estado_tiempo_resolucion_opcional(self):
        """Prueba que sea opcional si no es 'en proceso' (Line 64)."""
        data = {'estado': 'resuelto', 'tiempo_resolucion': '', 'submit': True}
        form = simular_form(FormEditarEstado, data)
        self.assertTrue(form.validate())

if __name__ == '__main__':
    unittest.main()