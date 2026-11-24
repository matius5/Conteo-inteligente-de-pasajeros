#!/usr/bin/env python3
"""Prueba de conexión serial con la ESP32.

Envía un mensaje JSON de ejemplo. No requiere que el contador esté activo.
Ejemplo: ./.venv/bin/python codigo/enviar_serial.py /dev/ttyUSB0 --baud 115200
"""
from __future__ import annotations

import argparse
import time

from serial_esp32 import EnviadorSerial


def main() -> int:
    parser = argparse.ArgumentParser(description="Envía un JSON de prueba a la ESP32")
    parser.add_argument("port", help="Puerto, por ejemplo /dev/ttyUSB0 o /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--entradas", type=int, default=3)
    parser.add_argument("--salidas", type=int, default=1)
    parser.add_argument("--ocupacion", type=int, default=2)
    parser.add_argument("--repetir", type=int, default=1, help="Número de mensajes")
    parser.add_argument("--intervalo", type=float, default=1.0)
    args = parser.parse_args()

    enviador = EnviadorSerial(args.port, args.baud, intervalo_min_s=0.0)
    mensaje = {
        "version": "prueba-serial",
        "fecha_hora": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "entradas": args.entradas,
        "salidas": args.salidas,
        "ocupacion": args.ocupacion,
    }
    enviados = 0
    for i in range(max(1, args.repetir)):
        if enviador.enviar(mensaje, forzar=True):
            enviados += 1
            print(f"Enviado {i + 1}/{args.repetir}: {mensaje}")
        else:
            print("No se pudo enviar. Comprueba el puerto y que la ESP32 esté conectada.")
        if i + 1 < args.repetir:
            time.sleep(max(0.0, args.intervalo))
    enviador.cerrar()
    return 0 if enviados else 1


if __name__ == "__main__":
    raise SystemExit(main())
