#!/bin/bash
# Ejecutar como el usuario normal de la Raspberry: bash instalar.sh
set -euo pipefail
trap 'printf "\nInstalación interrumpida en línea %s. Corrige el error mostrado y vuelve a ejecutar.\n" "$LINENO" >&2' ERR
if [ "$EUID" -eq 0 ]; then
    echo 'Ejecuta bash instalar.sh como usuario normal, sin sudo delante.' >&2
    exit 1
fi
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
APP_USER="$(id -un)"
if [[ ! "$PROJECT_DIR" =~ ^/[a-zA-Z0-9_./-]+$ ]] || [[ ! "$APP_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    echo 'Usa una ruta de proyecto sin espacios ni caracteres especiales.' >&2
    exit 1
fi
cd "$PROJECT_DIR"
if [ "$(uname -m)" != aarch64 ] || [ "$(getconf LONG_BIT)" != 64 ]; then
    echo 'Este instalador requiere Raspberry Pi con Linux ARM de 64 bits (aarch64).' >&2
    exit 1
fi
. /etc/os-release
if [ "${VERSION_CODENAME:-}" != trixie ]; then
    echo 'Entorno previsto: Debian/Raspberry Pi OS 13 Trixie de 64 bits.' >&2
    exit 1
fi
sudo -v
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip v4l-utils libgl1 libglib2.0-0t64 git curl
python3 -c 'import sys; assert sys.version_info[:2] == (3,13), "Se requiere Python 3.13"'
# Detener el contador antes de modificar su entorno o probar la cámara.
sudo systemctl stop contadorbus.service 2>/dev/null || true
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python codigo/preparar_modelo.py
mkdir -p registros evidencias
# Verificar cámara AN-VC500/MJPG antes de habilitar el servicio.
sudo usermod -aG video "$APP_USER"
sudo -u "$APP_USER" "$PROJECT_DIR/.venv/bin/python" codigo/probar_camara.py --camera 0 --width 640 --height 480 --fps 30
TMP_DIR="$(mktemp -d)"
trap 'rm -rf -- "$TMP_DIR"' EXIT
sed -e "s|@USER@|$APP_USER|g" -e "s|@PROJECT@|$PROJECT_DIR|g" \
    deploy/contadorbus.service.in > "$TMP_DIR/contadorbus.service"
printf '%s ALL=(root) NOPASSWD: /usr/local/sbin/contadorbus-apagar ""\n' "$APP_USER" > "$TMP_DIR/contadorbus-apagar"
sudo visudo -cf "$TMP_DIR/contadorbus-apagar"
# Conservar configuraciones anteriores al reinstalar.
BACKUP_DIR="$HOME/contadorbus-config-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$BACKUP_DIR"
if [ -f /etc/systemd/system/contadorbus.service ]; then
    sudo cp -a /etc/systemd/system/contadorbus.service "$BACKUP_DIR/"
fi
sudo install -o root -g root -m 755 deploy/contadorbus-apagar /usr/local/sbin/contadorbus-apagar
sudo install -o root -g root -m 440 "$TMP_DIR/contadorbus-apagar" /etc/sudoers.d/contadorbus-apagar
sudo install -o root -g root -m 644 "$TMP_DIR/contadorbus.service" /etc/systemd/system/contadorbus.service
sudo systemctl daemon-reload
sudo systemctl enable --now contadorbus.service
# Esperar datos procesados, no solo que el puerto esté abierto.
if ! .venv/bin/python - <<'PY'
import json, time, urllib.request
for _ in range(120):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/api/estado', timeout=2) as r:
            if json.load(r).get('activo'):
                print('Contador procesando y panel web disponible.'); break
    except (OSError, ValueError):
        pass
    time.sleep(1)
else:
    raise SystemExit('No se recibieron datos activos. Consulta journalctl -u contadorbus.service -n 60.')
PY
then
    sudo journalctl -u contadorbus.service -n 60 --no-pager
    exit 1
fi
.venv/bin/python -m pip freeze > registros/requirements-instalados.txt
printf '\nInstalación terminada. Abre http://IP_DE_LA_RASPBERRY:8080 desde tu celular.\n'
hostname -I
printf 'Tailscale se configura aparte: bash instalar_tailscale.sh\n'
printf 'Comprueba el botón de apagado y el siguiente arranque antes de dar por validada la reinstalación.\n'
