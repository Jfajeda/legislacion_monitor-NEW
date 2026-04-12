#!/bin/bash
cd "$(dirname "$0")/.."
python3 main.py --list --days 30
echo ""
echo "Presiona cualquier tecla para salir..."
read -n 1
