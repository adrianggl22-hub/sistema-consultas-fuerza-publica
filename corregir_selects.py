import sqlite3
import json

def corregir_selects():
    try:
        conn = sqlite3.connect('instance/sistema_consultas.db')
        cursor = conn.cursor()
        
        # Buscar preguntas de tipo 'select' sin opciones
        cursor.execute("""
            SELECT p.id, p.titulo, m.nombre 
            FROM preguntas p
            JOIN machotes_documentos m ON p.machote_id = m.id
            WHERE p.tipo = 'select' 
            AND (p.opciones IS NULL OR p.opciones = '' OR p.opciones = '[]' OR p.opciones = 'null')
        """)
        preguntas = cursor.fetchall()
        
        if not preguntas:
            print("Todas las preguntas de tipo 'select' tienen opciones")
            conn.close()
            return
        
        print(f"Corrigiendo {len(preguntas)} preguntas...")
        print("="*60)
        
        opciones_por_defecto = {
            'tipo': ['Homicidio', 'Suicidio', 'Accidente', 'Natural', 'Heridos'],
            'parte': ['Torax', 'Abdomen', 'Brazo', 'Gluteo', 'Pierna', 'Cabeza'],
            'arma': ['Arma blanca', 'Arma de fuego', 'Otro'],
            'estado': ['Fallecido', 'Delicado'],
            'genero': ['Masculino', 'Femenino', 'Otro'],
            'nacionalidad': ['Costarricense', 'Nicaraguense', 'Panameno', 'Otro']
        }
        
        for p in preguntas:
            pregunta_id = p[0]
            titulo = p[1]
            machote_nombre = p[2]
            
            opciones = None
            titulo_lower = titulo.lower()
            for key, value in opciones_por_defecto.items():
                if key in titulo_lower:
                    opciones = value
                    break
            
            if not opciones:
                opciones = ['Opcion 1', 'Opcion 2', 'Opcion 3']
            
            cursor.execute("UPDATE preguntas SET opciones = ? WHERE id = ?", 
                          (json.dumps(opciones), pregunta_id))
            
            print(f"  Pregunta '{titulo}' (en {machote_nombre}) -> {opciones}")
        
        conn.commit()
        print("="*60)
        print(f"Corregidas {len(preguntas)} preguntas")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    corregir_selects()