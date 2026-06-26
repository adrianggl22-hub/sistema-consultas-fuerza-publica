# eliminar_machotes_force.py
import sqlite3
import sys

def eliminar_machote_force(machote_id):
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print(f"\n{'='*60}")
        print(f"🗑️ FORZANDO eliminación de machote ID: {machote_id}")
        print(f"{'='*60}")
        
        # Verificar si existe el machote
        cursor.execute("SELECT id, nombre FROM machotes_documentos WHERE id = ?", (machote_id,))
        machote = cursor.fetchone()
        
        if not machote:
            print(f"❌ Machote con ID {machote_id} no encontrado")
            conn.close()
            return False
        
        print(f"📄 Machote encontrado: {machote[1]} (ID: {machote[0]})")
        
        # 1. Eliminar preguntas
        cursor.execute("DELETE FROM preguntas WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Preguntas eliminadas: {cursor.rowcount}")
        
        # 2. Eliminar respuestas
        cursor.execute("DELETE FROM respuestas WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Respuestas eliminadas: {cursor.rowcount}")
        
        # 3. Eliminar respuestas del formulario
        cursor.execute("DELETE FROM respuestas_formulario WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Respuestas Formulario eliminadas: {cursor.rowcount}")
        
        # 4. Eliminar documentos generados
        cursor.execute("DELETE FROM documentos_generados WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Documentos Generados eliminados: {cursor.rowcount}")
        
        # 5. Eliminar el machote
        cursor.execute("DELETE FROM machotes_documentos WHERE id = ?", (machote_id,))
        print(f"  ✅ Machote eliminado: {cursor.rowcount}")
        
        conn.commit()
        conn.close()
        print(f"\n✅ Machote ID {machote_id} eliminado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # IDs de los machotes problemáticos
    ids_a_eliminar = [19, 23]
    
    print("🔍 Conectando a la base de datos...")
    
    # Mostrar machotes actuales
    conn = sqlite3.connect('sistema_consultas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, tipo_documento FROM machotes_documentos ORDER BY id")
    machotes = cursor.fetchall()
    conn.close()
    
    print(f"\n📋 Machotes actuales ({len(machotes)}):")
    for m in machotes:
        print(f"  - ID: {m[0]}, Nombre: {m[1]}, Tipo: {m[2]}")
    
    print(f"\n{'='*60}")
    print("🗑️ Eliminando machotes problemáticos...")
    print(f"{'='*60}")
    
    for machote_id in ids_a_eliminar:
        eliminar_machote_force(machote_id)
    
    # Mostrar machotes restantes
    conn = sqlite3.connect('sistema_consultas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, tipo_documento FROM machotes_documentos ORDER BY id")
    machotes_restantes = cursor.fetchall()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"📋 Machotes restantes ({len(machotes_restantes)}):")
    for m in machotes_restantes:
        print(f"  - ID: {m[0]}, Nombre: {m[1]}, Tipo: {m[2]}")
    
    print(f"\n✅ Proceso completado")

if __name__ == "__main__":
    main()