from app import app, db
from sqlalchemy import text

with app.app_context():
    columnas = [
        ("observaciones", "TEXT"),
        ("latitud", "FLOAT"),
        ("longitud", "FLOAT"),
        ("direccion_ubicacion", "VARCHAR(300)")
    ]
    
    for col, tipo in columnas:
        try:
            db.session.execute(text(f"ALTER TABLE ordenes_captura ADD COLUMN {col} {tipo}"))
            db.session.commit()
            print(f"✅ Columna {col} agregada")
        except Exception as e:
            if "duplicate" in str(e).lower() or "exists" in str(e).lower():
                print(f"⚠️ Columna {col} ya existe")
            else:
                print(f"❌ Error con {col}: {e}")
    
    print("\n✅ Proceso completado")