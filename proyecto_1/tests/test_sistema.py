import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import unittest
from unittest.mock import MagicMock, patch
from modules.sistema import SubsistemaGestionReclamos
from modules.usuario import Usuario
from modules.reclamo import Reclamo
from modules.roles import JefeDepartamento, SecretarioTecnico
from modules.excepciones import UsuarioExistenteError, UsuarioInexistenteError, ReclamoInexistenteError
from io import StringIO
from modules.config_db import engine

#MOCKs de Dependencias

# Mock de la clase abstracta de repositorios
class MockRepo:
    def __init__(self):
        self.guardar = MagicMock()
        self.obtener_por_filtro = MagicMock()
        self.obtener_por_id = MagicMock()
        self.actualizar = MagicMock()
        self.obtener_todos_por_filtro = MagicMock()
        self.asociar_reclamo_a_usuario = MagicMock()
        #Mock de un atributo interno usado por listar_reclamos_usuario
        self.session_mock = MagicMock()
        self.session_mock.query.return_value.filter_by.return_value.first.return_value = MagicMock(id=1)
        self._RepositorioUsuariosSQLAlchemy__session = self.session_mock


#Entidades de Prueba
usuario_final = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass", id_bd=1)
jefe_soporte = JefeDepartamento("J", "S", "j@s.com", "jefe", "pass", "soporte informático", id_bd=2)
jefe_maestranza = JefeDepartamento("J", "M", "j@m.com", "jefe2", "pass", "maestranza", id_bd=3)
secretario = SecretarioTecnico("S", "T", "s@t.com", "sec", "pass", id_bd=4)

reclamo_soporte = Reclamo(usuario_final, "Red lenta", "soporte informático")
reclamo_soporte.id_reclamo = 1
reclamo_soporte._Reclamo__estado = "pendiente"

reclamo_maestranza = Reclamo(usuario_final, "Baño sucio", "maestranza")
reclamo_maestranza.id_reclamo = 2

@patch('builtins.print')
class TestSubsistemaGestionReclamos(unittest.TestCase):
    def setUp(self):
        self.repo_usuarios = MockRepo()
        self.repo_reclamos = MockRepo()

        self.patcher = patch('modules.sistema.ClasificadorReclamo') #patch necesario para testear, resuelve errores de importación de pickle
        MockClasificadorReclamo = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.mock_clasificador = MockClasificadorReclamo.return_value
        self.mock_clasificador.clasificar.return_value = "soporte informático"
        
        self.sistema = SubsistemaGestionReclamos(self.repo_usuarios, self.repo_reclamos)
        
    #Pruebas para la Gestión de Usuarios 

    def test_registrar_usuario_exitoso(self,mock_print):
        """Prueba que el registro llama a repo.guardar y no lanza excepción."""
        self.sistema.registrar_usuario("N", "A", "n@a.com", "nuevo", "docente", "pass")
        self.repo_usuarios.guardar.assert_called_once() #Se prueba que sea llamado exactamente una vez
        
    def test_registrar_usuario_existente(self, mock_print):
        """Prueba que se relance UsuarioExistenteError."""
        self.repo_usuarios.guardar.side_effect = ValueError("El email o nombre de usuario ya está registrado.") #Se asegura que el próximo llamado lanza ValueError
        with self.assertRaises(UsuarioExistenteError): #Prueba que el error lanzado sea el correcto
            self.sistema.registrar_usuario("N", "A", "n@a.com", "existente", "docente", "pass") #Este llamado lanza el ValueError

    def test_buscar_usuario_inexistente(self, mock_print): 
        """Prueba que se lance UsuarioInexistenteError."""
        self.repo_usuarios.obtener_por_filtro.return_value = None #El siguiente llamado lanzará None
        with self.assertRaises(UsuarioInexistenteError): #se verifica que se lanza el erro correcto
            self.sistema.buscar_usuario("no_existe") #Este llamado lanza None

    #Pruebas para la Gestión de Reclamos: Creación/Búsqueda

    def test_crear_reclamo_usuario_inexistente(self, mock_print): 
        """Prueba que falle si el usuario no tiene ID de BD (o sea, un usuario no válido)."""
        self.repo_usuarios.obtener_por_filtro.return_value = None #El próximo llamado lanza None
        with self.assertRaises(UsuarioInexistenteError): #Se comprueba el error
            self.sistema.crear_reclamo(usuario_final, "Test") #Este llamado es el que lanza None
 
    def test_crear_reclamo_exitoso(self, mock_print): 
        """Prueba el flujo completo de clasificación y guardado"""
        self.repo_usuarios.obtener_por_filtro.return_value = usuario_final 
        self.mock_clasificador.clasificar.return_value = "maestranza" #Se configura el siguiente resultado de la función
        
        reclamo = self.sistema.crear_reclamo(usuario_final, "Hay basura") #Se crea reclamo con correspondiente usuario y mensaje
        
        self.assertEqual(reclamo.departamento, "maestranza") #Se comprueba que el departamento del reclamo es correcto
        self.repo_reclamos.guardar.assert_called_once() #Prueba que se ha llamado una sola vez

    def test_buscar_reclamo_por_id_inexistente(self, mock_print):
        """Prueba que se lance ReclamoInexistenteError."""
        self.repo_reclamos.obtener_por_id.return_value = None
        with self.assertRaises(ReclamoInexistenteError):
            self.sistema.buscar_reclamo_por_id(99)

    #Prueba para la Gestión de Reclamos: Adherentes ---
    
    def test_adherir_a_reclamo_ya_adherido(self, mock_print):
        """Prueba que no se intente adherir si ya lo está."""
        # Mock para simular que el usuario ya está adherido
        reclamo_mock = MagicMock(Reclamo, adherentes=[usuario_final], id_reclamo=1) #Se crea un mock de un reclamo que ya tiene al adherente 'usuario_final'
        self.repo_reclamos.obtener_por_id.return_value = reclamo_mock #Simulamos pasar el reclamo que creamos en la proxima llamada (id =1)
        self.repo_usuarios.obtener_por_filtro.return_value = usuario_final #Simulamos que 'usuario_final' realmente existe
        
        self.sistema.adherir_a_reclamo(usuario_final, 1) #Se intenta adherir nuevamente
        
        self.repo_usuarios.asociar_reclamo_a_usuario.assert_not_called() #Se prueba que no ha llamado el método
        
    def test_adherir_a_reclamo_exitoso(self, mock_print):
        """Prueba el flujo de adhesión persistente."""
        reclamo_mock = MagicMock(Reclamo, adherentes=[], id_reclamo=1, agregar_adherente=MagicMock()) #Reclamo tipo mock sin adherentes
        self.repo_reclamos.obtener_por_id.return_value = reclamo_mock #Simulamos pasar el reclamo que creamos en la proxima llamada (id =1)
        self.repo_usuarios.obtener_por_filtro.return_value = usuario_final #Simulamos que 'usuario_final' realmente existe
        
        self.sistema.adherir_a_reclamo(usuario_final, 1) #Se intenta adherir
        
        self.repo_usuarios.asociar_reclamo_a_usuario.assert_called_once() #´Prueba que el método se llamó una vez
        reclamo_mock.agregar_adherente.assert_called_once_with(usuario_final) #Verificar que no solo se agregó a la BD, también se modificó el objeto reclamo
        
    def test_adherir_a_reclamo_usuario_sin_id(self, mock_print):
        """Prueba que si un usuario sin ID se adhiere, se busca en el repo
        usando sus datos y se usa el ID encontrado."""
        
        # Definimos los datos del MISMO usuario
        #    ("A", "B", "a@b.com", "user")
        
        #versión "fantasma" sin ID
        usuario_fantasma = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass") 
        
        #Versión "real" con ID que (simulamos) está en la BD
        usuario_real_con_id = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass", id_bd=1)
        
        reclamo_mock = MagicMock(Reclamo, adherentes=[], id_reclamo=1, agregar_adherente=MagicMock()) #Reclamo tipo mock sin adherentes
        self.repo_reclamos.obtener_por_id.return_value = reclamo_mock #Se devuelve el reclamo vacío cuando se pida
        
        self.repo_usuarios.obtener_por_filtro.return_value = usuario_real_con_id #La próxima llamada devuelve el usuario real
        
        self.sistema.adherir_a_reclamo(usuario_fantasma, 1) #Intentamos que se adhiera el usuario fantasma
        
        self.repo_usuarios.obtener_por_filtro.assert_called_once_with(
            nombre_usuario=usuario_fantasma.nombre_usuario # <--- "user"
        ) #Se prueba que se buscó por el user del usuario fantasma  (que es igual al del usuario real)
        
        #Verificamos que se guardó la adhesión usando el ID del usuario REAL
        self.repo_usuarios.asociar_reclamo_a_usuario.assert_called_once_with(
            id_usuario=usuario_real_con_id.id_bd, # <--- 1
            id_reclamo=reclamo_mock.id_reclamo
        )

    def test_adherir_a_reclamo_usuario_no_registrado(self, mock_print):
        """Prueba que falle si el usuario no está registrado."""
        usuario_sin_id = Usuario("B", "B", "b@b.com", "user_b", "estudiante", "pass")
        self.repo_usuarios.obtener_por_filtro.return_value = None #Se devolverá el valor None para demostrar que el usuario no existe
        
        
        with self.assertRaisesRegex(UsuarioInexistenteError, "El usuario no está registrado o no tiene ID de BD."): #Se prueba que se levanta el error correspondiente
             self.sistema.adherir_a_reclamo(usuario_sin_id, 1)


    #Pruebas para la Gestión de Reclamos: Cambio de Estado

    @patch.object(SubsistemaGestionReclamos, 'buscar_reclamo_por_id', return_value=reclamo_soporte)
    def test_cambiar_estado_permiso_denegado(self, mock_buscar, mock_print):
        """Prueba el error de permiso si el departamento no coincide."""
        with self.assertRaisesRegex(Exception, "Permiso denegado"): #Se prueba que se levanta el error correspondiente
            self.sistema.cambiar_estado_reclamo(jefe_maestranza, 1, "resuelto") #Jefe maestranza no puede cambiar el estado de reclamos de soporte técnico

    @patch.object(SubsistemaGestionReclamos, 'buscar_reclamo_por_id', return_value=reclamo_soporte)
    def test_cambiar_estado_dias_invalidos(self, mock_buscar, mock_print):
        """Prueba la excepción al pasar días inválidos."""
        with self.assertRaisesRegex(ValueError, "Se debe asignar un tiempo"): #Se debe levantar el error correspondiente
            self.sistema.cambiar_estado_reclamo(jefe_soporte, 1, "en proceso", 0) #Notar que el tiempo debe ser mayor a 0 y menor a 16 (linea 72, reclamo.py)

    @patch.object(SubsistemaGestionReclamos, 'buscar_reclamo_por_id', return_value=reclamo_soporte)
    def test_cambiar_estado_exitoso(self, mock_buscar, mock_print):
        """Prueba el flujo de cambio de estado y actualización."""
        self.sistema.cambiar_estado_reclamo(jefe_soporte, 1, "en proceso", 5) #Cambio válido
        self.repo_reclamos.actualizar.assert_called_once_with(reclamo_soporte) #Se prueba que se ha llamado al método una vez 

    #Prueba para la Gestión de Reclamos: Listados
    
    def test_listar_reclamos_usuario_inexistente(self, mock_print):
        """Prueba que listar falle si el usuario no existe."""
        self.repo_usuarios.obtener_por_filtro.return_value = None #El próximo llamado devuelve none
        with self.assertRaises(UsuarioInexistenteError): #Se debe levantar el error correspondiente
            self.sistema.listar_reclamos_usuario(usuario_final) #Este llamado es el que devuelve el error

    def test_listar_reclamos_usuario_exitoso(self, mock_print):
        """Prueba que el listado llame a los mocks correctos."""
        self.repo_usuarios.obtener_por_filtro.return_value = usuario_final
        #Mocks para simular que el modelo tiene ID 1
        mock_modelo_usuario = self.repo_usuarios._RepositorioUsuariosSQLAlchemy__session.query.return_value.filter_by.return_value.first.return_value
        mock_modelo_usuario.id = 1
        
        self.sistema.listar_reclamos_usuario(usuario_final)
        
        #Debe buscar por el ID del usuario
        self.repo_reclamos.obtener_todos_por_filtro.assert_called_once_with(id_usuario_creador=1) #Se preuba que se ha llamado una vez al método con determinado id


    def test_buscar_reclamos_pendientes_todos(self, mock_print): 
        """Prueba el filtro por estado 'pendiente'."""
        self.repo_reclamos.obtener_todos_por_filtro.return_value = [reclamo_soporte]
        
        resultado = self.sistema.buscar_reclamos_pendientes_todos()
        
        self.assertEqual(len(resultado), 1) #Se preuba que hay exactamente un resultado
        
        self.repo_reclamos.obtener_todos_por_filtro.assert_called_once_with(estado="pendiente") #Se prueba que se ha llamado una sola vez al método con el parámetro correcto


    def test_buscar_reclamos_pendientes_por_departamento(self, mock_print):
        """Prueba el filtro por estado y departamento."""

        self.repo_reclamos.obtener_todos_por_filtro.return_value = [reclamo_soporte]
        
        resultado = self.sistema.buscar_reclamos_pendientes_por_departamento("soporte informático")
        
        self.assertEqual(len(resultado), 1)
        
        self.repo_reclamos.obtener_todos_por_filtro.assert_called_once_with(estado="pendiente", departamento="soporte informático")

    def test_buscar_reclamos_similares_clasificacion_indefinida(self, mock_print):
        """Cubre el caso donde la clasificación falla."""
        self.mock_clasificador.clasificar.return_value = "indefinido"
        resultado = self.sistema.buscar_reclamos_similares("reclamo indefinido")
        self.assertEqual(resultado, [])
        self.mock_clasificador.clasificar.assert_called_once()

    #Prueba para la Gestión de Reclamos: Derivar ---

    def test_derivar_reclamo_permiso_denegado(self, mock_print):
        """Prueba el error si el usuario no es Secretario Tecnico."""
        with self.assertRaisesRegex(Exception, "Solo el Secretario Técnico puede derivar"): 
            self.sistema.derivar_reclamo(jefe_soporte, 1, "maestranza")

    @patch.object(SubsistemaGestionReclamos, 'buscar_reclamo_por_id', return_value=reclamo_soporte)
    def test_derivar_reclamo_departamento_invalido(self, mock_buscar, mock_print):
        """Prueba el error si el departamento de destino no es válido."""
        with self.assertRaisesRegex(ValueError, "no es un destino válido"): #Se verifica que devuelva ValueError cuando el departamento no es correcto
            self.sistema.derivar_reclamo(secretario, 1, "otro departamento") 

    @patch.object(SubsistemaGestionReclamos, 'buscar_reclamo_por_id', return_value=reclamo_soporte)
    def test_derivar_reclamo_exitoso(self, mock_buscar, mock_print): 
        """Prueba la derivación exitosa y la actualización."""
        self.sistema.derivar_reclamo(secretario, 1, "maestranza") #Se deriva el reclamo
        
        self.assertEqual(reclamo_soporte.departamento, "maestranza")  #Verificamos que el nuevo departamento es el correcto
        self.repo_reclamos.actualizar.assert_called_once_with(reclamo_soporte) #Se verifica que se ha llamado al método solo una vez
    
    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

if __name__ == '__main__':
    unittest.main()