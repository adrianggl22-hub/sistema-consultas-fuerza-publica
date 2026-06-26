# crear_tabla_respuestas_formulario.py
import sqlite3

def crear_tabla():
    try:
        conn = sqlite3.connect('sistema_consultas.db')
        cursor = conn.cursor()
        
        print("🔍 Verificando si existe la tabla respuestas_formulario...")
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='respuestas_formulario'")
        tabla_existe = cursor.fetchone()
        
        if tabla_existe:
            print("⚠️ La tabla respuestas_formulario ya existe. Verificando columnas...")
            
            # Verificar columnas
            cursor.execute("PRAGMA table_info(respuestas_formulario)")
            columnas = cursor.fetchall()
            columnas_existentes = [col[1] for col in columnas]
            
            print(f"📋 Columnas actuales: {columnas_existentes}")
            
            # Verificar columna titulo
            if 'titulo' not in columnas_existentes:
                print("⚠️ Agregando columna 'titulo'...")
                cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN titulo TEXT")
                print("✅ Columna 'titulo' agregada")
            
            # Verificar columna fecha_respuesta
            if 'fecha_respuesta' not in columnas_existentes:
                print("⚠️ Agregando columna 'fecha_respuesta'...")
                cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN fecha_respuesta DATETIME")
                print("✅ Columna 'fecha_respuesta' agregada")
            
            # Verificar columna usuario_responde
            if 'usuario_responde' not in columnas_existentes:
                print("⚠️ Agregando columna 'usuario_responde'...")
                cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN usuario_responde TEXT")
                print("✅ Columna 'usuario_responde' agregada")
            
            # Verificar columna ip_address
            if 'ip_address' not in columnas_existentes:
                print("⚠️ Agregando columna 'ip_address'...")
                cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN ip_address TEXT")
                print("✅ Columna 'ip_address' agregada")
            
            conn.commit()
            
            # Mostrar estructura final
            cursor.execute("PRAGMA table_info(respuestas_formulario)")
            columnas_finales = cursor.fetchall()
            print("\n📋 Estructura final de respuestas_formulario:")
            for col in columnas_finales:
                print(f"  - {col[1]} ({col[2]})")
            
        else:
            print("⚠️ La tabla respuestas_formulario no existe. Creándola...")
            
            cursor.execute('''
            CREATE TABLE respuestas_formulario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machote_id INTEGER NOT NULL,
                persona_id INTEGER,
                titulo TEXT,
                fecha_respuesta DATETIME DEFAULT CURRENT_TIMESTAMP,
                usuario_responde TEXT,
                ip_address TEXT,
                FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id),
                FOREIGN KEY (persona_id) REFERENCES personas(id)
            )
            ''')
            conn.commit()
            print("✅ Tabla respuestas_formulario creada correctamente")
        
        conn.close()
        print("\n✅ Proceso completado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    crear_tabla()