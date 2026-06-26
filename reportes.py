# reportes.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

def generar_reporte_ordenes(ordenes, mes, año):
    """Genera reporte PDF de órdenes de captura"""
    
    # Crear nombre del archivo
    filename = f'reportes/ordenes_{año}_{mes}.pdf'
    os.makedirs('reportes', exist_ok=True)
    
    # Configurar el documento
    doc = SimpleDocTemplate(filename, pagesize=letter, 
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    # Elementos del PDF
    elements = []
    
    # Título
    elements.append(Paragraph(f"ORDENES DE CAPTURA - REPORTE MENSUAL", title_style))
    elements.append(Paragraph(f"Mes: {mes}/{año} | Fecha de generacion: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Resumen de estadísticas
    total_ordenes = len(ordenes)
    activas = len([o for o in ordenes if o.get('estado') == 'ACTIVA'])
    vencidas = len([o for o in ordenes if o.get('estado') == 'VENCIDA'])
    canceladas = len([o for o in ordenes if o.get('estado') == 'CANCELADA'])
    deuda_total = sum([o.get('monto_deuda', 0) for o in ordenes])
    deuda_activa = sum([o.get('monto_deuda', 0) for o in ordenes if o.get('estado') == 'ACTIVA'])
    
    # Tabla de resumen
    resumen_data = [
        ['Total Ordenes', 'Activas', 'Vencidas', 'Canceladas', 'Deuda Total', 'Deuda Activa'],
        [str(total_ordenes), str(activas), str(vencidas), str(canceladas), 
         f"₡{deuda_total:,.2f}", f"₡{deuda_activa:,.2f}"]
    ]
    
    resumen_tabla = Table(resumen_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch, 1.5*inch])
    resumen_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
    ]))
    
    elements.append(resumen_tabla)
    elements.append(Spacer(1, 30))
    
    # Tabla de órdenes
    elements.append(Paragraph("Detalle de Ordenes", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    # Datos de la tabla
    tabla_data = [['N° Orden', 'Deudor', 'Cedula', 'Juzgado', 'Monto', 'Vencimiento', 'Estado']]
    
    for o in ordenes[:50]:
        tabla_data.append([
            o.get('numero_orden', '-'),
            (o.get('persona_nombre', '-') or '-')[:30],
            o.get('persona_cedula', '-'),
            (o.get('juzgado', '-') or '-')[:25],
            f"₡{o.get('monto_deuda', 0):,.2f}",
            o.get('fecha_vencimiento', '-') or '-',
            o.get('estado', '-')
        ])
    
    tabla = Table(tabla_data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(tabla)
    
    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Total de registros: {len(ordenes)} | Reporte generado por Sistema de Consultas - Fuerza Publica", 
                            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)))
    
    # Generar PDF
    doc.build(elements)
    return filename

def generar_reporte_acciones(acciones, mes, año):
    """Genera reporte PDF de acciones operativas con TODOS los datos"""
    
    filename = f'reportes/acciones_{año}_{mes}.pdf'
    os.makedirs('reportes', exist_ok=True)
    
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                  textColor=colors.HexColor('#27ae60'), alignment=TA_CENTER, spaceAfter=30)
    
    elements = []
    
    # Título
    elements.append(Paragraph(f"ACCIONES OPERATIVAS - REPORTE MENSUAL", title_style))
    elements.append(Paragraph(f"Mes: {mes}/{año} | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                            ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=20)))
    elements.append(Spacer(1, 20))
    
    # ==================== ESTADÍSTICAS GENERALES ====================
    total_acciones = len(acciones)
    total_personas = sum([a.get('personas_abordadas', 0) for a in acciones])
    total_investigados = sum([a.get('personas_investigadas_oij', 0) for a in acciones])
    total_motos = sum([a.get('motos', 0) for a in acciones])
    total_carros = sum([a.get('carros', 0) for a in acciones])
    total_armas_comunes = sum([a.get('armas', 0) for a in acciones])
    total_controles = sum([a.get('control_carretera', 0) for a in acciones])
    total_op_inter = sum([a.get('op_inter_institucionales', 0) for a in acciones])
    total_ganado = sum([a.get('ganado_seguro', 0) for a in acciones])
    total_visitas_comercio = sum([a.get('visitas_comercio', 0) for a in acciones])
    total_paso_escolar = sum([a.get('paso_escolar', 0) for a in acciones])
    total_notificaciones = sum([a.get('notificaciones', 0) for a in acciones])
    total_guardas = sum([a.get('guardas_seguridad', 0) for a in acciones])
    total_ordenes_apremio = sum([a.get('orden_apremio_corporal', 0) for a in acciones])
    total_partes = sum([a.get('partes_transito', 0) for a in acciones])
    total_placas = sum([a.get('placas_decomisadas', 0) for a in acciones])
    total_informes = sum([a.get('informes_policiales', 0) for a in acciones])
    total_incidentes = sum([a.get('incidentes_cerrados', 0) for a in acciones])
    total_vehiculos = sum([a.get('vehiculos_incautados', 0) for a in acciones])
    
    # Drogas
    total_puchos = sum([a.get('puchos_marihuana', 0) for a in acciones])
    total_cigarillos = sum([a.get('cigarillos_marihuana', 0) for a in acciones])
    total_gramos_marihuana = sum([a.get('gramos_marihuana', 0) for a in acciones])
    total_piedras_crack = sum([a.get('piedras_crack', 0) for a in acciones])
    total_gramos_crack = sum([a.get('gramos_crack', 0) for a in acciones])
    total_puntas_cocaina = sum([a.get('puntas_cocaina', 0) for a in acciones])
    total_gramos_cocaina = sum([a.get('gramos_cocaina', 0) for a in acciones])
    
    # Armas
    total_armas_fuego = sum([a.get('armas_fuego', 0) for a in acciones])
    total_armas_blancas = sum([a.get('armas_blancas', 0) for a in acciones])
    total_dinero = sum([a.get('dinero_efectivo', 0) for a in acciones])
    
    # Tabla de resumen general
    resumen_data = [
        ['MÉTRICA', 'TOTAL'],
        ['Total Acciones', str(total_acciones)],
        ['Personas Abordadas', str(total_personas)],
        ['Personas Investigadas OIJ', str(total_investigados)],
        ['Motos Revisadas', str(total_motos)],
        ['Carros Revisados', str(total_carros)],
        ['Armas Decomisadas (comunes)', str(total_armas_comunes)],
        ['Controles Carretera', str(total_controles)],
        ['Operaciones Interinstitucionales', str(total_op_inter)],
        ['Ganado Asegurado', str(total_ganado)],
        ['Visitas a Comercios', str(total_visitas_comercio)],
        ['Paso Escolar', str(total_paso_escolar)],
        ['Notificaciones', str(total_notificaciones)],
        ['Guardas de Seguridad', str(total_guardas)],
        ['Órdenes Apremio Corporal', str(total_ordenes_apremio)],
        ['Partes de Tránsito', str(total_partes)],
        ['Placas Decomisadas', str(total_placas)],
        ['Informes Policiales', str(total_informes)],
        ['Incidentes Cerrados', str(total_incidentes)],
        ['Vehículos Incautados', str(total_vehiculos)]
    ]
    
    resumen_tabla = Table(resumen_data, colWidths=[2.5*inch, 1.5*inch])
    resumen_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
    ]))
    
    elements.append(resumen_tabla)
    elements.append(Spacer(1, 20))
    
    # Tabla de drogas
    elements.append(Paragraph("Incautaciones de Drogas", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    drogas_data = [
        ['Tipo', 'Cantidad'],
        ['Puchos de Marihuana', str(total_puchos)],
        ['Cigarillos de Marihuana', str(total_cigarillos)],
        ['Gramos de Marihuana', f"{total_gramos_marihuana:.2f} g"],
        ['Piedras de Crack', str(total_piedras_crack)],
        ['Gramos de Crack', f"{total_gramos_crack:.2f} g"],
        ['Puntas de Cocaína', str(total_puntas_cocaina)],
        ['Gramos de Cocaína', f"{total_gramos_cocaina:.2f} g"]
    ]
    
    drogas_tabla = Table(drogas_data, colWidths=[2.5*inch, 1.5*inch])
    drogas_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
    ]))
    
    elements.append(drogas_tabla)
    elements.append(Spacer(1, 20))
    
    # Tabla de armas y dinero
    elements.append(Paragraph("Armas y Dinero Incautado", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    armas_data = [
        ['Tipo', 'Cantidad'],
        ['Armas de Fuego', str(total_armas_fuego)],
        ['Armas Blancas', str(total_armas_blancas)],
        ['Dinero en Efectivo', f"₡{total_dinero:,.2f}"]
    ]
    
    armas_tabla = Table(armas_data, colWidths=[2.5*inch, 1.5*inch])
    armas_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
    ]))
    
    elements.append(armas_tabla)
    elements.append(Spacer(1, 30))
    
    # Tabla de acciones individuales
    elements.append(Paragraph("Detalle de Acciones Operativas", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    tabla_data = [['Fecha', 'Unidad', 'Lugar', 'Personas', 'Motos', 'Carros', 'Drogas(g)', 'Armas', 'Dinero']]
    
    for a in acciones[:50]:
        drogas = (a.get('gramos_marihuana', 0) + a.get('gramos_crack', 0) + a.get('gramos_cocaina', 0))
        armas = (a.get('armas_fuego', 0) + a.get('armas_blancas', 0))
        dinero = a.get('dinero_efectivo', 0)
        tabla_data.append([
            a.get('fecha', '-'),
            a.get('cod_unidad', '-'),
            (a.get('lugar', '-') or '-')[:35],
            str(a.get('personas_abordadas', 0)),
            str(a.get('motos', 0)),
            str(a.get('carros', 0)),
            f"{drogas:.1f}",
            str(armas),
            f"₡{dinero:,.0f}" if dinero > 0 else "-"
        ])
    
    tabla = Table(tabla_data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(tabla)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Total de registros: {len(acciones)} | Sistema de Consultas - Fuerza Publica",
                            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)))
    
    doc.build(elements)
    return filename

def generar_reporte_incidentes(incidentes, mes, año):
    """Genera reporte PDF de incidentes"""
    
    filename = f'reportes/incidentes_{año}_{mes}.pdf'
    os.makedirs('reportes', exist_ok=True)
    
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter),
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                  textColor=colors.HexColor('#e74c3c'), alignment=TA_CENTER, spaceAfter=30)
    
    elements = []
    
    elements.append(Paragraph(f"INCIDENTES RELEVANTES - REPORTE MENSUAL", title_style))
    elements.append(Paragraph(f"Mes: {mes}/{año} | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 
                            ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=20)))
    elements.append(Spacer(1, 20))
    
    # Estadísticas
    tipos = {}
    total_aprehendidos = sum([i.get('aprehendidos', 0) for i in incidentes])
    total_ofendidos = sum([i.get('ofendidos', 0) for i in incidentes])
    total_testigos = sum([i.get('testigos', 0) for i in incidentes])
    
    for i in incidentes:
        tipo = i.get('tipo_incidente', 'Otros')
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    top_tipos = sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Tabla de resumen
    resumen_data = [
        ['Métrica', 'Total'],
        ['Total Incidentes', str(len(incidentes))],
        ['Total Aprehendidos', str(total_aprehendidos)],
        ['Total Ofendidos', str(total_ofendidos)],
        ['Total Testigos', str(total_testigos)]
    ]
    
    resumen_tabla = Table(resumen_data, colWidths=[2.5*inch, 1.5*inch])
    resumen_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
    ]))
    
    elements.append(resumen_tabla)
    elements.append(Spacer(1, 20))
    
    # Tabla de tipos de incidentes
    elements.append(Paragraph("Top 5 Tipos de Incidentes", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    tipos_data = [['Tipo de Incidente', 'Cantidad']]
    for tipo, cantidad in top_tipos:
        tipos_data.append([tipo, str(cantidad)])
    
    tipos_tabla = Table(tipos_data, colWidths=[3*inch, 2*inch])
    tipos_tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
    ]))
    
    elements.append(tipos_tabla)
    elements.append(Spacer(1, 30))
    
    # Tabla de incidentes
    elements.append(Paragraph("Detalle de Incidentes", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=12, spaceAfter=10)))
    
    tabla_data = [['N° Unidad', 'Fecha', 'Tipo', 'Oficial Actuante', 'Aprehendidos', 'Lugar']]
    
    for i in incidentes[:50]:
        tabla_data.append([
            i.get('numero_incidente', '-'),
            i.get('fecha_incidente', '-'),
            (i.get('tipo_incidente', '-') or '-')[:25],
            i.get('oficial_actuante', '-')[:25],
            str(i.get('aprehendidos', 0)),
            (i.get('lugar', '-') or '-')[:30]
        ])
    
    tabla = Table(tabla_data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(tabla)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Total de registros: {len(incidentes)} | Sistema de Consultas - Fuerza Publica",
                            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)))
    
    doc.build(elements)
    return filename