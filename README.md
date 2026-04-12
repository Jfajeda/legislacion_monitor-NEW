# Legislación Monitor

Sistema de seguimiento de publicaciones normativas para la Unión Europea, España y Cataluña en materia de Medio Ambiente, Ciberseguridad y Privacidad.

## Características

- **Monitoreo automático** de fuentes oficiales:
  - EUR-Lex (Diario Oficial de la UE)
  - BOE (Boletín Oficial del Estado)
  - DOGC (Diario Oficial de la Generalitat de Catalunya)
  - Gencat (Portal de la Generalitat)

- **Categorías monitoreadas**:
  - Medio Ambiente
  - Ciberseguridad
  - Privacidad / Protección de Datos

- **Notificaciones** por email cuando se detecten nuevas publicaciones

- **Base de datos local** para historial de publicaciones

## Requisitos

```bash
pip install -r requirements.txt
```

## Configuración

Editar `config.yaml`:

```yaml
database:
  type: sqlite
  path: data/publications.db

notifications:
  enabled: true
  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    sender: tu_email@gmail.com
    recipients:
      - email@ejemplo.com
```

## Uso

### Ejecutar verificación de publicaciones
```bash
python main.py --run
```

### Listar publicaciones recientes
```bash
python main.py --list --days 30
```

### Filtrar por fuente
```bash
python main.py --list --sources eurlex boe
```

### Filtrar por categoría
```bash
python main.py --run --categories medio_ambiente ciberseguridad
```

## Programar ejecución automática

### macOS / Linux (cron)
```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada día a las 8:00
0 8 * * * /usr/bin/python3 /ruta/a/main.py --run
```

### Windows (Task Scheduler)
Crear tarea programada que ejecute:
```
python.exe C:\ruta\a\main.py --run
```

## Estructura del proyecto

```
legislacion_monitor/
├── main.py              # Punto de entrada
├── config.py            # Gestión de configuración
├── database.py          # Base de datos SQLite
├── notifier.py         # Sistema de notificaciones
├── config.yaml         # Archivo de configuración
├── requirements.txt    # Dependencias
├── scrapers/
│   ├── __init__.py
│   ├── eurlex.py      # Scraper EUR-Lex
│   ├── boe.py        # Scraper BOE
│   ├── dogc.py       # Scraper DOGC
│   └── gencat.py     # Scraper Gencat
└── data/              # Base de datos (se crea automáticamente)
```

## Fuentes monitoreadas

### Unión Europea
- Pactos Verdes / Climate Law
- Directiva de Emisiones Industriales
- Reglamento REACH
- Directiva CSRD / ESRS
- NIS2

### España
- BOE (todas las secciones)
- MITECO
- AEPD

### Cataluña
- DOGC
- Gencat - Medi Ambient
- Gencat - Ciberseguridad
- APDCAT (Autoridad Protección de Datos)

## Notas

- El sistema utiliza web scraping. Las fuentes pueden cambiar su estructura HTML.
- Se recomienda ejecutar con frecuencia moderada para evitar sobrecargar los servidores.
- Para producción, considere implementar caché y rate limiting.
