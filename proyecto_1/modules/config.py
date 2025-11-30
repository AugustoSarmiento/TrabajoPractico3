# modules/config.py
import os
from flask import Flask

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ResourceWarning)


from flask_session import Session
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

# --- CONFIGURACIÓN DE SESIÓN (Estilo Ejemplos) ---
# Definimos la variable en MAYÚSCULAS en el scope global
SESSION_TYPE = 'filesystem' 
# -------------------------------------------------
RUTA_BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

app = Flask("server", static_folder='static', template_folder='templates')

# --- CARGA DE CONFIGURACIÓN ---
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# Esta línea carga las variables globales en mayúsculas (como SESSION_TYPE)
# en la configuración de la app. Es el método que usan tus ejemplos.
app.config.from_object(__name__) 

app.config["SESSION_FILE_DIR"] = os.path.join(RUTA_BASE, 'flask_session_cache')
app.config["SESSION_PERMANENT"] = False
# --------------------------------

# Inicializa la extensión de sesión DESPUÉS de configurar
Session(app)

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "Por favor, inicie sesión para acceder a esta página."
login_manager.login_view = 'login' 

# Inicializar Flask-Bootstrap
Bootstrap(app)