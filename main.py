#!/usr/bin/env python3
"""
Legislacion Monitor - Sistema de seguimiento de publicaciones normativas
European Union, Spain & Catalonia
Environment | Cybersecurity | Privacy | Information Security
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, List

from src.scrapers.norm_monitor import NormMonitor
from src.database import Database
from src.notifier import Notifier
from src.config import Config

Path('logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/legislacion_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LegislacionMonitor:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self.db = Database(self.config.get('database', {}))
        self.notifier = Notifier(self.config.get('notifications', {}))
        self.scraper = NormMonitor.from_config(self.config)
        self.all_categories = self.config.get('categorias') or [
            'medio_ambiente', 'residuos', 'cambio_climatico',
            'ciberseguridad', 'privacidad', 'seguridad_informacion'
        ]
    
    def run(self, categories: Optional[List[str]] = None):
        """Execute monitoring for specified categories"""
        logger.info("=" * 60)
        logger.info("Iniciando verificacion de publicaciones normativas...")
        logger.info("=" * 60)
        
        categories = categories or self.all_categories
        
        new_publications = []
        
        try:
            publications = self.scraper.fetch_publications(categories)
            
            for pub in publications:
                if not self.db.publication_exists(pub['url']):
                    self.db.save_publication(pub)
                    new_publications.append(pub)
                    logger.info(f"  Nueva publicacion: {pub['title']}")
                elif pub.get('changed'):
                    logger.info(f"  Cambio en contenido: {pub['title']}")
        except Exception as e:
            logger.error(f"Error al buscar: {e}")
        
        if new_publications:
            count = len(new_publications)
            logger.info(f"Se encontraron {count} nueva(s) publicacion(es)")
            self.notifier.send_notification(new_publications)
        else:
            logger.info("No se encontraron nuevas publicaciones")
        
        return new_publications
    
    def list_publications(self, source: Optional[str] = None, category: Optional[str] = None, 
                         days: int = 30) -> list:
        """List recent publications from database"""
        return self.db.get_publications(source=source, category=category, days=days)


def main():
    parser = argparse.ArgumentParser(
        description='Legislacion Monitor - Seguimiento de publicaciones normativas'
    )
    parser.add_argument('--run', action='store_true', 
                       help='Ejecutar verificacion de publicaciones')
    parser.add_argument('--list', action='store_true',
                       help='Listar publicaciones recientes')
    parser.add_argument('--categories', nargs='+',
                       help='Categorias a filtrar')
    parser.add_argument('--days', type=int, default=30,
                       help='Dias hacia atras para listar publicaciones')
    parser.add_argument('--config', default='config.yaml',
                       help='Ruta al archivo de configuracion')
    
    args = parser.parse_args()
    
    monitor = LegislacionMonitor(args.config)
    
    if args.run:
        monitor.run(categories=args.categories)
    elif args.list:
        publications = monitor.list_publications(
            category=args.categories[0] if args.categories else None,
            days=args.days
        )
        for pub in publications:
            vigente = pub.get('vigente', '')
            norma = pub.get('norma', '')
            print(f"[{pub['date']}] {pub['source']} - {pub['category']}: {pub['title']}")
            print(f"  Norma: {norma} | Vigente: {vigente}")
            print(f"  URL: {pub['url']}")
            print()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
