import sqlite3
import re

def corregir_machote_final():
    try:
        conn = sqlite3.connect('instance/sistema_consultas.db')
        cursor = conn.cursor()
        
        # Ver todos los machotes
        cursor.execute("SELECT id, nombre, contenido FROM machotes_documentos")
        machotes = cursor.fetchall()
        
        print("="*60)
        print("CORRIGIENDO MACHOTES")
        print("="*60)
        
        for machote in machotes:
            machote_id = machote[0]
            nombre = machote[1]
            contenido = machote[2]
            
            print(f"\nMachote: {nombre} (ID: {machote_id})")
            
            if '+ varName +' in contenido:
                print("  Contiene '+ varName +' - corrigiendo...")
                
                nuevo_contenido = contenido
                
                reemplazos = {
                    'nombre: + varName +': 'nombre: {{ nombre }}',
                    'cedula: + varName +': 'cedula: {{ cedula }}',
                    'observaciones: + varName +': 'observaciones: {{ observaciones }}',
                    'Nombre: + varName +': 'Nombre: {{ nombre }}',
                    'Cedula: + varName +': 'Cedula: {{ cedula }}',
                    'Observaciones: + varName +': 'Observaciones: {{ observaciones }}',
                    'Fecha: + varName +': 'Fecha: {{ fecha }}',
                    'Hora: + varName +': 'Hora: {{ hora }}',
                    'Lugar del incidente: + varName +': 'Lugar del incidente: {{ lugar_incidente }}',
                    'Canton: + varName +': 'Canton: {{ canton }}',
                    'Distrito: + varName +': 'Distrito: {{ distrito }}',
                    'Lugar exacto: + varName +': 'Lugar exacto: {{ lugar_exacto }}',
                    'Tipo de incidente: + varName +': 'Tipo de incidente: {{ tipo_incidente }}',
                    'Partes del cuerpo: + varName +': 'Partes del cuerpo: {{ partes_cuerpo }}',
                    'Tipo de arma: + varName +': 'Tipo de arma: {{ tipo_arma }}',
                    'Nombre completo: + varName +': 'Nombre completo: {{ nombre_completo }}',
                    'Edad: + varName +': 'Edad: {{ edad }}',
                    'Estado: + varName +': 'Estado: {{ estado }}',
                    'Nacionalidad: + varName +': 'Nacionalidad: {{ nacionalidad }}',
                    'Alias: + varName +': 'Alias: {{ alias }}',
                    'Descripcion de diligencias policiales: + varName +': 'Descripcion de diligencias policiales: {{ descripcion }}',
                }
                
                for viejo, nuevo in reemplazos.items():
                    if viejo in nuevo_contenido:
                        nuevo_contenido = nuevo_contenido.replace(viejo, nuevo)
                        print(f"    Reemplazado: {viejo[:30]}... -> {nuevo[:30]}...")
                
                if '+ varName +' in nuevo_contenido:
                    nuevo_contenido = re.sub(r'\+\s*varName\s*\+', '{{ variable }}', nuevo_contenido)
                    print("    Reemplazados los + varName + restantes")
                
                cursor.execute("UPDATE machotes_documentos SET contenido = ? WHERE id = ?", 
                              (nuevo_contenido, machote_id))
                conn.commit()
                print("  Contenido corregido y guardado")
            else:
                print("  Contenido correcto")
        
        print("\n" + "="*60)
        print("TODOS LOS MACHOTES CORREGIDOS")
        print("="*60)
        
        cursor.execute("SELECT id, nombre, contenido FROM machotes_documentos WHERE id = 11")
        registro = cursor.fetchone()
        if registro:
            print(f"\nContenido del machote ID 11:")
            print(registro[2])
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    corregir_machote_final()