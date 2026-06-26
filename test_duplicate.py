from app import app, db
from app import Incidente

with app.app_context():
    # Limpiar datos de prueba anteriores
    db.session.query(Incidente).filter(Incidente.oficial_actuante == 'TEST_UNIDAD').delete()
    db.session.commit()
    
    # Intentar crear dos incidentes con el mismo número
    try:
        # Crear primer incidente
        inc1 = Incidente(
            oficial_actuante='TEST_UNIDAD',
            numero_incidente='1943',
            tipo_incidente='TEST',
            descripcion='Test 1',
            fecha_incidente='2026-05-08'
        )
        db.session.add(inc1)
        db.session.commit()
        print("✅ Primer incidente con número 1943 creado")
        
        # Crear segundo incidente con el MISMO número
        inc2 = Incidente(
            oficial_actuante='TEST_UNIDAD',
            numero_incidente='1943',
            tipo_incidente='TEST',
            descripcion='Test 2',
            fecha_incidente='2026-05-08'
        )
        db.session.add(inc2)
        db.session.commit()
        print("✅ SEGUNDO incidente con número 1943 creado - ¡FUNCIONA!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()
    
    # Limpiar datos de prueba
    db.session.query(Incidente).filter(Incidente.oficial_actuante == 'TEST_UNIDAD').delete()
    db.session.commit()
    print("✅ Datos de prueba eliminados")