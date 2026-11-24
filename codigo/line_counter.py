#!/usr/bin/env python3
"""Lógica de conteo por cruce de línea, independiente de OpenCV y de YOLO.

La histéresis usa una banda de margen alrededor de la línea. Una persona debe
salir de la banda por un lado y aparecer fuera de la banda por el lado contrario
para que se registre un cruce. Así se evita contar pequeñas oscilaciones cuando
alguien permanece junto a la línea.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

Orientacion = Literal["horizontal", "vertical"]
Direccion = Literal[
    "top_to_bottom",
    "bottom_to_top",
    "left_to_right",
    "right_to_left",
]

_DIRECCIONES = {
    "horizontal": {"top_to_bottom": 1, "bottom_to_top": -1},
    "vertical": {"left_to_right": 1, "right_to_left": -1},
}


@dataclass(frozen=True)
class Evento:
    """Un cruce confirmado de la línea."""

    fecha_hora: str
    track_id: int
    direccion: str
    desde_lado: int
    hacia_lado: int
    entradas: int
    salidas: int
    ocupacion: int
    ancla: tuple[float, float]

    def como_dict(self) -> dict:
        return {
            "fecha_hora": self.fecha_hora,
            "track_id": self.track_id,
            "evento": self.direccion,
            "desde_lado": self.desde_lado,
            "hacia_lado": self.hacia_lado,
            "entradas": self.entradas,
            "salidas": self.salidas,
            "ocupacion": self.ocupacion,
            "ancla": [round(self.ancla[0], 1), round(self.ancla[1], 1)],
        }


@dataclass
class _EstadoTrack:
    armed_side: int
    last_seen: float
    pending_side: int = 0
    pending_count: int = 0
    last_count_at: float = float("-inf")
    updates: int = 1


class ContadorLinea:
    """Cuenta cruces de una línea horizontal o vertical."""

    def __init__(
        self,
        orientacion: Orientacion,
        linea_px: float,
        direccion_entrada: Direccion,
        margen_px: float = 18.0,
        frames_confirmacion: int = 1,
        cooldown_s: float = 0.8,
        max_gap_s: float = 1.5,
        timeout_track_s: float = 2.5,
        ocupacion_inicial: int = 0,
    ) -> None:
        if orientacion not in _DIRECCIONES:
            raise ValueError(f"Orientación no válida: {orientacion}")
        if direccion_entrada not in _DIRECCIONES[orientacion]:
            raise ValueError(
                f"Dirección {direccion_entrada!r} no válida para línea {orientacion}"
            )
        if margen_px <= 0:
            raise ValueError("El margen debe ser mayor que cero")
        if frames_confirmacion < 1:
            raise ValueError("frames_confirmacion debe ser >= 1")
        if cooldown_s < 0 or max_gap_s <= 0 or timeout_track_s <= 0:
            raise ValueError("Tiempos de conteo no válidos")

        self.orientacion = orientacion
        self.linea_px = float(linea_px)
        self.direccion_entrada = direccion_entrada
        self.signo_entrada = _DIRECCIONES[orientacion][direccion_entrada]
        self.margen_px = float(margen_px)
        self.frames_confirmacion = int(frames_confirmacion)
        self.cooldown_s = float(cooldown_s)
        self.max_gap_s = float(max_gap_s)
        self.timeout_track_s = float(timeout_track_s)
        self.ocupacion_inicial = int(ocupacion_inicial)

        self.entradas = 0
        self.salidas = 0
        self._tracks: dict[int, _EstadoTrack] = {}

    @property
    def ocupacion(self) -> int:
        return self.ocupacion_inicial + self.entradas - self.salidas

    @property
    def tracks_activos(self) -> int:
        return len(self._tracks)

    def _valor_eje(self, ancla: tuple[float, float]) -> float:
        return ancla[1] if self.orientacion == "horizontal" else ancla[0]

    def _lado(self, ancla: tuple[float, float]) -> int:
        diferencia = self._valor_eje(ancla) - self.linea_px
        if diferencia < -self.margen_px:
            return -1
        if diferencia > self.margen_px:
            return 1
        return 0

    def actualizar(
        self,
        track_id: int,
        ancla: tuple[float, float],
        ahora: float,
    ) -> Evento | None:
        """Actualiza un track y devuelve un evento si se confirmó un cruce.

        ``ahora`` debe ser un tiempo monótono en segundos (time.monotonic()).
        """
        lado = self._lado(ancla)
        estado = self._tracks.get(track_id)

        if estado is None:
            self._tracks[track_id] = _EstadoTrack(
                armed_side=lado,
                last_seen=ahora,
            )
            return None

        gap = ahora - estado.last_seen
        estado.last_seen = ahora
        estado.updates += 1

        # Si el track estuvo perdido demasiado tiempo, no inferimos un cruce:
        # solo lo rearmamos en el lado donde reapareció.
        if gap > self.max_gap_s:
            estado.armed_side = lado
            estado.pending_count = 0
            estado.pending_side = 0
            return None

        if lado == 0:
            # Dentro de la banda de histéresis: no se cuenta nada.
            estado.pending_count = 0
            estado.pending_side = 0
            return None

        if estado.armed_side == 0:
            estado.armed_side = lado
            return None

        if lado == estado.armed_side:
            estado.pending_count = 0
            estado.pending_side = 0
            return None

        # Lado contrario al último lado "armado": exigir confirmación.
        if estado.pending_side != lado:
            estado.pending_side = lado
            estado.pending_count = 1
        else:
            estado.pending_count += 1

        if estado.pending_count < self.frames_confirmacion:
            return None
        if ahora - estado.last_count_at < self.cooldown_s:
            return None

        es_entrada = (lado - estado.armed_side) * self.signo_entrada > 0
        if es_entrada:
            self.entradas += 1
        else:
            self.salidas += 1

        estado.armed_side = lado
        estado.pending_count = 0
        estado.pending_side = 0
        estado.last_count_at = ahora

        return Evento(
            fecha_hora=datetime.now().astimezone().isoformat(timespec="seconds"),
            track_id=track_id,
            direccion="entrada" if es_entrada else "salida",
            desde_lado=-lado,
            hacia_lado=lado,
            entradas=self.entradas,
            salidas=self.salidas,
            ocupacion=self.ocupacion,
            ancla=ancla,
        )

    def limpiar(self, ahora: float) -> int:
        """Elimina tracks que llevan demasiado tiempo sin verse."""
        viejos = [
            track_id
            for track_id, estado in self._tracks.items()
            if ahora - estado.last_seen > self.timeout_track_s
        ]
        for track_id in viejos:
            del self._tracks[track_id]
        return len(viejos)

    def reiniciar(self) -> None:
        self.entradas = 0
        self.salidas = 0
        self._tracks.clear()
