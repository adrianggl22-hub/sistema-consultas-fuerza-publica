# eliminar_tablas_machotes.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

print("Eliminando tablas de machotes...")
print("=" * 50)

# Eliminar tablas en orden
tablas = ['respuestas', 'preguntas', 'documentos_generados', 'respuestas_formulario', 'machotes_documentos']

for tabla in tablas:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {tabla}")
        print(f"  OK - Tabla {tabla} eliminada")
    except Exception as e:
        print(f"  ERROR - {tabla}: {e}")

conn.commit()
conn.close()

print("\nTodas las tablas de machotes eliminadas")