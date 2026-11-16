#!/bin/zsh
# Instala Nube De-Ess en REAPER (macOS) como enlace: los cambios del repo se ven al volver a insertar el FX.
set -e
DST="$HOME/Library/Application Support/REAPER/Effects/Nube De-Ess"
cd "$(dirname "$0")"
mkdir -p "$DST"
ln -sf "$PWD/nube_deess.jsfx" "$DST/nube_deess.jsfx"
echo "Listo: en REAPER busca \"Nube De-Ess\" en el navegador de FX (JS: Nube De-Ess)."
