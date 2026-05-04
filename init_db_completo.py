from app import app, db, Usuario, Persona, Antecedente, OrdenCaptura
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

with app.app_context():
    # Crear todas las tablas
    db.create_all()
    print("✅ Tablas creadas")
    
    # Verificar columnas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print(f"📋 Tablas: {inspector.get_table_names()}")
    
    # Crear usuarios
    usuarios_data = [
        ('admin', 'admin@test.com', 'admin123', 'admin'),
        ('supervisor', 'supervisor@test.com', 'super123', 'supervisor'),
        ('agente', 'agente@test.com', 'agente123', 'agente'),
        ('operador', 'operador@test.com', 'oper123', 'usuario'),
    ]
    
    for username, email, password, rol in usuarios_data:
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
    
    # Crear personas de prueba
    personas = [
        Persona(cedula='1-1001-2002', nombre='JUAN PEREZ GARCIA', fecha_registro=datetime.now().strftime("%Y-%m-%d"), estado='ACTIVO'),
        Persona(cedula='2-2002-3003', nombre='MARIA RODRIGUEZ', fecha_registro=datetime.now().strftime("%Y-%m-%d"), estado='ACTIVO'),
    ]
    for p in personas:
        db.session.add(p)
    db.session.commit()
    print(f"✅ {Persona.query.count()} personas creadas")
    
    # Crear órdenes de prueba
    hoy = datetime.now().date()
    ordenes = [
        OrdenCaptura(persona_id=1, numero_orden='ORD-001', monto_deuda=1500000,
                    fecha_emision=(hoy - timedelta(days=30)).strftime("%Y-%m-%d"),
                    fecha_vencimiento=(hoy + timedelta(days=5)).strftime("%Y-%m-%d"),
                    juzgado='JUZGADO DE MORA', expediente='EXP-001', estado='ACTIVA'),
        OrdenCaptura(persona_id=2, numero_orden='ORD-002', monto_deuda=2300000,
                    fecha_emision=(hoy - timedelta(days=30)).strftime("%Y-%m-%d"),
                    fecha_vencimiento=(hoy + timedelta(days=4)).strftime("%Y-%m-%d"),
                    juzgado='JUZGADO DE MORA', expediente='EXP-002', estado='ACTIVA'),
    ]
    for o in ordenes:
        db.session.add(o)
    db.session.commit()
    print(f"✅ {OrdenCaptura.query.count()} órdenes creadas")
    
    print("\n" + "="*40)
    print("📊 BASE DE DATOS INICIALIZADA")
    print("="*40)
    print(f"   Usuarios: {Usuario.query.count()}")
    print(f"   Personas: {Persona.query.count()}")
    print(f"   Órdenes: {OrdenCaptura.query.count()}")
    print("\n🔐 CREDENCIALES:")
    print("   admin / admin123")
    print("   supervisor / super123")
    print("   agente / agente123")
    print("   operador / oper123")
    print("="*40)