# fix_unique.py
import sqlite3
import os

# Encontrar la base de datos
db_path = 'instance/sistema_consultas.db'
if not os.path.exists(db_path):
    db_path = 'sistema_consultas.db'

print(f"📁 Base de datos: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ver la estructura actual
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='incidentes'")
estructura = cursor.fetchone()[0]
print(f"\n📋 Estructura actual:")
print(estructura)

# Crear tabla nueva SIN la restricción UNIQUE
cursor.execute('''
    CREATE TABLE incidentes_nueva (
        id INTEGER PRIMARY KEY,
        oficial_actuante VARCHAR(100) NOT NULL,
        oficial_asistente VARCHAR(100),
        numero_incidente VARCHAR(50) NOT NULL,
        tipo_incidente VARCHAR(100) NOT NULL,
        descripcion TEXT NOT NULL,
        diligencias_policiales TEXT,
        aprehendidos INTEGER DEFAULT 0,
        ofendidos INTEGER DEFAULT 0,
        testigos INTEGER DEFAULT 0,
        personas_interes INTEGER DEFAULT 0,
        vehiculos_involucrados INTEGER DEFAULT 0,
        decomisos TEXT,
        informe_policial BOOLEAN DEFAULT 0,
        numero_informe VARCHAR(50),
        acta_decomiso BOOLEAN DEFAULT 0,
        numero_acta_decomiso VARCHAR(50),
        fecha_incidente VARCHAR(20) NOT NULL,
        lugar VARCHAR(200),
        latitud FLOAT,
        longitud FLOAT,
        direccion_ubicacion VARCHAR(500),
        estado VARCHAR(20) DEFAULT 'ACTIVO',
        creado_por VARCHAR(50),
        fecha_registro VARCHAR(50)
    )
''')
print("\n✅ Tabla temporal creada SIN restricción UNIQUE")

# Copiar los datos existentes
cursor.execute('INSERT INTO incidentes_nueva SELECT * FROM incidentes')
print(f"✅ Datos copiados: {cursor.rowcount} registros")

# Eliminar la tabla vieja
cursor.execute('DROP TABLE incidentes')
print("✅ Tabla vieja eliminada")

# Renombrar la tabla nueva
cursor.execute('ALTER TABLE incidentes_nueva RENAME TO incidentes')
print("✅ Tabla nueva renombrada")

# Verificar que no hay restricción UNIQUE
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='incidentes'")
nueva_estructura = cursor.fetchone()[0]
print(f"\n📋 Nueva estructura (SIN UNIQUE):")
print(nueva_estructura)

# Verificar que se pueden insertar duplicados
cursor.execute("INSERT INTO incidentes (oficial_actuante, numero_incidente, tipo_incidente, descripcion, fecha_incidente) VALUES ('TEST1', '999', 'TEST', 'Test 1', '2026-05-08')")
cursor.execute("INSERT INTO incidentes (oficial_actuante, numero_incidente, tipo_incidente, descripcion, fecha_incidente) VALUES ('TEST2', '999', 'TEST', 'Test 2', '2026-05-08')")
cursor.execute("DELETE FROM incidentes WHERE oficial_actuante IN ('TEST1', 'TEST2')")
print("\n✅ Prueba de duplicados exitosa - RESTRICCIÓN ELIMINADA!")

conn.commit()
conn.close()

print("\n✨ ¡Proceso completado correctamente!")