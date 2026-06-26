# fix_machote_final.py
from app import app, db, MachoteDocumento

with app.app_context():
    # Buscar el machote por nombre
    machote = MachoteDocumento.query.filter_by(nombre='ROLL DE SERVICIO DELEGACIÓN POLICIAL DE MORA').first()
    
    if machote:
        # Contenido con 4 llaves (formato correcto)
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
        print(f"✅ Machote '{machote.nombre}' actualizado correctamente")
        print(f"📄 Nuevo contenido:\n{contenido_corregido}")
    else:
        print("❌ No se encontró el machote")
        
        # Mostrar todos los machotes disponibles
        todos = MachoteDocumento.query.all()
        print("\n📋 Machotes disponibles:")
        for m in todos:
            print(f"  - ID: {m.id}, Nombre: {m.nombre}")