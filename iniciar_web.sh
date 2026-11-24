#!/bin/bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
exec .venv/bin/python -u codigo/contador_web.py --camera 0 --model yolov8n_ncnn_model --imgsz 320 --fourcc MJPG --no-display --line-x 320 --entry-direction left_to_right --initial-occupancy 0 "$@"
