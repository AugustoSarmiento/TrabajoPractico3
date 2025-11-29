from modules.usuario import Usuario
import datetime

class Reclamo:
    """Modela un Reclamo realizado por un Usuario."""
    

    def __init__(self, usuario_creador: Usuario, contenido: str, departamento: str):
        self.__id_reclamo: int | None = None # El ID se asignará después de guardarlo 
        self.__usuario_creador: Usuario = usuario_creador # Relación de Agregación.
        self.__contenido: str = contenido
        self.__departamento: str = departamento
        self.__timestamp: datetime.datetime = datetime.datetime.now()
        self.__estado: str = "pendiente"
        self.__adherentes: list[Usuario] = [] # Relación de Asociación
        self.__tiempo_resolucion_asignado: int | None = None


    @property
    def id_reclamo(self) -> int:
        return self.__id_reclamo

    @id_reclamo.setter
    def id_reclamo(self, valor: int):
        self.__id_reclamo = valor
        
    @property
    def usuario_creador(self) -> Usuario:
        return self.__usuario_creador

    @property
    def contenido(self) -> str:
        return self.__contenido
    
    @property
    def departamento(self) -> str:
        return self.__departamento
    
    @departamento.setter
    def departamento(self, nuevo_depto: str):
        """Setter para cambiar el departamento (usado por Secretario Técnico)."""
        self.__departamento = nuevo_depto

    @property
    def timestamp(self) -> datetime.datetime:
        return self.__timestamp

    @property
    def estado(self) -> str:
        return self.__estado

    @property
    def numero_adherentes(self) -> int:
        return len(self.__adherentes)
        
    @property
    def tiempo_resolucion_asignado(self) -> int | None:
        return self.__tiempo_resolucion_asignado
    
    @property
    def adherentes(self) -> list[Usuario]:
        return self.__adherentes
    
    def agregar_adherente(self, usuario: Usuario):
        if usuario not in self.__adherentes:
            self.__adherentes.append(usuario)

    def cambiar_estado(self, nuevo_estado: str, dias_resolucion: int | None = None):
        if nuevo_estado in ["inválido", "pendiente", "en proceso", "resuelto"]:
            self.__estado = nuevo_estado
            if self.__estado == "en proceso":
                if dias_resolucion is not None and 1 <= dias_resolucion <= 15:
                    self.__tiempo_resolucion_asignado = dias_resolucion
                else:
                    # Lanza un error si el estado es 'en proceso' pero los días no son válidos.
                    raise ValueError("Se debe asignar un tiempo de resolución válido (1-15 días).")
        else:
            raise ValueError(f"El estado '{nuevo_estado}' no es un estado válido")