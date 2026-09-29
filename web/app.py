#!/usr/bin/env python3
"""
Legislacion Monitor - Web Interface
"""

import sys
import os
import logging
import threading
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request, send_file, abort, Response
from datetime import datetime, timedelta
from pathlib import Path

from src.scrapers.norm_monitor import NormMonitor
from src.scrapers.alerts_monitor import AlertsMonitor
from src.database import Database
from src.config import Config

# --- Logging --------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(32).hex())

# --- Autenticación básica para endpoints sensibles -------------------------

_EXPORT_USER = os.environ.get('EXPORT_USER', 'codanor')
_EXPORT_PASS = os.environ.get('EXPORT_PASS', 'legislacion2026')


def _require_auth(f):
    """Decorador de autenticación HTTP Basic para rutas sensibles."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != _EXPORT_USER or auth.password != _EXPORT_PASS:
            return Response(
                'Acceso no autorizado. Introduce tus credenciales.',
                401,
                {'WWW-Authenticate': 'Basic realm="Legislacion Monitor"'},
            )
        return f(*args, **kwargs)
    return decorated

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
    orden = request.args.get('orden', 'default')
    publications = db.get_publications_by_category(order_by=orden)
    dias_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    return render_template('legislacion.html', publications=publications,
                           now=datetime.now(), orden=orden, dias_limite=dias_limite)


@app.route('/legislacion/<category>')
def legislacion_category(category):
    orden = request.args.get('orden', 'default')
    publications = db.get_publications_by_category(category, order_by=orden)
    dias_limite = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    return render_template('legislacion.html', publications=publications,
                           filter_category=category, now=datetime.now(), orden=orden,
                           dias_limite=dias_limite)


@app.route('/alertas')
def alertas():
    monitor = AlertsMonitor.from_config(config)
    alerts = monitor.fetch_alerts()
    return render_template('alertas.html', alerts=alerts)


def _run_scrape():
    """Execute scraping in background thread."""
    _scrape_status['running'] = True
    _scrape_status['last_result'] = None
    log.info("Scraping iniciado en segundo plano")
    try:
        scraper = NormMonitor.from_config(config)
        categories = config.get('categorias') or [
            'medio_ambiente', 'residuos', 'cambio_climatico',
            'ciberseguridad', 'privacidad', 'seguridad_informacion'
        ]
        publications = scraper.fetch_publications(categories)

        new_count = 0
        changed_count = 0
        for pub in publications:
            if not db.publication_exists(pub['url']):
                db.save_publication(pub)
                new_count += 1
            if pub.get('changed'):
                changed_count += 1

        _scrape_status['last_result'] = {
            'ok': True,
            'new_count': new_count,
            'changed_count': changed_count,
            'total': len(publications),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        log.info(f"Scraping finalizado: {len(publications)} verificadas, {new_count} nuevas, {changed_count} con cambios")
    except Exception as e:
        log.error(f"Error en scraping: {e}")
        _scrape_status['last_result'] = {
            'ok': False,
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    finally:
        _scrape_status['running'] = False


@app.route('/ejecutar', methods=['GET'])
def ejecutar():
    """Muestra la pagina de ejecucion con estado actual."""
    return render_template('ejecutar.html')


@app.route('/ejecutar', methods=['POST'])
def ejecutar_post():
    """Lanza scraping en segundo plano (llamado via fetch desde JS)."""
    # Verificar que la petición es AJAX legítima (mitigación CSRF sin dependencia extra)
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        abort(403)

    if _scrape_status['running']:
        return jsonify({'started': False, 'reason': 'Ya hay un scraping en ejecucion'}), 409

    thread = threading.Thread(target=_run_scrape, daemon=True)
    thread.start()
    return jsonify({'started': True})


@app.route('/estado-scraping')
def estado_scraping():
    """API endpoint para consultar el estado del scraping."""
    return jsonify({
        'running': _scrape_status['running'],
        'last_result': _scrape_status['last_result'],
    })


@app.route('/exportar')
@_require_auth
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
    app.run(host='127.0.0.1', port=8080, debug=False)
