import requests
import hashlib
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

HASH_CACHE_PATH = Path('data/content_hashes.json')


class NormMonitor:
    """Monitor for specific legal norms with change detection"""
    
    def __init__(self, norms: Optional[List[Dict]] = None):
        self.source_name = "normativa"
        self.norms = norms or []
        self._hashes = self._load_hashes()
    
    @classmethod
    def from_config(cls, config) -> 'NormMonitor':
        """Create NormMonitor from a Config object, reading norms from YAML."""
        norms = config.get('normas') or []
        return cls(norms=norms)
    
    def _load_hashes(self) -> Dict[str, str]:
        """Load previously stored content hashes."""
        if HASH_CACHE_PATH.exists():
            try:
                with open(HASH_CACHE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error al cargar cache de hashes: {e}")
        return {}
    
    def _save_hashes(self):
        """Persist content hashes to disk."""
        HASH_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(HASH_CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._hashes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error al guardar cache de hashes: {e}")
    
    def fetch_publications(self, categories: List[str]) -> List[Dict[str, Any]]:
        """Fetch and check monitored norms, detecting content changes.
        
        Args:
            categories: List of category strings to filter norms.
        
        Returns:
            List of publication dicts for reachable norms.
            Each dict includes 'changed': True/False indicating content change.
        """
        filtered_norms = [n for n in self.norms if n.get('category') in categories]
        
        if not filtered_norms:
            logger.info("No hay normas configuradas para las categorias seleccionadas")
            return []
        
        logger.info(f"Verificando {len(filtered_norms)} normas en paralelo...")
        publications = []
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_norm = {
                executor.submit(self._check_norm, norm): norm
                for norm in filtered_norms
            }
            
            for future in as_completed(future_to_norm):
                norm = future_to_norm[future]
                try:
                    pub = future.result()
                    if pub:
                        publications.append(pub)
                except Exception as e:
                    logger.error(f"Error checking {norm.get('name', '?')}: {e}")
        
        self._save_hashes()
        
        logger.info(f"  Verificadas {len(publications)}/{len(filtered_norms)} normas accesibles")
        changed_count = sum(1 for p in publications if p.get('changed'))
        if changed_count:
            logger.info(f"  {changed_count} norma(s) con cambios de contenido detectados")
        
        return publications
    
    def _check_norm(self, norm: Dict) -> Optional[Dict[str, Any]]:
        """Check if a norm URL is reachable and detect content changes via hash."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        }
        
        url = norm.get('url', '')
        name = norm.get('name', '')
        
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                # Compute content hash for change detection
                content_hash = hashlib.sha256(response.content).hexdigest()
                previous_hash = self._hashes.get(url)
                changed = previous_hash is not None and content_hash != previous_hash
                is_new = previous_hash is None
                
                self._hashes[url] = content_hash
                
                if changed:
                    logger.info(f"  Cambio detectado: {name}")
                
                fecha_pub = norm.get('fecha_pub', '')
                
                return {
                    'source': f"{norm.get('source', '').lower()}_{norm.get('category', '')}",
                    'url': url,
                    'title': name,
                    'category': norm.get('category', ''),
                    'date': fecha_pub,
                    'vigente': norm.get('vigente', 'Si'),
                    'norma': norm.get('norma', ''),
                    'summary': f"Verificacion de norma: {name}",
                    'changed': changed,
                    'is_new': is_new,
                }
            else:
                logger.warning(f"  {name}: HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            logger.warning(f"  Timeout al acceder a {name} ({url})")
        except requests.exceptions.ConnectionError:
            logger.warning(f"  Sin conexion a {name} ({url})")
        except Exception as e:
            logger.warning(f"  Error accediendo a {name}: {e}")
        
        return None
