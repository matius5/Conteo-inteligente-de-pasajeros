# Arquitectura y decisiones pendientes
El procesamiento se propone en Raspberry Pi 4 (4 GB). La ESP32 únicamente recibe conteos y maneja pantalla OLED.
La cámara USB debe conectarse a Raspberry Pi, no a la ESP32. El enlace serial puede realizarse por USB.

**Por confirmar**: modelo exacto de ESP32, tipo de pantalla OLED/controlador, pinout I2C,
sentido físico de la línea, FPS real en Raspberry, fijación de cámara y alimentación.
