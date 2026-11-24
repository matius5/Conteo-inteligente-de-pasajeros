#!/usr/bin/env python3
"""Prueba mínima de cámara USB sin depender de una interfaz gráfica.

Fuerza MJPG porque la cámara LG AN-VC500 de este equipo falla con el formato
YUYV por defecto en algunas configuraciones. Guarda una imagen de evidencia.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2


def abrir_camara(indice: int, ancho: int, alto: int, fps: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(indice, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def main() -> int:
    parser = argparse.ArgumentParser(description="Captura una muestra real de la cámara")
    parser.add_argument("--camera", type=int, default=0, help="Índice de cámara (0 = /dev/video0)")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument(
        "--snapshot",
        default="evidencias/camara_prueba.jpg",
        help="Ruta de la imagen de verificación",
    )
    args = parser.parse_args()

    ruta_dispositivo = f"/dev/video{args.camera}"
    if not Path(ruta_dispositivo).exists():
        print(f"ERROR: no existe {ruta_dispositivo}. Revisa el cable USB de la cámara.")
        return 1

    cap = abrir_camara(args.camera, args.width, args.height, args.fps)
    if not cap.isOpened():
        print(f"ERROR: no se pudo abrir la cámara {args.camera}")
        return 1

    # Descartar los primeros fotogramas: algunas cámaras tardan en ajustar exposición.
    for _ in range(5):
        cap.read()

    inicio = time.perf_counter()
    ok_count = 0
    frame = None
    for _ in range(args.frames):
        ok, frame = cap.read()
        if ok:
            ok_count += 1
    transcurrido = time.perf_counter() - inicio
    fps_real = ok_count / transcurrido if transcurrido > 0 else 0.0

    print(f"Cámara abierta: {args.camera}")
    print(f"Resolución solicitada: {args.width}x{args.height} @ {args.fps} fps (MJPG)")
    if frame is not None:
        alto, ancho = frame.shape[:2]
        print(f"Resolución real del fotograma: {ancho}x{alto}")
        print(f"Fotogramas válidos: {ok_count}/{args.frames}")
        print(f"FPS de captura medidos: {fps_real:.2f}")
        print(f"Brillo medio: {frame.mean():.1f}")

        salida = Path(args.snapshot)
        salida.parent.mkdir(parents=True, exist_ok=True)
        if cv2.imwrite(str(salida), frame):
            print(f"Captura guardada: {salida.resolve()}")
        else:
            print(f"ERROR: no se pudo guardar {salida}")
    else:
        print("ERROR: no se recibió ningún fotograma")

    cap.release()
    return 0 if ok_count else 2


if __name__ == "__main__":
    raise SystemExit(main())
