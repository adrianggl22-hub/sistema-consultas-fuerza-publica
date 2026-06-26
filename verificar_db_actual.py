# verificar_db_actual.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

# Verificar todos los machotes
cursor.execute("SELECT id, nombre FROM machotes_documentos ORDER BY id")
machotes = cursor.fetchall()

print(f"📋 Machotes en la base de datos ({len(machotes)}):")
for m in machotes:
    print(f"  - ID: {m[0]}, Nombre: {m[1]}")

# Verificar los IDs problemáticos específicamente
ids_problematicos = [19, 23, 25, 26]
for id_problematico in ids_problematicos:
    cursor.execute("SELECT COUNT(*) FROM machotes_documentos WHERE id = ?", (id_problematico,))
    existe = cursor.fetchone()[0]
    if existe:
        print(f"⚠️ El machote ID {id_problematico} AÚN EXISTE en la base de datos")
    else:
        print(f"✅ El machote ID {id_problematico} NO existe en la base de datos")

conn.close()