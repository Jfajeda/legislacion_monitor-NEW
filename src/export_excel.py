from pathlib import Path
from datetime import datetime

def export_to_excel_formatted(db_path: str, output_path: str = None):
    """Export publications database to formatted Excel with two sheets"""
    
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    except ImportError:
        print("Instalando openpyxl...")
        import subprocess
        subprocess.run(['pip3', 'install', 'openpyxl'], capture_output=True)
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    
    Path('output').mkdir(exist_ok=True)
    if output_path is None:
        output_path = f"output/Legislacion_Monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT source, title, category, date, vigente, norma, url, summary
        FROM publications 
        ORDER BY category, source, title
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No hay publicaciones para exportar")
        return None
    
    wb = openpyxl.Workbook()
    
    # ============ HOJA 1: LEGISLACIÓN ============
    ws1 = wb.active
    ws1.title = "Legislación"
    
    colores = {
        'header': '1F4E79',
        'medio_ambiente': '2E7D32',
        'ciberseguridad': '1565C0',
        'privacidad': '6A1B9A',
        'seguridad_informacion': 'EF6C00',
        'border': 'BDC3C7'
    }
    
    header_fill = PatternFill(start_color=colores['header'], end_color=colores['header'], fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin', color=colores['border']),
        right=Side(style='thin', color=colores['border']),
        top=Side(style='thin', color=colores['border']),
        bottom=Side(style='thin', color=colores['border'])
    )
    
    headers = ['Fuente', 'Título', 'Categoría', 'Fecha', 'Vigente', 'Nº Norma', 'URL', 'Resumen']
    ws1.append(headers)
    
    for col_num, header in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    category_colors = {
        'medio_ambiente': colores['medio_ambiente'],
        'residuos': '4CAF50',
        'cambio_climatico': '00897B',
        'ciberseguridad': colores['ciberseguridad'],
        'privacidad': colores['privacidad'],
        'seguridad_informacion': colores['seguridad_informacion']
    }
    
    for row_num, row in enumerate(rows, 2):
        fuente = row['source'] or ''
        titulo = row['title'] or ''
        categoria = row['category'] or ''
        fecha = row['date'] or ''
        if not fecha or fecha.strip() == '':
            fecha = 'Pendiente'
        vigente = row['vigente'] or ''
        norma = row['norma'] or ''
        url = row['url'] or ''
        resumen = row['summary'] or ''
        
        ws1.append([fuente, titulo, categoria, fecha, vigente, norma, url, resumen])
        
        cat_color = category_colors.get(categoria, 'FFFFFF')
        cat_fill = PatternFill(start_color=cat_color, end_color=cat_color, fill_type='solid')
        
        for col_num in range(1, 9):
            cell = ws1.cell(row=row_num, column=col_num)
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            
            if col_num == 3:
                cell.fill = cat_fill
                cell.font = Font(bold=True, color='FFFFFF', size=10)
            elif col_num == 5:
                if 'En tramitación' in vigente or 'tramit' in vigente.lower():
                    cell.fill = PatternFill(start_color='FFA500', end_color='FFA500', fill_type='solid')
                    cell.font = Font(bold=True, size=10)
                else:
                    cell.fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
            elif col_num == 6:
                cell.font = Font(bold=True, size=10)
    
    col_widths = [18, 45, 22, 12, 18, 22, 50, 40]
    for i, width in enumerate(col_widths, 1):
        ws1.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    for cell in ws1[1]:
        ws1.row_dimensions[1].height = 25
    
    ws1.freeze_panes = 'A2'
    
    # ============ HOJA 2: ALERTAS SECTORIALES ============
    ws2 = wb.create_sheet("Alertas Sectoriales")
    
    from src.scrapers.alerts_monitor import AlertsMonitor
    from src.config import Config
    
    config_path = str(Path(db_path).parent.parent / 'config.yaml')
    config = Config(config_path)
    alert_monitor = AlertsMonitor.from_config(config)
    alerts = alert_monitor.fetch_alerts()
    
    headers_alerts = ['Entidad', 'Nombre', 'Descripción', 'Categoría', 'Última verificación', 'Estado', 'URL']
    ws2.append(headers_alerts)
    
    for col_num, header in enumerate(headers_alerts, 1):
        cell = ws2.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = thin_border
    
    entity_colors = {
        'AEPD': '1565C0',
        'APDCAT': '6A1B9A',
        'ENISA': '1565C0',
        'CCN-CERT': 'EF6C00',
        'INCIBE': 'EF6C00',
        'ACC': '00897B'
    }
    
    for row_num, alert in enumerate(alerts, 2):
        entity = alert.get('entity', '')
        name = alert.get('name', '')
        description = alert.get('description', '')
        category = alert.get('category', '')
        date = alert.get('date', '')
        status = alert.get('status', '')
        url = alert.get('url', '')
        
        ws2.append([entity, name, description, category, date, status, url])
        
        entity_color = entity_colors.get(entity, 'FFFFFF')
        entity_fill = PatternFill(start_color=entity_color, end_color=entity_color, fill_type='solid')
        
        for col_num in range(1, 8):
            cell = ws2.cell(row=row_num, column=col_num)
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            
            if col_num == 1:
                cell.fill = entity_fill
                cell.font = Font(bold=True, color='FFFFFF', size=10)
            elif col_num == 6:
                if 'Activo' in status:
                    cell.fill = PatternFill(start_color='C8E6C9', end_color='C8E6C9', fill_type='solid')
                else:
                    cell.fill = PatternFill(start_color='FFCDD2', end_color='FFCDD2', fill_type='solid')
    
    col_widths_alerts = [12, 30, 40, 18, 16, 18, 50]
    for i, width in enumerate(col_widths_alerts, 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width
    
    for cell in ws2[1]:
        ws2.row_dimensions[1].height = 25
    
    ws2.freeze_panes = 'A2'
    
    wb.save(output_path)
    print(f"Excel formateado: {output_path}")
    print(f"Total de normas: {len(rows)}")
    print(f"Total de alertas: {len(alerts)}")
    return output_path


if __name__ == '__main__':
    import sys
    
    db_path = 'data/publications.db'
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    export_to_excel_formatted(db_path)
