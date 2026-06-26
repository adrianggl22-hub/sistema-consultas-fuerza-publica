# eliminar_todo_machotes.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

print("ELIMINANDO TODAS LAS TABLAS DE MACHOTES")
print("=" * 50)

# Eliminar tablas en orden correcto
tablas = [
    'respuestas_detalle',
    'respuestas_formulario', 
    'respuestas',
    'preguntas',
    'documentos_generados',
    'machotes_documentos'
]

for tabla in tablas:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
        print(f"  OK - Tabla {tabla} eliminada")
    except Exception as e:
        print(f"  ERROR - {tabla}: {e}")

conn.commit()
conn.close()

print("\nTodas las tablas de machotes eliminadas")

# Verificar
conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%machote%' OR name LIKE '%pregunta%' OR name LIKE '%respuesta%' OR name LIKE '%documento%'")
tablas_restantes = cursor.fetchall()

if tablas_restantes:
    print("\nTablas restantes (deberían ser 0):")
    for t in tablas_restantes:
        print(f"  - {t[0]}")
else:
    print("\nNo hay tablas restantes relacionadas con machotes")

conn.close()