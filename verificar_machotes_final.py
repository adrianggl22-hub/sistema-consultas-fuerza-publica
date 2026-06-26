# verificar_machotes_final.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

# Verificar todas las tablas relacionadas
tablas = ['machotes_documentos', 'preguntas', 'respuestas', 'respuestas_formulario', 'documentos_generados']

print("📊 Estado de la base de datos:")
print("=" * 50)

for tabla in tablas:
    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
    count = cursor.fetchone()[0]
    print(f"  {tabla}: {count} registros")

# Verificar si hay machotes
cursor.execute("SELECT id, nombre FROM machotes_documentos")
machotes = cursor.fetchall()

if machotes:
    print(f"\n📋 Machotes existentes ({len(machotes)}):")
    for m in machotes:
        print(f"  - ID: {m[0]}, Nombre: {m[1]}")
else:
    print("\n✅ No hay machotes en la base de datos")

conn.close()