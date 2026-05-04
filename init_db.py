from app import app, db
from app import Usuario, Persona, Antecedente, OrdenCaptura
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

with app.app_context():
    # Eliminar todo
    db.drop_all()
    print("✅ Tablas eliminadas")
    
    # Crear tablas
    db.create_all()
    print("✅ Tablas creadas")
    
    # Crear usuario admin
    admin = Usuario(
        username='admin',
        email='admin@test.com',
        password_hash=generate_password_hash('admin123'),
        rol='admin',
        activo=True,
        fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ Usuario admin creado")
    
    # Crear personas
    personas = [
        Persona(cedula='1-1001-2002', nombre='JUAN PEREZ GARCIA', fecha_registro='2024-01-01', estado='ACTIVO'),
        Persona(cedula='2-2002-3003', nombre='MARIA RODRIGUEZ LOPEZ', fecha_registro='2024-01-01', estado='ACTIVO'),
        Persona(cedula='3-3003-4004', nombre='CARLOS MENDEZ ROJAS', fecha_registro='2024-01-01', estado='ACTIVO'),
        Persona(cedula='4-4004-5005', nombre='ANA JIMENEZ CASTRO', fecha_registro='2024-01-01', estado='ACTIVO'),
        Persona(cedula='5-5005-6006', nombre='LUIS FERNANDEZ MORA', fecha_registro='2024-01-01', estado='ACTIVO'),
    ]
    for p in personas:
        db.session.add(p)
    db.session.commit()
    print(f"✅ {Persona.query.count()} personas creadas")
    
    # Crear órdenes
    hoy = datetime.now().date()
    for i in range(1, 6):
        o = OrdenCaptura(
            persona_id=i,
            numero_orden=f'ORD-00{i}',
            monto_deuda=1000000 * i,
            fecha_emision=(hoy - timedelta(days=30)).strftime("%Y-%m-%d"),
            fecha_vencimiento=(hoy + timedelta(days=5)).strftime("%Y-%m-%d"),
            juzgado='JUZGADO DE MORA',
            expediente=f'EXP-00{i}',
            estado='ACTIVA'
        )
        db.session.add(o)
    db.session.commit()
    print(f"✅ {OrdenCaptura.query.count()} órdenes creadas")
    
    print("\n🎉 BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("🔐 Credenciales: admin / admin123")