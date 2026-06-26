# guarda como verificar_estructura.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

# Ver todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tablas en la base de datos:")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Ver estructura de respuestas_formulario
print("\nEstructura de respuestas_formulario:")
cursor.execute("PRAGMA table_info(respuestas_formulario)")
for col in cursor.fetchall():
    print(f"  {col}")

conn.close()