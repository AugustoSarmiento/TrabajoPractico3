from modules.factoria import crear_repositorio_usuarios, crear_repositorio_reclamos
from modules.usuario import Usuario
from modules.roles import JefeDepartamento, SecretarioTecnico
from modules.sistema import SubsistemaGestionReclamos # Para crear reclamos

# Importamos los datos de los archivos
from modules.inicializacion import DATOS_PERSONAL
from data.datos_iniciales import USUARIOS_INICIALES, RECLAMOS_INICIALES

def inicializar_base_de_datos():
    """
    Script para crear y poblar la base de datos con datos iniciales.
    Crea el personal (Jefes/Secretarios) y usuarios/reclamos de ejemplo.
    """
    print("--- Iniciando Script de Inicialización ---")
    
    # 1. Crear los repositorios
    repo_usuarios = crear_repositorio_usuarios()
    repo_reclamos = crear_repositorio_reclamos()
    
    # Creamos una instancia del sistema para usar la lógica de 'crear_reclamo'
    # (que incluye la clasificación automática)
    sistema = SubsistemaGestionReclamos(repo_usuarios, repo_reclamos)

    # 2. Crear Personal (Jefes y Secretarios)
    print("\n[PASO 1/3] Creando personal (Jefes y Secretarios)...")
    for datos in DATOS_PERSONAL:
        try:
            # Verificamos si ya existe
            if repo_usuarios.obtener_por_filtro(nombre_usuario=datos["nombre_usuario"]):
                print(f"  > Omitido: Usuario '{datos['nombre_usuario']}' ya existe.")
                continue

            # Creamos la entidad
            if datos["rol"] == "jefe":
                nuevo_personal = JefeDepartamento(
                    nombre=datos["nombre"], apellido=datos["apellido"], email=datos["email"],
                    nombre_usuario=datos["nombre_usuario"], contrasena=datos["contrasena"],
                    departamento_asignado=datos["departamento_asignado"]
                )
            elif datos["rol"] == "secretario":
                nuevo_personal = SecretarioTecnico(
                    nombre=datos["nombre"], apellido=datos["apellido"], email=datos["email"],
                    nombre_usuario=datos["nombre_usuario"], contrasena=datos["contrasena"]
                )
            
            # Guardamos usando el repositorio
            repo_usuarios.guardar(nuevo_personal)
            print(f"  > Creado: {datos['rol']} '{datos['nombre_usuario']}'")
        
        except Exception as e:
            print(f"  > Error al crear personal '{datos['nombre_usuario']}': {e}")

    # 3. Crear Usuarios Finales de Ejemplo
    print("\n[PASO 2/3] Creando usuarios finales de ejemplo...")
    for datos in USUARIOS_INICIALES:
        try:
            # Verificamos si ya existe
            if repo_usuarios.obtener_por_filtro(nombre_usuario=datos["nombre_usuario"]):
                print(f"  > Omitido: Usuario '{datos['nombre_usuario']}' ya existe.")
                continue

            # Usamos el método de 'sistema' para registrar (o el repo directamente)
            # Usar el repo es más directo aquí:
            nuevo_usuario = Usuario(
                nombre=datos["nombre"], apellido=datos["apellido"], email=datos["email"],
                nombre_usuario=datos["nombre_usuario"], claustro=datos["claustro"],
                contrasena=datos["contrasena"]
            )
            repo_usuarios.guardar(nuevo_usuario)
            print(f"  > Creado: Usuario final '{datos['nombre_usuario']}'")
        
        except Exception as e:
            print(f"  > Error al crear usuario '{datos['nombre_usuario']}': {e}")

    # 4. Crear Reclamos de Ejemplo
    print("\n[PASO 3/3] Creando reclamos de ejemplo...")
    for datos in RECLAMOS_INICIALES:
        try:
            # Buscamos al usuario creador en la BD
            creador = repo_usuarios.obtener_por_filtro(nombre_usuario=datos["creador_username"])
            if not creador:
                print(f"  > Omitido: Creador '{datos['creador_username']}' no encontrado.")
                continue
            
            # Verificamos si un reclamo con el mismo contenido ya existe
            if repo_reclamos.obtener_por_filtro(contenido=datos["contenido"]):
                 print(f"  > Omitido: Reclamo '{datos['contenido'][:30]}...' ya existe.")
                 continue

            # Usamos el método 'crear_reclamo' del sistema para que lo clasifique
            # automáticamente al crearlo.
            sistema.crear_reclamo(creador, datos["contenido"])
            print(f"  > Creado: Reclamo '{datos['contenido'][:30]}...' (por {creador.nombre_usuario})")
        
        except Exception as e:
            print(f"  > Error al crear reclamo '{datos['contenido'][:30]}...': {e}")

    print("\n--- Script de Inicialización Finalizado ---")

# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    # Esto asegura que el código solo se ejecute si corres 'python inicializar_db.py'
    inicializar_base_de_datos()