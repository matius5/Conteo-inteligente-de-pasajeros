#!/usr/bin/env python3
"""Descarga YOLOv8n si falta, exporta NCNN y comprueba una inferencia local."""
from pathlib import Path
import numpy as np
from ultralytics import YOLO


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / 'yolov8n_ncnn_model'
    if not all((target / f).is_file() for f in ('model.ncnn.param', 'model.ncnn.bin', 'metadata.yaml')):
        print('Descargando/exportando YOLOv8n a NCNN (320 px). Puede tardar varios minutos.')
        YOLO(str(root / 'yolov8n.pt')).export(format='ncnn', imgsz=320, device='cpu')
    model = YOLO(str(target), task='detect')
    model.predict(np.zeros((320, 320, 3), dtype=np.uint8), imgsz=320, device='cpu', verbose=False)
    print('Modelo NCNN preparado y comprobado.')


if __name__ == '__main__':
    main()
