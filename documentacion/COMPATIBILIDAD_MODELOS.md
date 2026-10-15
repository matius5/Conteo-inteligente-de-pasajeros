# Compatibilidad entre el informe ABPr y el prototipo del repositorio

## Lo documentado en el ABPr

- Prueba preliminar de detección con **YOLOv8** y cámara de portátil, reportada por el equipo.
- Propuesta de seguimiento y **línea vertical**, representada como `linea_x`.
- Raspberry Pi 4 (4 GB), ESP32 y OLED: arquitectura seleccionada, integración aún pendiente.

## Lo implementado en `codigo/conteo_yolo.py`

- Modelo por defecto: **`yolo11n.pt`**, configurable con `--model`.
- Línea de referencia **horizontal**: `--line-y 250`, configurable.
- Sentido provisional de entrada: desplazamiento de arriba hacia abajo.
- Conteo basado en cambios de lado por ID de seguimiento.
- Mensaje JSON por serial si se facilita `--serial-port`.

## Acción necesaria antes de sustentar pruebas de conteo

1. Recuperar el **código exacto** que se ejecutó durante la prueba inicial, guardándolo con nombre y fecha distintos.
2. Decidir si la puerta se cruza predominantemente de izquierda a derecha o de arriba hacia abajo en la imagen real.
3. Ajustar el algoritmo a la orientación y calibrar el sentido de entrada.
4. Verificar la estabilidad de IDs, los cruces múltiples y la tasa real de error.
5. Actualizar el informe cuando se disponga de evidencia, sin atribuir resultados al programa de referencia.

**Nota:** cambiar `--model` no cambia la orientación de la línea.
