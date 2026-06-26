# eliminar_machotes_agresivo.py
import sqlite3
import os

def eliminar_agresivo():
    try:
        # Cerrar cualquier conexión existente
        conn = sqlite3.connect('sistema_consultas.db', timeout=10)
        cursor = conn.cursor()
        
        print("🔍 Eliminando machotes de forma agresiva...")
        print("=" * 50)
        
        # Primero, listar todos los machotes
        cursor.execute("SELECT id, nombre FROM machotes_documentos")
        machotes = cursor.fetchall()
        
        if machotes:
            print(f"\n📋 Machotes encontrados ({len(machotes)}):")
            for m in machotes:
                print(f"  - ID: {m[0]}, Nombre: {m[1]}")
            
            # Eliminar uno por uno
            for m in machotes:
                machote_id = m[0]
                print(f"\n🗑️ Eliminando machote ID {machote_id}...")
                
                cursor.execute("DELETE FROM preguntas WHERE machote_id = ?", (machote_id,))
                print(f"  ✅ Preguntas: {cursor.rowcount}")
                
                cursor.execute("DELETE FROM respuestas WHERE machote_id = ?", (machote_id,))
                print(f"  ✅ Respuestas: {cursor.rowcount}")
                
                cursor.execute("DELETE FROM respuestas_formulario WHERE machote_id = ?", (machote_id,))
                print(f"  ✅ Respuestas Formulario: {cursor.rowcount}")
                
                cursor.execute("DELETE FROM documentos_generados WHERE machote_id = ?", (machote_id,))
                print(f"  ✅ Documentos Generados: {cursor.rowcount}")
                
                cursor.execute("DELETE FROM machotes_documentos WHERE id = ?", (machote_id,))
                print(f"  ✅ Machote eliminado: {cursor.rowcount}")
            
            conn.commit()
            print("\n✅ Todos los machotes eliminados")
        else:
            print("✅ No hay machotes en la base de datos")
        
        # Verificar
        cursor.execute("SELECT COUNT(*) FROM machotes_documentos")
        count = cursor.fetchone()[0]
        print(f"\n📊 Machotes restantes: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    eliminar_agresivo()