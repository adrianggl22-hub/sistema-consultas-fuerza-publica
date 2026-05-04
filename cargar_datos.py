from app import app, db, Persona, OrdenCaptura, Antecedente
from datetime import datetime, timedelta

with app.app_context():
    # Limpiar
    OrdenCaptura.query.delete()
    Antecedente.query.delete()
    Persona.query.delete()
    db.session.commit()
    
    # Crear personas
    for i in range(1, 6):
        p = Persona(
            cedula=f'{i}-{1000+i}-{2000+i}',
            nombre=f'PERSONA EJEMPLO {i}',
            fecha_registro='2024-01-01',
            estado='ACTIVO'
        )
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
    
    print("\n✅ DATOS CARGADOS EXITOSAMENTE")