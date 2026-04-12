#!/usr/bin/env python3
"""
Legislacion Monitor - Web Interface
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, send_file
from datetime import datetime
from pathlib import Path

from src.scrapers.norm_monitor import NormMonitor
from src.scrapers.alerts_monitor import AlertsMonitor
from src.database import Database
from src.config import Config

app = Flask(__name__)

# --- Configuracion global ------------------------------------------------

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
config = Config(CONFIG_PATH)
db = Database(config.get('database', {}))

# Estado del scraping en background
_scrape_status = {'running': False, 'last_result': None}


@app.route('/')
def dashboard():
    stats = db.get_stats()
    return render_template('dashboard.html',
        total=stats['total'],
        categories=stats['categories'],
        sources=stats['sources'],
        vigentes=stats['vigentes'],
        tramitacion=stats['tramitacion'],
        recent=stats['recent'])


@app.route('/legislacion')
def legislacion():
    publications = db.get_publications_by_category()
    return render_template('legislacion.html', publications=publications)


@app.route('/legislacion/<category>')
def legislacion_category(category):
    publications = db.get_publications_by_category(category)
    return render_template('legislacion.html', publications=publications, filter_category=category)


@app.route('/alertas')
def alertas():
    monitor = AlertsMonitor.from_config(config)
    alerts = monitor.fetch_alerts()
    return render_template('alertas.html', alerts=alerts)


def _run_scrape():
    """Execute scraping in background thread."""
    _scrape_status['running'] = True
    try:
        scraper = NormMonitor.from_config(config)
        categories = config.get('categorias') or [
            'medio_ambiente', 'residuos', 'cambio_climatico',
            'ciberseguridad', 'privacidad', 'seguridad_informacion'
        ]
        publications = scraper.fetch_publications(categories)
        
        new_count = 0
        for pub in publications:
            if not db.publication_exists(pub['url']):
                db.save_publication(pub)
                new_count += 1
        
        _scrape_status['last_result'] = {
            'new_count': new_count,
            'total': len(publications),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    except Exception as e:
        _scrape_status['last_result'] = {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    finally:
        _scrape_status['running'] = False


@app.route('/ejecutar')
def ejecutar():
    if _scrape_status['running']:
        return render_template('ejecutar.html',
            new_count=0, total=0,
            message="Ya hay un proceso de scraping en ejecucion. Espere a que termine.")
    
    # Lanzar en hilo de fondo
    thread = threading.Thread(target=_run_scrape, daemon=True)
    thread.start()
    
    return render_template('ejecutar.html',
        new_count=0, total=0,
        message="Scraping iniciado en segundo plano. Recargue la pagina en unos segundos para ver resultados.")


@app.route('/estado-scraping')
def estado_scraping():
    """API endpoint to check scraping status."""
    return jsonify({
        'running': _scrape_status['running'],
        'last_result': _scrape_status['last_result'],
    })


@app.route('/exportar')
def exportar():
    from src.export_excel import export_to_excel_formatted
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'publications.db')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    Path(output_dir).mkdir(exist_ok=True)
    
    output_path = os.path.join(output_dir, f"Legislacion_Monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    export_to_excel_formatted(db_path, output_path)
    
    return send_file(output_path, as_attachment=True)


if __name__ == '__main__':
    print("Abriendo navegador en http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
