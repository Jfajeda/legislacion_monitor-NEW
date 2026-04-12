import csv
from pathlib import Path
from datetime import datetime

def export_to_csv(db_path: str, output_path: str = None):
    """Export publications database to CSV"""
    
    if output_path is None:
        output_path = f"publications_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT source, title, category, date, vigente, norma, url, summary, created_at
        FROM publications 
        ORDER BY date DESC, created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No hay publicaciones para exportar")
        return
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Fuente', 'Título', 'Categoría', 'Fecha', 'Vigente', 'Nº Norma', 'URL', 'Resumen', 'Fecha Creación'])
        
        for row in rows:
            keys = row.keys()
            vigente = row['vigente'] if 'vigente' in keys else 'Sí'
            norma = row['norma'] if 'norma' in keys else ''
            writer.writerow([
                row['source'],
                row['title'],
                row['category'],
                row['date'],
                vigente,
                norma,
                row['url'],
                row['summary'],
                row['created_at']
            ])
    
    print(f"Exportado: {output_path}")
    print(f"Total de registros: {len(rows)}")
    return output_path


if __name__ == '__main__':
    import sys
    
    db_path = 'data/publications.db'
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    export_to_csv(db_path)
