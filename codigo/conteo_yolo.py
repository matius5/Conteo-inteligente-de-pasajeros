#!/usr/bin/env python3
"""Contador de pasajeros con YOLOv8n, ByteTrack y cruce de línea.

Ejecución típica:
    ./.venv/bin/python codigo/conteo_yolo.py --camera 0 --line-y 260 \
        --entry-direction top_to_bottom --serial-port /dev/ttyUSB0

Sin ESP32 simplemente omite --serial-port. El programa no graba vídeo.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from line_counter import ContadorLinea, Evento
from serial_esp32 import EnviadorSerial

VENTANA = "Conteo de pasajeros - Raspberry Pi 4"
VERSION = "1.0-raspberry"


def ahora_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def abrir_camara(fuente, ancho: int, alto: int, fps: int, fourcc: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(fuente, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def guardar_jsonl(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(datos, ensure_ascii=False) + "\n")


def dibujar_linea(
    frame: np.ndarray,
    orientacion: str,
    linea_px: int,
    margen: int,
    direccion: str,
) -> None:
    alto, ancho = frame.shape[:2]
    color_linea = (0, 220, 255)
    color_banda = (0, 140, 180)
    if orientacion == "horizontal":
        cv2.line(frame, (0, linea_px), (ancho, linea_px), color_linea, 2)
        for y in (linea_px - margen, linea_px + margen):
            if 0 <= y < alto:
                cv2.line(frame, (0, y), (ancho, y), color_banda, 1)
        texto = "ENTRADA: arriba -> abajo" if direccion == "top_to_bottom" else "ENTRADA: abajo -> arriba"
        cv2.putText(frame, texto, (12, max(20, linea_px - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, color_linea, 1, cv2.LINE_AA)
    else:
        cv2.line(frame, (linea_px, 0), (linea_px, alto), color_linea, 2)
        for x in (linea_px - margen, linea_px + margen):
            if 0 <= x < ancho:
                cv2.line(frame, (x, 0), (x, alto), color_banda, 1)
        texto = "ENTRADA: izq -> der" if direccion == "left_to_right" else "ENTRADA: der -> izq"
        cv2.putText(frame, texto, (max(12, linea_px + 8), 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, color_linea, 1, cv2.LINE_AA)


def dibujar_hud(frame: np.ndarray, contador: ContadorLinea, fps: float, inf_ms: float,
                personas: int, modo_serial: str) -> None:
    alto, ancho = frame.shape[:2]
    lineas = [
        f"Entradas: {contador.entradas}   Salidas: {contador.salidas}",
        f"Ocupacion: {contador.ocupacion}",
        f"Personas: {personas}   IDs activos: {contador.tracks_activos}",
        f"FPS bucle: {fps:.1f}   Inferencia: {inf_ms:.0f} ms",
        f"ESP32: {modo_serial}",
    ]
    ancho_caja = 360
    alto_caja = 18 * len(lineas) + 12
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (ancho_caja, alto_caja), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    for i, texto in enumerate(lineas):
        cv2.putText(frame, texto, (10, 20 + i * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

    if contador.ocupacion < 0:
        cv2.putText(frame, "OCUPACION NEGATIVA: revisar conteo",
                    (10, alto - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                    (0, 0, 255), 2, cv2.LINE_AA)


def construir_payload(
    contador: ContadorLinea,
    fps: float,
    inf_ms: float,
    personas: int,
    evento: Evento | None = None,
) -> dict:
    datos = {
        "version": VERSION,
        "fecha_hora": ahora_iso(),
        "entradas": contador.entradas,
        "salidas": contador.salidas,
        "ocupacion": contador.ocupacion,
        "ocupacion_inicial": contador.ocupacion_inicial,
        "personas": personas,
        "fps": round(fps, 2),
        "inferencia_ms": round(inf_ms, 1),
        "linea_orientacion": contador.orientacion,
        "linea_px": round(contador.linea_px, 1),
        "sentido_entrada": contador.direccion_entrada,
    }
    if evento is not None:
        datos["evento"] = evento.como_dict()
    return datos


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Conteo de pasajeros con YOLOv8n y seguimiento ByteTrack",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--camera", default="0", help="Índice o ruta, por ejemplo 0 o /dev/video0")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--camera-fps", type=int, default=30)
    parser.add_argument("--fourcc", default="MJPG", help="Formato de captura V4L2")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--tracker", default="bytetrack.yaml")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument(
        "--anchor", choices=("center", "bottom"), default="center",
        help="Punto del cuadro que se usa para cruzar la línea",
    )
    parser.add_argument(
        "--line-orientation", choices=("horizontal", "vertical"), default="horizontal",
        help="Se ignora si se indica --line-y o --line-x",
    )
    parser.add_argument("--line-y", type=int, default=None, help="Línea horizontal en píxeles")
    parser.add_argument("--line-x", type=int, default=None, help="Línea vertical en píxeles")
    parser.add_argument("--line-ratio", type=float, default=0.5,
                        help="Posición relativa 0..1 si no se indica línea en píxeles")
    parser.add_argument(
        "--entry-direction",
        choices=("top_to_bottom", "bottom_to_top", "left_to_right", "right_to_left"),
        default=None,
        help="Sentido que se contará como entrada",
    )
    parser.add_argument("--margin", type=int, default=None,
                        help="Histéresis en píxeles; por defecto 4%% del lado corto")
    parser.add_argument("--confirm-frames", type=int, default=1)
    parser.add_argument("--cooldown", type=float, default=0.8,
                        help="Tiempo mínimo entre dos cruces del mismo ID")
    parser.add_argument("--max-gap", type=float, default=1.5,
                        help="Hueco máximo entre detecciones para validar un cruce")
    parser.add_argument("--track-timeout", type=float, default=2.5,
                        help="Tiempo para eliminar un track perdido")
    parser.add_argument("--initial-occupancy", type=int, default=0)
    parser.add_argument("--serial-port", default=None, help="Ej.: /dev/ttyUSB0; omitir si no hay ESP32")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--serial-interval", type=float, default=1.0)
    parser.add_argument("--event-log", default="registros/eventos.jsonl")
    parser.add_argument("--session-log", default="registros/sesiones.jsonl")
    parser.add_argument("--snapshot", default=None,
                        help="Guardar una imagen anotada de verificación en esta ruta")
    parser.add_argument("--snapshot-frame", type=int, default=10)
    parser.add_argument("--display", action=argparse.BooleanOptionalAction, default=None,
                        help="Mostrar ventana; por defecto solo si hay entorno gráfico")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="Detener tras N fotogramas (pruebas)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Detener tras N segundos (pruebas)")
    parser.add_argument("--status-interval", type=float, default=2.0)
    args = parser.parse_args()

    if args.line_y is not None and args.line_x is not None:
        parser.error("Usa solo --line-y o --line-x, no ambos")
    if args.width <= 0 or args.height <= 0:
        parser.error("Resolución no válida")

    os.environ.setdefault("OMP_NUM_THREADS", str(max(1, args.threads)))
    try:
        import torch
        torch.set_num_threads(max(1, args.threads))
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
    except Exception:
        pass
    cv2.setNumThreads(1)

    fuente = int(args.camera) if str(args.camera).isdigit() else args.camera
    ruta_dispositivo = f"/dev/video{fuente}" if isinstance(fuente, int) else str(fuente)
    if not os.path.exists(ruta_dispositivo):
        print(f"ERROR: no existe {ruta_dispositivo}.")
        print("La cámara está desconectada o cambió de nodo. Revisa el cable USB.")
        print("Diagnóstico: ls -l /dev/video*; v4l2-ctl --list-devices")
        return 2
    cap = abrir_camara(fuente, args.width, args.height, args.camera_fps, args.fourcc)
    if not cap.isOpened():
        print(f"ERROR: no se pudo abrir la cámara {args.camera!r} en formato {args.fourcc}.")
        print("Comprueba que exista /dev/video0 y que el cable USB esté bien conectado.")
        print("Diagnóstico: ls -l /dev/video*; v4l2-ctl --list-devices")
        return 2

    # Descartar fotogramas iniciales para que la exposición se estabilice.
    for _ in range(5):
        cap.read()
    ok, primer_frame = cap.read()
    if not ok or primer_frame is None:
        cap.release()
        print("ERROR: la cámara se abrió pero no entregó ningún fotograma.")
        return 3

    alto, ancho = primer_frame.shape[:2]
    if args.line_y is not None:
        orientacion = "horizontal"
        linea_px = float(args.line_y)
    elif args.line_x is not None:
        orientacion = "vertical"
        linea_px = float(args.line_x)
    else:
        orientacion = args.line_orientation
        linea_px = float(args.line_ratio) * (alto if orientacion == "horizontal" else ancho)

    limite = alto if orientacion == "horizontal" else ancho
    if not 0 <= linea_px <= limite - 1:
        print(f"ERROR: la línea ({linea_px:.0f}) queda fuera de la imagen ({limite}px).")
        cap.release()
        return 4

    if args.entry_direction is None:
        direccion = "top_to_bottom" if orientacion == "horizontal" else "left_to_right"
    else:
        direccion = args.entry_direction
    try:
        margen = args.margin if args.margin is not None else max(10, round(0.04 * limite))
        contador = ContadorLinea(
            orientacion=orientacion,  # type: ignore[arg-type]
            linea_px=linea_px,
            direccion_entrada=direccion,  # type: ignore[arg-type]
            margen_px=margen,
            frames_confirmacion=args.confirm_frames,
            cooldown_s=args.cooldown,
            max_gap_s=args.max_gap,
            timeout_track_s=args.track_timeout,
            ocupacion_inicial=args.initial_occupancy,
        )
    except ValueError as exc:
        cap.release()
        print(f"ERROR de configuración: {exc}")
        return 4

    print("Cámara abierta correctamente.")
    print(f"Resolución real: {ancho}x{alto} | formato solicitado: {args.fourcc}")
    print(f"Modelo: {args.model} | imgsz={args.imgsz} | conf={args.conf}")
    print(f"Línea {orientacion} en {linea_px:.0f}px | margen {margen}px | "
          f"entrada={direccion} | confirmación={args.confirm_frames} frame(s)")

    try:
        from ultralytics import YOLO
    except Exception as exc:
        cap.release()
        print(f"ERROR: no se pudo importar Ultralytics: {exc}")
        return 5

    try:
        modelo = YOLO(args.model)
    except Exception as exc:
        cap.release()
        print(f"ERROR: no se pudo cargar el modelo {args.model!r}: {exc}")
        return 6

    enviador = None
    if args.serial_port:
        enviador = EnviadorSerial(
            args.serial_port, args.baud, intervalo_min_s=args.serial_interval
        )
        print(f"Serial configurado: {args.serial_port} @ {args.baud} baudios")
    else:
        print("Serial desactivado: el contador funcionará sin ESP32.")

    log_eventos = Path(args.event_log)
    log_sesiones = Path(args.session_log)
    mostrar = args.display
    if mostrar is None:
        mostrar = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    ventana_creada = False
    if mostrar:
        try:
            cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(VENTANA, 960, 720)
            ventana_creada = True
        except Exception as exc:
            print(f"AVISO: no se pudo crear la ventana ({exc}); modo sin interfaz.")
            mostrar = False

    inicio = time.monotonic()
    ultimo_estado = inicio
    ultimo_status_serial = float("-inf")
    frames = 0
    fps = 0.0
    inf_ms = 0.0
    personas = 0
    aviso_negativo = False
    snapshot_pendiente = bool(args.snapshot)
    motivo_fin = "fin normal"

    def detener_por_limites() -> bool:
        if args.max_frames is not None and frames >= args.max_frames:
            return True
        if args.duration is not None and time.monotonic() - inicio >= args.duration:
            return True
        return False

    try:
        while not detener_por_limites():
            ok, frame = cap.read()
            if not ok or frame is None:
                print("ERROR: se perdió la señal de la cámara.")
                motivo_fin = "fallo de cámara"
                break
            frames += 1
            t_frame = time.monotonic()

            try:
                resultado = modelo.track(
                    frame,
                    persist=True,
                    classes=[0],
                    conf=args.conf,
                    iou=args.iou,
                    imgsz=args.imgsz,
                    tracker=args.tracker,
                    verbose=False,
                    device="cpu",
                )[0]
            except Exception as exc:
                print(f"ERROR durante la inferencia: {exc}")
                motivo_fin = "fallo de inferencia"
                break

            velocidad = getattr(resultado, "speed", None) or {}
            inf_ms = float(velocidad.get("inference", inf_ms) or inf_ms)
            personas = 0
            evento_actual: Evento | None = None

            cajas = resultado.boxes
            if cajas is not None and cajas.id is not None:
                ids = cajas.id.int().cpu().tolist()
                xyxy = cajas.xyxy.cpu().tolist()
                confs = cajas.conf.cpu().tolist() if cajas.conf is not None else []
                for indice, (track_id, caja) in enumerate(zip(ids, xyxy)):
                    personas += 1
                    x1, y1, x2, y2 = [float(v) for v in caja]
                    if args.anchor == "bottom":
                        ancla = ((x1 + x2) / 2.0, y2)
                    else:
                        ancla = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                    ancla = (
                        min(max(ancla[0], 0.0), ancho - 1.0),
                        min(max(ancla[1], 0.0), alto - 1.0),
                    )
                    evento = contador.actualizar(int(track_id), ancla, t_frame)
                    if evento is not None:
                        evento_actual = evento
                        print(f"EVENTO {evento.direccion.upper()} id={evento.track_id} "
                              f"entradas={evento.entradas} salidas={evento.salidas} "
                              f"ocupacion={evento.ocupacion} | {evento.fecha_hora}")
                        guardar_jsonl(log_eventos, evento.como_dict())
                        if enviador is not None:
                            enviador.enviar(
                                construir_payload(contador, fps, inf_ms, personas, evento),
                                forzar=True,
                            )
                        if contador.ocupacion < 0 and not aviso_negativo:
                            print("ADVERTENCIA: ocupación negativa. Se conserva el valor real; "
                                  "revisa la ocupación inicial y los conteos.")
                            aviso_negativo = True

                    color = (0, 220, 0)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    etiqueta = f"ID {track_id}"
                    if confs:
                        etiqueta += f" {confs[indice]:.2f}"
                    cv2.putText(frame, etiqueta, (int(x1), max(16, int(y1) - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            contador.limpiar(t_frame)
            transcurrido = time.monotonic() - inicio
            fps = frames / transcurrido if transcurrido > 0 else 0.0

            if enviador is not None and t_frame - ultimo_status_serial >= args.serial_interval:
                enviador.enviar(construir_payload(contador, fps, inf_ms, personas))
                ultimo_status_serial = t_frame

            if t_frame - ultimo_estado >= args.status_interval:
                print(f"estado: entradas={contador.entradas} salidas={contador.salidas} "
                      f"ocupacion={contador.ocupacion} personas={personas} "
                      f"fps={fps:.1f} inferencia={inf_ms:.0f}ms")
                ultimo_estado = t_frame

            if ventana_creada:
                dibujar_linea(frame, orientacion, int(round(linea_px)), margen, direccion)
                modo_serial = "conectado" if enviador and enviador.conectado else (
                    "configurado" if enviador else "sin ESP32"
                )
                dibujar_hud(frame, contador, fps, inf_ms, personas, modo_serial)
                try:
                    cv2.imshow(VENTANA, frame)
                    tecla = cv2.waitKey(1) & 0xFF
                    if tecla == ord("q"):
                        motivo_fin = "tecla q"
                        break
                except Exception as exc:
                    print(f"AVISO: fallo al mostrar la ventana ({exc}); se continúa sin interfaz.")
                    ventana_creada = False

            if snapshot_pendiente and frames >= args.snapshot_frame:
                salida = Path(args.snapshot)
                salida.parent.mkdir(parents=True, exist_ok=True)
                dibujar_linea(frame, orientacion, int(round(linea_px)), margen, direccion)
                if cv2.imwrite(str(salida), frame):
                    print(f"Captura anotada guardada: {salida.resolve()}")
                snapshot_pendiente = False
    except KeyboardInterrupt:
        motivo_fin = "Ctrl+C"
        print("\nInterrupción solicitada por el usuario. Cerrando limpiamente...")
    finally:
        cap.release()
        if enviador is not None:
            enviador.cerrar()
        if ventana_creada:
            try:
                cv2.destroyAllWindows()
                cv2.waitKey(1)
            except Exception:
                pass

    duracion = time.monotonic() - inicio
    resumen = {
        "fecha_hora": ahora_iso(),
        "version": VERSION,
        "modelo": args.model,
        "imgsz": args.imgsz,
        "conf": args.conf,
        "camara": str(args.camera),
        "resolucion": f"{ancho}x{alto}",
        "formato": args.fourcc,
        "linea_orientacion": orientacion,
        "linea_px": linea_px,
        "margen_px": margen,
        "sentido_entrada": direccion,
        "entradas": contador.entradas,
        "salidas": contador.salidas,
        "ocupacion_inicial": contador.ocupacion_inicial,
        "ocupacion_final": contador.ocupacion,
        "frames": frames,
        "duracion_s": round(duracion, 2),
        "fps_promedio": round(frames / duracion, 2) if duracion > 0 else 0.0,
        "motivo_fin": motivo_fin,
        "serial": args.serial_port or "desactivado",
    }
    guardar_jsonl(log_sesiones, resumen)
    print("\nResumen de la sesión:")
    print(f"  Entradas: {contador.entradas} | Salidas: {contador.salidas} | "
          f"Ocupación: {contador.ocupacion}")
    print(f"  Fotogramas: {frames} | Duración: {duracion:.1f}s | "
          f"FPS promedio: {resumen['fps_promedio']}")
    print(f"  Motivo de cierre: {motivo_fin}")
    print(f"  Registro: {log_sesiones.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
