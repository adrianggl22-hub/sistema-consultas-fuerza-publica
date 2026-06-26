# fix_db_completo.py
import sqlite3

def fix_database():
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🔧 REPARANDO BASE DE DATOS")
        print("=" * 60)
        
        # 1. Verificar y agregar columna 'titulo' si no existe
        cursor.execute("PRAGMA table_info(respuestas_formulario)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'titulo' not in columnas:
            print("\n⚠️ Agregando columna 'titulo' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN titulo TEXT")
            print("✅ Columna 'titulo' agregada")
        else:
            print("\n✅ Columna 'titulo' ya existe")
        
        # 2. Eliminar TODOS los machotes y datos relacionados
        print("\n🗑️ Eliminando todos los machotes y datos relacionados...")
        
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
        
        # 3. Resetear auto-increment
        print("\n🔄 Resetando contadores...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='machotes_documentos'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='preguntas'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='respuestas'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='respuestas_formulario'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='documentos_generados'")
        print("  ✅ Contadores reseteados")
        
        # 4. Verificar estado final
        cursor.execute("SELECT COUNT(*) FROM machotes_documentos")
        machotes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM preguntas")
        preguntas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM respuestas")
        respuestas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM respuestas_formulario")
        respuestas_form_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documentos_generados")
        documentos_count = cursor.fetchone()[0]
        
        print("\n📊 Estado final:")
        print(f"  Machotes: {machotes_count}")
        print(f"  Preguntas: {preguntas_count}")
        print(f"  Respuestas: {respuestas_count}")
        print(f"  Respuestas Formulario: {respuestas_form_count}")
        print(f"  Documentos Generados: {documentos_count}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Base de datos reparada correctamente")
        print("\n📋 Ahora:")
        print("  1. Reinicia el servidor")
        print("  2. Limpia el caché del navegador (Ctrl+F5)")
        print("  3. Crea un nuevo machote")
        print("  4. Prueba eliminarlo")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()