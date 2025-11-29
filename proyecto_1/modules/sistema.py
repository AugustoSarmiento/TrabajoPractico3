from modules.usuario import Usuario
from modules.reclamo import Reclamo
from modules.excepciones import UsuarioExistenteError, UsuarioInexistenteError, InicializacionError, ReclamoInexistenteError
from modules.roles import JefeDepartamento, SecretarioTecnico
from modules.repositorio_abstracto import IRepositorio as RepositorioAbstracto
from modules.repositorio_concreto import RepositorioUsuariosSQLAlchemy, RepositorioReclamosSQLAlchemy # Importamos los concretos
from modules.modelos_db import ModeloUsuario, ModeloReclamo # Necesario para filtros
from typing import Optional, List # Mantenemos Optional y List
from modules.clasificador_reclamos import ClasificadorReclamo

class SubsistemaGestionReclamos:
    def __init__(self, repo_usuarios: RepositorioAbstracto, repo_reclamos: RepositorioAbstracto):
        """
        Constructor que recibe los repositorios para usuarios y reclamos.
        """
        self.__repo_usuarios = repo_usuarios
        self.__repo_reclamos = repo_reclamos
        self.__clasificador = ClasificadorReclamo() #Relación de composición
        

    # --- Métodos de gestión de Usuarios ---

    def registrar_usuario(self, nombre: str, apellido: str, email: str, nombre_usuario: str, claustro: str, contrasena: str):
        """
        Registra un nuevo usuario final usando el repositorio.
        Lanza ValueError si el email o nombre de usuario ya existen (manejado por el repo).
        """
        # Creamos la entidad Usuario (sin ID de BD porque es responsabilidad de la base de datos y queremos mantener abstracción)
        nuevo_usuario = Usuario(nombre, apellido, email, nombre_usuario, claustro, contrasena)
        try:
            # El repositorio se encarga de la validación de unicidad y de guardar
            self.__repo_usuarios.guardar(nuevo_usuario)
        except ValueError as e:
            # Si el repositorio lanza ValueError (usuario existe), lo relanzamos
            raise UsuarioExistenteError(str(e))

    def buscar_usuario(self, nombre_usuario: str) -> Usuario:
        """
        Busca un usuario por su nombre de usuario usando el repositorio.
        Lanza UsuarioInexistenteError si no existe.
        """
        # Usamos obtener_por_filtro del repositorio de usuarios
        usuario_encontrado = self.__repo_usuarios.obtener_por_filtro(nombre_usuario=nombre_usuario)
        if not usuario_encontrado:
            raise UsuarioInexistenteError("El usuario especificado no existe.")
        return usuario_encontrado

 # --- Métodos de gestión de Reclamos ---

    def crear_reclamo(self, usuario_creador: Usuario, contenido: str) -> Reclamo:
        """
        Crea un nuevo reclamo. El departamento se asigna automáticamente
        usando el clasificador.
        """
        # Verificamos que el usuario creador exista en la BD
        usuario_existente = self.__repo_usuarios.obtener_por_filtro(nombre_usuario=usuario_creador.nombre_usuario)
        if not usuario_existente:
            raise UsuarioInexistenteError("No se puede crear un reclamo para un usuario que no está registrado.")
        # 1. Clasificar el contenido
        departamento_asignado = self.__clasificador.clasificar(contenido)

        # 2. Crear la entidad Reclamo con el departamento clasificado
        nuevo_reclamo = Reclamo(usuario_existente, contenido, departamento_asignado)

        # 3. Guardar el reclamo usando el repositorio
        self.__repo_reclamos.guardar(nuevo_reclamo)

        return nuevo_reclamo
    
    def buscar_reclamo_por_id(self, id_reclamo: int) -> Reclamo:
        """Busca un reclamo por su ID usando el repositorio."""
        reclamo_encontrado = self.__repo_reclamos.obtener_por_id(id_reclamo)
        if not reclamo_encontrado:
            raise ReclamoInexistenteError(f"El reclamo con ID {id_reclamo} no existe.")
        return reclamo_encontrado

    def adherir_a_reclamo(self, usuario: Usuario, id_reclamo: int):
        """
        Permite a un usuario adherirse a un reclamo existente (AHORA PERSISTENTE).
        """
        # Verificamos que el usuario exista y tenga ID de BD
        if not usuario.id_bd:
            # Si el objeto 'usuario' no tiene ID (quizás recién creado), lo buscamos
            usuario_existente = self.__repo_usuarios.obtener_por_filtro(nombre_usuario=usuario.nombre_usuario)
            if not usuario_existente or not usuario_existente.id_bd:
                 raise UsuarioInexistenteError("El usuario no está registrado o no tiene ID de BD.")
            usuario_a_adherir = usuario_existente
        else:
            usuario_a_adherir = usuario
        
        # Verificamos que el reclamo exista (esto también lo carga con sus adherentes actuales)
        reclamo_a_adherir = self.buscar_reclamo_por_id(id_reclamo)

        # Validar que el usuario no esté ya adherido
        for adherente in reclamo_a_adherir.adherentes:
            if adherente.id_bd == usuario_a_adherir.id_bd:
                # Si ya está adherido, simplemente salimos.
                return 

        # Llamamos al método del repositorio de usuarios para crear la asociación
        try:
            self.__repo_usuarios.asociar_reclamo_a_usuario(
                id_usuario=usuario_a_adherir.id_bd,
                id_reclamo=reclamo_a_adherir.id_reclamo
            )
            # Actualizamos el objeto en memoria también para reflejar el cambio
            reclamo_a_adherir.agregar_adherente(usuario_a_adherir)
        except Exception as e:
            # Manejar error si la asociación falla
            raise Exception(f"Error al adherir al reclamo: {e}")

    def cambiar_estado_reclamo(self, jefe_departamento: JefeDepartamento, id_reclamo: int, nuevo_estado: str, dias_resolucion: Optional[int] = None):
        """
        Permite a un jefe de departamento cambiar el estado de un reclamo
        perteneciente a su área y actualiza en la BD.
        """
        reclamo_a_modificar = self.buscar_reclamo_por_id(id_reclamo)

        # Verificación de permisos (igual que antes)
        if reclamo_a_modificar.departamento != jefe_departamento.departamento_asignado:
            raise Exception("Permiso denegado: no puede modificar reclamos de otro departamento.")

        # Cambiamos el estado en el objeto
        try:
            reclamo_a_modificar.cambiar_estado(nuevo_estado, dias_resolucion)
        except ValueError as e:
             # Si cambiar_estado lanza error, lo relanzamos
             raise ValueError(str(e))

        # Actualizamos el reclamo en la base de datos usando el repositorio
        self.__repo_reclamos.actualizar(reclamo_a_modificar)

    def listar_reclamos_usuario(self, usuario: Usuario) -> List[Reclamo]:
        """
        Devuelve una lista con todos los reclamos creados por un usuario específico,
        consultando el repositorio de reclamos.
        """
        # Verificamos que el usuario exista en la BD
        usuario_existente = self.__repo_usuarios.obtener_por_filtro(nombre_usuario=usuario.nombre_usuario)
        if not usuario_existente:
            raise UsuarioInexistenteError("El usuario no está registrado en el sistema.")

        # Necesitamos el ID del ModeloUsuario para filtrar en ModeloReclamo
        # Asumimos que el repositorio de usuarios nos puede dar el modelo o el ID
        
        
        modelo_usuario = self.__repo_usuarios._RepositorioUsuariosSQLAlchemy__session.query(ModeloUsuario).filter_by(nombre_usuario=usuario_existente.nombre_usuario).first()
        if not modelo_usuario:
             raise Exception("Inconsistencia: Usuario existe como entidad pero no como modelo.")

        # Usamos obtener_todos_por_filtro del repositorio de reclamos
        reclamos_del_usuario = self.__repo_reclamos.obtener_todos_por_filtro(id_usuario_creador=modelo_usuario.id)
        return reclamos_del_usuario
    

    def buscar_reclamos_pendientes_todos(self) -> List[Reclamo]:
        """
        Busca en la BD todos los reclamos que están en estado 'pendiente'.
        Cumple con el requisito de "listar reclamos pendientes".
        """
        reclamos_encontrados = self.__repo_reclamos.obtener_todos_por_filtro(
            estado="pendiente"
        )
        return reclamos_encontrados

    def buscar_reclamos_pendientes_por_departamento(self, departamento: str) -> List[Reclamo]:
        """
        Busca en la BD todos los reclamos que están en estado 'pendiente'
        y pertenecen a un departamento específico.
        Cumple con el requisito de "permitir aplicar filtros por departamento".
        """
        # Como el clasificador asigna el departamento, podemos filtrar directamente por él.
        reclamos_encontrados = self.__repo_reclamos.obtener_todos_por_filtro(
            estado="pendiente",
            departamento=departamento
        )
        return reclamos_encontrados 

     
    def derivar_reclamo(self, usuario_secretario: Usuario, id_reclamo: int, nuevo_departamento: str):
        """
        Permite a un Secretario Técnico derivar un reclamo a un nuevo departamento.
        Valida que el usuario tenga el rol correcto antes de actuar.
        """
        if not isinstance(usuario_secretario, SecretarioTecnico):
            raise Exception("Permiso denegado: Solo el Secretario Técnico puede derivar reclamos.")

        
        departamentos_validos = ["secretaría técnica", "soporte informático", "maestranza"]
        if nuevo_departamento not in departamentos_validos:
            raise ValueError(f"El departamento '{nuevo_departamento}' no es un destino válido.")

        reclamo_a_derivar = self.buscar_reclamo_por_id(id_reclamo) # Ya lanza ReclamoInexistenteError si no existe

        reclamo_a_derivar.departamento = nuevo_departamento

        self.__repo_reclamos.actualizar(reclamo_a_derivar)


    def buscar_reclamos_similares(self, contenido_reclamo: str) -> List[Reclamo]:
    # 1. Clasificar el texto para saber qué buscar
    #    (Asumimos que self.__clasificador ya fue creado en el __init__)
        clasificacion = self.__clasificador.clasificar(contenido_reclamo)

        if clasificacion == "indefinido":
            print("Advertencia: El clasificador no pudo determinar una categoría.")
            return [] # Si no se puede clasificar, no hay similares

        # 2. Buscar en la BD reclamos pendientes CON ESA CLASIFICACIÓN
        #    (El 'departamento' de nuestro reclamo es la 'clasificación')
        reclamos_similares = self.__repo_reclamos.obtener_todos_por_filtro(
            estado="pendiente",
            departamento=clasificacion
        )
        return reclamos_similares