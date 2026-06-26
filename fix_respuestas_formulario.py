# fix_respuestas_formulario.py
import sqlite3

def fix_database():
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("🔍 Verificando estructura de respuestas_formulario...")
        
        # Verificar columnas existentes
        cursor.execute("PRAGMA table_info(respuestas_formulario)")
        columnas = cursor.fetchall()
        columnas_existentes = [col[1] for col in columnas]
        
        print(f"📋 Columnas actuales: {columnas_existentes}")
        
        # Verificar si falta la columna 'titulo'
        if 'titulo' not in columnas_existentes:
            print("⚠️ Agregando columna 'titulo' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN titulo TEXT")
            print("✅ Columna 'titulo' agregada")
        
        # Verificar si falta la columna 'fecha_respuesta'
        if 'fecha_respuesta' not in columnas_existentes:
            print("⚠️ Agregando columna 'fecha_respuesta' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN fecha_respuesta DATETIME")
            print("✅ Columna 'fecha_respuesta' agregada")
        
        # Verificar si falta la columna 'usuario_responde'
        if 'usuario_responde' not in columnas_existentes:
            print("⚠️ Agregando columna 'usuario_responde' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN usuario_responde TEXT")
            print("✅ Columna 'usuario_responde' agregada")
        
        # Verificar si falta la columna 'ip_address'
        if 'ip_address' not in columnas_existentes:
            print("⚠️ Agregando columna 'ip_address' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN ip_address TEXT")
            print("✅ Columna 'ip_address' agregada")
        
        conn.commit()
        
        # Verificar la estructura final
        cursor.execute("PRAGMA table_info(respuestas_formulario)")
        columnas_finales = cursor.fetchall()
        print("\n📋 Columnas finales de respuestas_formulario:")
        for col in columnas_finales:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        print("\n✅ Estructura de la base de datos actualizada correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_database()