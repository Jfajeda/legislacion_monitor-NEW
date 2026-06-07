# AGENTS.md — Legislacion Monitor (CODANOR)

Regulatory legislation monitoring system (EU, Spain, Catalonia) tracking norms across
environment, cybersecurity, privacy, and information security.
Python 3.11 + Flask + SQLite. All text in **Spanish**.

**Path:** `~/Proyectos/legislacion_monitor/`
OpenCode sessions may start at `~/Desktop/legislacion_monitor` — that path is stale. Always `cd` to the real path above.

## Structure

```
main.py              # CLI entrypoint (--run, --list)
config.yaml          # Norms catalog, alerts, categories, DB path, email — single source of truth
requirements.txt     # requests, pyyaml, openpyxl, flask
src/                 # All library code (import as src.*)
  config.py          # YAML loader with dot-key access: config.get('database.path')
  database.py        # SQLite wrapper (WAL mode, timeout=10)
  notifier.py        # SMTP email (reads SMTP_PASSWORD env var, fallback to YAML)
  export_csv.py      # CSV export (function: export_to_csv)
  export_excel.py    # XLSX export with 2 sheets: Legislacion + Alertas
  scrapers/
    norm_monitor.py  # Checks 43 norm URLs, SHA-256 change detection, ThreadPoolExecutor(8)
    alerts_monitor.py# Checks 10 entity URLs for availability, ThreadPoolExecutor(6)
web/
  app.py             # Flask on port 8080; sys.path.insert(0, project_root) for src.* imports
  templates/         # Jinja2: dashboard, legislacion, alertas, ejecutar
scripts/             # macOS .command shortcuts (all do cd "$(dirname "$0")/.." to reach project root)
tests/               # unittest only (no pytest)
data/                # Runtime: publications.db, content_hashes.json (auto-created)
output/              # Generated XLSX exports
```

## Commands

```bash
pip3 install -r requirements.txt           # Install deps
python3 main.py --run                      # Scrape all 43 norms, save new to DB
python3 main.py --list --days 30           # Query recent publications
python3 -m src.export_excel                # Generate XLSX in output/
python3 web/app.py                         # Start web dashboard on :8080
python3 -m unittest discover -s tests -v   # Run 8 tests (no pytest)
curl http://localhost:8080/estado-scraping  # Check scraping status (JSON)
```

## Flask routes

| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Dashboard with stats |
| GET | `/legislacion` | All publications table |
| GET | `/legislacion/<category>` | Filtered by category |
| GET | `/alertas` | **Slow** — 10 live HTTP requests on every load (no cache) |
| GET | `/ejecutar` | Renders scraping control page |
| POST | `/ejecutar` | Launches scraping in background thread; returns JSON. 409 if already running |
| GET | `/estado-scraping` | JSON polling endpoint: `{running, last_result}` |
| GET | `/exportar` | **Slow** — generates XLSX (includes live alert fetch for Sheet 2), returns file download |

## Import convention

All internal imports use the `src.` prefix. Never `from database import ...` — always `from src.database import Database`.
`web/app.py` adds the project root to `sys.path` so `src.*` resolves when Flask runs from `web/`.

## config.yaml is the source of truth for norms

The full catalog of 43 norms and 10 alerts is in `config.yaml` under `normas:` and `alertas:` keys.
Both `NormMonitor` and `AlertsMonitor` are created via `.from_config(config)` — do NOT hardcode norm lists in Python.
Six categories: `medio_ambiente`, `residuos`, `cambio_climatico`, `ciberseguridad`, `privacidad`, `seguridad_informacion`.

## Non-obvious details

- **README.md is outdated**: describes old flat structure with individual scrapers (`eurlex.py`, `boe.py`, etc.) and only 3 categories. The actual architecture is `src/scrapers/norm_monitor.py` (unified) + `alerts_monitor.py`. Trust this AGENTS.md over the README.
- **Change detection**: `norm_monitor.py` persists SHA-256 content hashes to `data/content_hashes.json`. Compares between runs.
- **DB dedup**: `INSERT OR IGNORE` on URL unique constraint. WAL journal mode. If all 43 norms are already in DB, `new_count` will be 0 — that's correct, not a bug.
- **Web /ejecutar route**: GET shows the page, POST launches scraping in `threading.Thread(daemon=True)`. Frontend JS polls `/estado-scraping` every 2s. Never call POST on page load.
- **Export as module**: `export_excel.py` must be run as `python3 -m src.export_excel` (not `python3 src/export_excel.py`), because it imports `src.scrapers.*`.
- **Export config path derivation**: `export_excel.py` computes config path as `Path(db_path).parent.parent / 'config.yaml'` — breaks if DB location changes.
- **Scripts cd trick**: all `.command` files use `cd "$(dirname "$0")/.."` since they live in `scripts/`, not project root.
- **No pytest**: `python3 -m unittest discover -s tests -v`. Tests create temp SQLite files and clean up WAL/SHM artifacts.
- **SMTP disabled by default**: `notifications.enabled: false` in config. Password from `$SMTP_PASSWORD` env var takes priority.
- **Logger alias**: `main.py` uses `logger`, `web/app.py` uses `log`. Both are `logging.getLogger(__name__)`.
- **`.gitignore` gaps**: `data/`, `output/`, `logs/` are NOT ignored — DB, hashes, exports, and log files are trackable by git.
- **No git remote, no CI**: single branch `main`, purely local repo. No linters, no formatters, no type checkers.
