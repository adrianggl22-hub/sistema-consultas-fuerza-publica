# eliminar_machotes_manual.py
import sqlite3
import sys

# IDs de los machotes problemáticos
IDS_A_ELIMINAR = [19, 23, 25]

def eliminar_machote(cursor, machote_id):
    """Elimina un machote y todos sus datos relacionados"""
    try:
        print(f"\n{'='*60}")
        print(f"🗑️ Eliminando machote ID: {machote_id}")
        print(f"{'='*60}")
        
        # Verificar si existe el machote
        cursor.execute("SELECT id, nombre FROM machotes_documentos WHERE id = ?", (machote_id,))
        machote = cursor.fetchone()
        
        if not machote:
            print(f"❌ Machote con ID {machote_id} no encontrado")
            return False
        
        print(f"📄 Machote encontrado: {machote[1]} (ID: {machote[0]})")
        
        # Contar registros relacionados
        cursor.execute("SELECT COUNT(*) FROM preguntas WHERE machote_id = ?", (machote_id,))
        preguntas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM respuestas WHERE machote_id = ?", (machote_id,))
        respuestas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM respuestas_formulario WHERE machote_id = ?", (machote_id,))
        respuestas_form_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documentos_generados WHERE machote_id = ?", (machote_id,))
        documentos_count = cursor.fetchone()[0]
        
        print(f"\n📊 Registros relacionados:")
        print(f"  - Preguntas: {preguntas_count}")
        print(f"  - Respuestas: {respuestas_count}")
        print(f"  - Respuestas Formulario: {respuestas_form_count}")
        print(f"  - Documentos Generados: {documentos_count}")
        
        # Eliminar en orden
        cursor.execute("DELETE FROM preguntas WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Preguntas eliminadas: {cursor.rowcount}")
        
        cursor.execute("DELETE FROM respuestas WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Respuestas eliminadas: {cursor.rowcount}")
        
        cursor.execute("DELETE FROM respuestas_formulario WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Respuestas Formulario eliminadas: {cursor.rowcount}")
        
        cursor.execute("DELETE FROM documentos_generados WHERE machote_id = ?", (machote_id,))
        print(f"  ✅ Documentos Generados eliminados: {cursor.rowcount}")
        
        cursor.execute("DELETE FROM machotes_documentos WHERE id = ?", (machote_id,))
        print(f"  ✅ Machote eliminado: {cursor.rowcount}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("🔍 Conectado a la base de datos")
        
        # Mostrar machotes actuales
        cursor.execute("SELECT id, nombre, tipo_documento FROM machotes_documentos ORDER BY id")
        machotes = cursor.fetchall()
        
        print(f"\n📋 Machotes actuales ({len(machotes)}):")
        for m in machotes:
            print(f"  - ID: {m[0]}, Nombre: {m[1]}, Tipo: {m[2]}")
        
        print(f"\n{'='*60}")
        print("🗑️ Eliminando machotes problemáticos...")
        print(f"{'='*60}")
        
        eliminados = 0
        for machote_id in IDS_A_ELIMINAR:
            if eliminar_machote(cursor, machote_id):
                eliminados += 1
        
        # Confirmar cambios
        conn.commit()
        print(f"\n{'='*60}")
        print(f"✅ Proceso completado. {eliminados} machotes eliminados.")
        print(f"{'='*60}")
        
        # Mostrar machotes restantes
        cursor.execute("SELECT id, nombre, tipo_documento FROM machotes_documentos ORDER BY id")
        machotes_restantes = cursor.fetchall()
        
        print(f"\n📋 Machotes restantes ({len(machotes_restantes)}):")
        for m in machotes_restantes:
            print(f"  - ID: {m[0]}, Nombre: {m[1]}, Tipo: {m[2]}")
        
        if len(machotes_restantes) == 0:
            print("\n⚠️ No hay machotes en la base de datos")
        
        conn.close()
        print("\n✅ Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()