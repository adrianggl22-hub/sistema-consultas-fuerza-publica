from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'clave_secreta_12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema_consultas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración para subir fotos
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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
    numero_orden = db.Column(db.String(50), unique=True, nullable=False)
    monto_deuda = db.Column(db.Float, nullable=False)
    fecha_emision = db.Column(db.String(20), nullable=False)
    fecha_vencimiento = db.Column(db.String(20))
    juzgado = db.Column(db.String(100), nullable=False)
    expediente = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), default='ACTIVA')
    fecha_registro = db.Column(db.String(50))

class AccionOperativa(db.Model):
    __tablename__ = 'acciones_operativas'
    id = db.Column(db.Integer, primary_key=True)
    
    # Datos de la acción
    cod_unidad = db.Column(db.String(20), nullable=False)
    fecha = db.Column(db.String(20), nullable=False)
    hora_inicio = db.Column(db.String(10), nullable=False)
    hora_fin = db.Column(db.String(10), nullable=False)
    lugar = db.Column(db.String(200), nullable=False)
    accion_realizada = db.Column(db.Text, nullable=False)
    instituciones = db.Column(db.String(200))
    
    # Escuadras
    escuadra_1 = db.Column(db.Boolean, default=False)
    escuadra_2 = db.Column(db.Boolean, default=False)
    escuadra_3 = db.Column(db.Boolean, default=False)
    escuadra_4 = db.Column(db.Boolean, default=False)
    
    # Personal
    mando = db.Column(db.String(100), nullable=False)
    oficiales = db.Column(db.Text, nullable=False)
    
    # Investigados
    personas_abordadas = db.Column(db.Integer, default=0)
    personas_investigadas_oij = db.Column(db.Integer, default=0)
    motos = db.Column(db.Integer, default=0)
    carros = db.Column(db.Integer, default=0)
    armas = db.Column(db.Integer, default=0)
    
    # Dispositivos
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
    
    # Incautaciones
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
    
    # Anotaciones
    anotaciones = db.Column(db.Text)
    
    # Metadatos
    fecha_registro = db.Column(db.String(50), nullable=False)
    usuario_registro = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='ACTIVA')

# ==================== FUNCIONES DE PERMISOS ====================
def tiene_permiso(usuario, permiso_requerido):
    """Verifica si un usuario tiene el rol necesario"""
    roles_permisos = {
        'admin': ['ver_personas', 'crear_personas', 'editar_personas', 'eliminar_personas',
                  'ver_ordenes', 'crear_ordenes', 'editar_ordenes', 'eliminar_ordenes',
                  'ver_antecedentes', 'crear_antecedentes', 'editar_antecedentes', 'eliminar_antecedentes',
                  'ver_estadisticas', 'ver_alertas', 'gestionar_usuarios',
                  'ver_acciones', 'crear_acciones', 'editar_acciones', 'eliminar_acciones'],
        'supervisor': ['ver_personas', 'crear_personas', 'editar_personas',
                       'ver_ordenes', 'crear_ordenes', 'editar_ordenes',
                       'ver_antecedentes', 'crear_antecedentes', 'editar_antecedentes',
                       'ver_estadisticas', 'ver_alertas',
                       'ver_acciones', 'crear_acciones', 'editar_acciones'],
        'agente': ['ver_personas', 'crear_personas', 'ver_ordenes', 'crear_ordenes',
                   'ver_antecedentes', 'ver_estadisticas', 'ver_alertas',
                   'ver_acciones'],
        'usuario': ['ver_personas', 'ver_ordenes', 'ver_estadisticas', 'ver_alertas',
                    'ver_acciones']
    }
    return permiso_requerido in roles_permisos.get(usuario.rol, [])

def permiso_requerido(permiso):
    """Decorador para verificar permisos de usuario"""
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
    """Agrega funciones útiles a todos los templates"""
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
                            'persona_id': o.persona_id
                        })
            except:
                pass
    return alertas

# ==================== CREAR BASE DE DATOS ====================
with app.app_context():
    db.create_all()
    
    # Crear usuarios por defecto
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
    ordenes = OrdenCaptura.query.filter_by(persona_id=id, estado='ACTIVA').all()
    return render_template('ficha.html', persona=persona, antecedentes=antecedentes, ordenes=ordenes)

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

# ==================== API ====================
@app.route('/api/verificar')
@login_required
def api_verificar():
    return jsonify({'success': True, 'actualizadas': verificar_vencimientos()})

@app.route('/api/ordenes')
@login_required
def api_ordenes():
    ordenes = OrdenCaptura.query.all()
    resultados = []
    for o in ordenes:
        p = Persona.query.get(o.persona_id)
        resultados.append({
            'id': o.id,
            'numero_orden': o.numero_orden,
            'persona_nombre': p.nombre if p else 'N/A',
            'persona_cedula': p.cedula if p else 'N/A',
            'monto_deuda': o.monto_deuda,
            'juzgado': o.juzgado,
            'fecha_vencimiento': o.fecha_vencimiento or '',
            'estado': o.estado,
            'persona_id': o.persona_id
        })
    return jsonify(resultados)

@app.route('/api/ordenes', methods=['POST'])
@login_required
@permiso_requerido('crear_ordenes')
def create_orden():
    try:
        data = request.json
        orden = OrdenCaptura(
            persona_id=data['persona_id'],
            numero_orden=data['numero_orden'],
            monto_deuda=float(data['monto_deuda']),
            fecha_emision=data.get('fecha_emision', datetime.now().strftime("%Y-%m-%d")),
            fecha_vencimiento=data.get('fecha_vencimiento', ''),
            juzgado=data.get('juzgado', '').upper(),
            expediente=data.get('expediente', '').upper(),
            estado='ACTIVA',
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(orden)
        db.session.commit()
        return jsonify({'success': True, 'id': orden.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ordenes/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_ordenes')
def delete_orden(id):
    orden = OrdenCaptura.query.get_or_404(id)
    db.session.delete(orden)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/personas')
@login_required
def api_personas():
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

@app.route('/api/personas', methods=['POST'])
@login_required
@permiso_requerido('crear_personas')
def create_persona():
    data = request.json
    persona = Persona(
        cedula=data['cedula'],
        nombre=data['nombre'].upper(),
        fecha_nacimiento=data.get('fecha_nacimiento', ''),
        genero=data.get('genero', ''),
        direccion=data.get('direccion', '').upper(),
        telefono=data.get('telefono', ''),
        email=data.get('email', ''),
        foto=data.get('foto', ''),
        fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        estado='ACTIVO'
    )
    db.session.add(persona)
    db.session.commit()
    return jsonify({'success': True, 'id': persona.id})

@app.route('/api/personas/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('editar_personas')
def update_persona(id):
    try:
        persona = Persona.query.get_or_404(id)
        data = request.json
        persona.cedula = data['cedula']
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
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/personas/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_personas')
def delete_persona(id):
    try:
        persona = Persona.query.get_or_404(id)
        Antecedente.query.filter_by(persona_id=id).delete()
        OrdenCaptura.query.filter_by(persona_id=id).delete()
        db.session.delete(persona)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/antecedentes/<int:persona_id>')
@login_required
def api_antecedentes(persona_id):
    antecedentes = Antecedente.query.filter_by(persona_id=persona_id).all()
    return jsonify([{
        'id': a.id,
        'delito': a.delito,
        'fecha_delito': a.fecha_delito or '',
        'lugar': a.lugar or '',
        'juzgado': a.juzgado or '',
        'estado': a.estado or ''
    } for a in antecedentes])

@app.route('/api/antecedentes', methods=['POST'])
@login_required
@permiso_requerido('crear_antecedentes')
def create_antecedente():
    try:
        data = request.json
        antecedente = Antecedente(
            persona_id=data['persona_id'],
            delito=data['delito'].upper(),
            fecha_delito=data.get('fecha_delito', ''),
            lugar=data.get('lugar', '').upper(),
            juzgado=data.get('juzgado', '').upper(),
            estado='REGISTRADO'
        )
        db.session.add(antecedente)
        db.session.commit()
        return jsonify({'success': True, 'id': antecedente.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/antecedentes/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_antecedentes')
def delete_antecedente(id):
    antecedente = Antecedente.query.get_or_404(id)
    db.session.delete(antecedente)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/upload_foto', methods=['POST'])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['foto']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'filename': f'/static/uploads/{filename}'})
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/estadisticas')
@login_required
def api_estadisticas():
    from sqlalchemy import func
    return jsonify({
        'personas': Persona.query.count(),
        'ordenes_activas': OrdenCaptura.query.filter_by(estado='ACTIVA').count(),
        'ordenes_vencidas': OrdenCaptura.query.filter_by(estado='VENCIDA').count(),
        'deuda_total': db.session.query(func.sum(OrdenCaptura.monto_deuda)).filter_by(estado='ACTIVA').scalar() or 0
    })

@app.route('/api/alertas')
@login_required
def api_alertas():
    return jsonify(obtener_alertas())

@app.route('/api/usuarios', methods=['GET'])
@login_required
@permiso_requerido('gestionar_usuarios')
def api_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'rol': u.rol,
        'activo': u.activo,
        'fecha_registro': u.fecha_registro
    } for u in usuarios])

@app.route('/api/usuarios', methods=['POST'])
@login_required
@permiso_requerido('gestionar_usuarios')
def create_usuario():
    data = request.json
    if Usuario.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'El usuario ya existe'}), 400
    
    nuevo = Usuario(
        username=data['username'],
        email=data['email'],
        rol=data.get('rol', 'usuario'),
        activo=True,
        fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    nuevo.set_password(data['password'])
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'success': True, 'id': nuevo.id})

@app.route('/api/usuarios/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('gestionar_usuarios')
def update_usuario(id):
    if id == current_user.id:
        return jsonify({'error': 'No puedes modificar tu propio usuario'}), 400
    usuario = Usuario.query.get_or_404(id)
    data = request.json
    usuario.rol = data.get('rol', usuario.rol)
    usuario.activo = data.get('activo', usuario.activo)
    if data.get('password'):
        usuario.set_password(data['password'])
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('gestionar_usuarios')
def delete_usuario(id):
    if id == current_user.id:
        return jsonify({'error': 'No puedes eliminar tu propio usuario'}), 400
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({'success': True})

# ==================== API ACCIONES OPERATIVAS ====================
@app.route('/api/acciones_operativas', methods=['GET'])
@login_required
def api_acciones_operativas():
    acciones = AccionOperativa.query.order_by(AccionOperativa.fecha.desc()).all()
    return jsonify([{
        'id': a.id,
        'cod_unidad': a.cod_unidad,
        'fecha': a.fecha,
        'lugar': a.lugar,
        'personas_abordadas': a.personas_abordadas,
        'mando': a.mando,
        'estado': a.estado
    } for a in acciones])

@app.route('/api/acciones_operativas', methods=['POST'])
@login_required
@permiso_requerido('crear_acciones')
def crear_accion_operativa():
    try:
        data = request.json
        accion = AccionOperativa(
            cod_unidad=data['cod_unidad'],
            fecha=data['fecha'],
            hora_inicio=data['hora_inicio'],
            hora_fin=data['hora_fin'],
            lugar=data['lugar'],
            accion_realizada=data['accion_realizada'],
            instituciones=data.get('instituciones', ''),
            escuadra_1=data.get('escuadra_1', False),
            escuadra_2=data.get('escuadra_2', False),
            escuadra_3=data.get('escuadra_3', False),
            escuadra_4=data.get('escuadra_4', False),
            mando=data['mando'],
            oficiales=data['oficiales'],
            personas_abordadas=data.get('personas_abordadas', 0),
            personas_investigadas_oij=data.get('personas_investigadas_oij', 0),
            motos=data.get('motos', 0),
            carros=data.get('carros', 0),
            armas=data.get('armas', 0),
            control_carretera=data.get('control_carretera', 0),
            op_inter_institucionales=data.get('op_inter_institucionales', 0),
            ganado_seguro=data.get('ganado_seguro', 0),
            visitas_comercio=data.get('visitas_comercio', 0),
            paso_escolar=data.get('paso_escolar', 0),
            notificaciones=data.get('notificaciones', 0),
            guardas_seguridad=data.get('guardas_seguridad', 0),
            orden_apremio_corporal=data.get('orden_apremio_corporal', 0),
            partes_transito=data.get('partes_transito', 0),
            placas_decomisadas=data.get('placas_decomisadas', 0),
            informes_policiales=data.get('informes_policiales', 0),
            incidentes_cerrados=data.get('incidentes_cerrados', 0),
            vehiculos_incautados=data.get('vehiculos_incautados', 0),
            puchos_marihuana=data.get('puchos_marihuana', 0),
            cigarillos_marihuana=data.get('cigarillos_marihuana', 0),
            gramos_marihuana=data.get('gramos_marihuana', 0),
            piedras_crack=data.get('piedras_crack', 0),
            gramos_crack=data.get('gramos_crack', 0),
            puntas_cocaina=data.get('puntas_cocaina', 0),
            gramos_cocaina=data.get('gramos_cocaina', 0),
            armas_fuego=data.get('armas_fuego', 0),
            armas_blancas=data.get('armas_blancas', 0),
            dinero_efectivo=data.get('dinero_efectivo', 0),
            otros_incautaciones=data.get('otros_incautaciones', ''),
            anotaciones=data.get('anotaciones', ''),
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            usuario_registro=current_user.username,
            estado='ACTIVA'
        )
        db.session.add(accion)
        db.session.commit()
        return jsonify({'success': True, 'id': accion.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/acciones_operativas/<int:id>', methods=['PUT'])
@login_required
@permiso_requerido('editar_acciones')
def update_accion_operativa(id):
    try:
        accion = AccionOperativa.query.get_or_404(id)
        data = request.json
        for key, value in data.items():
            if hasattr(accion, key):
                setattr(accion, key, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/acciones_operativas/<int:id>', methods=['DELETE'])
@login_required
@permiso_requerido('eliminar_acciones')
def delete_accion_operativa(id):
    accion = AccionOperativa.query.get_or_404(id)
    db.session.delete(accion)
    db.session.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)