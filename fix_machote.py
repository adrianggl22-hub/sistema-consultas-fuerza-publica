# fix_machote.py
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ejecutar el script
from app import app, db, MachoteDocumento

with app.app_context():
    try:
        # Buscar machotes que contengan "ROLL DE SERVICIO" en el nombre
        machotes = MachoteDocumento.query.filter(
            MachoteDocumento.nombre.like('%ROLL DE SERVICIO%')
        ).all()
        
        if machotes:
            for machote in machotes:
                # Contenido corregido con el formato correcto de 4 llaves
                contenido_corregido = """*ROLL DE SERVICIO DELEGACIÓN POLICIAL DE MORA*
═══════════════════════════════════════

*Turno*: {{{{ Turno }}}}
*Fecha*: {{{{ Fecha }}}}
*D23 Alfa*: {{{{ D23 Alfa }}}}
*D23 Bravo*: {{{{ D23 Bravo }}}}
*Encargado de Equipo Operativo*: {{{{ Encargado de Equipo Operativo }}}}
*Armeria*: {{{{ Armeria }}}}
*Operaciones*: {{{{ Operaciones }}}}
*Encargado Programas Preventivos*: {{{{ Encargado Programas Preventivos }}}}
*Apoyo Programas Preventivos*: {{{{ Apoyo Programas Preventivos }}}}
*Movil 3487*: {{{{ Movil 3487 }}}}
*Oficial de Guardia*: {{{{ Oficial de Guardia }}}}
*Incapacitados*: {{{{ Incapacitados }}}}
*Ausente*: {{{{ Ausente }}}}}"""
                
                machote.contenido = contenido_corregido
                db.session.commit()
                print(f"✅ Machote '{machote.nombre}' (ID: {machote.id}) actualizado correctamente")
        else:
            print("❌ No se encontró ningún machote con 'ROLL DE SERVICIO' en el nombre")
            
            # Mostrar todos los machotes disponibles
            todos = MachoteDocumento.query.all()
            print("\n📋 Machotes disponibles:")
            for m in todos:
                print(f"  - ID: {m.id}, Nombre: {m.nombre}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()