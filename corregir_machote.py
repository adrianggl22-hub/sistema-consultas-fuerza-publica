import sqlite3
import json
import sys

# Configurar encoding para evitar errores
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def corregir_machote():
    try:
        print("🔧 CORRIGIENDO MACHOTE...")
        print("=" * 60)
        
        # Conectar a la base de datos
        conn = sqlite3.connect('instance/sistema_consultas.db')
        cursor = conn.cursor()
        
        # Obtener el registro
        cursor.execute("SELECT id, nombre, estructura FROM machotes_documentos WHERE id = 1")
        registro = cursor.fetchone()
        
        if not registro:
            print("❌ No se encontró el machote con ID 1")
            conn.close()
            return
        
        machote_id = registro[0]
        nombre = registro[1]
        estructura = json.loads(registro[2])
        
        print(f"📄 Machote: {nombre}")
        print(f"📊 Preguntas actuales: {len(estructura.get('preguntas', []))}")
        print("-" * 60)
        
        if 'preguntas' in estructura:
            # Eliminar duplicados manteniendo la primera ocurrencia
            ids_vistos = {}
            preguntas_limpias = []
            preguntas_eliminadas = 0
            
            for pregunta in estructura['preguntas']:
                pregunta_id = pregunta.get('id')
                
                if pregunta_id in ids_vistos:
                    print(f"⚠️ Eliminando duplicado ID {pregunta_id}: '{pregunta.get('titulo')}'")
                    preguntas_eliminadas += 1
                    continue
                
                ids_vistos[pregunta_id] = True
                preguntas_limpias.append(pregunta)
            
            # Asignar nuevos IDs
            for i, pregunta in enumerate(preguntas_limpias, 1):
                pregunta['id'] = i
                tipo = pregunta.get('tipo', 'desconocido')
                titulo = pregunta.get('titulo', 'sin titulo')
                print(f"  ✅ Pregunta {i}: [{tipo}] {titulo}")
            
            # Actualizar estructura
            estructura['preguntas'] = preguntas_limpias
            nueva_estructura = json.dumps(estructura, ensure_ascii=False, indent=2)
            
            # Guardar en la base de datos
            cursor.execute(
                "UPDATE machotes_documentos SET estructura = ? WHERE id = ?",
                (nueva_estructura, machote_id)
            )
            conn.commit()
            
            print("-" * 60)
            print(f"✅ CORRECCIÓN COMPLETADA!")
            print(f"   Preguntas eliminadas: {preguntas_eliminadas}")
            print(f"   Preguntas finales: {len(preguntas_limpias)}")
            print(f"   IDs asignados: {[p['id'] for p in preguntas_limpias]}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    corregir_machote()