"""
SISTEMA DE BACKUP AUTOMÁTICO PARA BASE DE DATOS
===============================================
Este script crea copias de seguridad de la base de datos
y mantiene un historial de los últimos 10 backups.
"""

import os
import shutil
import json
from datetime import datetime
import glob

# Configuración
DB_PATH = 'sistema_consultas.db'
BACKUP_DIR = 'backups'
HISTORIAL_FILE = 'backup_historial.json'
MAX_BACKUPS = 10  # Número máximo de backups a mantener

def crear_backup():
    """Crea una copia de seguridad de la base de datos"""
    
    # Verificar que la base de datos existe
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: No se encontró {DB_PATH}")
        return False
    
    # Crear carpeta de backups si no existe
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"📁 Carpeta '{BACKUP_DIR}' creada")
    
    # Generar nombre del backup con fecha y hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # Obtener tamaño original
    tamaño_original = os.path.getsize(DB_PATH)
    
    try:
        # Copiar archivo
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup creado: {backup_filename}")
        print(f"   📊 Tamaño: {tamaño_original / 1024:.2f} KB")
        
        # Registrar en historial
        registrar_historial(backup_filename, tamaño_original)
        
        # Limpiar backups antiguos
        limpiar_backups_antiguos()
        
        return True
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return False

def registrar_historial(backup_filename, tamaño):
    """Registra el backup en un archivo JSON"""
    
    historial = []
    
    # Cargar historial existente
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            try:
                historial = json.load(f)
            except:
                historial = []
    
    # Agregar nuevo registro
    nuevo_registro = {
        'archivo': backup_filename,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'tamaño_bytes': tamaño,
        'tamaño_kb': round(tamaño / 1024, 2)
    }
    historial.insert(0, nuevo_registro)
    
    # Guardar historial
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)
    
    print(f"   📝 Registrado en historial")

def limpiar_backups_antiguos():
    """Elimina backups antiguos manteniendo solo los últimos MAX_BACKUPS"""
    
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")))
    
    if len(backups) > MAX_BACKUPS:
        eliminar = backups[:-MAX_BACKUPS]
        for old_backup in eliminar:
            os.remove(old_backup)
            print(f"   🗑️ Backup antiguo eliminado: {os.path.basename(old_backup)}")

def listar_backups():
    """Muestra la lista de backups disponibles"""
    
    if not os.path.exists(BACKUP_DIR):
        print("❌ No hay backups disponibles")
        return []
    
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")), reverse=True)
    
    if not backups:
        print("❌ No hay backups disponibles")
        return []
    
    print("\n📋 BACKUPS DISPONIBLES:")
    print("-" * 60)
    for i, backup in enumerate(backups, 1):
        nombre = os.path.basename(backup)
        tamaño = os.path.getsize(backup) / 1024
        fecha = nombre.replace("backup_", "").replace(".db", "")
        fecha_legible = f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]} {fecha[9:11]}:{fecha[11:13]}:{fecha[13:15]}"
        print(f"{i}. {nombre}")
        print(f"   📅 Fecha: {fecha_legible}")
        print(f"   📊 Tamaño: {tamaño:.2f} KB")
        print()
    
    return backups

def restaurar_backup(backup_filename=None):
    """Restaura un backup específico"""
    
    if not backup_filename:
        backups = listar_backups()
        if not backups:
            return False
        
        try:
            seleccion = int(input("\nSeleccione el número de backup a restaurar: ")) - 1
            backup_path = backups[seleccion]
        except:
            print("❌ Selección inválida")
            return False
    else:
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        if not os.path.exists(backup_path):
            print(f"❌ Backup no encontrado: {backup_filename}")
            return False
    
    # Confirmar restauración
    print(f"\n⚠️ ADVERTENCIA: Esto sobrescribirá la base de datos actual")
    confirmar = input(f"¿Restaurar backup {os.path.basename(backup_path)}? (s/n): ")
    
    if confirmar.lower() != 's':
        print("❌ Restauración cancelada")
        return False
    
    # Hacer backup del estado actual antes de restaurar
    if os.path.exists(DB_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_PATH, f"{DB_PATH}.pre_restauracion_{timestamp}")
        print(f"📦 Backup previo guardado: {DB_PATH}.pre_restauracion_{timestamp}")
    
    # Restaurar
    try:
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ Base de datos restaurada exitosamente")
        print(f"   📂 Origen: {os.path.basename(backup_path)}")
        return True
    except Exception as e:
        print(f"❌ Error al restaurar: {e}")
        return False

def programar_backup():
    """Configura el backup automático programado"""
    
    print("\n🔧 CONFIGURACIÓN DE BACKUP AUTOMÁTICO")
    print("=" * 40)
    print("1. Backup cada hora")
    print("2. Backup cada 6 horas")
    print("3. Backup cada 12 horas")
    print("4. Backup diario (recomendado)")
    print("5. Backup semanal")
    print("6. Cancelar")
    
    opcion = input("\nSeleccione una opción: ")
    
    if opcion == '1':
        horas = 1
    elif opcion == '2':
        horas = 6
    elif opcion == '3':
        horas = 12
    elif opcion == '4':
        horas = 24
    elif opcion == '5':
        horas = 168
    else:
        print("❌ Configuración cancelada")
        return
    
    # Crear script de tarea programada
    crear_tarea_programada(horas)

def crear_tarea_programada(horas):
    """Crea una tarea programada en Windows"""
    
    import subprocess
    
    script_path = os.path.abspath(__file__)
    task_name = "SistemaConsultasBackup"
    
    # Comando para crear tarea programada
    cmd = f'schtasks /create /tn "{task_name}" /tr "python {script_path} --auto" /sc hourly /mo {horas} /f'
    
    try:
        subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"✅ Tarea programada creada: Cada {horas} horas")
        print(f"   Nombre: {task_name}")
        print("\n📌 Para ver/eliminar la tarea:")
        print(f"   Ver: schtasks /query /tn \"{task_name}\"")
        print(f"   Eliminar: schtasks /delete /tn \"{task_name}\" /f")
    except Exception as e:
        print(f"❌ Error al crear tarea: {e}")
        print("\n💡 Puedes ejecutar el backup manualmente con: python backup_automatico.py --auto")

def mostrar_menu():
    """Muestra el menú principal"""
    
    print("\n" + "=" * 50)
    print("   SISTEMA DE BACKUP AUTOMÁTICO")
    print("=" * 50)
    print("1. Crear backup manual")
    print("2. Listar backups disponibles")
    print("3. Restaurar backup")
    print("4. Configurar backup automático")
    print("5. Salir")
    print("=" * 50)

if __name__ == "__main__":
    
    import sys
    
    # Modo automático (para tareas programadas)
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando backup automático...")
        crear_backup()
        sys.exit(0)
    
    # Modo interactivo
    while True:
        mostrar_menu()
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == '1':
            crear_backup()
        elif opcion == '2':
            listar_backups()
        elif opcion == '3':
            restaurar_backup()
        elif opcion == '4':
            programar_backup()
        elif opcion == '5':
            print("\n👋 Hasta luego!")
            break
        else:
            print("❌ Opción inválida")
        
        input("\nPresione Enter para continuar...")