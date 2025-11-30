import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import unittest
from unittest.mock import MagicMock, patch
from modules.repositorio_concreto import RepositorioUsuariosSQLAlchemy, RepositorioReclamosSQLAlchemy
from modules.usuario import Usuario
from modules.reclamo import Reclamo
from modules.roles import JefeDepartamento, SecretarioTecnico
from modules.modelos_db import ModeloUsuario, ModeloReclamo, Base
from modules.config_db import engine
import datetime
from typing import Optional, List 

#MOCKs de Entidades de Dominio
#Mock de objetos de la BD
def mock_modelo_usuario(id, rol="final", depto=None):
    modelo = ModeloUsuario(id=id, nombre='N', apellido='A', email=f'e{id}@t.com', 
                           nombre_usuario=f'user{id}', claustro='estudiante', contrasena='hash', 
                           rol=rol, departamento_asignado=depto)
    return modelo

def mock_modelo_reclamo(id, id_creador):
    return ModeloReclamo(id=id, contenido='Contenido', departamento='depto', 
                         timestamp=datetime.datetime.now(), estado='pendiente', 
                         id_usuario_creador=id_creador)


class TestRepositorioUsuariosSQLAlchemy(unittest.TestCase):

    def setUp(self):
        self.mock_session = MagicMock()
        with patch.object(Base.metadata, 'create_all'):
            self.repo = RepositorioUsuariosSQLAlchemy(self.mock_session)
        self.mock_query = self.mock_session.query.return_value
        self.mock_filter = self.mock_query.filter_by.return_value

    # --- Pruebas de Mapeo ---

    def test_map_modelo_a_entidad_jefe(self):
        """Prueba que el mapeo cree la entidad JefeDepartamento."""
        modelo = mock_modelo_usuario(1, rol="jefe", depto="Soporte")
        entidad = self.repo._RepositorioUsuariosSQLAlchemy__map_modelo_a_entidad(modelo)
        self.assertIsInstance(entidad, JefeDepartamento)
        self.assertEqual(entidad.departamento_asignado, "Soporte")

    def test_map_modelo_a_entidad_secretario(self):
        """Prueba que el mapeo cree la entidad SecretarioTecnico."""
        modelo = mock_modelo_usuario(1, rol="secretario")
        entidad = self.repo._RepositorioUsuariosSQLAlchemy__map_modelo_a_entidad(modelo)
        self.assertIsInstance(entidad, SecretarioTecnico)

    def test_map_modelo_a_entidad_usuario_final(self):
        """Prueba que el mapeo cree la entidad Usuario base."""
        modelo = mock_modelo_usuario(1, rol="final")
        entidad = self.repo._RepositorioUsuariosSQLAlchemy__map_modelo_a_entidad(modelo)
        self.assertIsInstance(entidad, Usuario)

    # --- Pruebas de CRUD/Filtros ---

    def test_guardar_usuario_existente(self):
        """
        [CORREGIDO] Prueba que guardar falle si el usuario ya existe.
        Mockea el resultado de la DB como un Modelo ORM simulado, no una entidad Usuario.
        """
        entidad = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass")
        
        # FIX: Crea un mock de ModeloUsuario (ORM) con los atributos mínimos
        mock_modelo_existente = MagicMock(
            rol="final", id=1, nombre='N', apellido='A', email='e@t.com', 
            nombre_usuario='user', claustro='docente', contrasena='hash', 
            departamento_asignado=None
        ) 
        
        # El filtro devuelve el mock del modelo (ORM)
        self.mock_filter.first.side_effect = [mock_modelo_existente, None]
        
        with self.assertRaises(ValueError):
            self.repo.guardar(entidad)
            
    def test_guardar_exitoso(self):
        """Prueba el proceso de guardado y asignación de ID."""
        entidad = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass")
        self.mock_filter.first.return_value = None # No existe
        self.mock_session.refresh.side_effect = lambda modelo: setattr(modelo, 'id', 1)
        
        self.repo.guardar(entidad)
        
        self.mock_session.add.assert_called_once()
        self.assertEqual(entidad.id_bd, 1) # Verifica que se asigne el ID

    def test_obtener_por_id_no_encontrado(self):
        """Prueba obtener_por_id cuando el modelo es None."""
        self.mock_query.get.return_value = None
        self.assertIsNone(self.repo.obtener_por_id(99))

    def test_actualizar_usuario_no_encontrado(self):
        """Prueba que actualizar falle si el usuario no existe."""
        entidad = Usuario("A", "B", "a@b.com", "user", "estudiante", "pass")
        self.mock_filter.first.return_value = None
        with self.assertRaises(ValueError):
            self.repo.actualizar(entidad)

    def test_eliminar_usuario_no_encontrado(self):
        """Prueba que eliminar falle si el usuario no existe."""
        self.mock_query.get.return_value = None
        with self.assertRaises(ValueError):
            self.repo.eliminar(99)

    def test_obtener_por_filtro_no_encontrado(self):
        """Prueba obtener_por_filtro cuando no hay resultado."""
        self.mock_filter.first.return_value = None
        self.assertIsNone(self.repo.obtener_por_filtro(nombre="X"))
        
    def test_asociar_reclamo_a_usuario_usuario_no_existe(self):
        """Cubre el error de asociación si el usuario no existe."""
        self.mock_query.get.side_effect = [None, mock_modelo_reclamo(id=1, id_creador=1)]
        with self.assertRaisesRegex(ValueError, "El usuario no existe."):
            self.repo.asociar_reclamo_a_usuario(id_usuario=99, id_reclamo=1)
            
    def test_asociar_reclamo_a_usuario_reclamo_no_existe(self):
        """Cubre el error de asociación si el reclamo no existe."""
        self.mock_query.get.side_effect = [mock_modelo_usuario(id=1), None]
        with self.assertRaisesRegex(ValueError, "El reclamo no existe."):
            self.repo.asociar_reclamo_a_usuario(id_usuario=1, id_reclamo=99)
            
    def test_asociar_reclamo_a_usuario_exitoso(self):
        """Prueba la creación de la asociación M-M."""
        mock_user = mock_modelo_usuario(id=1)
        mock_reclamo = mock_modelo_reclamo(id=1, id_creador=1)
        
        # FIX: Creamos un mock específico para el método 'append'
        mock_append = MagicMock()
        mock_user.reclamos_adheridos = MagicMock()
        mock_user.reclamos_adheridos.append = mock_append
        
        self.mock_query.get.side_effect = [mock_user, mock_reclamo]
        
        self.repo.asociar_reclamo_a_usuario(id_usuario=1, id_reclamo=1)
        
        mock_append.assert_called_once_with(mock_reclamo)
        self.mock_session.commit.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        """Cierra el pool de conexiones de la base de datos global."""
        if engine:
            engine.dispose()


class TestRepositorioReclamosSQLAlchemy(unittest.TestCase):
    
    def setUp(self):
        self.mock_session = MagicMock()
        with patch.object(Base.metadata, 'create_all'):
             self.repo = RepositorioReclamosSQLAlchemy(self.mock_session)
        self.mock_query = self.mock_session.query.return_value
        
        # Guardamos una referencia al mock de la instancia RepoUsuarios
        self.mock_repo_usuarios = self.repo._RepositorioReclamosSQLAlchemy__repo_usuarios

        # FIX 1: Reemplazar el método real con un mock instanciado para poder usar .return_value
        self.mock_repo_usuarios.obtener_por_id = MagicMock()
        
        # FIX 2: Usar un claustro válido ('estudiante') y el método mockeado.
        self.mock_repo_usuarios.obtener_por_id.return_value = Usuario("C", "R", "c@r.com", "creador", "estudiante", "pass", id_bd=1)


    # --- Pruebas de Mapeo ---
    
    def test_map_modelo_a_entidad_inconsistencia_usuario(self):
        """Cubre la excepción si el usuario creador no existe."""
        self.mock_repo_usuarios.obtener_por_id.return_value = None
        modelo = mock_modelo_reclamo(id=1, id_creador=99)
        with self.assertRaisesRegex(Exception, "Inconsistencia: No se encontró el usuario creador"):
            self.repo._RepositorioReclamosSQLAlchemy__map_modelo_a_entidad(modelo)

    def test_map_modelo_a_entidad_con_adherentes(self):
        """Prueba el mapeo cuando hay adherentes."""
        modelo = mock_modelo_reclamo(id=1, id_creador=1)
        mock_adherente_modelo = mock_modelo_usuario(id=2)
        modelo.adherentes = [mock_adherente_modelo]
        
        mock_adherente_entidad = Usuario("A", "D", "a@d.com", "adh", "estudiante", "pass", id_bd=2)
        # Necesitamos mockear el mapeador interno del repo de usuarios
        self.mock_repo_usuarios._RepositorioUsuariosSQLAlchemy__map_modelo_a_entidad = MagicMock(return_value=mock_adherente_entidad)
        
        entidad = self.repo._RepositorioReclamosSQLAlchemy__map_modelo_a_entidad(modelo)
        self.assertEqual(entidad.numero_adherentes, 1)
        
    def test_map_entidad_a_modelo_usuario_no_existe(self):
        """Cubre la excepción si el usuario creador no está en la BD."""
        entidad = Reclamo(Usuario("A", "B", "c@d.com", "fake", "estudiante", "p"), "contenido", "depto")
        self.mock_query.filter_by.return_value.first.return_value = None
        with self.assertRaisesRegex(ValueError, "El usuario creador del reclamo no existe"):
            self.repo._RepositorioReclamosSQLAlchemy__map_entidad_a_modelo(entidad)
            
    # --- Pruebas de CRUD/Rollback ---
    
    @patch('builtins.print') 
    def test_guardar_falla_con_rollback(self, mock_print):
        """Prueba que el método guardar haga rollback ante una excepción."""
        entidad = MagicMock(Reclamo, id_reclamo=None, usuario_creador=MagicMock(nombre_usuario="user", id_bd=1))
        self.mock_query.filter_by.return_value.first.return_value = MagicMock(id=1) 
        self.mock_session.add.side_effect = Exception("DB Constraint Error")

        with self.assertRaisesRegex(Exception, "DB Constraint Error"):
            self.repo.guardar(entidad)
            
        self.mock_session.rollback.assert_called_once()
        
    def test_actualizar_sin_id(self):
        """Cubre el error si se intenta actualizar sin ID."""
        entidad = Reclamo(Usuario("A","B","c@d.com","user","estudiante","p"), "Contenido", "Depto")
        self.assertIsNone(entidad.id_reclamo)
        with self.assertRaisesRegex(ValueError, "El Reclamo debe tener un ID"):
            self.repo.actualizar(entidad)
            
    def test_eliminar_no_encontrado(self):
        """Cubre el error si se intenta eliminar un reclamo inexistente."""
        self.mock_query.get.return_value = None
        with self.assertRaisesRegex(ValueError, "Reclamo no encontrado para eliminar"):
            self.repo.eliminar(99)

    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()