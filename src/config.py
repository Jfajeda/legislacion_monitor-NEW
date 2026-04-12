import yaml
import os
from typing import Any, Optional


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return self._default_config()
    
    def _default_config(self) -> dict:
        """Return default configuration when no YAML file exists."""
        return {
            'database': {
                'type': 'sqlite',
                'path': 'data/publications.db'
            },
            'notifications': {
                'enabled': False,
                'email': {
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_tls': True,
                    'sender': '',
                    'recipients': []
                }
            },
            'check_interval': 3600,
            'categorias': [
                'medio_ambiente', 'residuos', 'cambio_climatico',
                'ciberseguridad', 'privacidad', 'seguridad_informacion'
            ],
            'normas': [],
            'alertas': [],
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key.
        
        Examples:
            config.get('database.path')
            config.get('notifications.email.smtp_server')
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
