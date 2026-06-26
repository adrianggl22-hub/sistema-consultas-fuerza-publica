# guarda esto como fix_db.py y ejecútalo con: python fix_db.py
import sqlite3

def fix_database():
    conn = sqlite3.connect('sistema_consultas.db')
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna 'titulo' existe en respuestas_formulario
        cursor.execute("PRAGMA table_info(respuestas_formulario)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'titulo' not in columnas:
            print("⚠️ Agregando columna 'titulo' a respuestas_formulario...")
            cursor.execute("ALTER TABLE respuestas_formulario ADD COLUMN titulo TEXT")
            conn.commit()
            print("✅ Columna 'titulo' agregada correctamente")
        else:
            print("✅ La columna 'titulo' ya existe")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()