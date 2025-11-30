
from modules.factoria import crear_repositorio_usuarios, crear_repositorio_reclamos
from modules.sistema import SubsistemaGestionReclamos
from modules.inicializacion import DATOS_PERSONAL # Datos para inicializar personal
from modules.roles import JefeDepartamento, SecretarioTecnico # Clases específicas
from modules.excepciones import UsuarioExistenteError # Para manejar errores al inicializar
from flask import render_template, request, redirect, url_for, session, flash
from modules.config import app, login_manager # Importamos app y login_manager
from modules.formularios import FormRegistro, FormLogin, FormCrearReclamo, FormEditarEstado, FormDerivarReclamo
from modules.gestor_login import GestorDeLogin # Importamos el gestor
from modules.excepciones import UsuarioInexistenteError, UsuarioExistenteError
from modules.usuario import Usuario # Para el chequeo de contraseñas
from modules.estadisticas import GeneradorEstadisticas
from flask import send_from_directory
from modules.generador_reportes import GeneradorReportes, ReporteHTML, ReportePDF
import os
import datetime

repo_usuarios = crear_repositorio_usuarios()
repo_reclamos = crear_repositorio_reclamos()
sistema = SubsistemaGestionReclamos(repo_usuarios, repo_reclamos)

#print("Creando gestor de login...")
gestor_login = GestorDeLogin(login_manager, repo_usuarios)

@app.context_processor
def inject_gestor_login():
    """
    Inyecta la variable 'gestor_login' en el contexto de todas las plantillas.
    Esto es necesario para que 'base.html' pueda usarla en la barra de navegación.
    """
    return dict(gestor_login=gestor_login)

def inicializar_personal():
    """
    Función que contiene la lógica de inicialización y los logs, 
    para ser llamada solo al ejecutar server.py directamente.
    """
    print("Inicializando personal...")
    for datos_persona in DATOS_PERSONAL:
        try:
            usuario_existente = repo_usuarios.obtener_por_filtro(nombre_usuario=datos_persona["nombre_usuario"])
            if usuario_existente:
                print(f"Usuario '{datos_persona['nombre_usuario']}' ya existe, omitiendo creación inicial.")
                continue

            if datos_persona["rol"] == "jefe":
                nuevo_personal = JefeDepartamento(
                    nombre=datos_persona["nombre"], apellido=datos_persona["apellido"], email=datos_persona["email"],
                    nombre_usuario=datos_persona["nombre_usuario"],
                    contrasena=datos_persona["contrasena"], # Contraseña en texto plano
                    departamento_asignado=datos_persona["departamento_asignado"]
                )
            elif datos_persona["rol"] == "secretario":
                nuevo_personal = SecretarioTecnico(
                    nombre=datos_persona["nombre"], apellido=datos_persona["apellido"], email=datos_persona["email"],
                    nombre_usuario=datos_persona["nombre_usuario"],
                    contrasena=datos_persona["contrasena"] # Contraseña en texto plano
                )
            else:
                continue

            repo_usuarios.guardar(nuevo_personal)
            print(f"Usuario '{nuevo_personal.nombre_usuario}' ({datos_persona['rol']}) creado.")

        except KeyError as e:
            print(f"Error al inicializar personal: falta la clave {e} en los datos.")
        except UsuarioExistenteError as e:
             print(f"Error al guardar personal: {e}")
        except Exception as e:
             print(f"Error inesperado al inicializar personal '{datos_persona.get('nombre_usuario', 'Desconocido')}': {e}")

    print("Inicialización de personal completada.")


@app.route("/")
def inicio():
    """
    Ruta principal. Redirige al panel si el usuario está logueado,
    o muestra la página de inicio pública si no lo está.
    """
    if gestor_login.usuario_autenticado:
        return redirect(url_for('panel_principal'))
    
    return render_template("inicio.html")

# --- RUTAS DE AUTENTICACIÓN ---

@app.route("/register", methods=["GET", "POST"])
def register():
    """Ruta para registrar un nuevo usuario final."""
    form = FormRegistro()
    
    if form.validate_on_submit():
        # Si el formulario es válido, intentamos registrar al usuario
        try:
            sistema.registrar_usuario(
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                email=form.email.data,
                nombre_usuario=form.nombre_usuario.data,
                claustro=form.claustro.data,
                contrasena=form.password.data
                # No pasamos la 'confirmacion', ya fue validada por el formulario
            )
            # Si tiene éxito, mostramos un mensaje y lo mandamos a loguearse
            flash("¡Registro exitoso! Por favor, inicia sesión.", "success")
            return redirect(url_for('login'))
        except UsuarioExistenteError as e:
            # Si falla (ej. email ya existe), mostramos el error
            flash(str(e), "danger")
        except Exception as e:
            flash(f"Error inesperado al registrar: {e}", "danger")
            
    # Si es GET o el formulario no es válido, mostramos la plantilla de registro
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Ruta para iniciar sesión (todos los roles)."""
    form = FormLogin()
    
    if form.validate_on_submit():
        try:
            # 1. Buscar al usuario
            usuario_entidad = sistema.buscar_usuario(form.nombre_usuario.data)
            
            # 2. Validar la contraseña (SIN HASHING)
            if not usuario_entidad.validar_contrasena(form.password.data):
                raise ValueError("Contraseña incorrecta.")
                
            # 3. Iniciar sesión
            gestor_login.login(usuario_entidad)
            flash(f"Bienvenido, {usuario_entidad.nombre}!", "success")
            
            # 4. Redirigir al panel principal
            return redirect(url_for('panel_principal'))
            
        except (UsuarioInexistenteError, ValueError) as e:
            flash(f"Error al iniciar sesión: {e}", "danger")
        except Exception as e:
            flash(f"Error inesperado: {e}", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@gestor_login.se_requiere_login # Protegemos esta ruta
def logout():
    """Ruta para cerrar sesión."""
    gestor_login.logout()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for('inicio'))


# --- RUTA PRINCIPAL (LOGUEADO) ---

@app.route("/panel")
@gestor_login.se_requiere_login # Esta es la protección de Flask-Login
def panel_principal():
    """
    Panel principal al que accede el usuario tras iniciar sesión.
    Aquí se mostrarán distintas cosas según el rol.
    """
    mensaje_prueba = session.pop('prueba_manual', None)
    print(f"VALOR DE PRUEBA EN SESIÓN: {mensaje_prueba}")
    usuario_actual = gestor_login.usuario_actual
    
    # (Aún no hemos creado esta plantilla, lo haremos ahora)
    return render_template("panel_usuario.html", usuario=usuario_actual, mensaje_prueba=mensaje_prueba)

@app.route("/crear_reclamo", methods=["GET", "POST"])
@gestor_login.se_requiere_login
def crear_reclamo():
    """
    Paso 1 del flujo de creación:
    - Muestra el formulario para escribir el reclamo.
    - Al enviar (POST), clasifica el contenido y busca similares.
    - Muestra la lista de similares para que el usuario decida.
    """
    form = FormCrearReclamo()

    if form.validate_on_submit():
        # El formulario es válido, procesamos el contenido
        contenido = form.contenido.data

        # Usamos el método del sistema para clasificar y buscar
        reclamos_similares = sistema.buscar_reclamos_similares(contenido)

        if not reclamos_similares:
            # No se encontraron similares
            try:
                # Creamos el reclamo directamente
                nuevo_reclamo = sistema.crear_reclamo(
                    usuario_creador=gestor_login.usuario_actual.entidad,
                    contenido=contenido
                )
                flash(f"Reclamo #{nuevo_reclamo.id_reclamo} creado exitosamente y derivado a '{nuevo_reclamo.departamento}'.", "success")
                return redirect(url_for('panel_principal')) # Volvemos al panel
            except Exception as e:
                flash(f"Error al crear el reclamo: {e}", "danger")

        else:
            # ¡Se encontraron reclamos similares!
            # Guardamos el contenido temporalmente en la sesión
            session['reclamo_temporal'] = contenido

            # Mostramos la página de "confirmación"
            return render_template("confirmar_reclamo.html", 
                                   reclamos_similares=reclamos_similares, 
                                   contenido_nuevo=contenido)

    # Si es GET (o el form no es válido), solo mostramos el formulario
    return render_template("crear_reclamo.html", form=form)


@app.route("/crear_reclamo_confirmado", methods=["POST"])
@gestor_login.se_requiere_login
def crear_reclamo_confirmado():
    """
    Ruta que procesa la decisión final de crear un reclamo nuevo
    después de haber visto los similares.
    """
    # Recuperamos el contenido del reclamo que guardamos temporalmente en la sesión
    contenido = session.pop('reclamo_temporal', None) 
    
    if not contenido:
        flash("Error: No hay un reclamo temporal para crear. Por favor, intente de nuevo.", "danger")
        return redirect(url_for('crear_reclamo'))
        
    try:
        # Usamos el método 'crear_reclamo' del sistema
        nuevo_reclamo = sistema.crear_reclamo(
            usuario_creador=gestor_login.usuario_actual.entidad,
            contenido=contenido
        )
        session['prueba_manual'] = 'ESTO ES UNA PRUEBA DE SESION'
        flash(f"Reclamo #{nuevo_reclamo.id_reclamo} creado exitosamente y derivado a '{nuevo_reclamo.departamento}'.", "success")
    except Exception as e:
        flash(f"Error al crear el reclamo: {e}", "danger")

    # Siempre redirigimos al panel principal después de la acción
    return redirect(url_for('panel_principal'))


@app.route("/adherir/<int:id_reclamo>", methods=["POST"])
@gestor_login.se_requiere_login
def adherir_reclamo(id_reclamo):
    """
    Ruta para adherir el usuario actual a un reclamo existente.
    """
    # Borramos el reclamo temporal de la sesión, ya que no lo vamos a crear
    session.pop('reclamo_temporal', None) 
    
    try:
        # Obtenemos la entidad del usuario actual
        usuario_actual = gestor_login.usuario_actual.entidad
        
        # Llamamos al método del sistema para adherir
        sistema.adherir_a_reclamo(usuario_actual, id_reclamo)
        flash(f"Te has adherido exitosamente al reclamo #{id_reclamo}.", "success")
    
    except Exception as e:
        flash(f"Error al adherirse al reclamo: {e}", "danger")

    return redirect(url_for('panel_principal'))

@app.route("/listar_reclamos")
@gestor_login.se_requiere_login
def listar_reclamos():
    """
    Ruta para la Opción 2: Listar todos los reclamos pendientes,
    con opción de filtrar por departamento.

    """
    # Obtenemos el departamento del filtro (si existe en la URL)
    filtro_depto = request.args.get('departamento', None)

    lista_reclamos = []
    if filtro_depto:
        # Si hay un filtro, buscamos por ese departamento
        lista_reclamos = sistema.buscar_reclamos_pendientes_por_departamento(filtro_depto)
    else:
        # Si no hay filtro, traemos todos los pendientes
        lista_reclamos = sistema.buscar_reclamos_pendientes_todos()

    # Lista de departamentos para armar los botones de filtro
    departamentos_posibles = ["soporte informático", "secretaría técnica", "maestranza"]

    return render_template("listar_reclamos.html", 
                           reclamos=lista_reclamos,
                           departamentos=departamentos_posibles,
                           filtro_actual=filtro_depto)


@app.route("/mis_reclamos")
@gestor_login.se_requiere_login
def mis_reclamos():
    try:
        # 1. Obtenemos la entidad del usuario actual
        usuario_actual = gestor_login.usuario_actual.entidad

        # 2. Usamos el método del sistema para buscar sus reclamos
        reclamos_del_usuario = sistema.listar_reclamos_usuario(usuario_actual)

        # 3. Renderizamos la nueva plantilla
        return render_template("mis_reclamos.html", 
                               reclamos=reclamos_del_usuario)
    except Exception as e:
        flash(f"Error al cargar tus reclamos: {e}", "danger")
        return redirect(url_for('panel_principal'))
    

@app.route("/manejar_reclamos")
@gestor_login.se_requiere_login
@gestor_login.rol_requerido(roles_permitidos=['jefe', 'secretario'])
def manejar_reclamos():
    """
    Ruta para la Opción 1 del Admin: Manejar Reclamos.
    Muestra una lista de reclamos filtrada por rol.
    - Jefes: Solo ven reclamos de su departamento.
    - Secretarios: Ven todos los reclamos.

    """
    usuario_actual = gestor_login.usuario_actual
    lista_reclamos = []

    try:
        if usuario_actual.rol == 'jefe':
            # Un Jefe solo ve los reclamos de su departamento asignado [cite: 602]
            lista_reclamos = repo_reclamos.obtener_todos_por_filtro(
                departamento=usuario_actual.departamento
            )
        elif usuario_actual.rol == 'secretario':
            # El Secretario Técnico puede ver todos los reclamos
            lista_reclamos = repo_reclamos.obtener_todos()

        # Ordenamos la lista por estado (ej. pendientes primero)
        lista_reclamos.sort(key=lambda r: r.estado)

        return render_template("manejar_reclamos.html", 
                               reclamos=lista_reclamos, 
                               usuario=usuario_actual)

    except Exception as e:
        flash(f"Error al cargar los reclamos: {e}", "danger")
        return redirect(url_for('panel_principal'))


@app.route("/editar_estado/<int:id_reclamo>", methods=["GET", "POST"])
@gestor_login.se_requiere_login
@gestor_login.rol_requerido(roles_permitidos=['jefe'])
def editar_estado(id_reclamo):
    """
    Ruta para mostrar y procesar el formulario de edición de estado de un reclamo.

    """
    try:
        # Buscamos el reclamo por su ID
        reclamo = sistema.buscar_reclamo_por_id(id_reclamo)
    except Exception as e:
        flash(f"Error: {e}", "danger")
        return redirect(url_for('manejar_reclamos'))

    # Verificación de permisos (un Jefe solo puede editar los de su depto)
    usuario_actual = gestor_login.usuario_actual
    if usuario_actual.rol == 'jefe' and reclamo.departamento != usuario_actual.departamento:
        flash("Permiso denegado: No puede editar reclamos de otro departamento.", "danger")
        return redirect(url_for('manejar_reclamos'))

    form = FormEditarEstado()

    if form.validate_on_submit():
        # Si el formulario se envió (POST) y es válido
        try:
            nuevo_estado = form.estado.data
            tiempo_res = form.tiempo_resolucion.data

            # --- Validación de Lógica de Negocio ---
            # La consigna dice que el tiempo es OBLIGATORIO si el estado es "en proceso"
            #
            if nuevo_estado == 'en proceso' and not tiempo_res:
                # Si el estado es "en proceso" pero los días están vacíos, es un error.
                flash("Error: Debe asignar un tiempo de resolución (1-15 días) para el estado 'En Proceso'.", "danger")
            else:
                # Si la validación pasa, llamamos al sistema
                sistema.cambiar_estado_reclamo(
                    jefe_departamento=usuario_actual.entidad, # Pasamos la entidad del admin
                    id_reclamo=id_reclamo,
                    nuevo_estado=nuevo_estado,
                    dias_resolucion=tiempo_res if tiempo_res else None # Pasamos None si está vacío
                )
                flash(f"El estado del Reclamo #{id_reclamo} ha sido actualizado a '{nuevo_estado}'.", "success")
                return redirect(url_for('manejar_reclamos'))

        except Exception as e:
            flash(f"Error al actualizar el reclamo: {e}", "danger")

    # Si es un GET (primera vez que carga la página)
    # Seteamos el valor actual del estado en el formulario
    form.estado.data = reclamo.estado
    form.tiempo_resolucion.data = reclamo.tiempo_resolucion_asignado

    return render_template("editar_estado.html", reclamo=reclamo, form=form)

@app.route("/derivar_reclamo/<int:id_reclamo>", methods=["GET", "POST"])
@gestor_login.se_requiere_login
# Protegemos esta ruta para que SOLO el Secretario Técnico pueda entrar
@gestor_login.rol_requerido(roles_permitidos=['secretario'])
def derivar_reclamo(id_reclamo):
    """
    Ruta para mostrar y procesar el formulario de derivación de un reclamo.
    Solo accesible por Secretaría Técnica.
    """
    try:
        # Buscamos el reclamo por su ID
        reclamo = sistema.buscar_reclamo_por_id(id_reclamo)
    except Exception as e:
        flash(f"Error: {e}", "danger")
        return redirect(url_for('manejar_reclamos'))

    # 1. Instanciar el formulario
    form = FormDerivarReclamo()
    
    # 2. Definir la lista de departamentos válidos para derivar (excluyendo Secretaría Técnica)
    # Solución simple: Solo incluimos los destinos de trabajo.
    DEP_SECRETARIA_TECNICA = 'secretaría técnica'
    
    # Lista de todos los departamentos (tomada de la lógica de validación de sistema.py)
    todos_los_departamentos = ["secretaría técnica", "soporte informático", "maestranza"]
    
    # Lista filtrada (solo Soporte y Maestranza)
    lista_deps_filtrada = [dep for dep in todos_los_departamentos if dep != DEP_SECRETARIA_TECNICA]
    
    # Crear las opciones para el SelectField (valor, texto visible)
    choices = [(dep, dep.title()) for dep in lista_deps_filtrada]

    # 3. FORZAR LA ACTUALIZACIÓN DE LAS OPCIONES DEL CAMPO
    # ESTA ES LA CLAVE PARA QUE NO APAREZCA 'secretaría técnica'
    form.departamento.choices = choices 
    
    # --- Lógica de POST (validate_on_submit) ---
    if form.validate_on_submit():
        try:
            nuevo_depto = form.departamento.data

            # Verificamos que no lo esté derivando al mismo departamento
            if reclamo.departamento == nuevo_depto:
                flash(f"El reclamo ya pertenece al departamento '{nuevo_depto.title()}'. No se realizaron cambios.", "info")
            else:
                # Llamamos al método del sistema que ya creamos
                sistema.derivar_reclamo(
                    usuario_secretario=gestor_login.usuario_actual.entidad,
                    id_reclamo=id_reclamo,
                    nuevo_departamento=nuevo_depto
                )
                flash(f"Reclamo #{id_reclamo} derivado exitosamente a '{nuevo_depto.title()}'.", "success")

            return redirect(url_for('manejar_reclamos'))

        except Exception as e:
            flash(f"Error al derivar el reclamo: {e}", "danger")

    # Si es un GET (primera vez que carga la página)
    # Seteamos el valor actual del departamento en el formulario (opcional)
    if not form.departamento.data:
        form.departamento.data = reclamo.departamento
        
    return render_template("derivar_reclamo.html", reclamo=reclamo, form=form)

@app.route("/analitica")
@gestor_login.se_requiere_login
@gestor_login.rol_requerido(roles_permitidos=['jefe', 'secretario'])
def analitica():
    """
    Ruta para la Opción 2 del Admin: "Analítica".
    Muestra estadísticas sobre los reclamos y genera el gráfico.
    """
    usuario_actual = gestor_login.usuario_actual
    reclamos_a_procesar = []
    departamento_titulo = ""
    ruta_web_grafico_final = None # Inicializamos la ruta del gráfico

    try:
        # Filtramos los reclamos según el rol (código existente)
        if usuario_actual.rol == 'jefe':
            departamento_titulo = usuario_actual.departamento.title()
            reclamos_a_procesar = repo_reclamos.obtener_todos_por_filtro(
                departamento=usuario_actual.departamento
            )
        elif usuario_actual.rol == 'secretario':
            departamento_titulo = "Todos los Departamentos"
            reclamos_a_procesar = repo_reclamos.obtener_todos()

        # Si no hay reclamos, salimos pronto
        if not reclamos_a_procesar:
            return render_template("analitica.html", 
                                   departamento=departamento_titulo, 
                                   stats_porcentaje={"total": 0}, 
                                   stats_mediana=0, 
                                   stats_palabras=[])

        # Calculamos las estadísticas (código existente)
        generador_stats = GeneradorEstadisticas(reclamos_a_procesar)
        stats_porcentaje = generador_stats.calcular_porcentajes_estado()
        stats_mediana = generador_stats.calcular_mediana_tiempos_resolucion()
        stats_palabras = generador_stats.calcular_palabras_frecuentes(15) # Top 15

        # --- NUEVO: GENERACIÓN DEL GRÁFICO PARA VISUALIZACIÓN EN LA WEB ---
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"grafico_estados_{usuario_actual.rol}_{timestamp}.png"
        # Ruta de guardado físico (dentro de static para que Flask lo sirva)
        ruta_guardado = os.path.join("static", "graficos", nombre_archivo)
        
        # La ruta que pasamos al template debe ser relativa a la carpeta 'static'
        # Convertimos la ruta física a ruta web:
        ruta_web_grafico_final = os.path.join("graficos", nombre_archivo).replace('\\', '/')
        # --- FIN GENERACIÓN GRÁFICO ---


        return render_template("analitica.html",
                               departamento=departamento_titulo,
                               stats_porcentaje=stats_porcentaje,
                               stats_mediana=stats_mediana,
                               stats_palabras=stats_palabras,
                               ruta_grafico=ruta_web_grafico_final) # <-- NUEVO: RUTA DEL GRÁFICO

    except Exception as e:
        flash(f"Error al generar las estadísticas: {e}", "danger")
        return redirect(url_for('panel_principal'))
    

@app.route("/generar_reporte/<string:formato>")
@gestor_login.se_requiere_login
@gestor_login.rol_requerido(roles_permitidos=['jefe', 'secretario'])
def generar_reporte(formato):
    """
    Ruta para la Opción 3 del Admin: "Generar Reporte".
    Genera un archivo HTML o PDF y lo ofrece para descargar.
    """
    usuario_actual = gestor_login.usuario_actual
    reclamos_a_procesar = []
    departamento_titulo = ""
    
    # 1. Obtener los reclamos y calcular estadísticas (código existente)
    if usuario_actual.rol == 'jefe':
        departamento_titulo = usuario_actual.departamento
        reclamos_a_procesar = repo_reclamos.obtener_todos_por_filtro(
            departamento=usuario_actual.departamento
        )
    elif usuario_actual.rol == 'secretario':
        departamento_titulo = "Sistema Completo"
        reclamos_a_procesar = repo_reclamos.obtener_todos()

    # 2. Calcular las estadísticas 
    if usuario_actual.rol == 'jefe':
        departamento_titulo = usuario_actual.departamento
        reclamos_a_procesar = repo_reclamos.obtener_todos_por_filtro(
            departamento=usuario_actual.departamento
        )
    elif usuario_actual.rol == 'secretario':
        departamento_titulo = "Sistema Completo"
        reclamos_a_procesar = repo_reclamos.obtener_todos()

    stats_porcentaje = {"total": 0}
    stats_mediana = 0

    if reclamos_a_procesar:
        generador_stats = GeneradorEstadisticas(reclamos_a_procesar)
        stats_porcentaje = generador_stats.calcular_porcentajes_estado()
        stats_mediana = generador_stats.calcular_mediana_tiempos_resolucion()

    estadisticas_completas = {
        **stats_porcentaje,
        "mediana_tiempos": stats_mediana
    }

    # --- GENERACIÓN DEL GRÁFICO PARA EL REPORTE ---
    timestamp_reporte = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # La ruta de guardado debe ser dentro de la carpeta 'reportes' para que sea accesible por el generador
    nombre_archivo_grafico = f"grafico_estados_{usuario_actual.rol}_{timestamp_reporte}.png"
    ruta_guardado_grafico = os.path.join("reportes", "graficos", nombre_archivo_grafico) 
    

    # 3. Elegir la Estrategia de Reporte
    if formato.lower() == 'html':
        estrategia = ReporteHTML()
    elif formato.lower() == 'pdf':
        estrategia = ReportePDF()
    else:
        flash("Formato de reporte no válido.", "danger")
        return redirect(url_for('panel_principal'))

    # 4. Generar el reporte
    generador = GeneradorReportes(estrategia)
    ruta_archivo_generado = generador.generar_reporte(
        lista_reclamos=reclamos_a_procesar,
        estadisticas=estadisticas_completas,
        departamento=departamento_titulo,
    )

    # 5. Ofrecer el archivo para descargar 
    directorio = os.path.abspath("reportes")
    nombre_archivo = os.path.basename(ruta_archivo_generado)

    return send_from_directory(
        directory=directorio,
        path=nombre_archivo,
        as_attachment=True
    )

@app.route("/ayuda")
@gestor_login.se_requiere_login
@gestor_login.rol_requerido(roles_permitidos=['jefe', 'secretario'])
def ayuda():
    """
    Ruta para la Opción 4 del Admin: "Ayuda".
    Muestra una página estática con un tutorial.

    """
    # Esta ruta solo renderiza la plantilla de ayuda
    return render_template("ayuda.html")

# --- Punto de entrada para ejecutar la aplicación ---
if __name__ == "__main__":
    print("Creando gestor de login...")

    inicializar_personal()
    # debug=True reinicia el servidor automáticamente con cada cambio
    # host='0.0.0.0' permite que sea accesible desde la red local
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False, threaded=False)