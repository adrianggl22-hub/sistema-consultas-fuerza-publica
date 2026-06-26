# recrear_tablas.py
import sqlite3

conn = sqlite3.connect('sistema_consultas.db')
cursor = conn.cursor()

print("RECREANDO TABLAS DE MACHOTES")
print("=" * 50)

# 1. machotes_documentos
cursor.execute("""
CREATE TABLE machotes_documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    tipo_documento TEXT NOT NULL,
    categoria TEXT,
    contenido TEXT NOT NULL,
    variables TEXT,
    estructura TEXT,
    archivo_adjunto TEXT,
    es_activo BOOLEAN DEFAULT 1,
    creado_por TEXT,
    fecha_registro TEXT,
    ultima_modificacion TEXT
)
""")
print("  OK - machotes_documentos")

# 2. preguntas
cursor.execute("""
CREATE TABLE preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machote_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0,
    tipo TEXT DEFAULT 'texto',
    titulo TEXT NOT NULL,
    variable TEXT NOT NULL,
    opciones TEXT,
    requerido BOOLEAN DEFAULT 1,
    FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id) ON DELETE CASCADE
)
""")
print("  OK - preguntas")

# 3. respuestas
cursor.execute("""
CREATE TABLE respuestas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machote_id INTEGER NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario TEXT,
    datos TEXT,
    FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id) ON DELETE CASCADE
)
""")
print("  OK - respuestas")

# 4. respuestas_formulario
cursor.execute("""
CREATE TABLE respuestas_formulario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machote_id INTEGER NOT NULL,
    persona_id INTEGER,
    titulo TEXT,
    fecha_respuesta DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_responde TEXT,
    ip_address TEXT,
    FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id) ON DELETE CASCADE,
    FOREIGN KEY (persona_id) REFERENCES personas(id) ON DELETE SET NULL
)
""")
print("  OK - respuestas_formulario")

# 5. respuestas_detalle
cursor.execute("""
CREATE TABLE respuestas_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    respuesta_id INTEGER NOT NULL,
    pregunta_id INTEGER NOT NULL,
    pregunta_titulo TEXT,
    pregunta_tipo TEXT,
    respuesta TEXT,
    FOREIGN KEY (respuesta_id) REFERENCES respuestas_formulario(id) ON DELETE CASCADE
)
""")
print("  OK - respuestas_detalle")

# 6. documentos_generados
cursor.execute("""
CREATE TABLE documentos_generados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machote_id INTEGER NOT NULL,
    titulo TEXT,
    contenido TEXT NOT NULL,
    variables_utilizadas TEXT,
    generado_por TEXT,
    fecha_generacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machote_id) REFERENCES machotes_documentos(id) ON DELETE CASCADE
)
""")
print("  OK - documentos_generados")

conn.commit()

# Verificar
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tablas = cursor.fetchall()

print("\nTablas creadas:")
for tabla in tablas:
    print(f"  - {tabla[0]}")

conn.close()

print("\nTodas las tablas de machotes recreadas correctamente")