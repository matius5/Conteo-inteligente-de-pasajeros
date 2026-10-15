# Sistema inteligente para conteo de pasajeros en un bus
**Asignatura:** Sistemas Inteligentes para Electrónica · **Modalidad:** ABPr

> **Estado:** prototipo de visión artificial probado previamente en un computador, según los avances reportados por el equipo. Este repositorio contiene una **implementación de referencia nueva** y no sustituye el código exacto que ya desarrollaron. Raspberry Pi, ESP32 y pantalla OLED requieren integración y pruebas físicas.

## 1. Problema
Determinar el número de personas que ingresan y salen de un bus mediante una cámara situada en la zona de acceso, evitando contar repetidamente a la misma persona.

## 2. Objetivo
Detectar y seguir personas, identificar cruces de una línea virtual y calcular la ocupación estimada, mostrando el resultado en una pantalla conectada a una ESP32.

## 3. Arquitectura propuesta
```mermaid
flowchart LR
    A[Cámara USB] --> B[Raspberry Pi 4 - 4 GB]
    B --> C[YOLO + seguimiento por ID]
    C --> D[Conteo de cruces]
    D --> E[USB serial JSON]
    E --> F[ESP32]
    F --> G[Pantalla OLED I2C]
```

## 4. Hardware
- Raspberry Pi 4 (4 GB) como candidato de procesamiento (aún por validar rendimiento).
- Cámara USB, modelo por confirmar.
- ESP32, placa exacta y mapeo de pines pendientes de confirmar.
- Pantalla OLED I2C; controlador y dirección I2C pendientes de verificar.
- Fuente(s) de alimentación y cableado adecuados.

## 5. Algoritmo
1. Capturar fotogramas con OpenCV.
2. Detectar personas con un modelo YOLO preentrenado.
3. Seguir cada persona por identificador para comparar su posición entre fotogramas.
4. Registrar el cruce de una línea horizontal; sumar entrada o salida según la dirección calibrada.
5. Calcular ocupación = máx(0, entradas − salidas) y enviar por puerto serial a la ESP32.

**Importante:** una línea horizontal supone que el movimiento relevante ocurre verticalmente en la imagen. La orientación entrada/salida debe verificarse con videos reales. Oclusiones, cambios de ID y embarque simultáneo pueden provocar errores.

## 6. Organización
- [`codigo/conteo_yolo.py`](codigo/conteo_yolo.py): prototipo de seguimiento y conteo 
- [`codigo/enviar_serial.py`](codigo/enviar_serial.py): emisor opcional de mensajes JSON a ESP32.
- [`codigo/esp32_oled/esp32_oled.ino`](codigo/esp32_oled/esp32_oled.ino): ejemplo Arduino ESP32 OLED, sujeto a confirmar pantalla y pines.
- [`documentacion/avances.md`](documentacion/avances.md): bitácora de avances.
- [`hardware/`](hardware/): lugar reservado para esquemático y PCB KiCad reales.
- [`evidencias/`](evidencias/): fotografías, videos y capturas.

## 7. Ejecución en PC (prototipo)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python codigo/conteo_yolo.py --camera 0 --line-y 250
```
El primer arranque puede requerir descargar el modelo `yolo11n.pt` desde Ultralytics. Para emitir datos por serial, agrega `--serial-port COM3` (ajusta puerto según el equipo). No ejecutes código de ESP32 hasta revisar pines, pantalla, librerías y alimentación.

## 8. Evidencias que faltan por subir
- [ ] Código original YOLO desarrollado por el equipo.
- [ ] Capturas y video de prueba en la cámara del computador.
- [ ] Pruebas de conteo de entrada/salida y tasa de error.
- [ ] Prueba del sistema en Raspberry Pi 4.
- [ ] Capturas o fotos de pantalla OLED con ocupación.
- [ ] Esquemático y PCB KiCad verificables.

## 9. Consideraciones
Evitar publicar videos con rostros identificables sin autorización. No subir credenciales, claves Wi-Fi ni tokens.

## 10. Resultados y conclusiones
**Pendientes de medición y documentación.** No se atribuyen métricas sin evidencia.
