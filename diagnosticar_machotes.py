# diagnosticar_machotes.py
import sqlite3

def diagnosticar():
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🔍 DIAGNÓSTICO DE MACHOTES")
        print("=" * 60)
        
        # Verificar machotes
        cursor.execute("SELECT id, nombre, es_activo FROM machotes_documentos")
        machotes = cursor.fetchall()
        
        print(f"\n📋 Machotes en la base de datos ({len(machotes)}):")
        for m in machotes:
            print(f"  - ID: {m[0]}, Nombre: {m[1]}, Activo: {m[2]}")
            
            # Verificar preguntas
            cursor.execute("SELECT COUNT(*) FROM preguntas WHERE machote_id = ?", (m[0],))
            preguntas = cursor.fetchone()[0]
            print(f"    Preguntas: {preguntas}")
            
            # Verificar respuestas
            cursor.execute("SELECT COUNT(*) FROM respuestas WHERE machote_id = ?", (m[0],))
            respuestas = cursor.fetchone()[0]
            print(f"    Respuestas: {respuestas}")
            
            # Verificar respuestas formulario
            cursor.execute("SELECT COUNT(*) FROM respuestas_formulario WHERE machote_id = ?", (m[0],))
            respuestas_form = cursor.fetchone()[0]
            print(f"    Respuestas Formulario: {respuestas_form}")
            
            # Verificar documentos generados
            cursor.execute("SELECT COUNT(*) FROM documentos_generados WHERE machote_id = ?", (m[0],))
            documentos = cursor.fetchone()[0]
            print(f"    Documentos Generados: {documentos}")
        
        # Verificar la tabla respuestas_formulario
        cursor.execute("PRAGMA table_info(respuestas_formulario)")
        columnas = cursor.fetchall()
        print("\n📊 Columnas de respuestas_formulario:")
        for col in columnas:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnosticar()