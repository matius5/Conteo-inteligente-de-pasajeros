#!/usr/bin/env python3
"""Envío tolerante a fallos de datos de conteo a un ESP32 por USB serial."""
from __future__ import annotations

import json
import time
from typing import Any

try:
    import serial
except ImportError:  # Permite ejecutar el contador sin pyserial instalado.
    serial = None


class EnviadorSerial:
    """Abre el puerto de forma perezosa y nunca detiene el conteo si falla."""

    def __init__(
        self,
        puerto: str,
        baudios: int = 115200,
        intervalo_min_s: float = 1.0,
        reintento_s: float = 5.0,
    ) -> None:
        self.puerto = puerto
        self.baudios = int(baudios)
        self.intervalo_min_s = float(intervalo_min_s)
        self.reintento_s = float(reintento_s)
        self._ser = None
        self._ultimo_envio = float("-inf")
        self._ultimo_intento = float("-inf")
        self._aviso_mostrado = False
        self._ultimo_error = ""

    @property
    def conectado(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def _conectar(self) -> bool:
        if serial is None:
            self._ultimo_error = "pyserial no está instalado"
            return False
        try:
            self._ser = serial.Serial(
                self.puerto,
                self.baudios,
                timeout=0,
                write_timeout=0.25,
            )
            self._ser.reset_input_buffer()
            print(f"ESP32 conectado en {self.puerto} @ {self.baudios} baudios")
            self._aviso_mostrado = False
            return True
        except Exception as exc:  # El puerto puede no existir o estar ocupado.
            self._ser = None
            self._ultimo_error = str(exc)
            if not self._aviso_mostrado:
                print(
                    f"AVISO: ESP32 no disponible en {self.puerto}: {exc}. "
                    "El conteo continúa sin serial."
                )
                self._aviso_mostrado = True
            return False

    def enviar(self, datos: dict[str, Any], forzar: bool = False) -> bool:
        ahora = time.monotonic()
        if not forzar and ahora - self._ultimo_envio < self.intervalo_min_s:
            return False
        if self._ser is None:
            if ahora - self._ultimo_intento < self.reintento_s:
                return False
            self._ultimo_intento = ahora
            if not self._conectar():
                return False

        linea = json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + "\n"
        try:
            self._ser.write(linea.encode("utf-8"))
            self._ser.flush()
            self._ultimo_envio = ahora
            return True
        except Exception as exc:
            print(f"AVISO: se perdió el ESP32 ({exc}). Se reintentará automáticamente.")
            self.cerrar()
            self._aviso_mostrado = True
            self._ultimo_error = str(exc)
            self._ultimo_intento = ahora
            return False

    def cerrar(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
