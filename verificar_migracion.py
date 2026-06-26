# verificar_migracion.py
import sqlite3
import os

def verificar_migracion():
    db_path = None
    if os.path.exists('sistema_consultas.db'):
        db_path = 'sistema_consultas.db'
    elif os.path.exists('instance/sistema_consultas.db'):
        db_path = 'instance/sistema_consultas.db'
    
    if not db_path:
        print("❌ No se encontró la base de datos")
        return
    
    print(f"📁 Base de datos: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verificando estructura de la base de datos...")
    print("=" * 50)
    
    # Verificar tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [t[0] for t in cursor.fetchall()]
    print(f"📋 Tablas existentes: {', '.join(tablas) if tablas else 'Ninguna'}")
    print("=" * 50)
    
    # Verificar columnas de ordenes_captura
    if 'ordenes_captura' in tablas:
        cursor.execute("PRAGMA table_info(ordenes_captura)")
        columnas = cursor.fetchall()
        print("📋 Columnas en 'ordenes_captura':")
        for col in columnas:
            print(f"  - {col[1]} ({col[2]})")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM ordenes_captura")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total de órdenes: {count}")
        
        # Mostrar un ejemplo
        if count > 0:
            cursor.execute("SELECT id, numero_orden, expediente, fecha_emision FROM ordenes_captura LIMIT 3")
            ejemplos = cursor.fetchall()
            print("\n📝 Ejemplos de órdenes:")
            for ej in ejemplos:
                print(f"  ID: {ej[0]}, N°: {ej[1]}, Expediente: {ej[2] or 'No especificado'}, Fecha: {ej[3] or 'No especificada'}")
    else:
        print("❌ La tabla 'ordenes_captura' NO existe")
    
    print("=" * 50)
    
    # Verificar usuarios
    if 'usuarios' in tablas:
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        count = cursor.fetchone()[0]
        print(f"👤 Usuarios: {count}")
    else:
        print("❌ La tabla 'usuarios' NO existe")
    
    # Verificar personas
    if 'personas' in tablas:
        cursor.execute("SELECT COUNT(*) FROM personas")
        count = cursor.fetchone()[0]
        print(f"👤 Personas: {count}")
    else:
        print("❌ La tabla 'personas' NO existe")
    
    conn.close()
    print("\n✅ Verificación completada")

if __name__ == "__main__":
    verificar_migracion()