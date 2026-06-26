# migrar_db_sin_perder_datos.py
import sqlite3
import os
from datetime import datetime

def migrar_base_datos():
    print("🔄 Migrando base de datos SIN perder datos...")
    
    # Buscar la base de datos
    db_path = None
    if os.path.exists('sistema_consultas.db'):
        db_path = 'sistema_consultas.db'
    elif os.path.exists('instance/sistema_consultas.db'):
        db_path = 'instance/sistema_consultas.db'
    
    if not db_path:
        print("❌ No se encontró la base de datos")
        return
    
    print(f"📁 Base de datos encontrada: {db_path}")
    
    # Verificar tamaño
    tamaño = os.path.getsize(db_path)
    print(f"📊 Tamaño actual: {tamaño} bytes ({tamaño/1024:.2f} KB)")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar todas las tablas existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = [t[0] for t in cursor.fetchall()]
    print(f"📋 Tablas existentes: {', '.join(tablas)}")
    
    # ==================== CREAR TABLA ordenes_captura SI NO EXISTE ====================
    if 'ordenes_captura' not in tablas:
        print("⚠️ La tabla 'ordenes_captura' no existe. Creándola con todos los datos...")
        
        # Crear la tabla con todas las columnas necesarias
        cursor.execute('''
            CREATE TABLE ordenes_captura (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id INTEGER NOT NULL,
                numero_orden VARCHAR(50) NOT NULL,
                monto_deuda FLOAT NOT NULL,
                fecha_emision VARCHAR(20) NOT NULL,
                fecha_vencimiento VARCHAR(20),
                juzgado VARCHAR(100) NOT NULL,
                expediente VARCHAR(50),
                estado VARCHAR(20) DEFAULT 'ACTIVA',
                resultado TEXT,
                observaciones TEXT,
                latitud FLOAT,
                longitud FLOAT,
                direccion_ubicacion VARCHAR(300),
                fecha_registro VARCHAR(50),
                FOREIGN KEY (persona_id) REFERENCES personas (id)
            )
        ''')
        conn.commit()
        print("✅ Tabla 'ordenes_captura' creada correctamente")
        
        # Verificar si hay datos que migrar desde otra tabla
        # (por si antes se llamaba de otra forma)
        tablas_alternativas = ['ordenes', 'orden_captura', 'ordenes_captura_old']
        for tabla_alt in tablas_alternativas:
            if tabla_alt in tablas:
                try:
                    # Obtener estructura de la tabla alternativa
                    cursor.execute(f"PRAGMA table_info({tabla_alt})")
                    columnas_alt = [col[1] for col in cursor.fetchall()]
                    
                    # Intentar migrar datos
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla_alt}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"📊 Encontrados {count} registros en tabla '{tabla_alt}'")
                        print(f"🔄 Migrando datos de '{tabla_alt}' a 'ordenes_captura'...")
                        
                        # Construir consulta de inserción dinámica
                        columnas_comunes = ['id', 'persona_id', 'numero_orden', 'monto_deuda', 
                                          'fecha_emision', 'fecha_vencimiento', 'juzgado', 
                                          'expediente', 'estado', 'resultado', 'observaciones',
                                          'latitud', 'longitud', 'direccion_ubicacion', 'fecha_registro']
                        
                        columnas_existentes = [col for col in columnas_comunes if col in columnas_alt]
                        
                        if columnas_existentes:
                            columnas_str = ', '.join(columnas_existentes)
                            placeholders = ', '.join(['?'] * len(columnas_existentes))
                            
                            cursor.execute(f"SELECT {columnas_str} FROM {tabla_alt}")
                            datos = cursor.fetchall()
                            
                            for dato in datos:
                                cursor.execute(f"INSERT INTO ordenes_captura ({columnas_str}) VALUES ({placeholders})", dato)
                            
                            conn.commit()
                            print(f"✅ {len(datos)} registros migrados desde '{tabla_alt}'")
                            
                            # Eliminar tabla antigua si se migró correctamente
                            # cursor.execute(f"DROP TABLE {tabla_alt}")
                            # print(f"🗑️ Tabla '{tabla_alt}' eliminada")
                except Exception as e:
                    print(f"⚠️ Error migrando desde '{tabla_alt}': {e}")
    else:
        print("✅ La tabla 'ordenes_captura' ya existe")
        
        # ==================== VERIFICAR Y AGREGAR COLUMNAS FALTANTES ====================
        cursor.execute("PRAGMA table_info(ordenes_captura)")
        columnas_actuales = [col[1] for col in cursor.fetchall()]
        print(f"📋 Columnas actuales en ordenes_captura: {', '.join(columnas_actuales)}")
        
        # Lista de columnas que deben existir
        columnas_necesarias = [
            ('expediente', 'VARCHAR(50)'),
            ('latitud', 'FLOAT'),
            ('longitud', 'FLOAT'),
            ('direccion_ubicacion', 'VARCHAR(300)'),
            ('resultado', 'TEXT')
        ]
        
        # Agregar columnas faltantes
        columnas_agregadas = 0
        for col_name, col_type in columnas_necesarias:
            if col_name not in columnas_actuales:
                try:
                    print(f"⚠️ Agregando columna '{col_name}'...")
                    cursor.execute(f"ALTER TABLE ordenes_captura ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"✅ Columna '{col_name}' agregada")
                    columnas_agregadas += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"ℹ️ La columna '{col_name}' ya existe")
                    else:
                        print(f"❌ Error agregando '{col_name}': {e}")
            else:
                print(f"✅ Columna '{col_name}' ya existe")
        
        if columnas_agregadas > 0:
            print(f"🔄 Se agregaron {columnas_agregadas} columnas nuevas")
        
        # ==================== ACTUALIZAR REGISTROS EXISTENTES ====================
        print("🔄 Actualizando registros existentes...")
        
        # Verificar si hay registros
        cursor.execute("SELECT COUNT(*) FROM ordenes_captura")
        total_registros = cursor.fetchone()[0]
        print(f"📊 Total de registros: {total_registros}")
        
        if total_registros > 0:
            # Si expediente está vacío, usar numero_orden
            cursor.execute("UPDATE ordenes_captura SET expediente = numero_orden WHERE expediente IS NULL OR expediente = ''")
            conn.commit()
            print("✅ Expediente actualizado para registros vacíos")
            
            # Si fecha_emision está vacía, usar fecha_registro
            cursor.execute("UPDATE ordenes_captura SET fecha_emision = fecha_registro WHERE fecha_emision IS NULL OR fecha_emision = ''")
            conn.commit()
            print("✅ Fecha de emisión actualizada para registros vacíos")
    
    # ==================== VERIFICAR OTRAS TABLAS ====================
    # Verificar que la tabla 'personas' existe
    if 'personas' not in tablas:
        print("⚠️ La tabla 'personas' no existe. Creándola...")
        cursor.execute('''
            CREATE TABLE personas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula VARCHAR(20) UNIQUE NOT NULL,
                nombre VARCHAR(100) NOT NULL,
                fecha_nacimiento VARCHAR(20),
                genero VARCHAR(20),
                direccion VARCHAR(200),
                telefono VARCHAR(20),
                email VARCHAR(100),
                foto VARCHAR(500),
                fecha_registro VARCHAR(50),
                estado VARCHAR(20) DEFAULT 'ACTIVO'
            )
        ''')
        conn.commit()
        print("✅ Tabla 'personas' creada")
    
    # Verificar que la tabla 'usuarios' existe
    if 'usuarios' not in tablas:
        print("⚠️ La tabla 'usuarios' no existe. Creándola...")
        cursor.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(200) NOT NULL,
                rol VARCHAR(20) DEFAULT 'usuario',
                activo BOOLEAN DEFAULT 1,
                fecha_registro VARCHAR(50)
            )
        ''')
        conn.commit()
        print("✅ Tabla 'usuarios' creada")
    
    # ==================== VERIFICAR DATOS FINALES ====================
    print("\n📊 Resumen final:")
    
    # Contar registros en cada tabla
    tablas_verificar = ['usuarios', 'personas', 'ordenes_captura']
    for tabla in tablas_verificar:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
            count = cursor.fetchone()[0]
            print(f"  📋 {tabla}: {count} registros")
        except:
            print(f"  ❌ {tabla}: No existe")
    
    # Verificar columnas de ordenes_captura
    cursor.execute("PRAGMA table_info(ordenes_captura)")
    columnas_finales = [col[1] for col in cursor.fetchall()]
    print(f"  📋 Columnas en ordenes_captura: {', '.join(columnas_finales)}")
    
    conn.close()
    print("\n✅ Migración completada exitosamente SIN perder datos")

if __name__ == "__main__":
    migrar_base_datos()