# modules/repositorio_concreto.py

from sqlalchemy.orm import Session
import datetime

# Cambiamos el nombre de la interfaz para que coincida con los ejemplos
from modules.repositorio_abstracto import IRepositorio as RepositorioAbstracto
# Importamos nuestras clases de dominio específicas
from modules.usuario import Usuario
from modules.reclamo import Reclamo
from modules.roles import JefeDepartamento, SecretarioTecnico
# Importamos nuestros modelos de BD específicos y la Base
from modules.modelos_db import ModeloUsuario, ModeloReclamo, Base
# Ya no necesitamos importar 'engine', usaremos el 'bind' de la sesión
from typing import Optional, List # Usamos Optional/List para claridad en los retornos


# --- Repositorio para Usuarios ---

class RepositorioUsuariosSQLAlchemy(RepositorioAbstracto):
    """Implementación concreta para manejar la persistencia de Usuarios."""

    def __init__(self, session: Session):
        self.__session = session
        # Asegura que la tabla de usuarios exista
        Base.metadata.create_all(bind=self.__session.bind)

    # --- Métodos de Mapeo (Usuario) ---

    def __map_modelo_a_entidad(self, modelo: ModeloUsuario) -> Usuario:
        """Convierte un ModeloUsuario (tabla) a un objeto Usuario/Jefe/Secretario (dominio)."""
        # Decide qué clase instanciar basado en el rol guardado en la BD
        if modelo.rol == "jefe":
            entidad = JefeDepartamento(
                nombre=modelo.nombre,
                apellido=modelo.apellido,
                email=modelo.email,
                nombre_usuario=modelo.nombre_usuario,
                contrasena=modelo.contrasena, # Pendiente encriptación
                departamento_asignado=modelo.departamento_asignado,
                id_bd=modelo.id
            )
        elif modelo.rol == "secretario":
            entidad = SecretarioTecnico(
                nombre=modelo.nombre,
                apellido=modelo.apellido,
                email=modelo.email,
                nombre_usuario=modelo.nombre_usuario,
                contrasena=modelo.contrasena,  # Pendiente encriptación
                id_bd=modelo.id
            )
        else: # Usuario final
            entidad = Usuario(
                nombre=modelo.nombre,
                apellido=modelo.apellido,
                email=modelo.email,
                nombre_usuario=modelo.nombre_usuario,
                claustro=modelo.claustro,
                contrasena=modelo.contrasena, # Pendiente encriptación
                id_bd=modelo.id
            )
        # Guardamos el ID de la BD en un atributo que no está en el constructor
        # (Necesitaremos añadir un setter o hacerlo público si queremos actualizarlo)
        # Por ahora, lo omitimos para mantener la clase Usuario simple.
        # setattr(entidad, '_id_bd', modelo.id) # Ejemplo si tuviéramos _id_bd
        return entidad

    def __map_entidad_a_modelo(self, entidad: Usuario) -> ModeloUsuario:
        """Convierte un objeto Usuario/Jefe/Secretario (dominio) a un ModeloUsuario (tabla)."""
        modelo = ModeloUsuario(
            # Si la entidad ya tiene un ID de BD (ej. al actualizar), lo usamos.
            # id=getattr(entidad, '_id_bd', None), # Ejemplo si tuviéramos _id_bd
            nombre=entidad.nombre,
            apellido=entidad.apellido,
            email=entidad.email,
            nombre_usuario=entidad.nombre_usuario,
            # Accedemos a la contraseña "privada". Idealmente, Usuario tendría un getter.
            contrasena=entidad._Usuario__contrasena, # Pendiente encriptación
            claustro=entidad.claustro if hasattr(entidad, 'claustro') else None, # Solo si es Usuario base
            rol="final" # Rol por defecto
        )
        # Asignamos el rol y atributos específicos si es Jefe o Secretario
        if isinstance(entidad, JefeDepartamento):
            modelo.rol = "jefe"
            modelo.departamento_asignado = entidad.departamento_asignado
            modelo.claustro = entidad.claustro # Sobrescribimos claustro
        elif isinstance(entidad, SecretarioTecnico):
            modelo.rol = "secretario"
            modelo.claustro = entidad.claustro # Sobrescribimos claustro

        return modelo

    # --- Implementación Métodos Repositorio (Usuario) ---

    def guardar(self, entidad: Usuario):
        # Validación específica para Usuario antes de mapear
        existente_email = self.obtener_por_filtro(email=entidad.email)
        existente_nom_usr = self.obtener_por_filtro(nombre_usuario=entidad.nombre_usuario)
        if existente_email or existente_nom_usr:
            raise ValueError("El email o nombre de usuario ya está registrado.")

        modelo = self.__map_entidad_a_modelo(entidad)
        self.__session.add(modelo)
        self.__session.commit()
        self.__session.refresh(modelo) 
        entidad.id_bd = modelo.id
        

    def obtener_por_id(self, id: int) -> Optional[Usuario]:
        modelo = self.__session.query(ModeloUsuario).get(id)
        return self.__map_modelo_a_entidad(modelo) if modelo else None

    def obtener_todos(self) -> List[Usuario]:
        modelos = self.__session.query(ModeloUsuario).all()
        return [self.__map_modelo_a_entidad(m) for m in modelos]

    def actualizar(self, entidad: Usuario):
        # Buscamos por nombre_usuario que es único y asumimos que la entidad lo tiene bien
        modelo_actualizar = self.__session.query(ModeloUsuario).filter_by(nombre_usuario=entidad.nombre_usuario).first()
        if not modelo_actualizar:
             raise ValueError("Usuario no encontrado para actualizar.")

        # Actualizamos los campos desde la entidad mapeada (excepto ID y contraseña)
        modelo_mapeado = self.__map_entidad_a_modelo(entidad)
        modelo_actualizar.nombre = modelo_mapeado.nombre
        modelo_actualizar.apellido = modelo_mapeado.apellido
        # Validar unicidad de email si cambia? Depende del requisito
        modelo_actualizar.email = modelo_mapeado.email
        modelo_actualizar.claustro = modelo_mapeado.claustro
        modelo_actualizar.rol = modelo_mapeado.rol
        modelo_actualizar.departamento_asignado = modelo_mapeado.departamento_asignado
        # La contraseña se actualiza en un método separado y con hashing

        self.__session.commit()

    def eliminar(self, id: int):
        modelo_eliminar = self.__session.query(ModeloUsuario).get(id)
        if not modelo_eliminar:
             raise ValueError("Usuario no encontrado para eliminar.")
        # Considerar qué hacer con los reclamos creados por este usuario (depende del requisito)
        self.__session.delete(modelo_eliminar)
        self.__session.commit()

    def obtener_por_filtro(self, **kwargs) -> Optional[Usuario]:
        #kwarg permite pasar una cantidad de argumentos con nombre, nos permite mayor flexibilidad.
        # El filtro se aplica directamente al query del modelo
        modelo = self.__session.query(ModeloUsuario).filter_by(**kwargs).first()
        return self.__map_modelo_a_entidad(modelo) if modelo else None

    def obtener_todos_por_filtro(self, **kwargs) -> List[Usuario]:
        modelos = self.__session.query(ModeloUsuario).filter_by(**kwargs).all()
        return [self.__map_modelo_a_entidad(m) for m in modelos]

    def asociar_reclamo_a_usuario(self, id_usuario: int, id_reclamo: int):
        # 1. Encontrar el modelo del usuario
        usuario_modelo = self.__session.query(ModeloUsuario).get(id_usuario)
        if not usuario_modelo:
            raise ValueError("El usuario no existe.")

        # 2. Encontrar el modelo del reclamo
        reclamo_modelo = self.__session.query(ModeloReclamo).get(id_reclamo)
        if not reclamo_modelo:
            raise ValueError("El reclamo no existe.")
        
        # 3. Añadir la relación
        usuario_modelo.reclamos_adheridos.append(reclamo_modelo)
        
        # 4. Guardar los cambios
        self.__session.commit()

# --- Repositorio para Reclamos ---

class RepositorioReclamosSQLAlchemy(RepositorioAbstracto):
    """Implementación concreta para manejar la persistencia de Reclamos."""

    def __init__(self, session: Session):
        self.__session = session
        # Asegura que la tabla de reclamos (y usuarios por dependencia) exista
        Base.metadata.create_all(bind=self.__session.bind)
        # Guardamos una referencia al repo de usuarios para buscar creadores
        # Esto es una forma de hacerlo, otra sería pasar el ID directamente
        self.__repo_usuarios = RepositorioUsuariosSQLAlchemy(session)


    # --- Métodos de Mapeo (Reclamo) ---

    def __map_modelo_a_entidad(self, modelo: ModeloReclamo) -> Reclamo:
        """Convierte un ModeloReclamo (tabla) a un objeto Reclamo (dominio)."""
        # Buscamos la entidad Usuario creadora usando el repo de usuarios
        creador_entidad = self.__repo_usuarios.obtener_por_id(modelo.id_usuario_creador)
        if not creador_entidad:
             raise Exception(f"Inconsistencia: No se encontró el usuario creador ID {modelo.id_usuario_creador}")

        # Creamos la entidad Reclamo
        entidad = Reclamo(
             usuario_creador=creador_entidad,
             contenido=modelo.contenido,
             departamento=modelo.departamento
        )
        # Asignamos atributos que no están en el __init__ usando nombres "privados"
        entidad._Reclamo__id_reclamo = modelo.id
        entidad._Reclamo__timestamp = modelo.timestamp
        entidad._Reclamo__estado = modelo.estado
        entidad._Reclamo__tiempo_resolucion_asignado = modelo.tiempo_resolucion_asignado
        
        if modelo.adherentes:
            for adherente_modelo in modelo.adherentes:
                # Convertimos cada ModeloUsuario a una entidad Usuario
                # Usamos el mapeador interno del repo de usuarios para esto
                adherente_entidad = self.__repo_usuarios._RepositorioUsuariosSQLAlchemy__map_modelo_a_entidad(adherente_modelo)
                # Usamos el método público de la entidad Reclamo para agregarlo
                entidad.agregar_adherente(adherente_entidad)

        return entidad

    def __map_entidad_a_modelo(self, entidad: Reclamo) -> ModeloReclamo:
        """Convierte un objeto Reclamo (dominio) a un ModeloReclamo (tabla)."""
        # Necesitamos el ID del ModeloUsuario creador
        modelo_creador = self.__session.query(ModeloUsuario).filter_by(
            nombre_usuario=entidad.usuario_creador.nombre_usuario
        ).first()
        if not modelo_creador:
            # El usuario creador DEBE existir en la BD antes de guardar un reclamo
            raise ValueError("El usuario creador del reclamo no existe en la base de datos.")

        # Si el reclamo ya existe (tiene ID), lo usamos para actualizar, sino es nuevo
        id_reclamo_bd = entidad.id_reclamo if entidad.id_reclamo is not None else None

        return ModeloReclamo(
            id=id_reclamo_bd, 
            contenido=entidad.contenido,
            departamento=entidad.departamento,
            timestamp=entidad.timestamp,
            estado=entidad.estado,
            tiempo_resolucion_asignado=entidad.tiempo_resolucion_asignado,
            id_usuario_creador=modelo_creador.id
        )

    # --- Implementación Métodos Repositorio (Reclamo) ---

    def guardar(self, entidad: Reclamo):
        try:
            modelo = self.__map_entidad_a_modelo(entidad)
            self.__session.add(modelo)
            self.__session.commit()
            self.__session.refresh(modelo) 
            entidad.id_reclamo = modelo.id 
        except Exception as e:
            # ¡Importante! Si algo falla (como un UNIQUE constraint),
            # limpiamos la sesión para que no se rompa.
            self.__session.rollback()
            print(f"Error al guardar reclamo: {e}")
            # Relanzamos el error para que la capa de servicio se entere
            raise e
        

    def obtener_por_id(self, id: int) -> Optional[Reclamo]:
        modelo = self.__session.query(ModeloReclamo).get(id)
        return self.__map_modelo_a_entidad(modelo) if modelo else None

    def obtener_todos(self) -> List[Reclamo]:
        modelos = self.__session.query(ModeloReclamo).all()
        return [self.__map_modelo_a_entidad(m) for m in modelos]

    def actualizar(self, entidad: Reclamo):
        if not entidad.id_reclamo: # Necesitamos el ID para saber cuál actualizar
             raise ValueError("El Reclamo debe tener un ID para ser actualizado.")

        modelo_actualizar = self.__session.query(ModeloReclamo).get(entidad.id_reclamo)
        if not modelo_actualizar:
             raise ValueError("Reclamo no encontrado para actualizar.")

        # Actualizamos campos desde la entidad mapeada (excepto ID, creador, timestamp)
        modelo_mapeado = self.__map_entidad_a_modelo(entidad)
        modelo_actualizar.contenido = modelo_mapeado.contenido
        modelo_actualizar.departamento = modelo_mapeado.departamento
        modelo_actualizar.estado = modelo_mapeado.estado
        modelo_actualizar.tiempo_resolucion_asignado = modelo_mapeado.tiempo_resolucion_asignado

        self.__session.commit()

    def eliminar(self, id: int):
        modelo_eliminar = self.__session.query(ModeloReclamo).get(id)
        if not modelo_eliminar:
             raise ValueError("Reclamo no encontrado para eliminar.")
        self.__session.delete(modelo_eliminar)
        self.__session.commit()

    def obtener_por_filtro(self, **kwargs) -> Optional[Reclamo]:
        modelo = self.__session.query(ModeloReclamo).filter_by(**kwargs).first()
        return self.__map_modelo_a_entidad(modelo) if modelo else None

    def obtener_todos_por_filtro(self, **kwargs) -> List[Reclamo]:
        modelos = self.__session.query(ModeloReclamo).filter_by(**kwargs).all()
        return [self.__map_modelo_a_entidad(m) for m in modelos]