# crear_accion_prueba.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app import AccionOperativa
from datetime import datetime

with app.app_context():
    # Verificar si ya existe una acción de prueba
    existe = AccionOperativa.query.filter_by(accion_realizada="OPERATIVO DE PRUEBA ESTADISTICAS").first()
    
    if existe:
        print("⚠️ Ya existe una acción de prueba. Eliminándola...")
        db.session.delete(existe)
        db.session.commit()
    
    print("📝 Creando acción operativa de prueba con datos reales...")
    
    nueva_accion = AccionOperativa(
        cod_unidad="1943-TEST",
        fecha=datetime.now().strftime("%Y-%m-%d"),
        hora_inicio="10:00",
        hora_fin="12:00",
        lugar="COLON, MORA - CENTRO (Zona de prueba)",
        accion_realizada="OPERATIVO DE PRUEBA ESTADISTICAS",
        instituciones="MUNICIPALIDAD DE MORA",
        escuadra_1=True,
        escuadra_2=False,
        escuadra_3=True,
        escuadra_4=False,
        mando="SGTO ADRIAN GARITA",
        oficiales="OFICIAL YOSSER FUENTES, OFICIAL EDWIN CARMONA",
        # Datos de prueba con valores REALES para que se vean en estadísticas
        personas_abordadas=25,
        personas_investigadas_oij=3,
        motos=8,
        carros=5,
        armas=1,
        control_carretera=2,
        op_inter_institucionales=1,
        ganado_seguro=0,
        visitas_comercio=4,
        paso_escolar=1,
        notificaciones=2,
        guardas_seguridad=0,
        orden_apremio_corporal=0,
        partes_transito=3,
        placas_decomisadas=0,
        informes_policiales=1,
        incidentes_cerrados=1,
        vehiculos_incautados=1,
        # Drogas - VALORES REALES
        puchos_marihuana=5,
        cigarillos_marihuana=3,
        gramos_marihuana=25.5,
        piedras_crack=2,
        gramos_crack=1.5,
        puntas_cocaina=4,
        gramos_cocaina=2.0,
        # Armas - VALORES REALES
        armas_fuego=1,
        armas_blancas=2,
        # Dinero - VALOR REAL
        dinero_efectivo=25000,
        otros_incautaciones="2 celulares, 1 laptop",
        anotaciones="Operativo de prueba para verificar estadísticas. Incluye incautaciones de drogas, armas y dinero.",
        fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        usuario_registro="admin",
        estado="ACTIVA"
    )
    
    db.session.add(nueva_accion)
    db.session.commit()
    print("✅ Acción operativa de prueba creada con datos reales")
    print(f"   ID: {nueva_accion.id}")
    print(f"   📊 Datos incluidos:")
    print(f"      - Gramos marihuana: 25.5g")
    print(f"      - Gramos crack: 1.5g")
    print(f"      - Gramos cocaína: 2.0g")
    print(f"      - Armas de fuego: 1")
    print(f"      - Armas blancas: 2")
    print(f"      - Dinero: ₡25,000")
    print(f"      - Personas abordadas: 25")
    print(f"      - Motos: 8, Carros: 5")