#!/bin/bash
set -euo pipefail
if ! command -v tailscale >/dev/null; then
    TEMP_INSTALLER="$(mktemp)"
    trap 'rm -f -- "$TEMP_INSTALLER"' EXIT
    curl -fsSL https://tailscale.com/install.sh -o "$TEMP_INSTALLER"
    sudo sh "$TEMP_INSTALLER"
fi
sudo systemctl enable --now tailscaled
sudo tailscale up
tailscale ip -4
printf 'En el celular conectado a la misma red Tailscale: http://IP_TAILSCALE:8080\n'
