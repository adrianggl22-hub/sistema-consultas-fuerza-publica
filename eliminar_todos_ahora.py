# eliminar_todos_ahora.py
import sqlite3

def eliminar_todos():
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🗑️ ELIMINANDO TODOS LOS MACHOTES")
        print("=" * 60)
        
        # Mostrar machotes actuales
        cursor.execute("SELECT id, nombre FROM machotes_documentos")
        machotes = cursor.fetchall()
        
        if machotes:
            print(f"\n📋 Machotes a eliminar ({len(machotes)}):")
            for m in machotes:
                print(f"  - ID: {m[0]}, Nombre: {m[1]}")
            
            print("\n🗑️ Eliminando...")
            
            # Eliminar en orden
            cursor.execute("DELETE FROM preguntas")
            print(f"  ✅ Preguntas eliminadas: {cursor.rowcount}")
            
            cursor.execute("DELETE FROM respuestas")
            print(f"  ✅ Respuestas eliminadas: {cursor.rowcount}")
            
            cursor.execute("DELETE FROM respuestas_formulario")
            print(f"  ✅ Respuestas Formulario eliminadas: {cursor.rowcount}")
            
            cursor.execute("DELETE FROM documentos_generados")
            print(f"  ✅ Documentos Generados eliminados: {cursor.rowcount}")
            
            cursor.execute("DELETE FROM machotes_documentos")
            print(f"  ✅ Machotes eliminados: {cursor.rowcount}")
            
            # Resetear auto-increment
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='machotes_documentos'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='preguntas'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='respuestas'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='respuestas_formulario'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='documentos_generados'")
            
            conn.commit()
            print("\n✅ Todos los machotes eliminados correctamente")
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
    eliminar_todos()