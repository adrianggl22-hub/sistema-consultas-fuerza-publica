# ver_acciones.py
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app import AccionOperativa

with app.app_context():
    acciones = AccionOperativa.query.all()
    print(f"📊 Total de acciones operativas: {len(acciones)}")
    
    if len(acciones) == 0:
        print("\n⚠️ No hay acciones operativas registradas.")
        print("   Crea una desde el menú 'Acciones Operativas'")
    else:
        for a in acciones:
            print(f"\n📋 Acción ID: {a.id}")
            print(f"   Fecha: {a.fecha}")
            print(f"   Unidad: {a.cod_unidad}")
            print(f"   Lugar: {a.lugar}")
            print(f"   Personas abordadas: {a.personas_abordadas}")
            print(f"   Gramos marihuana: {a.gramos_marihuana}")
            print(f"   Gramos crack: {a.gramos_crack}")
            print(f"   Gramos cocaina: {a.gramos_cocaina}")
            print(f"   Armas fuego: {a.armas_fuego}")
            print(f"   Armas blancas: {a.armas_blancas}")
            print(f"   Motos: {a.motos}")
            print(f"   Carros: {a.carros}")
            print(f"   Control carretera: {a.control_carretera}")
            print(f"   Visitas comercio: {a.visitas_comercio}")