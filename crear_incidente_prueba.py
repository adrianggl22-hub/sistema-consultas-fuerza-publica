# crear_incidente_prueba.py
from app import app, db
from app import Incidente
from datetime import datetime

with app.app_context():
    print("📝 Creando incidente de prueba...")
    
    try:
        nuevo = Incidente(
            oficial_actuante="YOSSER FUENTES CARDENAS",
            oficial_asistente="",
            numero_incidente="1943",
            tipo_incidente="PERTURBACIÓN DEL ORDEN PÚBLICO",
            descripcion="Personas causando disturbios en la vía pública",
            diligencias_policiales="Se identificaron a las personas",
            aprehendidos=0,
            ofendidos=0,
            testigos=0,
            personas_interes=0,
            vehiculos_involucrados=0,
            decomisos="Ninguno",
            informe_policial=False,
            numero_informe="",
            acta_decomiso=False,
            numero_acta_decomiso="",
            fecha_incidente="2026-05-08",
            lugar="MORA, COLON CENTRO",
            estado="ACTIVO",
            creado_por="admin",
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(nuevo)
        db.session.commit()
        print(f"✅ Incidente creado con ID: {nuevo.id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()