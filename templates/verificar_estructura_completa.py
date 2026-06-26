# verificar_estructura_completa.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

print("📋 Verificando todas las tablas...")
print("=" * 50)

# Verificar respuestas_formulario
cursor.execute("PRAGMA table_info(respuestas_formulario)")
columnas = cursor.fetchall()
print("\n📊 Tabla: respuestas_formulario")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

# Verificar machotes_documentos
cursor.execute("PRAGMA table_info(machotes_documentos)")
columnas = cursor.fetchall()
print("\n📊 Tabla: machotes_documentos")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

# Verificar preguntas
cursor.execute("PRAGMA table_info(preguntas)")
columnas = cursor.fetchall()
print("\n📊 Tabla: preguntas")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

# Verificar respuestas
cursor.execute("PRAGMA table_info(respuestas)")
columnas = cursor.fetchall()
print("\n📊 Tabla: respuestas")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

conn.close()