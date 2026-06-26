# ver_incidentes.py
from app import app, db
from app import Incidente

with app.app_context():
    print("📊 Verificando incidentes...")
    total = Incidente.query.count()
    print(f"   Total de incidentes: {total}")
    
    incidentes = Incidente.query.all()
    for i in incidentes:
        print(f"   ID: {i.id} | Unidad: {i.numero_incidente} | Tipo: {i.tipo_incidente}")