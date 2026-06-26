from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func
import os
import json
import glob
import shutil
import re
import urllib.parse
import io
import pytesseract
import cv2
import numpy as np
from PIL import Image
import requests
from bs4 import BeautifulSoup
import easyocr
import base64

# ==================== NOTA: NO USAMOS PYZBAR, USAMOS OPENCV PARA QR ====================

app = Flask(__name__)
app.secret_key = 'clave_secreta_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_consultas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración para subir fotos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuración de backups
BACKUP_DIR = 'backups'
MAX_BACKUPS = 10
os.makedirs(BACKUP_DIR, exist_ok=True)

# ==================== CONFIGURACIÓN OCR ====================
# Configurar ruta de Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ==================== FILTROS DE JINJA2 ====================

@app.template_filter('from_json')
def from_json_filter(value):
    """Convierte una cadena JSON en un objeto Python"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

@app.template_filter('to_json')
def to_json_filter(value):
    """Convierte un objeto Python en una cadena JSON"""
    try:
        return json.dumps(value)
    except:
        return '{}'

@app.template_filter('split')
def split_filter(value, delimiter=','):
    """Divide una cadena en una lista usando un delimitador"""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter)]

# ==================== MODELOS ====================
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default='usuario')
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.String(50))

class Persona(db.Model):
    __tablename__ = 'personas'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.String(20))
    genero = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    foto = db.Column(db.String(500))
    fecha_registro = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='ACTIVO')

class Antecedente(db.Model):
    __tablename__ = 'antecedentes'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'))
    delito = db.Column(db.String(100), nullable=False)
    fecha_delito = db.Column(db.String(20))
    lugar = db.Column(db.String(100))
    juzgado = db.Column(db.String(100))
    estado = db.Column(db.String(20))

class OrdenCaptura(db.Model):
    __tablename__ = 'ordenes_captura'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'))
    numero_orden = db.Column(db.String(50), nullable=False)
    monto_deuda = db.Column(db.Float, nullable=False)
    fecha_emision = db.Column(db.String(20), nullable=False)
    fecha_vencimiento = db.Column(db.String(20))
    juzgado = db.Column(db.String(100), nullable=False)
    expediente = db.Column(db.String(50), nullable=True)
    estado = db.Column(db.String(20), default='ACTIVA')
    resultado = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    direccion_ubicacion = db.Column(db.String(300))
    fecha_registro = db.Column(db.String(50))

class AccionOperativa(db.Model):
    __tablename__ = 'acciones_operativas'
    id = db.Column(db.Integer, primary_key=True)
    cod_unidad = db.Column(db.String(20), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    hora_inicio = db.Column(db.String(10), nullable=False)
    hora_fin = db.Column(db.String(10), nullable=False)
    lugar = db.Column(db.String(200), nullable=False)
    accion_realizada = db.Column(db.Text, nullable=False)
    instituciones = db.Column(db.String(200))
    escuadra_1 = db.Column(db.Boolean, default=False)
    escuadra_2 = db.Column(db.Boolean, default=False)
    escuadra_3 = db.Column(db.Boolean, default=False)
    escuadra_4 = db.Column(db.Boolean, default=False)
    mando = db.Column(db.String(100), nullable=False)
    oficiales = db.Column(db.Text, nullable=False)
    personas_abordadas = db.Column(db.Integer, default=0)
    personas_investigadas_oij = db.Column(db.Integer, default=0)
    motos = db.Column(db.Integer, default=0)
    carros = db.Column(db.Integer, default=0)
    armas = db.Column(db.Integer, default=0)
    control_carretera = db.Column(db.Integer, default=0)
    op_inter_institucionales = db.Column(db.Integer, default=0)
    ganado_seguro = db.Column(db.Integer, default=0)
    visitas_comercio = db.Column(db.Integer, default=0)
    paso_escolar = db.Column(db.Integer, default=0)
    notificaciones = db.Column(db.Integer, default=0)
    guardas_seguridad = db.Column(db.Integer, default=0)
    orden_apremio_corporal = db.Column(db.Integer, default=0)
    partes_transito = db.Column(db.Integer, default=0)
    placas_decomisadas = db.Column(db.Integer, default=0)
    informes_policiales = db.Column(db.Integer, default=0)
    incidentes_cerrados = db.Column(db.Integer, default=0)
    vehiculos_incautados = db.Column(db.Integer, default=0)
    puchos_marihuana = db.Column(db.Integer, default=0)
    cigarillos_marihuana = db.Column(db.Integer, default=0)
    gramos_marihuana = db.Column(db.Float, default=0)
    piedras_crack = db.Column(db.Integer, default=0)
    gramos_crack = db.Column(db.Float, default=0)
    puntas_cocaina = db.Column(db.Integer, default=0)
    gramos_cocaina = db.Column(db.Float, default=0)
    armas_fuego = db.Column(db.Integer, default=0)
    armas_blancas = db.Column(db.Integer, default=0)
    dinero_efectivo = db.Column(db.Float, default=0)
    otros_incautaciones = db.Column(db.String(200))
    anotaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.String(50), nullable=False)
    usuario_registro = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='ACTIVA')

# ==================== MODELO DE INCIDENTES ====================
class Incidente(db.Model):
    __tablename__ = 'incidentes'
    id = db.Column(db.Integer, primary_key=True)
    oficial_actuante = db.Column(db.String(100), nullable=False)
    oficial_asistente = db.Column(db.String(100))
    numero_incidente = db.Column(db.String(50), nullable=False)
    tipo_incidente = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    diligencias_policiales = db.Column(db.Text)
    aprehendidos = db.Column(db.Integer, default=0)
    ofendidos = db.Column(db.Integer, default=0)
    testigos = db.Column(db.Integer, default=0)
    personas_interes = db.Column(db.Integer, default=0)
    vehiculos_involucrados = db.Column(db.Integer, default=0)
    decomisos = db.Column(db.Text)
    informe_policial = db.Column(db.Boolean, default=False)
    numero_informe = db.Column(db.String(50))
    acta_decomiso = db.Column(db.Boolean, default=False)
    numero_acta_decomiso = db.Column(db.String(50))
    fecha_incidente = db.Column(db.String(20), nullable=False)
    lugar = db.Column(db.String(200))
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    direccion_ubicacion = db.Column(db.String(500))
    estado = db.Column(db.String(20), default='ACTIVO')
    creado_por = db.Column(db.String(50))
    fecha_registro = db.Column(db.String(50))

# ==================== MODELO DE ÓRDENES JUDICIALES ====================
class OrdenJudicial(db.Model):
    __tablename__ = 'ordenes_judiciales'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'))
    
    despacho = db.Column(db.String(200), nullable=False)
    fecha_emision = db.Column(db.String(20), nullable=False)
    numero_unico = db.Column(db.String(50), nullable=False)
    numero_oficio = db.Column(db.String(50))
    consecutivo_interno = db.Column(db.String(50))
    correo_despacho = db.Column(db.String(100))
    telefono_despacho = db.Column(db.String(20))
    delitos = db.Column(db.String(500))
    
    ofendido_nombre = db.Column(db.String(200))
    ofendido_identificacion = db.Column(db.String(50))
    hay_mas_ofendidos = db.Column(db.Boolean, default=False)
    
    imputado_nombre = db.Column(db.String(200), nullable=False)
    imputado_identificacion = db.Column(db.String(50), nullable=False)
    
    tipo_solicitud = db.Column(db.String(50))
    dejar_orden = db.Column(db.String(50))
    condicion_requerido = db.Column(db.String(50))
    
    tipo_captura = db.Column(db.String(100))
    lugar_captura = db.Column(db.String(300))
    remision_a = db.Column(db.String(200))
    
    nacionalidad = db.Column(db.String(50))
    estado_civil = db.Column(db.String(50))
    genero = db.Column(db.String(20))
    nombre_padre = db.Column(db.String(200))
    nombre_madre = db.Column(db.String(200))
    
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    direccion_ubicacion = db.Column(db.String(500))
    
    estado = db.Column(db.String(20), default='ACTIVA')
    observaciones = db.Column(db.Text)
    
    creado_por = db.Column(db.String(50))
    fecha_registro = db.Column(db.String(50))

# ==================== MODELO DE MACHOTES DE DOCUMENTOS ====================
class MachoteDocumento(db.Model):
    __tablename__ = 'machotes_documentos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo_documento = db.Column(db.String(50), nullable=False)
    categoria = db.Column(db.String(50))
    contenido = db.Column(db.Text, nullable=False)
    variables = db.Column(db.Text)
    estructura = db.Column(db.Text)
    archivo_adjunto = db.Column(db.String(200))
    es_activo = db.Column(db.Boolean, default=True)
    creado_por = db.Column(db.String(50))
    fecha_registro = db.Column(db.String(50))
    ultima_modificacion = db.Column(db.String(50))

# ==================== MODELO DE DOCUMENTOS GENERADOS (HISTORIAL) ====================
class DocumentoGenerado(db.Model):
    __tablename__ = 'documentos_generados'
    id = db.Column(db.Integer, primary_key=True)
    machote_id = db.Column(db.Integer, db.ForeignKey('machotes_documentos.id'), nullable=False)
    titulo = db.Column(db.String(200))
    contenido = db.Column(db.Text, nullable=False)
    variables_utilizadas = db.Column(db.Text)
    generado_por = db.Column(db.String(50))
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    machote = db.relationship('MachoteDocumento', backref='documentos_generados')

# ==================== MODELO DE RESPUESTAS ====================
class RespuestaFormulario(db.Model):
    __tablename__ = 'respuestas_formulario'
    
    id = db.Column(db.Integer, primary_key=True)
    machote_id = db.Column(db.Integer, db.ForeignKey('machotes_documentos.id'), nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('personas.id'), nullable=True)
    titulo = db.Column(db.String(200))
    fecha_respuesta = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_responde = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    
    machote = db.relationship('MachoteDocumento', backref='respuestas')
    persona = db.relationship('Persona', backref='respuestas')


class RespuestaDetalle(db.Model):
    __tablename__ = 'respuestas_detalle'
    
    id = db.Column(db.Integer, primary_key=True)
    respuesta_id = db.Column(db.Integer, db.ForeignKey('respuestas_formulario.id'), nullable=False)
    pregunta_id = db.Column(db.Integer, nullable=False)
    pregunta_titulo = db.Column(db.String(255))
    pregunta_tipo = db.Column(db.String(50))
    respuesta = db.Column(db.Text)
    
    respuesta_formulario = db.relationship('RespuestaFormulario', backref='detalles')

# ==================== NUEVO SISTEMA DE MACHOTES SIMPLIFICADO ====================

class Pregunta(db.Model):
    __tablename__ = 'preguntas'
    id = db.Column(db.Integer, primary_key=True)
    machote_id = db.Column(db.Integer, db.ForeignKey('machotes_documentos.id'), nullable=False)
    orden = db.Column(db.Integer, default=0)
    tipo = db.Column(db.String(50), default='texto')
    titulo = db.Column(db.String(200), nullable=False)
    variable = db.Column(db.String(50), nullable=False)
    opciones = db.Column(db.Text)
    requerido = db.Column(db.Boolean, default=True)
    
    machote = db.relationship('MachoteDocumento', backref='preguntas_simple')


class Respuesta(db.Model):
    __tablename__ = 'respuestas'
    id = db.Column(db.Integer, primary_key=True)
    machote_id = db.Column(db.Integer, db.ForeignKey('machotes_documentos.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.Column(db.String(50))
    datos = db.Column(db.Text)
    
    machote = db.relationship('MachoteDocumento', backref='respuestas_simple')

# ==================== FUNCIONES DE PERMISOS ====================
def tiene_permiso(usuario, permiso_requerido):
    roles_permisos = {
        'admin': ['ver_personas', 'crear_personas', 'editar_personas', 'eliminar_personas',
                  'ver_ordenes', 'crear_ordenes', 'editar_ordenes', 'eliminar_ordenes',
                  'ver_antecedentes', 'crear_antecedentes', 'editar_antecedentes', 'eliminar_antecedentes',
                  'ver_estadisticas', 'ver_alertas', 'gestionar_usuarios',
                  'ver_acciones', 'crear_acciones', 'editar_acciones', 'eliminar_acciones',
                  'gestionar_backups',
                  'ver_incidentes', 'crear_incidentes', 'editar_incidentes', 'eliminar_incidentes',
                  'ver_ordenes_judiciales', 'crear_ordenes_judiciales', 'editar_ordenes_judiciales', 'eliminar_ordenes_judiciales',
                  'ver_machotes', 'crear_machotes', 'editar_machotes', 'eliminar_machotes',
                  'ver_respuestas', 'crear_respuestas', 'eliminar_respuestas',
                  'ver_historial_machotes'],
        'supervisor': ['ver_personas', 'crear_personas', 'editar_personas',
                       'ver_ordenes', 'crear_ordenes', 'editar_ordenes',
                       'ver_antecedentes', 'crear_antecedentes', 'editar_antecedentes',
                       'ver_estadisticas', 'ver_alertas',
                       'ver_acciones', 'crear_acciones', 'editar_acciones',
                       'ver_incidentes', 'crear_incidentes', 'editar_incidentes',
                       'ver_ordenes_judiciales', 'crear_ordenes_judiciales', 'editar_ordenes_judiciales',
                       'ver_machotes', 'crear_machotes', 'editar_machotes',
                       'ver_respuestas', 'crear_respuestas',
                       'ver_historial_machotes'],
        'agente': ['ver_personas', 'crear_personas', 'ver_ordenes', 'crear_ordenes',
                   'ver_antecedentes', 'ver_estadisticas', 'ver_alertas',
                   'ver_acciones',
                   'ver_incidentes', 'crear_incidentes',
                   'ver_ordenes_judiciales', 'crear_ordenes_judiciales',
                   'ver_machotes',
                   'ver_respuestas', 'crear_respuestas'],
        'usuario': ['ver_personas', 'ver_ordenes', 'ver_estadisticas', 'ver_alertas',
                    'ver_acciones',
                    'ver_incidentes',
                    'ver_ordenes_judiciales',
                    'ver_machotes',
                    'ver_respuestas']
    }
    return permiso_requerido in roles_permisos.get(usuario.rol, [])

# ==================== DECORADOR DE PERMISOS ====================
def permiso_requerido(permiso):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not tiene_permiso(current_user, permiso):
                flash('No tienes permiso para acceder a esta sección', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== CONTEXTO GLOBAL PARA TEMPLATES ====================
@app.context_processor
def utility_processor():
    def tiene_permiso_template(usuario, permiso):
        if not usuario or not usuario.is_authenticated:
            return False
        return tiene_permiso(usuario, permiso)
    return dict(tiene_permiso=tiene_permiso_template)

# ==================== FUNCIONES ====================
def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)

Usuario.set_password = set_password
Usuario.check_password = check_password

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verificar_vencimientos():
    hoy = datetime.now().date()
    ordenes = OrdenCaptura.query.filter_by(estado='ACTIVA').all()
    actualizadas = 0
    for o in ordenes:
        if o.fecha_vencimiento:
            try:
                if datetime.strptime(o.fecha_vencimiento, '%Y-%m-%d').date() < hoy:
                    o.estado = 'VENCIDA'
                    if o.observaciones:
                        o.observaciones += f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Orden vencida automáticamente"
                    else:
                        o.observaciones = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Orden vencida automáticamente"
                    actualizadas += 1
            except:
                pass
    if actualizadas > 0:
        db.session.commit()
    return actualizadas

def obtener_alertas():
    hoy = datetime.now().date()
    alertas = []
    for o in OrdenCaptura.query.filter_by(estado='ACTIVA').all():
        if o.fecha_vencimiento:
            try:
                fecha = datetime.strptime(o.fecha_vencimiento, '%Y-%m-%d').date()
                dias = (fecha - hoy).days
                if 0 <= dias <= 7:
                    p = Persona.query.get(o.persona_id)
                    if p:
                        alertas.append({
                            'numero_orden': o.numero_orden,
                            'persona_nombre': p.nombre,
                            'persona_cedula': p.cedula,
                            'dias_restantes': dias,
                            'persona_id': p.id
                        })
            except:
                pass
    return alertas

# ==================== FUNCIÓN PARA CONSULTAR TSE ====================

def obtener_datos_tse(cedula):
    """
    Obtiene los datos de una persona desde el TSE usando la cédula
    """
    try:
        # URL de consulta del TSE
        url = f"https://www.tse.go.cr/consulta/cedula/{cedula}"
        
        print(f"🔍 Consultando TSE: {url}")
        
        # Hacer la solicitud
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error al consultar TSE: {response.status_code}")
            return None
        
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar los datos en la página
        datos = {
            'cedula': cedula,
            'nombre': None,
            'primer_apellido': None,
            'segundo_apellido': None,
            'fecha_nacimiento': None,
            'fecha_vencimiento': None,
            'conocido_como': None
        }
        
        # Buscar tablas con los datos
        tablas = soup.find_all('table')
        for tabla in tablas:
            filas = tabla.find_all('tr')
            for fila in filas:
                celdas = fila.find_all('td')
                if len(celdas) >= 2:
                    etiqueta = celdas[0].get_text(strip=True)
                    valor = celdas[1].get_text(strip=True)
                    
                    if 'Nombre' in etiqueta:
                        datos['nombre'] = valor.title()
                    elif 'Primer Apellido' in etiqueta:
                        datos['primer_apellido'] = valor.title()
                    elif 'Segundo Apellido' in etiqueta:
                        datos['segundo_apellido'] = valor.title()
                    elif 'Fecha de Nacimiento' in etiqueta:
                        try:
                            fecha = datetime.strptime(valor, '%d/%m/%Y')
                            datos['fecha_nacimiento'] = fecha.strftime('%Y-%m-%d')
                        except:
                            datos['fecha_nacimiento'] = valor
                    elif 'Fecha de Vencimiento' in etiqueta:
                        try:
                            fecha = datetime.strptime(valor, '%d/%m/%Y')
                            datos['fecha_vencimiento'] = fecha.strftime('%Y-%m-%d')
                        except:
                            datos['fecha_vencimiento'] = valor
                    elif 'Conocido Como' in etiqueta:
                        datos['conocido_como'] = valor
        
        # Si no se encontraron datos en tablas, buscar en divs
        if not datos['nombre']:
            divs = soup.find_all('div', class_='campo')
            for div in divs:
                etiqueta = div.find('label')
                valor = div.find('span')
                if etiqueta and valor:
                    etiqueta_text = etiqueta.get_text(strip=True)
                    valor_text = valor.get_text(strip=True)
                    
                    if 'Nombre' in etiqueta_text:
                        datos['nombre'] = valor_text.title()
                    elif 'Primer Apellido' in etiqueta_text:
                        datos['primer_apellido'] = valor_text.title()
                    elif 'Segundo Apellido' in etiqueta_text:
                        datos['segundo_apellido'] = valor_text.title()
                    elif 'Fecha de Nacimiento' in etiqueta_text:
                        datos['fecha_nacimiento'] = valor_text
                    elif 'Fecha de Vencimiento' in etiqueta_text:
                        datos['fecha_vencimiento'] = valor_text
        
        # Si encontramos nombre, asumimos que los datos son válidos
        if datos['nombre']:
            print(f"✅ Datos obtenidos del TSE: {datos}")
            return datos
        else:
            print("❌ No se encontraron datos en la página del TSE")
            return None
        
    except Exception as e:
        print(f"❌ Error al consultar TSE: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==================== FUNCIONES QR Y MRZ (CON OPENCV - NO PYZBAR) ====================

def decodificar_mrz(texto_mrz):
    """Decodifica el MRZ de una cédula costarricense"""
    datos = {
        'cedula': None,
        'nombre': None,
        'primer_apellido': None,
        'segundo_apellido': None,
        'fecha_nacimiento': None,
        'genero': None,
        'nacionalidad': None,
        'fecha_vencimiento': None,
        'tipo_documento': None
    }
    
    try:
        # Limpiar texto
        lineas = [linea.strip() for linea in texto_mrz.split('\n') if linea.strip()]
        
        if len(lineas) < 3:
            print("❌ MRZ incompleto (menos de 3 líneas)")
            return datos
        
        linea1 = lineas[0]
        linea2 = lineas[1] if len(lineas) > 1 else ''
        linea3 = lineas[2] if len(lineas) > 2 else ''
        
        print(f"📄 MRZ línea 1: {linea1}")
        if linea2:
            print(f"📄 MRZ línea 2: {linea2}")
        if linea3:
            print(f"📄 MRZ línea 3: {linea3}")
        
        # Extraer cédula
        match_cedula = re.search(r'IDCRI(\d{10})', linea1)
        if match_cedula:
            cedula = match_cedula.group(1)
            datos['cedula'] = f"{cedula[0]}-{cedula[1:5]}-{cedula[5:]}"
            print(f"✅ Cédula desde MRZ: {datos['cedula']}")
        
        # Extraer número de documento
        match_doc = re.search(r'<C(\d{8})', linea1)
        if match_doc:
            datos['tipo_documento'] = f"C{match_doc.group(1)}"
            print(f"✅ Documento: {datos['tipo_documento']}")
        
        # Extraer fecha de nacimiento
        if linea2:
            match_fecha = re.search(r'^(\d{6})', linea2)
            if match_fecha:
                fecha_raw = match_fecha.group(1)
                dia = fecha_raw[4:6]
                mes = fecha_raw[2:4]
                año = fecha_raw[0:2]
                año_completo = f"19{año}" if int(año) > 50 else f"20{año}"
                datos['fecha_nacimiento'] = f"{año_completo}-{mes}-{dia}"
                print(f"✅ Fecha nacimiento desde MRZ: {datos['fecha_nacimiento']}")
            
            # Extraer fecha de vencimiento
            match_venc = re.search(r'(\d{6})CR1', linea2)
            if match_venc:
                fecha_raw = match_venc.group(1)
                dia = fecha_raw[4:6]
                mes = fecha_raw[2:4]
                año = fecha_raw[0:2]
                año_completo = f"20{año}" if int(año) < 50 else f"19{año}"
                datos['fecha_vencimiento'] = f"{año_completo}-{mes}-{dia}"
                print(f"✅ Vencimiento desde MRZ: {datos['fecha_vencimiento']}")
        
        # Extraer nombre y apellidos
        if linea3:
            partes = linea3.split('<<')
            if len(partes) >= 2:
                apellidos = partes[0].replace('<', ' ').strip().title()
                apellidos_lista = apellidos.split()
                if len(apellidos_lista) >= 2:
                    datos['primer_apellido'] = apellidos_lista[0]
                    datos['segundo_apellido'] = apellidos_lista[1] if len(apellidos_lista) > 1 else ''
                elif len(apellidos_lista) == 1:
                    datos['primer_apellido'] = apellidos_lista[0]
                
                nombre_parte = partes[1].replace('<', ' ').strip().title()
                if nombre_parte:
                    datos['nombre'] = nombre_parte
                    print(f"✅ Nombre desde MRZ: {datos['nombre']}")
                    print(f"✅ Primer apellido: {datos['primer_apellido']}")
                    print(f"✅ Segundo apellido: {datos['segundo_apellido']}")
        
        # Nacionalidad
        if linea2 and 'CR1' in linea2:
            datos['nacionalidad'] = 'Costarricense'
            print(f"✅ Nacionalidad: {datos['nacionalidad']}")
        
        return datos
        
    except Exception as e:
        print(f"❌ Error decodificando MRZ: {e}")
        import traceback
        traceback.print_exc()
        return datos

def extraer_desde_qr_mejorado(imagen_bytes):
    """
    Intenta extraer datos desde el código QR de la cédula usando OpenCV
    y luego consulta el TSE si encuentra una URL
    """
    try:
        # Convertir bytes a imagen numpy
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ No se pudo decodificar la imagen para QR")
            return None
        
        # Guardar imagen original para debug
        cv2.imwrite('debug_qr_original.jpg', img)
        
        # Redimensionar si la imagen es muy grande (más de 2000px)
        height, width = img.shape[:2]
        if height > 2000 or width > 2000:
            factor = min(2000/height, 2000/width)
            nuevo_height = int(height * factor)
            nuevo_width = int(width * factor)
            img = cv2.resize(img, (nuevo_width, nuevo_height), interpolation=cv2.INTER_AREA)
            print(f"📐 Imagen redimensionada de {width}x{height} a {nuevo_width}x{nuevo_height}")
        
        # Probar con diferentes tamaños y rotaciones
        configuraciones = [
            (img, "original"),
        ]
        
        # Agregar versiones escaladas
        height, width = img.shape[:2]
        configuraciones.append((cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC), "escalada_1.5x"))
        configuraciones.append((cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), "escalada_0.5x"))
        
        configuraciones.append((cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE), "rotada_90"))
        configuraciones.append((cv2.rotate(img, cv2.ROTATE_180), "rotada_180"))
        configuraciones.append((cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE), "rotada_270"))
        
        # Crear detector de QR
        detector = cv2.QRCodeDetector()
        
        for img_probar, nombre in configuraciones:
            try:
                # Convertir a grises para mejor detección
                if len(img_probar.shape) == 3:
                    gray = cv2.cvtColor(img_probar, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img_probar
                
                # Mejorar contraste
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray = clahe.apply(gray)
                
                # Binarizar para mejor detección
                _, gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Guardar imagen procesada para debug
                cv2.imwrite(f'debug_qr_{nombre}.jpg', gray)
                
                # Detectar y decodificar QR
                data, bbox, straight_qrcode = detector.detectAndDecode(gray)
                
                if data and len(data) > 10:
                    print(f"📱 Código QR detectado ({nombre}): {data[:100]}...")
                    
                    # Verificar si es una URL del TSE
                    if 'tse.go.cr' in data or 'consulta/cedula' in data:
                        print("✅ Código QR contiene URL del TSE")
                        
                        # Extraer la cédula de la URL
                        match_cedula = re.search(r'consulta/cedula/(\d+)', data)
                        if match_cedula:
                            cedula = match_cedula.group(1)
                            print(f"📋 Cédula extraída de la URL: {cedula}")
                            
                            # Consultar el TSE
                            datos_tse = obtener_datos_tse(cedula)
                            if datos_tse and datos_tse.get('nombre'):
                                return datos_tse
                    
                    # Verificar si es un MRZ de cédula costarricense
                    elif 'IDCRI' in data and '<' in data:
                        print("✅ Código QR válido para cédula costarricense (MRZ)")
                        datos = decodificar_mrz(data)
                        if datos['cedula']:
                            # Si tenemos la cédula, consultar el TSE
                            cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
                            if len(cedula_limpia) >= 9:
                                datos_tse = obtener_datos_tse(cedula_limpia)
                                if datos_tse and datos_tse.get('nombre'):
                                    return datos_tse
                            return datos
                    else:
                        # Intentar extraer datos manualmente del texto
                        print("⚠️ El código QR no parece ser una URL del TSE ni MRZ estándar, intentando extraer datos...")
                        datos = extraer_datos_cedula_mejorado(data)
                        if datos['cedula'] or datos['nombre']:
                            # Si tenemos la cédula, consultar el TSE
                            if datos['cedula']:
                                cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
                                if len(cedula_limpia) >= 9:
                                    datos_tse = obtener_datos_tse(cedula_limpia)
                                    if datos_tse and datos_tse.get('nombre'):
                                        return datos_tse
                            return datos
                            
            except Exception as e:
                print(f"⚠️ Error con configuración {nombre}: {e}")
                continue
        
        print("❌ No se encontraron códigos QR válidos en la imagen")
        return None
        
    except Exception as e:
        print(f"❌ Error procesando QR: {e}")
        import traceback
        traceback.print_exc()
        return None

# ==================== FUNCIONES OCR MEJORADAS ====================

def preprocesar_imagen_mejorado(imagen_bytes):
    """Mejora la calidad de la imagen para OCR con técnicas avanzadas"""
    try:
        # Convertir bytes a imagen numpy
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ Error: No se pudo decodificar la imagen")
            return None
        
        # Redimensionar para mejor OCR
        height, width = img.shape[:2]
        print(f"📐 Dimensiones originales: {width}x{height}")
        
        # Si la imagen es muy grande, reducirla
        if height > 3000 or width > 3000:
            factor = min(2000/height, 2000/width)
            nuevo_height = int(height * factor)
            nuevo_width = int(width * factor)
            img = cv2.resize(img, (nuevo_width, nuevo_height), interpolation=cv2.INTER_AREA)
            print(f"📐 Dimensiones reducidas: {nuevo_width}x{nuevo_height}")
        
        # Convertir a escala de grises
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Reducción de ruido con filtro bilateral
        gris = cv2.bilateralFilter(gris, 9, 75, 75)
        
        # 2. Mejora de contraste con CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8,8))
        gris = clahe.apply(gris)
        
        # 3. Umbralización adaptativa
        thresh = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # 4. Operaciones morfológicas para limpiar
        kernel = np.ones((2,2), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 5. Nitidez
        kernel_sharpen = np.array([[-1,-1,-1],
                                   [-1, 9,-1],
                                   [-1,-1,-1]])
        thresh = cv2.filter2D(thresh, -1, kernel_sharpen)
        
        # Guardar imágenes para debug
        cv2.imwrite('debug_original.jpg', img)
        cv2.imwrite('debug_gris.jpg', gris)
        cv2.imwrite('debug_umbral.jpg', thresh)
        
        print("✅ Imagen preprocesada correctamente")
        return thresh
        
    except Exception as e:
        print(f"❌ Error preprocesando imagen: {e}")
        import traceback
        traceback.print_exc()
        return None

def extraer_texto_imagen_mejorado(imagen_bytes):
    """Extrae texto de una imagen usando OCR con múltiples configuraciones"""
    try:
        img_procesada = preprocesar_imagen_mejorado(imagen_bytes)
        if img_procesada is None:
            return ""
        
        # Lista de configuraciones a probar
        configuraciones = [
            ('--psm 4 -l spa', 'PSM 4 (bloques de texto)'),
            ('--psm 6 -l spa', 'PSM 6 (texto uniforme)'),
            ('--psm 3 -l spa', 'PSM 3 (automático)'),
            ('--psm 11 -l spa', 'PSM 11 (texto disperso)'),
            ('--psm 4 -l spa+eng', 'PSM 4 (español+inglés)'),
            ('--psm 6 -l spa+eng', 'PSM 6 (español+inglés)'),
        ]
        
        mejor_texto = ""
        mejor_longitud = 0
        
        for config, nombre in configuraciones:
            try:
                print(f"🔍 Probando configuración: {nombre}")
                texto = pytesseract.image_to_string(img_procesada, config=config)
                texto = texto.strip()
                
                if texto:
                    # Limpiar caracteres extraños
                    texto_limpio = re.sub(r'[^A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s\-\.\,:]', ' ', texto)
                    texto_limpio = ' '.join(texto_limpio.split())
                    
                    if len(texto_limpio) > mejor_longitud and len(texto_limpio) > 10:
                        mejor_texto = texto_limpio
                        mejor_longitud = len(texto_limpio)
                        print(f"✅ {nombre} - {len(texto_limpio)} caracteres")
                        
                        # Si encontramos texto de buena calidad, usar esta configuración
                        if len(texto_limpio) > 50 and any(c.isalpha() for c in texto_limpio):
                            print(f"✅ Usando configuración: {nombre}")
                            print(f"📄 Muestra: {texto_limpio[:200]}...")
                            return texto_limpio
                            
            except Exception as e:
                print(f"⚠️ Error con {nombre}: {e}")
                continue
        
        # Si no se encontró buen texto, usar el mejor encontrado
        if mejor_texto:
            print(f"📄 Usando mejor texto encontrado ({mejor_longitud} caracteres)")
            return mejor_texto
        
        # Fallback: intentar con configuraciones básicas
        print("⚠️ Intentando con configuraciones básicas...")
        try:
            texto = pytesseract.image_to_string(img_procesada, lang='spa')
            return texto.strip()
        except:
            try:
                texto = pytesseract.image_to_string(img_procesada)
                return texto.strip()
            except:
                return ""
        
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        import traceback
        traceback.print_exc()
        return ""

def extraer_datos_cedula_mejorado(texto):
    """Extrae los datos de una cédula costarricense desde texto OCR mejorado"""
    datos = {
        'cedula': None,
        'nombre': None,
        'primer_apellido': None,
        'segundo_apellido': None,
        'fecha_nacimiento': None,
        'genero': None,
        'nacionalidad': None
    }
    
    print(f"\n📝 Procesando texto: {texto[:200]}...")
    
    # Limpiar texto
    texto = texto.replace('|', 'I').replace('¡', 'i').replace('!', 'I')
    texto = texto.replace('0', 'O').replace('1', 'I')  # Correcciones comunes
    
    # Dividir en líneas
    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
    print(f"📄 Líneas encontradas: {len(lineas)}")
    
    # 1. BUSCAR CÉDULA (más importante)
    # Patrones para cédula costarricense
    patrones_cedula = [
        # Formato 1-1111-1111
        r'\b(\d{1,2})[-]?(\d{4})[-]?(\d{4})\b',
        # Cédula: 1-1111-1111
        r'(?:CÉDULA|CEDULA|IDENTIFICACIÓN|IDENTIFICACION)[\s:]*(\d{1,2}[-]?\d{4}[-]?\d{4})',
        # Número suelto de 9 dígitos
        r'\b(\d{9})\b',
    ]
    
    for patron in patrones_cedula:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3:
                # Formato 1-1111-1111
                cedula_raw = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            elif len(match.groups()) == 1:
                # Cédula con etiqueta
                cedula_raw = match.group(1)
            else:
                cedula_raw = match.group(0)
            
            # Limpiar cédula (solo números y guiones)
            cedula_limpia = re.sub(r'[^\d-]', '', cedula_raw)
            
            # Verificar que sea una cédula válida (9-10 dígitos)
            digitos = re.sub(r'[^0-9]', '', cedula_limpia)
            if len(digitos) >= 8 and len(digitos) <= 10:
                datos['cedula'] = cedula_limpia
                print(f"✅ Cédula encontrada: {datos['cedula']}")
                break
    
    # 2. BUSCAR NOMBRE COMPLETO
    # Buscar líneas que contengan el nombre (3 palabras o más, solo letras)
    for i, linea in enumerate(lineas):
        # Limpiar línea
        linea_limpia = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', linea).strip()
        
        # Verificar que sea un nombre válido (solo letras, 3+ palabras, longitud razonable)
        palabras = linea_limpia.split()
        if len(palabras) >= 3 and len(linea_limpia) > 10 and len(linea_limpia) < 100:
            # Verificar que no sea una etiqueta
            if not any(etiqueta in linea_limpia.upper() for etiqueta in ['CÉDULA', 'CEDULA', 'FECHA', 'NACIMIENTO']):
                # Verificar que tenga al menos 3 palabras
                if len(palabras) >= 3:
                    datos['nombre'] = linea_limpia.title()
                    datos['primer_apellido'] = palabras[-2].title()
                    datos['segundo_apellido'] = palabras[-1].title()
                    print(f"✅ Nombre encontrado: {datos['nombre']}")
                    print(f"✅ Primer apellido: {datos['primer_apellido']}")
                    print(f"✅ Segundo apellido: {datos['segundo_apellido']}")
                    break
    
    # Si no se encontró nombre completo, buscar NOMBRE:
    if not datos['nombre']:
        for patron in [
            r'NOMBRE:?\s*([A-ZÁÉÍÓÚÑ\s]{3,50})',
            r'NOMBRE:?\s*([A-ZÁÉÍÓÚÑ\s]+?)(?:\n|$|,)',
        ]:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
                if len(nombre) > 5 and len(nombre) < 80:
                    datos['nombre'] = nombre.title()
                    # Intentar extraer apellidos del nombre
                    partes = nombre.split()
                    if len(partes) >= 3:
                        datos['primer_apellido'] = partes[-2].title()
                        datos['segundo_apellido'] = partes[-1].title()
                    print(f"✅ Nombre encontrado (patrón): {datos['nombre']}")
                    break
    
    # 3. BUSCAR FECHA DE NACIMIENTO
    patrones_fecha = [
        r'(?:FECHA DE NACIMIENTO|FECHA NAC|NACIMIENTO)[\s:]*(\d{2})[/-](\d{2})[/-](\d{4})',
        r'(\d{2})[/-](\d{2})[/-](\d{4})',
    ]
    
    for patron in patrones_fecha:
        matches = re.findall(patron, texto, re.IGNORECASE)
        for match in matches:
            if len(match) == 3:
                dia, mes, año = match
                try:
                    if int(dia) <= 31 and int(mes) <= 12 and 1900 < int(año) < 2100:
                        datos['fecha_nacimiento'] = f"{año}-{mes}-{dia}"
                        print(f"✅ Fecha nacimiento: {datos['fecha_nacimiento']}")
                        break
                except:
                    continue
        if datos['fecha_nacimiento']:
            break
    
    # 4. BUSCAR GÉNERO
    texto_upper = texto.upper()
    if 'FEMENINO' in texto_upper or 'MUJER' in texto_upper:
        datos['genero'] = 'Femenino'
        print(f"✅ Género: Femenino")
    elif 'MASCULINO' in texto_upper or 'HOMBRE' in texto_upper:
        datos['genero'] = 'Masculino'
        print(f"✅ Género: Masculino")
    
    # 5. BUSCAR NACIONALIDAD
    if 'COSTA RICA' in texto_upper or 'COSTARRICENSE' in texto_upper:
        datos['nacionalidad'] = 'Costarricense'
        print(f"✅ Nacionalidad: Costarricense")
    
    # Mostrar resumen
    print(f"\n📊 Resumen de datos extraídos:")
    print(f"  Cédula: {datos['cedula']}")
    print(f"  Nombre: {datos['nombre']}")
    print(f"  1er Apellido: {datos['primer_apellido']}")
    print(f"  2do Apellido: {datos['segundo_apellido']}")
    print(f"  Fecha Nac: {datos['fecha_nacimiento']}")
    print(f"  Género: {datos['genero']}")
    print(f"  Nacionalidad: {datos['nacionalidad']}")
    
    return datos

# ==================== FUNCIONES EASYOCR MEJORADAS ====================

# Variable global para el lector de EasyOCR (se inicializa una sola vez)
_lector_easyocr = None

def inicializar_lector_easyocr():
    """Inicializa el lector de EasyOCR en el idioma deseado (español)."""
    global _lector_easyocr
    if _lector_easyocr is None:
        print("🔍 Cargando modelo de EasyOCR (esto puede tardar unos segundos la primera vez)...")
        try:
            # Intentar con GPU, si fallar usar CPU
            _lector_easyocr = easyocr.Reader(['es', 'en'], gpu=False)
            print("✅ EasyOCR inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando EasyOCR: {e}")
            # Fallback a solo español sin GPU
            _lector_easyocr = easyocr.Reader(['es'], gpu=False)
    return _lector_easyocr

def extraer_datos_cedula_easyocr(texto_lineas):
    """
    Filtra las líneas de texto para encontrar patrones comunes
    como números de identificación o nombres.
    Versión mejorada para cédulas costarricenses.
    """
    datos = {
        'cedula': None,
        'nombre': None,
        'primer_apellido': None,
        'segundo_apellido': None,
        'fecha_nacimiento': None,
        'genero': None,
        'nacionalidad': None
    }
    
    print(f"\n📝 Procesando {len(texto_lineas)} líneas de texto desde EasyOCR...")
    
    # Mostrar todas las líneas para debug
    for i, linea in enumerate(texto_lineas):
        print(f"  Línea {i+1}: {linea}")
    
    # Unir todas las líneas para búsquedas globales
    texto_completo = ' '.join(texto_lineas)
    texto_upper = texto_completo.upper()
    
    # 1. BUSCAR CÉDULA - Priorizar formato 1-0583-0776 (con guiones)
    patrones_cedula = [
        # Formato 1-0583-0776 (con guiones) - capturar 9 o 10 dígitos
        r'\b(\d{1,2})[-.\s]?(\d{4})[-.\s]?(\d{3,4})\b',
        # Cédula con etiqueta
        r'(?:C[EÉ]DULA|CEDULA|IDENTIFICACI[OÓ]N|IDENTIFICACION)[\s:]*(\d{1,2}[-.\s]?\d{4}[-.\s]?\d{3,4})',
        # Números sueltos de 9 o 10 dígitos
        r'\b(\d{9,10})\b',
        # Formato IDCRI (MRZ)
        r'IDCRI(\d{10})',
    ]
    
    cedula_encontrada = False
    for patron in patrones_cedula:
        match = re.search(patron, texto_upper, re.IGNORECASE)
        if match:
            if len(match.groups()) == 3:
                # Formato con guiones: grupo1-grupo2-grupo3
                parte1 = match.group(1)
                parte2 = match.group(2)
                parte3 = match.group(3)
                cedula_raw = f"{parte1}-{parte2}-{parte3}"
            elif len(match.groups()) == 1:
                cedula_raw = match.group(1)
            else:
                cedula_raw = match.group(0)
            
            # Limpiar y validar
            cedula_limpia = re.sub(r'[^\d-]', '', cedula_raw)
            digitos = re.sub(r'[^0-9]', '', cedula_limpia)
            
            # Aceptar 9 o 10 dígitos
            if len(digitos) >= 9 and len(digitos) <= 10:
                # Si tiene 9 dígitos, buscar si hay un número de 10 dígitos en el texto
                if len(digitos) == 9:
                    # Buscar un número de 10 dígitos en el texto
                    match_completo = re.search(r'\b(\d{10})\b', texto_upper)
                    if match_completo:
                        digitos = match_completo.group(1)
                        cedula_limpia = f"{digitos[0]}-{digitos[1:5]}-{digitos[5:]}"
                        print(f"🔍 Cédula completada a 10 dígitos: {cedula_limpia}")
                    else:
                        # Intentar con 9 dígitos
                        cedula_limpia = f"{digitos[0]}-{digitos[1:5]}-{digitos[5:]}"
                datos['cedula'] = cedula_limpia
                print(f"✅ Cédula encontrada: {datos['cedula']}")
                cedula_encontrada = True
                break
    
    # 2. BUSCAR NOMBRE - Priorizar líneas con "Nombre:" o "NOMBRE:"
    nombre_encontrado = False
    for i, linea in enumerate(texto_lineas):
        linea_upper = linea.upper()
        # Buscar patrón "Nombre: JAVIER"
        if 'NOMBRE:' in linea_upper or 'NOMBRE ' in linea_upper:
            # Extraer el nombre después de "Nombre:"
            match = re.search(r'NOMBRE:?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)', linea_upper, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
                if len(nombre) > 2 and len(nombre) < 50:
                    datos['nombre'] = nombre.title()
                    print(f"✅ Nombre encontrado: {datos['nombre']}")
                    nombre_encontrado = True
                    # Intentar extraer apellidos de líneas siguientes
                    for j in range(i + 1, min(i + 3, len(texto_lineas))):
                        linea_siguiente = texto_lineas[j].upper()
                        if '1 APELLIDO' in linea_siguiente or '1ER APELLIDO' in linea_siguiente:
                            match_ap = re.search(r'1[ER]*\.?\s*APELLIDO:?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)', linea_siguiente, re.IGNORECASE)
                            if match_ap:
                                datos['primer_apellido'] = match_ap.group(1).strip().title()
                                print(f"✅ Primer apellido encontrado: {datos['primer_apellido']}")
                        elif '2 APELLIDO' in linea_siguiente or '2DO APELLIDO' in linea_siguiente:
                            match_ap = re.search(r'2[DO]*\.?\s*APELLIDO:?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)', linea_siguiente, re.IGNORECASE)
                            if match_ap:
                                datos['segundo_apellido'] = match_ap.group(1).strip().title()
                                print(f"✅ Segundo apellido encontrado: {datos['segundo_apellido']}")
                    break
    
    # Si no se encontró nombre con "Nombre:", buscar líneas que parezcan nombres
    if not nombre_encontrado:
        for i, linea in enumerate(texto_lineas):
            linea_limpia = re.sub(r'[^A-ZÁÉÍÓÚÑa-záéíóúñ\s]', '', linea).strip()
            palabras = linea_limpia.split()
            
            # Verificar que sea un nombre válido (solo letras, 2-3 palabras)
            if len(palabras) >= 2 and len(palabras) <= 4 and len(linea_limpia) > 5 and len(linea_limpia) < 40:
                # Verificar que no sea una etiqueta conocida
                etiquetas = ['CÉDULA', 'CEDULA', 'FECHA', 'NACIMIENTO', 'GENERO', 'SEXO', 'NACIONALIDAD', 
                            'TRIBUNAL', 'SUPREMO', 'ELECCIONES', 'REPUBLICA', 'COSTA', 'RICA', 'IDENTIDAD']
                if not any(et in linea_upper for et in etiquetas):
                    datos['nombre'] = linea_limpia.title()
                    if len(palabras) >= 3:
                        datos['primer_apellido'] = palabras[-2].title()
                        datos['segundo_apellido'] = palabras[-1].title()
                    elif len(palabras) == 2:
                        datos['primer_apellido'] = palabras[-1].title()
                    print(f"✅ Nombre encontrado (línea): {datos['nombre']}")
                    if datos['primer_apellido']:
                        print(f"✅ Primer apellido: {datos['primer_apellido']}")
                    if datos['segundo_apellido']:
                        print(f"✅ Segundo apellido: {datos['segundo_apellido']}")
                    nombre_encontrado = True
                    break
    
    # 3. BUSCAR APELLIDOS con etiquetas específicas
    if not datos['primer_apellido']:
        for linea in texto_lineas:
            linea_upper = linea.upper()
            # Buscar "1 Apellido: ROJAS" o "1er Apellido: ROJAS"
            if '1 APELLIDO' in linea_upper or '1ER APELLIDO' in linea_upper or '1ER.' in linea_upper:
                match = re.search(r'1[ER]*\.?\s*APELLIDO:?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)', linea_upper, re.IGNORECASE)
                if match:
                    datos['primer_apellido'] = match.group(1).strip().title()
                    print(f"✅ Primer apellido encontrado: {datos['primer_apellido']}")
                    break
    
    if not datos['segundo_apellido']:
        for linea in texto_lineas:
            linea_upper = linea.upper()
            # Buscar "2 Apellido: TORRES" o "2do Apellido: TORRES"
            if '2 APELLIDO' in linea_upper or '2DO APELLIDO' in linea_upper or '2°' in linea_upper:
                match = re.search(r'2[DO]*\.?\s*APELLIDO:?\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s]+)', linea_upper, re.IGNORECASE)
                if match:
                    datos['segundo_apellido'] = match.group(1).strip().title()
                    print(f"✅ Segundo apellido encontrado: {datos['segundo_apellido']}")
                    break
    
    # 4. BUSCAR FECHA DE NACIMIENTO
    patrones_fecha = [
        r'(?:FECHA DE NACIMIENTO|F\.NAC|FNAC|NACIMIENTO)[\s:]*(\d{2})[/.-](\d{2})[/.-](\d{4})',
        r'(?:FECHA DE NACIMIENTO|F\.NAC|FNAC|NACIMIENTO)[\s:]*(\d{2})[/.-](\d{2})[/.-](\d{2})',
        r'(\d{2})[/.-](\d{2})[/.-](\d{4})',
        r'(\d{2})[/.-](\d{2})[/.-](\d{2})',
    ]
    
    for patron in patrones_fecha:
        matches = re.findall(patron, texto_completo)
        for match in matches:
            if len(match) == 3:
                try:
                    dia, mes, año = match
                    if len(año) == 2:
                        año = f"19{año}" if int(año) > 50 else f"20{año}"
                    if int(dia) <= 31 and int(mes) <= 12 and 1900 < int(año) < 2100:
                        datos['fecha_nacimiento'] = f"{año}-{mes}-{dia}"
                        print(f"✅ Fecha nacimiento: {datos['fecha_nacimiento']}")
                        break
                except:
                    continue
        if datos['fecha_nacimiento']:
            break
    
    # 5. BUSCAR GÉNERO
    if 'FEMENINO' in texto_upper or 'MUJER' in texto_upper:
        datos['genero'] = 'Femenino'
        print(f"✅ Género: Femenino")
    elif 'MASCULINO' in texto_upper or 'HOMBRE' in texto_upper:
        datos['genero'] = 'Masculino'
        print(f"✅ Género: Masculino")
    
    # 6. BUSCAR NACIONALIDAD
    if 'COSTA RICA' in texto_upper or 'COSTARRICENSE' in texto_upper:
        datos['nacionalidad'] = 'Costarricense'
        print(f"✅ Nacionalidad: Costarricense")
    
    # 7. SI HAY CÉDULA PERO NO HAY NOMBRE, CONSULTAR TSE
    if datos['cedula'] and not datos['nombre']:
        cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
        if len(cedula_limpia) >= 9:
            print(f"🔍 Consultando TSE para obtener nombre de cédula {cedula_limpia}")
            datos_tse = obtener_datos_tse(cedula_limpia)
            if datos_tse and datos_tse.get('nombre'):
                print("✅ Datos obtenidos del TSE")
                datos.update(datos_tse)
    
    # Mostrar resumen final
    print(f"\n📊 Resumen de datos extraídos por EasyOCR:")
    print(f"  Cédula: {datos['cedula']}")
    print(f"  Nombre: {datos['nombre']}")
    print(f"  1er Apellido: {datos['primer_apellido']}")
    print(f"  2do Apellido: {datos['segundo_apellido']}")
    print(f"  Fecha Nac: {datos['fecha_nacimiento']}")
    print(f"  Género: {datos['genero']}")
    print(f"  Nacionalidad: {datos['nacionalidad']}")
    
    return datos

def extraer_texto_easyocr(imagen_bytes):
    """
    Extrae texto de una imagen usando EasyOCR.
    """
    try:
        # Convertir bytes a imagen numpy
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("❌ Error: No se pudo decodificar la imagen")
            return ""
        
        # Redimensionar si la imagen es muy grande
        height, width = img.shape[:2]
        if height > 3000 or width > 3000:
            factor = min(2000/height, 2000/width)
            nuevo_height = int(height * factor)
            nuevo_width = int(width * factor)
            img = cv2.resize(img, (nuevo_width, nuevo_height), interpolation=cv2.INTER_AREA)
            print(f"📐 Imagen redimensionada a {nuevo_width}x{nuevo_height}")
        
        # Convertir a grises para mejor OCR
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Mejorar contraste con CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gris = clahe.apply(gris)
        
        # Guardar imagen procesada para debug
        cv2.imwrite('debug_easyocr.jpg', gris)
        
        # Inicializar EasyOCR
        lector = inicializar_lector_easyocr()
        
        # Extraer texto con EasyOCR
        print("🔍 Extrayendo texto con EasyOCR...")
        resultados = lector.readtext(gris, detail=0, paragraph=False)
        
        # Unir resultados en un texto
        texto_completo = '\n'.join(resultados)
        print(f"✅ EasyOCR extrajo {len(resultados)} líneas de texto")
        
        return texto_completo
        
    except Exception as e:
        print(f"❌ Error en EasyOCR: {e}")
        import traceback
        traceback.print_exc()
        return ""

def procesar_ocr_easyocr(imagen_bytes):
    """
    Procesa una imagen usando EasyOCR y extrae datos estructurados.
    """
    try:
        # Extraer texto con EasyOCR
        texto = extraer_texto_easyocr(imagen_bytes)
        
        if not texto or len(texto.strip()) < 5:
            print("❌ No se pudo extraer texto con EasyOCR")
            return "", {}
        
        # Dividir en líneas
        lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
        
        print(f"\n📄 Texto extraído por EasyOCR:")
        print("-" * 60)
        for i, linea in enumerate(lineas[:20]):  # Mostrar primeras 20 líneas
            print(f"{i+1}: {linea}")
        if len(lineas) > 20:
            print(f"... y {len(lineas) - 20} líneas más")
        print("-" * 60)
        
        # Extraer datos estructurados
        datos = extraer_datos_cedula_easyocr(lineas)
        
        return texto, datos
        
    except Exception as e:
        print(f"❌ Error en procesar_ocr_easyocr: {e}")
        import traceback
        traceback.print_exc()
        return "", {}

# ==================== FUNCIONES PARA REPORTES CON ESCUDO ====================

def get_imagen_base64(ruta):
    """Convierte una imagen a base64 para incrustar en HTML"""
    try:
        # Verificar si el archivo existe
        if not os.path.exists(ruta):
            print(f"⚠️ Imagen no encontrada: {ruta}")
            return ""
        with open(ruta, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"⚠️ Error al leer imagen: {e}")
        return ""

def generar_header_reporte(nombre_mes, año):
    """Genera el encabezado HTML con el escudo de la Fuerza Pública"""
    imagen_base64 = get_imagen_base64('static/img/escudo_fuerza_publica.png')
    
    if imagen_base64:
        img_tag = f'<img src="data:image/png;base64,{imagen_base64}" alt="Escudo Fuerza Pública" style="height: 70px; width: auto; margin-right: 20px;">'
    else:
        # Si no se encuentra la imagen, usar un ícono de fallback
        img_tag = '<div style="width: 70px; height: 70px; background: #1a2236; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #fbbf24; margin-right: 20px;"><span style="font-size: 28px; color: #fbbf24;">🛡️</span></div>'
    
    return f"""
    <div style="display: flex; align-items: center; border-bottom: 3px solid #fbbf24; padding-bottom: 15px; margin-bottom: 20px;">
        {img_tag}
        <div style="flex: 1;">
            <h1 style="color: #1f2937; font-size: 22px; margin: 0;">Sistema de Consultas</h1>
            <p style="color: #fbbf24; font-weight: 600; font-size: 14px; margin: 0; text-transform: uppercase;">Fuerza Pública de Costa Rica</p>
            <p style="color: #6b7280; font-size: 12px; margin: 4px 0 0 0;">{nombre_mes} {año}</p>
        </div>
    </div>
    """

# ==================== CREAR BASE DE DATOS ====================
with app.app_context():
    import sqlite3
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(machotes_documentos)")
        columnas = [col[1] for col in cursor.fetchall()]
        if 'estructura' not in columnas:
            print("⚠️ Agregando columna 'estructura' a machotes_documentos...")
            cursor.execute("ALTER TABLE machotes_documentos ADD COLUMN estructura TEXT")
            conn.commit()
            print("✅ Columna 'estructura' agregada")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='respuestas_formulario'")
        if not cursor.fetchone():
            print("⚠️ Creando tablas de respuestas...")
            cursor.execute('''
            CREATE TABLE respuestas_formulario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machote_id INTEGER NOT NULL,
                persona_id INTEGER,
                titulo TEXT,
                fecha_respuesta DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario_responde TEXT,
                ip_address TEXT,
                FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id),
                FOREIGN KEY (persona_id) REFERENCES personas(id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE respuestas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                respuesta_id INTEGER NOT NULL,
                pregunta_id INTEGER NOT NULL,
                pregunta_titulo TEXT,
                pregunta_tipo TEXT,
                respuesta TEXT,
                FOREIGN KEY (respuesta_id) REFERENCES respuestas_formulario(id)
            )
            ''')
            conn.commit()
            print("✅ Tablas de respuestas creadas")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documentos_generados'")
        if not cursor.fetchone():
            print("⚠️ Creando tabla de documentos generados...")
            cursor.execute('''
            CREATE TABLE documentos_generados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machote_id INTEGER NOT NULL,
                titulo TEXT,
                contenido TEXT NOT NULL,
                variables_utilizadas TEXT,
                generado_por TEXT,
                fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id)
            )
            ''')
            conn.commit()
            print("✅ Tabla de documentos generados creada")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preguntas'")
        if not cursor.fetchone():
            print("⚠️ Creando tablas del nuevo sistema...")
            cursor.execute('''
            CREATE TABLE preguntas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machote_id INTEGER NOT NULL,
                orden INTEGER DEFAULT 0,
                tipo TEXT DEFAULT 'texto',
                titulo TEXT NOT NULL,
                variable TEXT NOT NULL,
                opciones TEXT,
                requerido BOOLEAN DEFAULT 1,
                FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE respuestas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machote_id INTEGER NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT,
                datos TEXT,
                FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id)
            )
            ''')
            conn.commit()
            print("✅ Tablas del nuevo sistema creadas")
        else:
            print("✅ Tablas del nuevo sistema ya existen")
        
        conn.close()
    except Exception as e:
        print(f"⚠️ Error al verificar/crear tablas: {e}")
    
    db.create_all()
    
    usuarios_default = [
        ('admin', 'admin@test.com', 'admin123', 'admin'),
        ('supervisor', 'supervisor@test.com', 'super123', 'supervisor'),
        ('agente', 'agente@test.com', 'agente123', 'agente'),
        ('operador', 'operador@test.com', 'oper123', 'usuario'),
    ]
    
    for username, email, password, rol in usuarios_default:
        if not Usuario.query.filter_by(username=username).first():
            user = Usuario(
                username=username,
                email=email,
                rol=rol,
                activo=True,
                fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            user.set_password(password)
            db.session.add(user)
            print(f"✅ Usuario {username} creado")
    db.session.commit()
    print("✅ Todos los usuarios creados")

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ==================== RUTAS PRINCIPALES ====================
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.activo:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/acceso-remoto')
@login_required
@permiso_requerido('ver_estadisticas')
def acesso_remoto():
    return render_template('acceso_remoto.html')

@app.route('/personas')
@login_required
@permiso_requerido('ver_personas')
def personas():
    return render_template('personas.html')

@app.route('/ordenes')
@login_required
@permiso_requerido('ver_ordenes')
def ordenes():
    verificar_vencimientos()
    return render_template('ordenes.html')

@app.route('/estadisticas')
@login_required
@permiso_requerido('ver_estadisticas')
def estadisticas():
    return render_template('estadisticas.html')

@app.route('/alertas')
@login_required
@permiso_requerido('ver_alertas')
def alertas():
    return render_template('alertas.html')

@app.route('/usuarios')
@login_required
@permiso_requerido('gestionar_usuarios')
def usuarios():
    return render_template('usuarios.html')

@app.route('/ficha/<int:id>')
@login_required
@permiso_requerido('ver_personas')
def ficha(id):
    persona = Persona.query.get_or_404(id)
    antecedentes = Antecedente.query.filter_by(persona_id=id).all()
    ordenes = OrdenCaptura.query.filter_by(persona_id=id).all()
    ordenes_judiciales = OrdenJudicial.query.filter_by(persona_id=id).all()
    return render_template('ficha.html', 
                           persona=persona, 
                           antecedentes=antecedentes, 
                           ordenes=ordenes,
                           ordenes_judiciales=ordenes_judiciales)

# ==================== RUTAS ACCIONES OPERATIVAS ====================
@app.route('/acciones_operativas')
@login_required
@permiso_requerido('ver_acciones')
def acciones_operativas():
    return render_template('acciones_operativas.html')

@app.route('/accion_operativa/nueva')
@login_required
@permiso_requerido('crear_acciones')
def nueva_accion_operativa():
    return render_template('nueva_accion_operativa.html')

@app.route('/accion_operativa/<int:id>')
@login_required
@permiso_requerido('ver_acciones')
def ver_accion_operativa(id):
    accion = AccionOperativa.query.get_or_404(id)
    return render_template('ver_accion_operativa.html', accion=accion)

@app.route('/accion_operativa/editar/<int:id>')
@login_required
@permiso_requerido('editar_acciones')
def editar_accion_operativa(id):
    accion = AccionOperativa.query.get_or_404(id)
    return render_template('nueva_accion_operativa.html', accion=accion)

# ==================== RUTAS BACKUPS ====================
@app.route('/backups')
@login_required
@permiso_requerido('gestionar_backups')
def backups_page():
    return render_template('backups.html')


# ==================== RUTAS API BACKUPS ====================
@app.route('/api/backups')
@login_required
@permiso_requerido('gestionar_backups')
def api_listar_backups():
    """Lista todos los backups disponibles"""
    try:
        backup_files = []
        if os.path.exists(BACKUP_DIR):
            for file in os.listdir(BACKUP_DIR):
                if file.endswith('.db'):
                    file_path = os.path.join(BACKUP_DIR, file)
                    stat = os.stat(file_path)
                    tamaño_kb = stat.st_size / 1024
                    
                    # Extraer fecha del nombre del archivo
                    fecha_humana = file
                    try:
                        # Formato: backup_YYYY-MM-DD_HH-MM-SS.db
                        if file.startswith('backup_') and file.endswith('.db'):
                            fecha_str = file.replace('backup_', '').replace('.db', '')
                            fecha_humana = fecha_str.replace('_', ' ').replace('-', ':').replace(':', '-', 2)
                    except:
                        pass
                    
                    backup_files.append({
                        'nombre': file,
                        'tamaño_kb': round(tamaño_kb, 2),
                        'fecha_humana': fecha_humana,
                        'fecha_modificacion': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # Ordenar por fecha de modificación (más reciente primero)
        backup_files.sort(key=lambda x: x['fecha_modificacion'], reverse=True)
        
        return jsonify(backup_files)
    except Exception as e:
        print(f"❌ Error en api_listar_backups: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/backups/crear', methods=['POST'])
@login_required
@permiso_requerido('gestionar_backups')
def api_crear_backup():
    """Crea un nuevo backup de la base de datos"""
    try:
        # Crear directorio de backups si no existe
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_name = f'backup_{timestamp}.db'
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Ruta de la base de datos actual
        db_path = 'sistema_consultas.db'
        
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': 'Base de datos no encontrada'}), 404
        
        # Crear copia
        shutil.copy2(db_path, backup_path)
        
        # Verificar que se creó correctamente
        if os.path.exists(backup_path):
            size = os.path.getsize(backup_path)
            
            # Limpiar backups antiguos
            limpiar_backups_antiguos()
            
            return jsonify({
                'success': True,
                'message': f'Backup creado correctamente: {backup_name}',
                'nombre': backup_name,
                'tamaño_kb': round(size / 1024, 2)
            })
        else:
            return jsonify({'success': False, 'error': 'Error al crear el backup'}), 500
            
    except Exception as e:
        print(f"❌ Error en api_crear_backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backups/restaurar', methods=['POST'])
@login_required
@permiso_requerido('gestionar_backups')
def api_restaurar_backup():
    """Restaura un backup seleccionado"""
    try:
        data = request.json
        nombre = data.get('nombre')
        
        if not nombre:
            return jsonify({'success': False, 'error': 'Nombre del backup requerido'}), 400
        
        # Verificar que existe
        backup_path = os.path.join(BACKUP_DIR, nombre)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup no encontrado'}), 404
        
        # Crear backup del estado actual antes de restaurar
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        pre_restore_name = f'pre_restore_{timestamp}.db'
        pre_restore_path = os.path.join(BACKUP_DIR, pre_restore_name)
        shutil.copy2('sistema_consultas.db', pre_restore_path)
        
        # Restaurar backup
        shutil.copy2(backup_path, 'sistema_consultas.db')
        
        return jsonify({
            'success': True,
            'message': f'Backup restaurado correctamente: {nombre}',
            'pre_restore': pre_restore_name
        })
        
    except Exception as e:
        print(f"❌ Error en api_restaurar_backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backups/eliminar', methods=['POST'])
@login_required
@permiso_requerido('gestionar_backups')
def api_eliminar_backup():
    """Elimina un backup"""
    try:
        data = request.json
        nombre = data.get('nombre')
        
        if not nombre:
            return jsonify({'success': False, 'error': 'Nombre del backup requerido'}), 400
        
        backup_path = os.path.join(BACKUP_DIR, nombre)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup no encontrado'}), 404
        
        os.remove(backup_path)
        
        return jsonify({
            'success': True,
            'message': f'Backup eliminado correctamente: {nombre}'
        })
        
    except Exception as e:
        print(f"❌ Error en api_eliminar_backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def limpiar_backups_antiguos():
    """Mantiene solo los MAX_BACKUPS backups más recientes"""
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        # Obtener todos los archivos .db (excluyendo pre_restore_*)
        backup_files = []
        for file in os.listdir(BACKUP_DIR):
            if file.endswith('.db') and not file.startswith('pre_restore_'):
                file_path = os.path.join(BACKUP_DIR, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))
        
        # Ordenar por fecha (más reciente primero)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Eliminar los más antiguos si exceden el límite
        for file_path, _ in backup_files[MAX_BACKUPS:]:
            os.remove(file_path)
            print(f"🗑️ Backup antiguo eliminado: {os.path.basename(file_path)}")
            
    except Exception as e:
        print(f"⚠️ Error al limpiar backups antiguos: {e}")


# ==================== RUTAS INCIDENTES ====================
@app.route('/incidentes')
@login_required
@permiso_requerido('ver_incidentes')
def incidentes():
    return render_template('incidentes.html')

@app.route('/incidente/<int:id>')
@login_required
@permiso_requerido('ver_incidentes')
def ver_incidente(id):
    incidente = Incidente.query.get_or_404(id)
    return render_template('ver_incidente.html', incidente=incidente)

# ==================== RUTAS ÓRDENES JUDICIALES ====================
@app.route('/ordenes_judiciales')
@login_required
@permiso_requerido('ver_ordenes_judiciales')
def ordenes_judiciales():
    return render_template('ordenes_judiciales.html')

@app.route('/orden_judicial/<int:id>')
@login_required
@permiso_requerido('ver_ordenes_judiciales')
def ver_orden_judicial(id):
    orden = OrdenJudicial.query.get_or_404(id)
    return render_template('ver_orden_judicial.html', orden=orden)

# ===== RUTA API PARA OBTENER TODAS LAS ÓRDENES JUDICIALES =====
@app.route('/api/ordenes_judiciales')
@login_required
@permiso_requerido('ver_ordenes_judiciales')
def api_ordenes_judiciales():
    """Obtiene todas las órdenes judiciales"""
    try:
        ordenes = OrdenJudicial.query.order_by(OrdenJudicial.id.desc()).all()
        resultados = []
        for o in ordenes:
            persona = Persona.query.get(o.persona_id)
            resultados.append({
                'id': o.id,
                'persona_id': o.persona_id,
                'persona_nombre': persona.nombre if persona else 'N/A',
                'persona_cedula': persona.cedula if persona else 'N/A',
                'despacho': o.despacho,
                'fecha_emision': o.fecha_emision,
                'numero_unico': o.numero_unico,
                'numero_oficio': o.numero_oficio or '',
                'consecutivo_interno': o.consecutivo_interno or '',
                'correo_despacho': o.correo_despacho or '',
                'telefono_despacho': o.telefono_despacho or '',
                'delitos': o.delitos or '',
                'ofendido_nombre': o.ofendido_nombre or '',
                'ofendido_identificacion': o.ofendido_identificacion or '',
                'hay_mas_ofendidos': o.hay_mas_ofendidos or False,
                'imputado_nombre': o.imputado_nombre,
                'imputado_identificacion': o.imputado_identificacion,
                'tipo_solicitud': o.tipo_solicitud or '',
                'dejar_orden': o.dejar_orden or '',
                'condicion_requerido': o.condicion_requerido or '',
                'tipo_captura': o.tipo_captura or '',
                'lugar_captura': o.lugar_captura or '',
                'remision_a': o.remision_a or '',
                'nacionalidad': o.nacionalidad or '',
                'estado_civil': o.estado_civil or '',
                'genero': o.genero or '',
                'nombre_padre': o.nombre_padre or '',
                'nombre_madre': o.nombre_madre or '',
                'latitud': o.latitud,
                'longitud': o.longitud,
                'direccion_ubicacion': o.direccion_ubicacion or '',
                'estado': o.estado,
                'observaciones': o.observaciones or '',
                'creado_por': o.creado_por or 'Sistema',
                'fecha_registro': o.fecha_registro or ''
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en api_ordenes_judiciales: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ===== RUTA API PARA OBTENER ÓRDENES JUDICIALES POR PERSONA =====
@app.route('/api/ordenes_judiciales/persona/<int:persona_id>')
@login_required
@permiso_requerido('ver_ordenes_judiciales')
def api_ordenes_judiciales_por_persona(persona_id):
    """Obtiene las órdenes judiciales de una persona específica"""
    try:
        ordenes = OrdenJudicial.query.filter_by(persona_id=persona_id).order_by(OrdenJudicial.id.desc()).all()
        resultados = []
        for o in ordenes:
            resultados.append({
                'id': o.id,
                'persona_id': o.persona_id,
                'despacho': o.despacho,
                'fecha_emision': o.fecha_emision,
                'numero_unico': o.numero_unico,
                'numero_oficio': o.numero_oficio or '',
                'consecutivo_interno': o.consecutivo_interno or '',
                'correo_despacho': o.correo_despacho or '',
                'telefono_despacho': o.telefono_despacho or '',
                'delitos': o.delitos or '',
                'ofendido_nombre': o.ofendido_nombre or '',
                'ofendido_identificacion': o.ofendido_identificacion or '',
                'hay_mas_ofendidos': o.hay_mas_ofendidos or False,
                'imputado_nombre': o.imputado_nombre,
                'imputado_identificacion': o.imputado_identificacion,
                'tipo_solicitud': o.tipo_solicitud or '',
                'dejar_orden': o.dejar_orden or '',
                'condicion_requerido': o.condicion_requerido or '',
                'tipo_captura': o.tipo_captura or '',
                'lugar_captura': o.lugar_captura or '',
                'remision_a': o.remision_a or '',
                'nacionalidad': o.nacionalidad or '',
                'estado_civil': o.estado_civil or '',
                'genero': o.genero or '',
                'nombre_padre': o.nombre_padre or '',
                'nombre_madre': o.nombre_madre or '',
                'latitud': o.latitud,
                'longitud': o.longitud,
                'direccion_ubicacion': o.direccion_ubicacion or '',
                'estado': o.estado,
                'observaciones': o.observaciones or '',
                'creado_por': o.creado_por or 'Sistema',
                'fecha_registro': o.fecha_registro or ''
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en api_ordenes_judiciales_por_persona: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ===== RUTA POST PARA CREAR ÓRDENES JUDICIALES =====
@app.route('/api/ordenes_judiciales', methods=['POST'])
@login_required
@permiso_requerido('crear_ordenes_judiciales')
def api_crear_orden_judicial():
    """Crea una nueva orden judicial"""
    try:
        data = request.json
        
        # Validar campos requeridos
        if not data.get('persona_id'):
            return jsonify({'success': False, 'error': 'La persona es requerida'}), 400
        if not data.get('despacho'):
            return jsonify({'success': False, 'error': 'El despacho es requerido'}), 400
        if not data.get('numero_unico'):
            return jsonify({'success': False, 'error': 'El número único es requerido'}), 400
        if not data.get('imputado_nombre'):
            return jsonify({'success': False, 'error': 'El nombre del imputado es requerido'}), 400
        if not data.get('imputado_identificacion'):
            return jsonify({'success': False, 'error': 'La identificación del imputado es requerida'}), 400
        
        # Verificar que la persona existe
        persona = Persona.query.get(data['persona_id'])
        if not persona:
            return jsonify({'success': False, 'error': 'La persona no existe'}), 404
        
        orden = OrdenJudicial(
            persona_id=data['persona_id'],
            despacho=data['despacho'],
            fecha_emision=data.get('fecha_emision', datetime.now().strftime('%Y-%m-%d')),
            numero_unico=data['numero_unico'],
            numero_oficio=data.get('numero_oficio', ''),
            consecutivo_interno=data.get('consecutivo_interno', ''),
            correo_despacho=data.get('correo_despacho', ''),
            telefono_despacho=data.get('telefono_despacho', ''),
            delitos=data.get('delitos', ''),
            ofendido_nombre=data.get('ofendido_nombre', ''),
            ofendido_identificacion=data.get('ofendido_identificacion', ''),
            hay_mas_ofendidos=data.get('hay_mas_ofendidos', False),
            imputado_nombre=data['imputado_nombre'],
            imputado_identificacion=data['imputado_identificacion'],
            tipo_solicitud=data.get('tipo_solicitud', ''),
            dejar_orden=data.get('dejar_orden', ''),
            condicion_requerido=data.get('condicion_requerido', ''),
            tipo_captura=data.get('tipo_captura', ''),
            lugar_captura=data.get('lugar_captura', ''),
            remision_a=data.get('remision_a', ''),
            nacionalidad=data.get('nacionalidad', ''),
            estado_civil=data.get('estado_civil', ''),
            genero=data.get('genero', ''),
            nombre_padre=data.get('nombre_padre', ''),
            nombre_madre=data.get('nombre_madre', ''),
            latitud=data.get('latitud'),
            longitud=data.get('longitud'),
            direccion_ubicacion=data.get('direccion_ubicacion', ''),
            estado=data.get('estado', 'ACTIVA'),
            observaciones=data.get('observaciones', ''),
            creado_por=current_user.username,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.session.add(orden)
        db.session.commit()
        
        return jsonify({'success': True, 'id': orden.id, 'message': 'Orden judicial creada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_crear_orden_judicial: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RUTA PUT PARA ACTUALIZAR ÓRDENES JUDICIALES =====
@app.route('/api/ordenes_judiciales/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('editar_ordenes_judiciales')
def api_actualizar_orden_judicial(id):
    """Actualiza una orden judicial existente"""
    try:
        orden = OrdenJudicial.query.get_or_404(id)
        data = request.json
        
        orden.despacho = data.get('despacho', orden.despacho)
        orden.fecha_emision = data.get('fecha_emision', orden.fecha_emision)
        orden.numero_unico = data.get('numero_unico', orden.numero_unico)
        orden.numero_oficio = data.get('numero_oficio', orden.numero_oficio)
        orden.consecutivo_interno = data.get('consecutivo_interno', orden.consecutivo_interno)
        orden.correo_despacho = data.get('correo_despacho', orden.correo_despacho)
        orden.telefono_despacho = data.get('telefono_despacho', orden.telefono_despacho)
        orden.delitos = data.get('delitos', orden.delitos)
        orden.ofendido_nombre = data.get('ofendido_nombre', orden.ofendido_nombre)
        orden.ofendido_identificacion = data.get('ofendido_identificacion', orden.ofendido_identificacion)
        orden.hay_mas_ofendidos = data.get('hay_mas_ofendidos', orden.hay_mas_ofendidos)
        orden.imputado_nombre = data.get('imputado_nombre', orden.imputado_nombre)
        orden.imputado_identificacion = data.get('imputado_identificacion', orden.imputado_identificacion)
        orden.tipo_solicitud = data.get('tipo_solicitud', orden.tipo_solicitud)
        orden.dejar_orden = data.get('dejar_orden', orden.dejar_orden)
        orden.condicion_requerido = data.get('condicion_requerido', orden.condicion_requerido)
        orden.tipo_captura = data.get('tipo_captura', orden.tipo_captura)
        orden.lugar_captura = data.get('lugar_captura', orden.lugar_captura)
        orden.remision_a = data.get('remision_a', orden.remision_a)
        orden.nacionalidad = data.get('nacionalidad', orden.nacionalidad)
        orden.estado_civil = data.get('estado_civil', orden.estado_civil)
        orden.genero = data.get('genero', orden.genero)
        orden.nombre_padre = data.get('nombre_padre', orden.nombre_padre)
        orden.nombre_madre = data.get('nombre_madre', orden.nombre_madre)
        orden.latitud = data.get('latitud', orden.latitud)
        orden.longitud = data.get('longitud', orden.longitud)
        orden.direccion_ubicacion = data.get('direccion_ubicacion', orden.direccion_ubicacion)
        orden.estado = data.get('estado', orden.estado)
        orden.observaciones = data.get('observaciones', orden.observaciones)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Orden judicial actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_actualizar_orden_judicial: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RUTA DELETE PARA ELIMINAR ÓRDENES JUDICIALES =====
@app.route('/api/ordenes_judiciales/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_ordenes_judiciales')
def api_eliminar_orden_judicial(id):
    """Elimina una orden judicial"""
    try:
        orden = OrdenJudicial.query.get_or_404(id)
        db.session.delete(orden)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Orden judicial eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_eliminar_orden_judicial: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTAS DE REPORTES ====================
@app.route('/reportes')
@login_required
@permiso_requerido('ver_estadisticas')
def reportes():
    return render_template('reportes.html')


# ===== RUTAS API PARA ESTADÍSTICAS DE REPORTES =====
@app.route('/api/estadisticas/ordenes')
@login_required
def api_estadisticas_ordenes():
    """Obtiene estadísticas de órdenes por mes"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        fecha_inicio = f"{año}-{mes}-01"
        
        # Calcular fin de mes
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        ordenes = OrdenCaptura.query.filter(
            OrdenCaptura.fecha_emision >= fecha_inicio,
            OrdenCaptura.fecha_emision < fecha_fin
        ).all()
        
        total = len(ordenes)
        deuda_total = sum(o.monto_deuda or 0 for o in ordenes)
        
        return jsonify({
            'total': total,
            'deuda': deuda_total
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_ordenes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticas/acciones')
@login_required
def api_estadisticas_acciones():
    """Obtiene estadísticas de acciones operativas por mes"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        fecha_inicio = f"{año}-{mes}-01"
        
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        acciones = AccionOperativa.query.filter(
            AccionOperativa.fecha >= fecha_inicio,
            AccionOperativa.fecha < fecha_fin
        ).all()
        
        total = len(acciones)
        personas = sum(a.personas_abordadas or 0 for a in acciones)
        
        return jsonify({
            'total': total,
            'personas': personas
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_acciones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticas/incidentes')
@login_required
def api_estadisticas_incidentes():
    """Obtiene estadísticas de incidentes por mes"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        fecha_inicio = f"{año}-{mes}-01"
        
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        incidentes = Incidente.query.filter(
            Incidente.fecha_incidente >= fecha_inicio,
            Incidente.fecha_incidente < fecha_fin
        ).all()
        
        total = len(incidentes)
        aprehendidos = sum(i.aprehendidos or 0 for i in incidentes)
        
        return jsonify({
            'total': total,
            'aprehendidos': aprehendidos
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_incidentes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/estadisticas/judiciales')
@login_required
def api_estadisticas_judiciales():
    """Obtiene estadísticas de órdenes judiciales por mes"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        fecha_inicio = f"{año}-{mes}-01"
        
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        ordenes = OrdenJudicial.query.filter(
            OrdenJudicial.fecha_emision >= fecha_inicio,
            OrdenJudicial.fecha_emision < fecha_fin
        ).all()
        
        total = len(ordenes)
        activas = sum(1 for o in ordenes if o.estado == 'ACTIVA')
        
        return jsonify({
            'total': total,
            'activas': activas
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_judiciales: {e}")
        return jsonify({'error': str(e)}), 500


# ===== RUTAS PARA GENERAR REPORTES CON ESCUDO =====
@app.route('/api/reportes/ordenes')
@login_required
def generar_reporte_ordenes():
    """Genera reporte HTML de órdenes de captura (para imprimir/PDF)"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        
        fecha_inicio = f"{año}-{mes}-01"
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        ordenes = OrdenCaptura.query.filter(
            OrdenCaptura.fecha_emision >= fecha_inicio,
            OrdenCaptura.fecha_emision < fecha_fin
        ).all()
        
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        nombre_mes = meses[int(mes)-1]
        
        total_deuda = sum(o.monto_deuda or 0 for o in ordenes)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reporte de Órdenes - {nombre_mes} {año}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #1a2236; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
                .total {{ font-weight: bold; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
            </style>
        </head>
        <body>
            {generar_header_reporte(nombre_mes, año)}
            
            <p><strong>Total de órdenes:</strong> {len(ordenes)}</p>
            <p><strong>Deuda total:</strong> ₡{total_deuda:,.0f}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>N° Orden</th>
                        <th>Deudor</th>
                        <th>Cédula</th>
                        <th>Monto</th>
                        <th>Juzgado</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for o in ordenes:
            persona = Persona.query.get(o.persona_id)
            nombre = persona.nombre if persona else 'N/A'
            cedula = persona.cedula if persona else 'N/A'
            html += f"""
                    <tr>
                        <td>{o.numero_orden}</td>
                        <td>{nombre}</td>
                        <td>{cedula}</td>
                        <td>₡{o.monto_deuda:,.0f}</td>
                        <td>{o.juzgado}</td>
                        <td>{o.estado}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            <div class="total">
                <strong>Resumen:</strong> {len(ordenes)} órdenes | Deuda total: ₡{total_deuda:,.0f}
            </div>
            <div class="footer">
                Sistema de Consultas - Fuerza Pública<br>
                Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </body>
        </html>
        """
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"❌ Error en generar_reporte_ordenes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/acciones')
@login_required
def generar_reporte_acciones():
    """Genera reporte HTML de acciones operativas (para imprimir/PDF)"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        
        fecha_inicio = f"{año}-{mes}-01"
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        acciones = AccionOperativa.query.filter(
            AccionOperativa.fecha >= fecha_inicio,
            AccionOperativa.fecha < fecha_fin
        ).all()
        
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        nombre_mes = meses[int(mes)-1]
        
        total_personas = sum(a.personas_abordadas or 0 for a in acciones)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reporte de Acciones - {nombre_mes} {año}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #1a4a3a; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
                .total {{ font-weight: bold; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
            </style>
        </head>
        <body>
            {generar_header_reporte(nombre_mes, año)}
            
            <p><strong>Total de acciones:</strong> {len(acciones)}</p>
            <p><strong>Total personas abordadas:</strong> {total_personas}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Unidad</th>
                        <th>Fecha</th>
                        <th>Lugar</th>
                        <th>Acción</th>
                        <th>Mando</th>
                        <th>Personas</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for a in acciones:
            html += f"""
                    <tr>
                        <td>{a.cod_unidad}</td>
                        <td>{a.fecha}</td>
                        <td>{a.lugar[:30] if a.lugar else ''}</td>
                        <td>{a.accion_realizada[:30] if a.accion_realizada else ''}</td>
                        <td>{a.mando}</td>
                        <td>{a.personas_abordadas or 0}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            <div class="total">
                <strong>Resumen:</strong> {len(acciones)} acciones | {total_personas} personas abordadas
            </div>
            <div class="footer">
                Sistema de Consultas - Fuerza Pública<br>
                Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </body>
        </html>
        """
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"❌ Error en generar_reporte_acciones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/incidentes')
@login_required
def generar_reporte_incidentes():
    """Genera reporte HTML de incidentes (para imprimir/PDF)"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        
        fecha_inicio = f"{año}-{mes}-01"
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        incidentes = Incidente.query.filter(
            Incidente.fecha_incidente >= fecha_inicio,
            Incidente.fecha_incidente < fecha_fin
        ).all()
        
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        nombre_mes = meses[int(mes)-1]
        
        total_aprehendidos = sum(i.aprehendidos or 0 for i in incidentes)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reporte de Incidentes - {nombre_mes} {año}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #4a1a1a; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
                .total {{ font-weight: bold; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
            </style>
        </head>
        <body>
            {generar_header_reporte(nombre_mes, año)}
            
            <p><strong>Total de incidentes:</strong> {len(incidentes)}</p>
            <p><strong>Total aprehendidos:</strong> {total_aprehendidos}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>N° Incidente</th>
                        <th>Fecha</th>
                        <th>Tipo</th>
                        <th>Lugar</th>
                        <th>Oficial</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for i in incidentes:
            html += f"""
                    <tr>
                        <td>{i.numero_incidente}</td>
                        <td>{i.fecha_incidente}</td>
                        <td>{i.tipo_incidente}</td>
                        <td>{i.lugar[:30] if i.lugar else ''}</td>
                        <td>{i.oficial_actuante}</td>
                        <td>{i.estado}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            <div class="total">
                <strong>Resumen:</strong> {len(incidentes)} incidentes | {total_aprehendidos} aprehendidos
            </div>
            <div class="footer">
                Sistema de Consultas - Fuerza Pública<br>
                Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </body>
        </html>
        """
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"❌ Error en generar_reporte_incidentes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reportes/judiciales')
@login_required
def generar_reporte_judiciales():
    """Genera reporte HTML de órdenes judiciales (para imprimir/PDF)"""
    try:
        mes = request.args.get('mes', datetime.now().strftime('%m'))
        año = request.args.get('año', datetime.now().strftime('%Y'))
        
        fecha_inicio = f"{año}-{mes}-01"
        if int(mes) == 12:
            fecha_fin = f"{int(año)+1}-01-01"
        else:
            fecha_fin = f"{año}-{int(mes)+1:02d}-01"
        
        ordenes = OrdenJudicial.query.filter(
            OrdenJudicial.fecha_emision >= fecha_inicio,
            OrdenJudicial.fecha_emision < fecha_fin
        ).all()
        
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        nombre_mes = meses[int(mes)-1]
        
        activas = sum(1 for o in ordenes if o.estado == 'ACTIVA')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reporte de Órdenes Judiciales - {nombre_mes} {año}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background: #2d1b4a; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
                .total {{ font-weight: bold; margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .footer {{ margin-top: 40px; text-align: center; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
            </style>
        </head>
        <body>
            {generar_header_reporte(nombre_mes, año)}
            
            <p><strong>Total de órdenes:</strong> {len(ordenes)}</p>
            <p><strong>Órdenes activas:</strong> {activas}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>N° Único</th>
                        <th>Despacho</th>
                        <th>Fecha</th>
                        <th>Imputado</th>
                        <th>Delito</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for o in ordenes:
            html += f"""
                    <tr>
                        <td>{o.numero_unico}</td>
                        <td>{o.despacho}</td>
                        <td>{o.fecha_emision}</td>
                        <td>{o.imputado_nombre}</td>
                        <td>{o.delitos[:30] if o.delitos else ''}</td>
                        <td>{o.estado}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            <div class="total">
                <strong>Resumen:</strong> {len(ordenes)} órdenes | {activas} activas
            </div>
            <div class="footer">
                Sistema de Consultas - Fuerza Pública<br>
                Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </body>
        </html>
        """
        
        return html, 200, {'Content-Type': 'text/html'}
        
    except Exception as e:
        print(f"❌ Error en generar_reporte_judiciales: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== RUTAS MACHOTES DE DOCUMENTOS (UNIFICADO) ====================

# ===== RUTAS DE VISTA =====
@app.route('/machotes')
@login_required
@permiso_requerido('ver_machotes')
def machotes():
    return render_template('machotes.html')

@app.route('/machote/nuevo')
@login_required
@permiso_requerido('crear_machotes')
def nuevo_machote():
    return render_template('machote_editor_simple.html', machote=None, preguntas=[])

@app.route('/machote/editar/<int:id>')
@login_required
@permiso_requerido('editar_machotes')
def editar_machote(id):
    machote = MachoteDocumento.query.get_or_404(id)
    preguntas = Pregunta.query.filter_by(machote_id=id).order_by(Pregunta.orden).all()
    return render_template('machote_editor_simple.html', machote=machote, preguntas=preguntas)

@app.route('/machote/ver/<int:id>')
@login_required
@permiso_requerido('ver_machotes')
def ver_machote(id):
    machote = MachoteDocumento.query.get_or_404(id)
    preguntas = Pregunta.query.filter_by(machote_id=id).order_by(Pregunta.orden).all()
    return render_template('ver_machote.html', machote=machote, preguntas=preguntas)

@app.route('/machote/generar/<int:id>')
@login_required
@permiso_requerido('ver_machotes')
def generar_machote(id):
    machote = MachoteDocumento.query.get_or_404(id)
    preguntas = Pregunta.query.filter_by(machote_id=id).order_by(Pregunta.orden).all()
    return render_template('machote_generar_simple.html', machote=machote, preguntas=preguntas)

# ===== RUTAS API =====
@app.route('/api/machotes')
@login_required
def api_machotes():
    """Obtiene la lista de machotes"""
    try:
        machotes = MachoteDocumento.query.filter_by(es_activo=True).order_by(
            MachoteDocumento.fecha_registro.desc()
        ).all()
        
        resultados = []
        for m in machotes:
            preguntas_count = Pregunta.query.filter_by(machote_id=m.id).count()
            resultados.append({
                'id': m.id,
                'nombre': m.nombre or 'Sin nombre',
                'descripcion': m.descripcion or '',
                'tipo_documento': m.tipo_documento or 'informe',
                'categoria': m.categoria or '',
                'contenido': m.contenido or '',
                'creado_por': m.creado_por or 'Sistema',
                'fecha_registro': m.fecha_registro or '',
                'preguntas_count': preguntas_count
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en api_machotes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/machotes/<int:id>')
@login_required
def api_machote(id):
    """Obtiene un machote específico con sus preguntas"""
    try:
        machote = MachoteDocumento.query.get_or_404(id)
        preguntas = Pregunta.query.filter_by(machote_id=id).order_by(Pregunta.orden).all()
        
        preguntas_data = []
        for p in preguntas:
            pregunta = {
                'id': p.id,
                'orden': p.orden or 0,
                'tipo': p.tipo or 'texto',
                'titulo': p.titulo or '',
                'variable': p.variable or '',
                'requerido': p.requerido if p.requerido is not None else True
            }
            if p.opciones:
                try:
                    pregunta['opciones'] = json.loads(p.opciones)
                except:
                    pregunta['opciones'] = []
            else:
                pregunta['opciones'] = []
            preguntas_data.append(pregunta)
        
        return jsonify({
            'id': machote.id,
            'nombre': machote.nombre or 'Sin nombre',
            'descripcion': machote.descripcion or '',
            'tipo_documento': machote.tipo_documento or 'informe',
            'categoria': machote.categoria or '',
            'contenido': machote.contenido or '',
            'estructura': machote.estructura or '{}',
            'preguntas': preguntas_data
        })
    except Exception as e:
        print(f"❌ Error en api_machote: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/machotes', methods=['POST'])
@login_required
def api_crear_machote():
    """Crea un nuevo machote"""
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({'success': False, 'error': 'El nombre es requerido'}), 400
        
        # Verificar nombre único
        if MachoteDocumento.query.filter_by(nombre=nombre).first():
            return jsonify({'success': False, 'error': 'Ya existe un machote con este nombre'}), 400
        
        descripcion = data.get('descripcion', '')
        tipo_documento = data.get('tipo_documento', 'informe')
        categoria = data.get('categoria', '')
        preguntas_data = data.get('preguntas', [])
        
        machote = MachoteDocumento(
            nombre=nombre,
            descripcion=descripcion,
            tipo_documento=tipo_documento,
            categoria=categoria,
            contenido='',
            es_activo=True,
            creado_por=current_user.username,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ultima_modificacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(machote)
        db.session.flush()
        
        # Crear preguntas
        contenido = ''
        for i, p in enumerate(preguntas_data):
            opciones_json = None
            if p.get('tipo') == 'select':
                opciones = p.get('opciones', ['Opción 1', 'Opción 2'])
                if opciones and len(opciones) > 0:
                    opciones_json = json.dumps(opciones)
            
            pregunta = Pregunta(
                machote_id=machote.id,
                orden=i,
                tipo=p.get('tipo', 'texto'),
                titulo=p.get('titulo', ''),
                variable=p.get('variable', ''),
                opciones=opciones_json,
                requerido=p.get('requerido', True)
            )
            db.session.add(pregunta)
            
            # Generar contenido
            contenido += f"{p.get('titulo', '')}: {{{{ {p.get('variable', '')} }}}}\n"
        
        machote.contenido = contenido
        estructura = {'preguntas': preguntas_data}
        machote.estructura = json.dumps(estructura)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': machote.id,
            'message': 'Machote creado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_crear_machote: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/machotes/<int:id>', methods=['PUT'])
@login_required
def api_actualizar_machote(id):
    """Actualiza un machote existente"""
    try:
        data = request.json
        machote = MachoteDocumento.query.get_or_404(id)
        
        nombre = data.get('nombre', '').strip()
        if not nombre:
            return jsonify({'success': False, 'error': 'El nombre es requerido'}), 400
        
        # Verificar nombre único (excepto si es el mismo)
        if nombre != machote.nombre:
            if MachoteDocumento.query.filter_by(nombre=nombre).first():
                return jsonify({'success': False, 'error': 'Ya existe un machote con este nombre'}), 400
        
        machote.nombre = nombre
        machote.descripcion = data.get('descripcion', machote.descripcion)
        machote.tipo_documento = data.get('tipo_documento', machote.tipo_documento)
        machote.categoria = data.get('categoria', machote.categoria)
        machote.ultima_modificacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Eliminar preguntas existentes
        Pregunta.query.filter_by(machote_id=id).delete()
        db.session.flush()
        
        # Crear nuevas preguntas
        preguntas_data = data.get('preguntas', [])
        contenido = ''
        for i, p in enumerate(preguntas_data):
            opciones_json = None
            if p.get('tipo') == 'select':
                opciones = p.get('opciones', ['Opción 1', 'Opción 2'])
                if opciones and len(opciones) > 0:
                    opciones_json = json.dumps(opciones)
            
            pregunta = Pregunta(
                machote_id=machote.id,
                orden=i,
                tipo=p.get('tipo', 'texto'),
                titulo=p.get('titulo', ''),
                variable=p.get('variable', ''),
                opciones=opciones_json,
                requerido=p.get('requerido', True)
            )
            db.session.add(pregunta)
            
            contenido += f"{p.get('titulo', '')}: {{{{ {p.get('variable', '')} }}}}\n"
        
        machote.contenido = contenido
        estructura = {'preguntas': preguntas_data}
        machote.estructura = json.dumps(estructura)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Machote actualizado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_actualizar_machote: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTA DELETE CORREGIDA (USANDO SQL DIRECTO) ====================
@app.route('/api/machotes/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_machotes')
def api_eliminar_machote(id):
    """Elimina un machote y todos sus datos relacionados usando SQL directo"""
    try:
        from sqlalchemy import text
        
        # Primero verificar si el machote existe
        machote = MachoteDocumento.query.get(id)
        if not machote:
            return jsonify({'success': False, 'error': 'Machote no encontrado'}), 404
        
        nombre_machote = machote.nombre
        print(f"🗑️ Eliminando machote: {nombre_machote} (ID: {id})")
        
        # 1. Eliminar respuestas_detalle (hijos de respuestas_formulario)
        db.session.execute(text("""
            DELETE FROM respuestas_detalle 
            WHERE respuesta_id IN (
                SELECT id FROM respuestas_formulario WHERE machote_id = :machote_id
            )
        """), {"machote_id": id})
        print(f"  ✅ Respuestas detalle eliminadas")
        
        # 2. Eliminar respuestas_formulario
        db.session.execute(text("DELETE FROM respuestas_formulario WHERE machote_id = :machote_id"), {"machote_id": id})
        print(f"  ✅ Respuestas de formulario eliminadas")
        
        # 3. Eliminar preguntas
        db.session.execute(text("DELETE FROM preguntas WHERE machote_id = :machote_id"), {"machote_id": id})
        print(f"  ✅ Preguntas eliminadas")
        
        # 4. Eliminar respuestas (modelo Respuesta)
        db.session.execute(text("DELETE FROM respuestas WHERE machote_id = :machote_id"), {"machote_id": id})
        print(f"  ✅ Respuestas eliminadas")
        
        # 5. Eliminar documentos generados
        db.session.execute(text("DELETE FROM documentos_generados WHERE machote_id = :machote_id"), {"machote_id": id})
        print(f"  ✅ Documentos generados eliminados")
        
        # 6. Eliminar el machote
        db.session.execute(text("DELETE FROM machotes_documentos WHERE id = :machote_id"), {"machote_id": id})
        print(f"  ✅ Machote eliminado")
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Machote "{nombre_machote}" eliminado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_eliminar_machote: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generar_documento', methods=['POST'])
@login_required
def api_generar_documento():
    """Genera un documento basado en un machote y los datos proporcionados"""
    try:
        data = request.json
        machote_id = data.get('machote_id')
        datos = data.get('datos', {})
        
        if not machote_id:
            return jsonify({'success': False, 'error': 'ID del machote requerido'}), 400
        
        machote = MachoteDocumento.query.get_or_404(machote_id)
        
        # Obtener el contenido del machote
        contenido = machote.contenido or ''
        
        # Reemplazar variables en todos los formatos posibles
        for variable, valor in datos.items():
            valor_str = str(valor) if valor is not None else ''
            
            # Formato 1: {{{{ variable }}}} (4 llaves)
            contenido = contenido.replace(f'{{{{{ variable }}}}}', valor_str)
            
            # Formato 2: {{{ variable }}} (3 llaves)
            contenido = contenido.replace(f'{{{{{ variable }}}}}', valor_str)
            
            # Formato 3: {{ variable }} (2 llaves)
            contenido = contenido.replace(f'{{{{ {variable} }}}}', valor_str)
            
            # Formato 4: {{ variable: }} (2 llaves con dos puntos)
            contenido = contenido.replace(f'{{{{ {variable}: }}}}', valor_str)
            
            # Formato 5: { variable } (1 llave)
            contenido = contenido.replace(f'{{ {variable} }}', valor_str)
            
            # Formato 6: variable sin llaves (solo para compatibilidad)
            contenido = contenido.replace(f'{{{variable}}}', valor_str)
        
        # Verificar si quedaron variables sin reemplazar
        variables_restantes = []
        patrones = [
            r'\{\{\{\{\s*(\w+)\s*\}\}\}\}',  # 4 llaves
            r'\{\{\{\s*(\w+)\s*\}\}\}',      # 3 llaves
            r'\{\{\s*(\w+)\s*:?\s*\}\}',     # 2 llaves
            r'\{(\w+)\s*\}'                  # 1 llave
        ]
        for patron in patrones:
            variables_restantes.extend(re.findall(patron, contenido))
        
        # Guardar documento generado
        doc_generado = DocumentoGenerado(
            machote_id=machote_id,
            titulo=f"Documento generado desde {machote.nombre}",
            contenido=contenido,
            variables_utilizadas=json.dumps(datos),
            generado_por=current_user.username,
            fecha_generacion=datetime.utcnow()
        )
        db.session.add(doc_generado)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contenido': contenido,
            'variables_restantes': variables_restantes,
            'documento_id': doc_generado.id,
            'message': 'Documento generado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_generar_documento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/machotes/tipos')
@login_required
def api_tipos_documento():
    """Obtiene los tipos de documento disponibles"""
    try:
        tipos = ['oficio', 'informe', 'acta', 'citacion', 'otro']
        return jsonify(tipos)
    except Exception as e:
        print(f"❌ Error en api_tipos_documento: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS RESPUESTAS ====================
@app.route('/respuestas')
@login_required
@permiso_requerido('ver_respuestas')
def respuestas():
    return render_template('respuestas.html')

@app.route('/respuesta/<int:id>')
@login_required
@permiso_requerido('ver_respuestas')
def ver_respuesta(id):
    respuesta = RespuestaFormulario.query.get_or_404(id)
    return render_template('ver_respuesta.html', respuesta=respuesta)

# ==================== RUTAS OCR ====================

@app.route('/ocr/cedula', methods=['GET'])
@login_required
@permiso_requerido('crear_personas')
def ocr_cedula_page():
    """Página para escanear cédulas con OCR + QR"""
    return render_template('ocr_cedula.html')

@app.route('/api/ocr/cedula', methods=['POST'])
@login_required
@permiso_requerido('crear_personas')
def api_ocr_cedula():
    """API para procesar imagen de cédula con QR + EasyOCR + Tesseract"""
    try:
        if 'imagen' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ninguna imagen'}), 400
        
        archivo = request.files['imagen']
        if archivo.filename == '':
            return jsonify({'success': False, 'error': 'No se seleccionó ningún archivo'}), 400
        
        print(f"\n{'='*60}")
        print(f"📸 Procesando imagen: {archivo.filename}")
        print(f"{'='*60}")
        
        imagen_bytes = archivo.read()
        
        # ==================== PASO 1: INTENTAR CON QR ====================
        print("\n🔍 Buscando código QR en la imagen...")
        datos_qr = extraer_desde_qr_mejorado(imagen_bytes)
        
        if datos_qr and datos_qr.get('cedula') and datos_qr.get('nombre'):
            print("\n✅ DATOS EXTRAÍDOS DESDE QR + TSE CON ÉXITO!")
            print(f"📊 Datos: {datos_qr}")
            
            # Buscar persona existente
            persona_existente = None
            if datos_qr.get('cedula'):
                cedula_limpia = re.sub(r'[^0-9]', '', datos_qr['cedula'])
                personas = Persona.query.filter_by(cedula=cedula_limpia).all()
                if personas:
                    p = personas[0]
                    persona_existente = {
                        'id': p.id,
                        'cedula': p.cedula,
                        'nombre': p.nombre,
                        'fecha_nacimiento': p.fecha_nacimiento,
                        'genero': p.genero,
                        'direccion': p.direccion,
                        'telefono': p.telefono,
                        'estado': p.estado
                    }
                    print(f"✅ Persona encontrada en sistema: {p.nombre}")
            
            print(f"\n✅ OCR completado exitosamente (método: QR + TSE)")
            print(f"{'='*60}\n")
            
            return jsonify({
                'success': True,
                'datos': datos_qr,
                'persona_existente': persona_existente,
                'texto_completo': 'Datos extraídos desde código QR + TSE',
                'metodo': 'QR-TSE'
            })
        
        # ==================== PASO 2: INTENTAR CON QR (sin TSE) ====================
        if datos_qr and datos_qr.get('cedula'):
            print("\n✅ DATOS EXTRAÍDOS DESDE QR (MRZ)")
            print(f"📊 Datos QR: {datos_qr}")
            
            # Buscar persona existente
            persona_existente = None
            if datos_qr.get('cedula'):
                cedula_limpia = re.sub(r'[^0-9]', '', datos_qr['cedula'])
                personas = Persona.query.filter_by(cedula=cedula_limpia).all()
                if personas:
                    p = personas[0]
                    persona_existente = {
                        'id': p.id,
                        'cedula': p.cedula,
                        'nombre': p.nombre,
                        'fecha_nacimiento': p.fecha_nacimiento,
                        'genero': p.genero,
                        'direccion': p.direccion,
                        'telefono': p.telefono,
                        'estado': p.estado
                    }
                    print(f"✅ Persona encontrada en sistema: {p.nombre}")
            
            return jsonify({
                'success': True,
                'datos': datos_qr,
                'persona_existente': persona_existente,
                'texto_completo': 'Datos extraídos desde código QR (MRZ)',
                'metodo': 'QR-MRZ'
            })
        
        # ==================== PASO 3: INTENTAR CON EASYOCR ====================
        print("\n⚠️ No se encontró QR válido. Intentando con EasyOCR...")
        
        texto, datos = procesar_ocr_easyocr(imagen_bytes)
        
        if datos and (datos.get('cedula') or datos.get('nombre')):
            print("\n✅ DATOS EXTRAÍDOS CON EASYOCR!")
            print(f"📊 Datos: {datos}")
            
            # Si tenemos la cédula, intentar consultar el TSE para completar datos
            if datos.get('cedula'):
                cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
                if len(cedula_limpia) >= 9:
                    print(f"🔍 Consultando TSE con cédula: {cedula_limpia}")
                    datos_tse = obtener_datos_tse(cedula_limpia)
                    if datos_tse and datos_tse.get('nombre'):
                        print("✅ Datos completados desde TSE")
                        datos.update(datos_tse)
            
            # Buscar persona existente
            persona_existente = None
            if datos.get('cedula'):
                cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
                personas = Persona.query.filter_by(cedula=cedula_limpia).all()
                if personas:
                    p = personas[0]
                    persona_existente = {
                        'id': p.id,
                        'cedula': p.cedula,
                        'nombre': p.nombre,
                        'fecha_nacimiento': p.fecha_nacimiento,
                        'genero': p.genero,
                        'direccion': p.direccion,
                        'telefono': p.telefono,
                        'estado': p.estado
                    }
                    print(f"✅ Persona encontrada en sistema: {p.nombre}")
            
            return jsonify({
                'success': True,
                'datos': datos,
                'persona_existente': persona_existente,
                'texto_completo': texto[:1000] if texto else '',
                'metodo': 'EasyOCR'
            })
        
        # ==================== PASO 4: FALLBACK A TESSERACT ====================
        print("\n⚠️ EasyOCR no extrajo datos suficientes. Intentando con Tesseract...")
        
        # Extraer texto con Tesseract
        texto = extraer_texto_imagen_mejorado(imagen_bytes)
        print(f"\n📄 Texto extraído con Tesseract (primeros 500 caracteres):")
        print("-" * 60)
        print(texto[:500] if texto else "TEXTO VACÍO")
        print("-" * 60)
        print(f"📄 Longitud total del texto: {len(texto)} caracteres")
        
        if not texto or len(texto.strip()) < 5:
            print("❌ No se pudo extraer texto suficiente con Tesseract")
            return jsonify({
                'success': False, 
                'error': 'No se pudo extraer texto de la imagen. Asegúrate de que la imagen sea clara y esté bien enfocada.',
                'texto_completo': 'Texto no extraído'
            }), 400
        
        datos = extraer_datos_cedula_mejorado(texto)
        print(f"\n📊 Datos extraídos con Tesseract: {datos}")
        
        if not datos['cedula'] and not datos['nombre']:
            print("❌ No se pudo identificar cédula o nombre")
            return jsonify({
                'success': False,
                'error': 'No se pudo identificar la cédula o el nombre en la imagen. Intenta con una foto más clara o asegúrate de incluir el código QR.',
                'texto_completo': texto[:1000]
            }), 400
        
        # Si tenemos la cédula, intentar consultar el TSE
        if datos.get('cedula'):
            cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
            if len(cedula_limpia) >= 9:
                print(f"🔍 Consultando TSE con cédula: {cedula_limpia}")
                datos_tse = obtener_datos_tse(cedula_limpia)
                if datos_tse and datos_tse.get('nombre'):
                    print("✅ Datos completados desde TSE")
                    datos = datos_tse
        
        # Buscar persona existente
        persona_existente = None
        if datos.get('cedula'):
            cedula_limpia = re.sub(r'[^0-9]', '', datos['cedula'])
            personas = Persona.query.filter_by(cedula=cedula_limpia).all()
            if personas:
                p = personas[0]
                persona_existente = {
                    'id': p.id,
                    'cedula': p.cedula,
                    'nombre': p.nombre,
                    'fecha_nacimiento': p.fecha_nacimiento,
                    'genero': p.genero,
                    'direccion': p.direccion,
                    'telefono': p.telefono,
                    'estado': p.estado
                }
                print(f"✅ Persona encontrada en sistema: {p.nombre}")
        
        print(f"\n✅ OCR completado exitosamente (método: Tesseract)")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'datos': datos,
            'persona_existente': persona_existente,
            'texto_completo': texto[:1000],
            'metodo': 'Tesseract'
        })
        
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTAS API PARA EL DASHBOARD, ESTADÍSTICAS Y ÓRDENES ====================

@app.route('/api/estadisticas')
@login_required
def api_estadisticas_dashboard():
    """Obtiene estadísticas para el dashboard - formato esperado por el frontend"""
    try:
        total_personas = Persona.query.count()
        total_ordenes = OrdenCaptura.query.count()
        ordenes_activas = OrdenCaptura.query.filter_by(estado='ACTIVA').count()
        ordenes_vencidas = OrdenCaptura.query.filter_by(estado='VENCIDA').count()
        deuda_total = db.session.query(func.sum(OrdenCaptura.monto_deuda)).filter_by(estado='ACTIVA').scalar() or 0
        
        return jsonify({
            'personas': total_personas,
            'total_ordenes': total_ordenes,
            'ordenes_activas': ordenes_activas,
            'ordenes_vencidas': ordenes_vencidas,
            'deuda_total': float(deuda_total)
        })
    except Exception as e:
        print(f"❌ Error en estadisticas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alertas')
@login_required
def api_alertas_dashboard():
    """Obtiene las alertas para el dashboard - formato esperado por el frontend"""
    try:
        alertas = obtener_alertas()
        return jsonify(alertas)
    except Exception as e:
        print(f"❌ Error en alertas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes')
@login_required
def api_ordenes_dashboard():
    """Obtiene las órdenes recientes para el dashboard - formato esperado por el frontend"""
    try:
        ordenes = OrdenCaptura.query.order_by(OrdenCaptura.id.desc()).limit(10).all()
        resultados = []
        for o in ordenes:
            p = Persona.query.get(o.persona_id)
            resultados.append({
                'id': o.id,
                'numero_orden': o.numero_orden,
                'persona_nombre': p.nombre if p else 'N/A',
                'persona_cedula': p.cedula if p else 'N/A',
                'monto_deuda': float(o.monto_deuda),
                'juzgado': o.juzgado,
                'estado': o.estado,
                'fecha_emision': o.fecha_emision
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en ordenes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard_stats')
@login_required
def api_dashboard_stats():
    """Obtiene estadísticas para el dashboard"""
    try:
        total_personas = Persona.query.count()
        total_ordenes = OrdenCaptura.query.count()
        ordenes_activas = OrdenCaptura.query.filter_by(estado='ACTIVA').count()
        ordenes_vencidas = OrdenCaptura.query.filter_by(estado='VENCIDA').count()
        deuda_total = db.session.query(func.sum(OrdenCaptura.monto_deuda)).filter_by(estado='ACTIVA').scalar() or 0
        
        return jsonify({
            'success': True,
            'total_personas': total_personas,
            'total_ordenes': total_ordenes,
            'ordenes_activas': ordenes_activas,
            'ordenes_vencidas': ordenes_vencidas,
            'deuda_total': float(deuda_total)
        })
    except Exception as e:
        print(f"❌ Error en dashboard_stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas_recientes')
@login_required
def api_personas_recientes():
    """Obtiene las últimas personas registradas para el dashboard"""
    try:
        personas = Persona.query.order_by(Persona.id.desc()).limit(10).all()
        return jsonify([{
            'id': p.id,
            'cedula': p.cedula,
            'nombre': p.nombre,
            'fecha_registro': p.fecha_registro
        } for p in personas])
    except Exception as e:
        print(f"❌ Error en personas_recientes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/alertas_dashboard')
@login_required
def api_alertas_dashboard_alt():
    """Obtiene las alertas para el dashboard"""
    try:
        alertas = obtener_alertas()
        return jsonify(alertas)
    except Exception as e:
        print(f"❌ Error en alertas_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes_recientes')
@login_required
def api_ordenes_recientes():
    """Obtiene las últimas órdenes para el dashboard"""
    try:
        ordenes = OrdenCaptura.query.order_by(OrdenCaptura.id.desc()).limit(10).all()
        resultados = []
        for o in ordenes:
            p = Persona.query.get(o.persona_id)
            resultados.append({
                'id': o.id,
                'numero_orden': o.numero_orden,
                'persona_nombre': p.nombre if p else 'N/A',
                'persona_cedula': p.cedula if p else 'N/A',
                'monto_deuda': float(o.monto_deuda),
                'juzgado': o.juzgado,
                'estado': o.estado,
                'fecha_emision': o.fecha_emision
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en ordenes_recientes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS API PARA PERSONAS ====================

@app.route('/api/personas')
@login_required
def api_personas():
    """Obtiene todas las personas para la página de personas"""
    try:
        busqueda = request.args.get('busqueda', '')
        if busqueda:
            personas = Persona.query.filter(
                (Persona.cedula.like(f'%{busqueda}%')) | 
                (Persona.nombre.like(f'%{busqueda}%'))
            ).all()
        else:
            personas = Persona.query.all()
        
        return jsonify([{
            'id': p.id,
            'cedula': p.cedula,
            'nombre': p.nombre,
            'fecha_nacimiento': p.fecha_nacimiento or '',
            'genero': p.genero or '',
            'direccion': p.direccion or '',
            'telefono': p.telefono or '',
            'email': p.email or '',
            'foto': p.foto or '',
            'estado': p.estado
        } for p in personas])
    except Exception as e:
        print(f"❌ Error en personas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas/<int:id>')
@login_required
def api_persona_unica(id):
    """Obtiene una persona específica por su ID"""
    try:
        persona = Persona.query.get_or_404(id)
        return jsonify({
            'id': persona.id,
            'cedula': persona.cedula,
            'nombre': persona.nombre,
            'fecha_nacimiento': persona.fecha_nacimiento or '',
            'genero': persona.genero or '',
            'direccion': persona.direccion or '',
            'telefono': persona.telefono or '',
            'email': persona.email or '',
            'foto': persona.foto or '',
            'estado': persona.estado,
            'fecha_registro': persona.fecha_registro or ''
        })
    except Exception as e:
        print(f"❌ Error en api_persona_unica: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas', methods=['POST'])
@login_required
@permiso_requerido('crear_personas')
def create_persona():
    """Crea una nueva persona"""
    try:
        data = request.json
        
        # Verificar si ya existe una persona con esa cédula
        cedula_limpia = re.sub(r'[^0-9]', '', data['cedula'])
        existente = Persona.query.filter_by(cedula=cedula_limpia).first()
        if existente:
            return jsonify({'error': 'Ya existe una persona con esta cédula'}), 400
        
        persona = Persona(
            cedula=cedula_limpia,
            nombre=data['nombre'].upper(),
            fecha_nacimiento=data.get('fecha_nacimiento', ''),
            genero=data.get('genero', ''),
            direccion=data.get('direccion', '').upper(),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            foto=data.get('foto', ''),
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            estado=data.get('estado', 'ACTIVO')
        )
        db.session.add(persona)
        db.session.commit()
        return jsonify({'success': True, 'id': persona.id, 'message': 'Persona creada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en create_persona: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('editar_personas')
def update_persona(id):
    """Actualiza una persona existente"""
    try:
        persona = Persona.query.get_or_404(id)
        data = request.json
        
        # Verificar si la cédula ya existe en otra persona
        cedula_limpia = re.sub(r'[^0-9]', '', data['cedula'])
        existente = Persona.query.filter_by(cedula=cedula_limpia).first()
        if existente and existente.id != id:
            return jsonify({'error': 'Ya existe otra persona con esta cédula'}), 400
        
        persona.cedula = cedula_limpia
        persona.nombre = data['nombre'].upper()
        persona.fecha_nacimiento = data.get('fecha_nacimiento', '')
        persona.genero = data.get('genero', '')
        persona.direccion = data.get('direccion', '').upper()
        persona.telefono = data.get('telefono', '')
        persona.email = data.get('email', '')
        if data.get('foto'):
            persona.foto = data['foto']
        persona.estado = data.get('estado', 'ACTIVO')
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Persona actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en update_persona: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_personas')
def delete_persona(id):
    """Elimina una persona y sus relaciones"""
    try:
        persona = Persona.query.get_or_404(id)
        
        # Eliminar antecedentes asociados
        Antecedente.query.filter_by(persona_id=id).delete()
        # Eliminar órdenes de captura asociadas
        OrdenCaptura.query.filter_by(persona_id=id).delete()
        # Eliminar órdenes judiciales asociadas
        OrdenJudicial.query.filter_by(persona_id=id).delete()
        
        db.session.delete(persona)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Persona eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en delete_persona: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS API PARA ÓRDENES DE CAPTURA ====================

@app.route('/api/ordenes_captura')
@login_required
def api_ordenes_captura():
    """Obtiene todas las órdenes de captura"""
    try:
        ordenes = OrdenCaptura.query.order_by(OrdenCaptura.id.desc()).all()
        resultados = []
        for o in ordenes:
            p = Persona.query.get(o.persona_id)
            resultados.append({
                'id': o.id,
                'persona_id': o.persona_id,
                'persona_nombre': p.nombre if p else 'N/A',
                'persona_cedula': p.cedula if p else 'N/A',
                'numero_orden': o.numero_orden,
                'monto_deuda': float(o.monto_deuda) if o.monto_deuda else 0,
                'fecha_emision': o.fecha_emision,
                'fecha_vencimiento': o.fecha_vencimiento,
                'juzgado': o.juzgado,
                'expediente': o.expediente,
                'estado': o.estado,
                'resultado': o.resultado,
                'observaciones': o.observaciones,
                'latitud': o.latitud,
                'longitud': o.longitud,
                'direccion_ubicacion': o.direccion_ubicacion,
                'fecha_registro': o.fecha_registro
            })
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en api_ordenes_captura: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes_captura/<int:id>')
@login_required
def api_orden_captura_unica(id):
    """Obtiene una orden de captura específica por su ID"""
    try:
        o = OrdenCaptura.query.get_or_404(id)
        p = Persona.query.get(o.persona_id)
        return jsonify({
            'id': o.id,
            'persona_id': o.persona_id,
            'persona_nombre': p.nombre if p else 'N/A',
            'persona_cedula': p.cedula if p else 'N/A',
            'numero_orden': o.numero_orden,
            'monto_deuda': float(o.monto_deuda) if o.monto_deuda else 0,
            'fecha_emision': o.fecha_emision,
            'fecha_vencimiento': o.fecha_vencimiento,
            'juzgado': o.juzgado,
            'expediente': o.expediente,
            'estado': o.estado,
            'resultado': o.resultado,
            'observaciones': o.observaciones,
            'latitud': o.latitud,
            'longitud': o.longitud,
            'direccion_ubicacion': o.direccion_ubicacion,
            'fecha_registro': o.fecha_registro
        })
    except Exception as e:
        print(f"❌ Error en api_orden_captura_unica: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes_captura', methods=['POST'])
@login_required
def crear_orden_captura():
    """Crea una nueva orden de captura"""
    try:
        data = request.json
        
        # Validar campos requeridos
        if not data.get('persona_id'):
            return jsonify({'success': False, 'error': 'Debe seleccionar una persona'}), 400
        if not data.get('numero_orden'):
            return jsonify({'success': False, 'error': 'El número de orden es requerido'}), 400
        if not data.get('juzgado'):
            return jsonify({'success': False, 'error': 'El juzgado es requerido'}), 400
        
        # Verificar que la persona existe
        persona = Persona.query.get(data['persona_id'])
        if not persona:
            return jsonify({'success': False, 'error': 'La persona seleccionada no existe'}), 404
        
        # Verificar que no exista una orden con el mismo número
        existente = OrdenCaptura.query.filter_by(numero_orden=data['numero_orden']).first()
        if existente:
            return jsonify({'success': False, 'error': 'Ya existe una orden con este número'}), 400
        
        # Crear la orden
        orden = OrdenCaptura(
            persona_id=data['persona_id'],
            numero_orden=data['numero_orden'],
            monto_deuda=float(data.get('monto_deuda', 0)),
            juzgado=data['juzgado'].upper(),
            expediente=data.get('expediente', data['numero_orden']),
            fecha_emision=data.get('fecha_emision', datetime.now().strftime('%Y-%m-%d')),
            fecha_vencimiento=data.get('fecha_vencimiento', ''),
            estado=data.get('estado', 'ACTIVA'),
            resultado=data.get('resultado', ''),
            observaciones=data.get('observaciones', ''),
            latitud=data.get('latitud'),
            longitud=data.get('longitud'),
            direccion_ubicacion=data.get('direccion_ubicacion', ''),
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.session.add(orden)
        db.session.commit()
        
        return jsonify({'success': True, 'id': orden.id, 'message': 'Orden creada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en crear_orden_captura: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ordenes_captura/<int:id>', methods=['PUT'])
@login_required
def actualizar_orden_captura(id):
    """Actualiza una orden de captura existente"""
    try:
        orden = OrdenCaptura.query.get_or_404(id)
        data = request.json
        
        # Validar campos requeridos
        if not data.get('persona_id'):
            return jsonify({'success': False, 'error': 'Debe seleccionar una persona'}), 400
        if not data.get('numero_orden'):
            return jsonify({'success': False, 'error': 'El número de orden es requerido'}), 400
        if not data.get('juzgado'):
            return jsonify({'success': False, 'error': 'El juzgado es requerido'}), 400
        
        # Verificar que la persona existe
        persona = Persona.query.get(data['persona_id'])
        if not persona:
            return jsonify({'success': False, 'error': 'La persona seleccionada no existe'}), 404
        
        # Verificar que no exista otra orden con el mismo número
        existente = OrdenCaptura.query.filter(
            OrdenCaptura.numero_orden == data['numero_orden'],
            OrdenCaptura.id != id
        ).first()
        if existente:
            return jsonify({'success': False, 'error': 'Ya existe otra orden con este número'}), 400
        
        # Actualizar la orden
        orden.persona_id = data['persona_id']
        orden.numero_orden = data['numero_orden']
        orden.monto_deuda = float(data.get('monto_deuda', 0))
        orden.juzgado = data['juzgado'].upper()
        orden.expediente = data.get('expediente', data['numero_orden'])
        orden.fecha_emision = data.get('fecha_emision', datetime.now().strftime('%Y-%m-%d'))
        orden.fecha_vencimiento = data.get('fecha_vencimiento', '')
        orden.estado = data.get('estado', 'ACTIVA')
        orden.resultado = data.get('resultado', '')
        orden.observaciones = data.get('observaciones', '')
        orden.latitud = data.get('latitud')
        orden.longitud = data.get('longitud')
        orden.direccion_ubicacion = data.get('direccion_ubicacion', '')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Orden actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en actualizar_orden_captura: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ordenes_captura/<int:id>', methods=['DELETE'])
@login_required
def eliminar_orden_captura(id):
    """Elimina una orden de captura"""
    try:
        orden = OrdenCaptura.query.get_or_404(id)
        db.session.delete(orden)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Orden eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en eliminar_orden_captura: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTAS API PARA ACCIONES OPERATIVAS ====================

@app.route('/api/acciones_operativas')
@login_required
def api_acciones_operativas():
    """Obtiene todas las acciones operativas"""
    try:
        acciones = AccionOperativa.query.order_by(AccionOperativa.fecha.desc()).all()
        return jsonify([{
            'id': a.id,
            'cod_unidad': a.cod_unidad,
            'fecha': a.fecha,
            'hora_inicio': a.hora_inicio,
            'hora_fin': a.hora_fin,
            'lugar': a.lugar,
            'accion_realizada': a.accion_realizada,
            'instituciones': a.instituciones,
            'escuadra_1': a.escuadra_1,
            'escuadra_2': a.escuadra_2,
            'escuadra_3': a.escuadra_3,
            'escuadra_4': a.escuadra_4,
            'mando': a.mando,
            'oficiales': a.oficiales,
            'personas_abordadas': a.personas_abordadas or 0,
            'personas_investigadas_oij': a.personas_investigadas_oij or 0,
            'motos': a.motos or 0,
            'carros': a.carros or 0,
            'armas': a.armas or 0,
            'control_carretera': a.control_carretera or 0,
            'op_inter_institucionales': a.op_inter_institucionales or 0,
            'ganado_seguro': a.ganado_seguro or 0,
            'visitas_comercio': a.visitas_comercio or 0,
            'paso_escolar': a.paso_escolar or 0,
            'notificaciones': a.notificaciones or 0,
            'guardas_seguridad': a.guardas_seguridad or 0,
            'orden_apremio_corporal': a.orden_apremio_corporal or 0,
            'partes_transito': a.partes_transito or 0,
            'placas_decomisadas': a.placas_decomisadas or 0,
            'informes_policiales': a.informes_policiales or 0,
            'incidentes_cerrados': a.incidentes_cerrados or 0,
            'vehiculos_incautados': a.vehiculos_incautados or 0,
            'puchos_marihuana': a.puchos_marihuana or 0,
            'cigarillos_marihuana': a.cigarillos_marihuana or 0,
            'gramos_marihuana': float(a.gramos_marihuana) if a.gramos_marihuana else 0,
            'piedras_crack': a.piedras_crack or 0,
            'gramos_crack': float(a.gramos_crack) if a.gramos_crack else 0,
            'puntas_cocaina': a.puntas_cocaina or 0,
            'gramos_cocaina': float(a.gramos_cocaina) if a.gramos_cocaina else 0,
            'armas_fuego': a.armas_fuego or 0,
            'armas_blancas': a.armas_blancas or 0,
            'dinero_efectivo': float(a.dinero_efectivo) if a.dinero_efectivo else 0,
            'otros_incautaciones': a.otros_incautaciones or '',
            'anotaciones': a.anotaciones or '',
            'fecha_registro': a.fecha_registro,
            'usuario_registro': a.usuario_registro,
            'estado': a.estado
        } for a in acciones])
    except Exception as e:
        print(f"❌ Error en api_acciones_operativas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/acciones_operativas/<int:id>')
@login_required
def api_accion_operativa_unica(id):
    """Obtiene una acción operativa específica"""
    try:
        a = AccionOperativa.query.get_or_404(id)
        return jsonify({
            'id': a.id,
            'cod_unidad': a.cod_unidad,
            'fecha': a.fecha,
            'hora_inicio': a.hora_inicio,
            'hora_fin': a.hora_fin,
            'lugar': a.lugar,
            'accion_realizada': a.accion_realizada,
            'instituciones': a.instituciones,
            'escuadra_1': a.escuadra_1,
            'escuadra_2': a.escuadra_2,
            'escuadra_3': a.escuadra_3,
            'escuadra_4': a.escuadra_4,
            'mando': a.mando,
            'oficiales': a.oficiales,
            'personas_abordadas': a.personas_abordadas or 0,
            'personas_investigadas_oij': a.personas_investigadas_oij or 0,
            'motos': a.motos or 0,
            'carros': a.carros or 0,
            'armas': a.armas or 0,
            'control_carretera': a.control_carretera or 0,
            'op_inter_institucionales': a.op_inter_institucionales or 0,
            'ganado_seguro': a.ganado_seguro or 0,
            'visitas_comercio': a.visitas_comercio or 0,
            'paso_escolar': a.paso_escolar or 0,
            'notificaciones': a.notificaciones or 0,
            'guardas_seguridad': a.guardas_seguridad or 0,
            'orden_apremio_corporal': a.orden_apremio_corporal or 0,
            'partes_transito': a.partes_transito or 0,
            'placas_decomisadas': a.placas_decomisadas or 0,
            'informes_policiales': a.informes_policiales or 0,
            'incidentes_cerrados': a.incidentes_cerrados or 0,
            'vehiculos_incautados': a.vehiculos_incautados or 0,
            'puchos_marihuana': a.puchos_marihuana or 0,
            'cigarillos_marihuana': a.cigarillos_marihuana or 0,
            'gramos_marihuana': float(a.gramos_marihuana) if a.gramos_marihuana else 0,
            'piedras_crack': a.piedras_crack or 0,
            'gramos_crack': float(a.gramos_crack) if a.gramos_crack else 0,
            'puntas_cocaina': a.puntas_cocaina or 0,
            'gramos_cocaina': float(a.gramos_cocaina) if a.gramos_cocaina else 0,
            'armas_fuego': a.armas_fuego or 0,
            'armas_blancas': a.armas_blancas or 0,
            'dinero_efectivo': float(a.dinero_efectivo) if a.dinero_efectivo else 0,
            'otros_incautaciones': a.otros_incautaciones or '',
            'anotaciones': a.anotaciones or '',
            'fecha_registro': a.fecha_registro,
            'usuario_registro': a.usuario_registro,
            'estado': a.estado
        })
    except Exception as e:
        print(f"❌ Error en api_accion_operativa_unica: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/acciones_operativas', methods=['POST'])
@login_required
def crear_accion_operativa():
    """Crea una nueva acción operativa"""
    try:
        data = request.json
        
        # Validar campos requeridos
        if not data.get('cod_unidad'):
            return jsonify({'success': False, 'error': 'El código de unidad es requerido'}), 400
        if not data.get('fecha'):
            return jsonify({'success': False, 'error': 'La fecha es requerida'}), 400
        if not data.get('lugar'):
            return jsonify({'success': False, 'error': 'El lugar es requerido'}), 400
        if not data.get('accion_realizada'):
            return jsonify({'success': False, 'error': 'La acción realizada es requerida'}), 400
        if not data.get('mando'):
            return jsonify({'success': False, 'error': 'El mando es requerido'}), 400
        if not data.get('oficiales'):
            return jsonify({'success': False, 'error': 'Los oficiales son requeridos'}), 400
        
        # Crear la acción
        accion = AccionOperativa(
            cod_unidad=data['cod_unidad'],
            fecha=data['fecha'],
            hora_inicio=data.get('hora_inicio', ''),
            hora_fin=data.get('hora_fin', ''),
            lugar=data['lugar'],
            accion_realizada=data['accion_realizada'],
            instituciones=data.get('instituciones', ''),
            escuadra_1=data.get('escuadra_1', False),
            escuadra_2=data.get('escuadra_2', False),
            escuadra_3=data.get('escuadra_3', False),
            escuadra_4=data.get('escuadra_4', False),
            mando=data['mando'],
            oficiales=data['oficiales'],
            personas_abordadas=int(data.get('personas_abordadas', 0)),
            personas_investigadas_oij=int(data.get('personas_investigadas_oij', 0)),
            motos=int(data.get('motos', 0)),
            carros=int(data.get('carros', 0)),
            armas=int(data.get('armas', 0)),
            control_carretera=int(data.get('control_carretera', 0)),
            op_inter_institucionales=int(data.get('op_inter_institucionales', 0)),
            ganado_seguro=int(data.get('ganado_seguro', 0)),
            visitas_comercio=int(data.get('visitas_comercio', 0)),
            paso_escolar=int(data.get('paso_escolar', 0)),
            notificaciones=int(data.get('notificaciones', 0)),
            guardas_seguridad=int(data.get('guardas_seguridad', 0)),
            orden_apremio_corporal=int(data.get('orden_apremio_corporal', 0)),
            partes_transito=int(data.get('partes_transito', 0)),
            placas_decomisadas=int(data.get('placas_decomisadas', 0)),
            informes_policiales=int(data.get('informes_policiales', 0)),
            incidentes_cerrados=int(data.get('incidentes_cerrados', 0)),
            vehiculos_incautados=int(data.get('vehiculos_incautados', 0)),
            puchos_marihuana=int(data.get('puchos_marihuana', 0)),
            cigarillos_marihuana=int(data.get('cigarillos_marihuana', 0)),
            gramos_marihuana=float(data.get('gramos_marihuana', 0)),
            piedras_crack=int(data.get('piedras_crack', 0)),
            gramos_crack=float(data.get('gramos_crack', 0)),
            puntas_cocaina=int(data.get('puntas_cocaina', 0)),
            gramos_cocaina=float(data.get('gramos_cocaina', 0)),
            armas_fuego=int(data.get('armas_fuego', 0)),
            armas_blancas=int(data.get('armas_blancas', 0)),
            dinero_efectivo=float(data.get('dinero_efectivo', 0)),
            otros_incautaciones=data.get('otros_incautaciones', ''),
            anotaciones=data.get('anotaciones', ''),
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            usuario_registro=current_user.username,
            estado=data.get('estado', 'ACTIVA')
        )
        
        db.session.add(accion)
        db.session.commit()
        
        return jsonify({'success': True, 'id': accion.id, 'message': 'Acción operativa creada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en crear_accion_operativa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/acciones_operativas/<int:id>', methods=['PUT'])
@login_required
def actualizar_accion_operativa(id):
    """Actualiza una acción operativa existente"""
    try:
        accion = AccionOperativa.query.get_or_404(id)
        data = request.json
        
        # Validar campos requeridos
        if not data.get('cod_unidad'):
            return jsonify({'success': False, 'error': 'El código de unidad es requerido'}), 400
        if not data.get('fecha'):
            return jsonify({'success': False, 'error': 'La fecha es requerida'}), 400
        if not data.get('lugar'):
            return jsonify({'success': False, 'error': 'El lugar es requerido'}), 400
        if not data.get('accion_realizada'):
            return jsonify({'success': False, 'error': 'La acción realizada es requerida'}), 400
        if not data.get('mando'):
            return jsonify({'success': False, 'error': 'El mando es requerido'}), 400
        if not data.get('oficiales'):
            return jsonify({'success': False, 'error': 'Los oficiales son requeridos'}), 400
        
        # Actualizar la acción
        accion.cod_unidad = data['cod_unidad']
        accion.fecha = data['fecha']
        accion.hora_inicio = data.get('hora_inicio', '')
        accion.hora_fin = data.get('hora_fin', '')
        accion.lugar = data['lugar']
        accion.accion_realizada = data['accion_realizada']
        accion.instituciones = data.get('instituciones', '')
        accion.escuadra_1 = data.get('escuadra_1', False)
        accion.escuadra_2 = data.get('escuadra_2', False)
        accion.escuadra_3 = data.get('escuadra_3', False)
        accion.escuadra_4 = data.get('escuadra_4', False)
        accion.mando = data['mando']
        accion.oficiales = data['oficiales']
        accion.personas_abordadas = int(data.get('personas_abordadas', 0))
        accion.personas_investigadas_oij = int(data.get('personas_investigadas_oij', 0))
        accion.motos = int(data.get('motos', 0))
        accion.carros = int(data.get('carros', 0))
        accion.armas = int(data.get('armas', 0))
        accion.control_carretera = int(data.get('control_carretera', 0))
        accion.op_inter_institucionales = int(data.get('op_inter_institucionales', 0))
        accion.ganado_seguro = int(data.get('ganado_seguro', 0))
        accion.visitas_comercio = int(data.get('visitas_comercio', 0))
        accion.paso_escolar = int(data.get('paso_escolar', 0))
        accion.notificaciones = int(data.get('notificaciones', 0))
        accion.guardas_seguridad = int(data.get('guardas_seguridad', 0))
        accion.orden_apremio_corporal = int(data.get('orden_apremio_corporal', 0))
        accion.partes_transito = int(data.get('partes_transito', 0))
        accion.placas_decomisadas = int(data.get('placas_decomisadas', 0))
        accion.informes_policiales = int(data.get('informes_policiales', 0))
        accion.incidentes_cerrados = int(data.get('incidentes_cerrados', 0))
        accion.vehiculos_incautados = int(data.get('vehiculos_incautados', 0))
        accion.puchos_marihuana = int(data.get('puchos_marihuana', 0))
        accion.cigarillos_marihuana = int(data.get('cigarillos_marihuana', 0))
        accion.gramos_marihuana = float(data.get('gramos_marihuana', 0))
        accion.piedras_crack = int(data.get('piedras_crack', 0))
        accion.gramos_crack = float(data.get('gramos_crack', 0))
        accion.puntas_cocaina = int(data.get('puntas_cocaina', 0))
        accion.gramos_cocaina = float(data.get('gramos_cocaina', 0))
        accion.armas_fuego = int(data.get('armas_fuego', 0))
        accion.armas_blancas = int(data.get('armas_blancas', 0))
        accion.dinero_efectivo = float(data.get('dinero_efectivo', 0))
        accion.otros_incautaciones = data.get('otros_incautaciones', '')
        accion.anotaciones = data.get('anotaciones', '')
        accion.estado = data.get('estado', 'ACTIVA')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Acción operativa actualizada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en actualizar_accion_operativa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/acciones_operativas/<int:id>', methods=['DELETE'])
@login_required
def eliminar_accion_operativa(id):
    """Elimina una acción operativa"""
    try:
        accion = AccionOperativa.query.get_or_404(id)
        db.session.delete(accion)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Acción operativa eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en eliminar_accion_operativa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTAS API PARA INCIDENTES ====================

@app.route('/api/incidentes')
@login_required
def api_incidentes():
    """Obtiene todos los incidentes para la página de incidentes"""
    try:
        incidentes = Incidente.query.order_by(Incidente.fecha_incidente.desc()).all()
        return jsonify([{
            'id': i.id,
            'oficial_actuante': i.oficial_actuante,
            'oficial_asistente': i.oficial_asistente,
            'numero_incidente': i.numero_incidente,
            'tipo_incidente': i.tipo_incidente,
            'descripcion': i.descripcion,
            'diligencias_policiales': i.diligencias_policiales,
            'aprehendidos': i.aprehendidos or 0,
            'ofendidos': i.ofendidos or 0,
            'testigos': i.testigos or 0,
            'personas_interes': i.personas_interes or 0,
            'vehiculos_involucrados': i.vehiculos_involucrados or 0,
            'decomisos': i.decomisos,
            'informe_policial': i.informe_policial,
            'numero_informe': i.numero_informe,
            'acta_decomiso': i.acta_decomiso,
            'numero_acta_decomiso': i.numero_acta_decomiso,
            'fecha_incidente': i.fecha_incidente,
            'lugar': i.lugar,
            'latitud': i.latitud,
            'longitud': i.longitud,
            'direccion_ubicacion': i.direccion_ubicacion,
            'estado': i.estado,
            'creado_por': i.creado_por,
            'fecha_registro': i.fecha_registro
        } for i in incidentes])
    except Exception as e:
        print(f"❌ Error en api_incidentes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/incidentes/<int:id>')
@login_required
def api_incidente_unico(id):
    """Obtiene un incidente específico"""
    try:
        i = Incidente.query.get_or_404(id)
        return jsonify({
            'id': i.id,
            'oficial_actuante': i.oficial_actuante,
            'oficial_asistente': i.oficial_asistente,
            'numero_incidente': i.numero_incidente,
            'tipo_incidente': i.tipo_incidente,
            'descripcion': i.descripcion,
            'diligencias_policiales': i.diligencias_policiales,
            'aprehendidos': i.aprehendidos or 0,
            'ofendidos': i.ofendidos or 0,
            'testigos': i.testigos or 0,
            'personas_interes': i.personas_interes or 0,
            'vehiculos_involucrados': i.vehiculos_involucrados or 0,
            'decomisos': i.decomisos,
            'informe_policial': i.informe_policial,
            'numero_informe': i.numero_informe,
            'acta_decomiso': i.acta_decomiso,
            'numero_acta_decomiso': i.numero_acta_decomiso,
            'fecha_incidente': i.fecha_incidente,
            'lugar': i.lugar,
            'latitud': i.latitud,
            'longitud': i.longitud,
            'direccion_ubicacion': i.direccion_ubicacion,
            'estado': i.estado,
            'creado_por': i.creado_por,
            'fecha_registro': i.fecha_registro
        })
    except Exception as e:
        print(f"❌ Error en api_incidente_unico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ===== RUTA POST PARA CREAR INCIDENTES =====
@app.route('/api/incidentes', methods=['POST'])
@login_required
@permiso_requerido('crear_incidentes')
def api_crear_incidente():
    """Crea un nuevo incidente"""
    try:
        data = request.json
        
        # Validar campos requeridos
        if not data.get('oficial_actuante'):
            return jsonify({'success': False, 'error': 'El oficial actuante es requerido'}), 400
        if not data.get('numero_incidente'):
            return jsonify({'success': False, 'error': 'El número de incidente es requerido'}), 400
        if not data.get('tipo_incidente'):
            return jsonify({'success': False, 'error': 'El tipo de incidente es requerido'}), 400
        if not data.get('descripcion'):
            return jsonify({'success': False, 'error': 'La descripción es requerida'}), 400
        if not data.get('fecha_incidente'):
            return jsonify({'success': False, 'error': 'La fecha es requerida'}), 400
        
        # Crear el incidente
        incidente = Incidente(
            oficial_actuante=data['oficial_actuante'],
            oficial_asistente=data.get('oficial_asistente', ''),
            numero_incidente=data['numero_incidente'],
            tipo_incidente=data['tipo_incidente'],
            descripcion=data['descripcion'],
            diligencias_policiales=data.get('diligencias_policiales', ''),
            aprehendidos=int(data.get('aprehendidos', 0)),
            ofendidos=int(data.get('ofendidos', 0)),
            testigos=int(data.get('testigos', 0)),
            personas_interes=int(data.get('personas_interes', 0)),
            vehiculos_involucrados=int(data.get('vehiculos_involucrados', 0)),
            decomisos=data.get('decomisos', ''),
            informe_policial=data.get('informe_policial', False),
            numero_informe=data.get('numero_informe', ''),
            acta_decomiso=data.get('acta_decomiso', False),
            numero_acta_decomiso=data.get('numero_acta_decomiso', ''),
            fecha_incidente=data['fecha_incidente'],
            lugar=data.get('lugar', ''),
            latitud=data.get('latitud'),
            longitud=data.get('longitud'),
            direccion_ubicacion=data.get('direccion_ubicacion', ''),
            estado=data.get('estado', 'ACTIVO'),
            creado_por=current_user.username,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        db.session.add(incidente)
        db.session.commit()
        
        return jsonify({'success': True, 'id': incidente.id, 'message': 'Incidente creado correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_crear_incidente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RUTA PUT PARA ACTUALIZAR INCIDENTES =====
@app.route('/api/incidentes/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('editar_incidentes')
def api_actualizar_incidente(id):
    """Actualiza un incidente existente"""
    try:
        incidente = Incidente.query.get_or_404(id)
        data = request.json
        
        # Actualizar campos
        incidente.oficial_actuante = data.get('oficial_actuante', incidente.oficial_actuante)
        incidente.oficial_asistente = data.get('oficial_asistente', incidente.oficial_asistente)
        incidente.numero_incidente = data.get('numero_incidente', incidente.numero_incidente)
        incidente.tipo_incidente = data.get('tipo_incidente', incidente.tipo_incidente)
        incidente.descripcion = data.get('descripcion', incidente.descripcion)
        incidente.diligencias_policiales = data.get('diligencias_policiales', incidente.diligencias_policiales)
        incidente.aprehendidos = int(data.get('aprehendidos', incidente.aprehendidos or 0))
        incidente.ofendidos = int(data.get('ofendidos', incidente.ofendidos or 0))
        incidente.testigos = int(data.get('testigos', incidente.testigos or 0))
        incidente.personas_interes = int(data.get('personas_interes', incidente.personas_interes or 0))
        incidente.vehiculos_involucrados = int(data.get('vehiculos_involucrados', incidente.vehiculos_involucrados or 0))
        incidente.decomisos = data.get('decomisos', incidente.decomisos)
        incidente.informe_policial = data.get('informe_policial', incidente.informe_policial)
        incidente.numero_informe = data.get('numero_informe', incidente.numero_informe)
        incidente.acta_decomiso = data.get('acta_decomiso', incidente.acta_decomiso)
        incidente.numero_acta_decomiso = data.get('numero_acta_decomiso', incidente.numero_acta_decomiso)
        incidente.fecha_incidente = data.get('fecha_incidente', incidente.fecha_incidente)
        incidente.lugar = data.get('lugar', incidente.lugar)
        incidente.latitud = data.get('latitud', incidente.latitud)
        incidente.longitud = data.get('longitud', incidente.longitud)
        incidente.direccion_ubicacion = data.get('direccion_ubicacion', incidente.direccion_ubicacion)
        incidente.estado = data.get('estado', incidente.estado)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Incidente actualizado correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_actualizar_incidente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== RUTA DELETE PARA ELIMINAR INCIDENTES =====
@app.route('/api/incidentes/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_incidentes')
def api_eliminar_incidente(id):
    """Elimina un incidente"""
    try:
        incidente = Incidente.query.get_or_404(id)
        db.session.delete(incidente)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Incidente eliminado correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en api_eliminar_incidente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== RUTAS API PARA TIPOS DE INCIDENTE ====================

@app.route('/api/tipos_incidente')
@login_required
def api_tipos_incidente():
    """Obtiene la lista de tipos de incidente"""
    try:
        tipos = [
            'ROBO', 'HURTO', 'ALTERACION AL ORDEN PUBLICO', 'AGRESIÓN', 'LESIONES', 'HOMICIDIO', 'VIOLENCIA DOMÉSTICA',
            'ALLANAMIENTO', 'DAÑOS', 'AMENAZAS', 'ACOSO', 'ESTAFA', 'APROPIACIÓN INDEBIDA',
            'TRÁFICO DE DROGAS', 'POSESIÓN DE DROGAS', 'CONDUCCIÓN TEMERARIA', 'ACCIDENTE DE TRÁNSITO',
            'ATENTADO A LA AUTORIDAD', 'RESISTENCIA', 'PERTURBACIÓN DEL ORDEN PÚBLICO',
            'INCUMPLIMIENTO DE MEDIDAS', 'VIOLACIÓN DE DOMICILIO', 'USURPACIÓN',
            'INCENDIO', 'LESIONES CULPOSAS', 'MENOR EN RIESGO', 'SUICIDIO', 'HALLAZGO DE CADÁVER',
            'PERSONA EXTRAVIADA', 'VIOLENCIA CONTRA LA MUJER', 'VIOLENCIA CONTRA MENORES',
            'TRATA DE PERSONAS', 'SECUESTRO', 'EXTORSIÓN', 'ASALTO', 'ROBO DE VEHÍCULO',
            'ROBO COMERCIO', 'ROBO RESIDENCIA', 'VEHICULO ABANDONADO', 'ESTAFA INFORMÁTICA',
            'HALLAZGO DE DROGA', 'PORNOGRAFÍA INFANTIL', 'DELITOS INFORMÁTICOS', 'FALSIFICACIÓN',
            'DELITO ADUANERO', 'CONTRABANDO', 'CAZA ILEGAL', 'PESCA ILEGAL', 'DELITO AMBIENTAL',
            'MALTRATO ANIMAL', 'TENENCIA ILEGAL DE ARMAS', 'PORTACIÓN ILEGAL DE ARMAS',
            'DISPARO AL AIRE', 'RIÑA', 'BALACERA', 'BANDALISMO', 'NARCOMENUDEO',
            'MICROTRÁFICO', 'LABORATORIO DE DROGAS', 'CULTIVO DE DROGAS', 'LAVADO DE ACTIVOS',
            'ASOCIACIÓN ILÍCITA', 'ESCANDALO MUSICAL', 'FALSIFICACIÓN DE DOCUMENTOS', 'USURPACIÓN DE IDENTIDAD',
            'SUPLANTACIÓN DE IDENTIDAD', 'FRAUDE', 'DELITO FINANCIERO', 'CORRUPCIÓN',
            'COHECHO', 'ACOMPAÑAMIENTO POLICIAL', 'NEGLIGENCIA', 'OMISIÓN DE DEBERES', 'ABUSO DE AUTORIDAD',
            'VIOLACIÓN DE DATOS', 'SECRETO PROFESIONAL', 'CALUMNIA', 'INJURIA', 'DIFAMACIÓN',
            'ACOSO LABORAL', 'ACOSO ESCOLAR', 'DISCRIMINACIÓN', 'DISCURSO DE ODIO',
            'VIOLACIÓN DE DERECHOS HUMANOS', 'DETENCIÓN ILEGAL', 'TORTURA', 'DESAPARICIÓN FORZADA',
            'VERIFICACION DE DOMICILIO', 'ALTERACION DE SEÑAS Y MARCAS', 'VEHICULO SOSPECHOSO',
            'PERSONA HERIDA', 'PERSONA AGRESIVA', 'ACOMPAÑAMIENTO REGIMEN DE VISITA'
        ]
        return jsonify(sorted(tipos))
    except Exception as e:
        print(f"❌ Error en tipos_incidente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS API PARA ANTECEDENTES ====================

@app.route('/api/antecedentes/<int:persona_id>')
@login_required
def api_antecedentes_por_persona(persona_id):
    """Obtiene los antecedentes de una persona específica"""
    try:
        antecedentes = Antecedente.query.filter_by(persona_id=persona_id).all()
        return jsonify([{
            'id': a.id,
            'delito': a.delito,
            'fecha_delito': a.fecha_delito or '',
            'lugar': a.lugar or '',
            'juzgado': a.juzgado or '',
            'estado': a.estado or ''
        } for a in antecedentes])
    except Exception as e:
        print(f"❌ Error en api_antecedentes_por_persona: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== RUTAS API PARA ESTADÍSTICAS Y MAPAS ====================

@app.route('/api/estadisticas/evolucion')
@login_required
def api_estadisticas_evolucion():
    """Obtiene la evolución mensual de órdenes"""
    try:
        meses = int(request.args.get('meses', 6))
        hoy = datetime.now()
        fechas = []
        ordenes_creadas = []
        ordenes_vencidas = []
        
        for i in range(meses - 1, -1, -1):
            fecha = hoy - timedelta(days=30 * i)
            mes_str = fecha.strftime('%Y-%m')
            nombre_mes = fecha.strftime('%b %Y')
            fechas.append(nombre_mes)
            
            creadas = OrdenCaptura.query.filter(OrdenCaptura.fecha_registro.like(f'{mes_str}%')).count()
            ordenes_creadas.append(creadas)
            
            vencidas = OrdenCaptura.query.filter(OrdenCaptura.fecha_vencimiento.like(f'{mes_str}%')).count()
            ordenes_vencidas.append(vencidas)
        
        return jsonify({
            'meses': fechas,
            'ordenes_creadas': ordenes_creadas,
            'ordenes_vencidas': ordenes_vencidas
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_evolucion: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/estadisticas/tendencia')
@login_required
def api_estadisticas_tendencia():
    """Obtiene la tendencia de deuda mensual"""
    try:
        hoy = datetime.now()
        meses = []
        deuda_por_mes = []
        
        for i in range(11, -1, -1):
            fecha = hoy - timedelta(days=30 * i)
            mes_str = fecha.strftime('%Y-%m')
            nombre_mes = fecha.strftime('%b %Y')
            meses.append(nombre_mes)
            
            deuda = db.session.query(func.sum(OrdenCaptura.monto_deuda)).filter(
                OrdenCaptura.fecha_emision.like(f'{mes_str}%')
            ).scalar() or 0
            deuda_por_mes.append(float(deuda))
        
        return jsonify({
            'meses': meses,
            'deuda_por_mes': deuda_por_mes
        })
    except Exception as e:
        print(f"❌ Error en api_estadisticas_tendencia: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/incidentes/geolocalizados')
@login_required
def api_incidentes_geolocalizados():
    """Obtiene los incidentes geolocalizados para el mapa"""
    try:
        mes_actual = datetime.now().strftime('%m')
        año_actual = datetime.now().strftime('%Y')
        
        incidentes = Incidente.query.filter(
            Incidente.fecha_incidente.like(f'{año_actual}-{mes_actual}%'),
            Incidente.latitud.isnot(None),
            Incidente.longitud.isnot(None)
        ).all()
        
        resultados = []
        for i in incidentes:
            resultados.append({
                'id': i.id,
                'numero_incidente': i.numero_incidente,
                'tipo_incidente': i.tipo_incidente,
                'descripcion': i.descripcion[:150] + '...' if len(i.descripcion) > 150 else i.descripcion,
                'fecha_incidente': i.fecha_incidente,
                'lugar': i.lugar,
                'oficial_actuante': i.oficial_actuante,
                'aprehendidos': i.aprehendidos or 0,
                'latitud': i.latitud,
                'longitud': i.longitud,
                'direccion_ubicacion': i.direccion_ubicacion,
                'estado': i.estado
            })
        
        return jsonify(resultados)
    except Exception as e:
        print(f"❌ Error en api_incidentes_geolocalizados: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/incidentes/geolocalizados/resumen')
@login_required
def api_incidentes_resumen_mapa():
    """Obtiene el resumen de incidentes para el mapa"""
    try:
        mes_actual = datetime.now().strftime('%m')
        año_actual = datetime.now().strftime('%Y')
        
        incidentes = Incidente.query.filter(
            Incidente.fecha_incidente.like(f'{año_actual}-{mes_actual}%'),
            Incidente.latitud.isnot(None),
            Incidente.longitud.isnot(None)
        ).all()
        
        tipos = {}
        for i in incidentes:
            tipo = i.tipo_incidente or 'Sin clasificar'
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        top_tipos = sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'total': len(incidentes),
            'tipos': [{'nombre': t[0], 'cantidad': t[1]} for t in top_tipos]
        })
    except Exception as e:
        print(f"❌ Error en api_incidentes_resumen_mapa: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ==================== CAMBIAR CONTRASEÑA ====================
@app.route('/cambiar_password')
@login_required
def cambiar_password_page():
    return render_template('cambiar_password.html')

@app.route('/api/cambiar_password', methods=['POST'])
@login_required
def cambiar_password_api():
    try:
        data = request.json
        password_actual = data.get('password_actual')
        password_nueva = data.get('password_nueva')
        password_confirmar = data.get('password_confirmar')
        
        usuario = Usuario.query.get(current_user.id)
        
        if not usuario.check_password(password_actual):
            return jsonify({'success': False, 'error': 'La contraseña actual es incorrecta'}), 400
        
        if len(password_nueva) < 8:
            return jsonify({'success': False, 'error': 'La nueva contraseña debe tener al menos 8 caracteres'}), 400
        
        if password_nueva != password_confirmar:
            return jsonify({'success': False, 'error': 'Las contraseñas no coinciden'}), 400
        
        usuario.set_password(password_nueva)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Contraseña cambiada correctamente'})
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== FUNCIONES AUXILIARES ====================
def generar_contenido_machote_simple(machote_id):
    preguntas = Pregunta.query.filter_by(machote_id=machote_id).order_by(Pregunta.orden).all()
    contenido = ''
    for p in preguntas:
        contenido += f"{p.titulo}: {{{{ {p.variable} }}}}\n"
    return contenido

if __name__ == '__main__':
    app.run(debug=True, host='100.80.109.7', port=3000)