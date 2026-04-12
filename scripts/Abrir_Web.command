#!/bin/bash
cd "$(dirname "$0")/.."

echo "============================================================"
echo "  LEGISLACION MONITOR - Dashboard Web"
echo "============================================================"
echo ""
echo "Iniciando servidor en http://localhost:8080 ..."
echo ""

# Arranca Flask en segundo plano
python3 web/app.py &
SERVER_PID=$!

# Espera a que el servidor este listo
sleep 2

# Abre el navegador
open http://localhost:8080

echo "Dashboard abierto en el navegador."
echo ""
echo "Para cerrar el servidor, pulsa Ctrl+C o cierra esta ventana."
echo ""

# Espera a que el usuario cierre (Ctrl+C o cierre de ventana)
wait $SERVER_PID
