import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AlertsMonitor:
    """Monitor for alerts from security and data protection entities"""
    
    def __init__(self, alerts_config: Optional[List[Dict]] = None):
        self.alerts_config = alerts_config or []
    
    @classmethod
    def from_config(cls, config) -> 'AlertsMonitor':
        """Create AlertsMonitor from a Config object, reading alerts from YAML."""
        alerts = config.get('alertas') or []
        return cls(alerts_config=alerts)
    
    def fetch_alerts(self) -> List[Dict[str, Any]]:
        """Fetch latest alerts from all entities in parallel."""
        if not self.alerts_config:
            logger.info("No hay alertas configuradas")
            return []
        
        alerts = []
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_config = {
                executor.submit(self._check_url, ac): ac
                for ac in self.alerts_config
            }
            
            for future in as_completed(future_to_config):
                ac = future_to_config[future]
                try:
                    alert = future.result()
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error checking {ac.get('name', '?')}: {e}")
        
        return alerts
    
    def _check_url(self, config: Dict) -> Dict[str, Any]:
        """Check a single URL for availability."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        
        url = config.get('url', '')
        base_result = {
            'entity': config.get('entity', ''),
            'name': config.get('name', ''),
            'description': config.get('description', ''),
            'url': url,
            'category': config.get('category', ''),
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                return {
                    **base_result,
                    'url': response.url,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'status': 'Activo',
                }
            elif response.status_code == 404:
                return {
                    **base_result,
                    'date': '',
                    'status': 'Pagina no encontrada (404)',
                }
            else:
                return {
                    **base_result,
                    'date': '',
                    'status': f'Error {response.status_code}',
                }
        except Exception as e:
            return {
                **base_result,
                'date': '',
                'status': 'Sin conexion',
            }
