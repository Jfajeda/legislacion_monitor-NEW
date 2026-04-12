#!/bin/bash
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  LEGISLACION MONITOR - Actualizacion completa"
echo "============================================================"
echo ""

# --- Paso 1: Scraping de normas ---
echo "[1/2] Ejecutando scraping de normas..."
echo ""
python3 main.py --run
echo ""

# --- Paso 2: Exportar Excel ---
echo "[2/2] Generando Excel con legislacion + alertas..."
echo ""
python3 -m src.export_excel
echo ""

echo "============================================================"
echo "  PROCESO COMPLETADO"
echo ""
echo "  El archivo Excel esta en la carpeta output/"
echo "  Hoja 1: Legislacion  |  Hoja 2: Alertas Sectoriales"
echo "============================================================"
echo ""
echo "Presiona cualquier tecla para salir..."
read -n 1
