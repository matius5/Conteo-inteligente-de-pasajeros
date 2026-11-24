# Conteo inteligente de pasajeros

Contador para Raspberry Pi 4 con cámara USB, YOLOv8n/NCNN, seguimiento ByteTrack y panel web para celular. Funciona sin ESP32, monitor ni teclado. Cuenta entradas y salidas al cruzar una línea virtual. Al iniciar cada proceso, los contadores comienzan en cero.

## Instalar después de preparar la Raspberry Pi

Instalar primero Debian 13 / Raspberry Pi OS Trixie **de 64 bits**, con Python 3.13, configurar Wi-Fi y conectar la cámara. El entorno de referencia es Raspberry Pi 4 de 4 GB y cámara LG AN-VC500. Ejecutar como usuario normal con permiso sudo:

```bash
sudo apt update
sudo apt install -y git
cd ~
git clone https://github.com/matius5/Conteo-inteligente-de-pasajeros.git
cd Conteo-inteligente-de-pasajeros
bash instalar.sh
```

No necesitas GitHub Desktop ni iniciar sesión en GitHub para descargar este repositorio público. Si la carpeta ya existe, no la borres: conserva sus cambios y usa otro nombre para la descarga. La secuencia anterior está pensada para un sistema limpio.

El instalador crea `.venv`, instala las versiones principales registradas, descarga YOLOv8n si hace falta, lo exporta a NCNN a 320 píxeles, comprueba una inferencia y la cámara, e instala el servicio `contadorbus.service`. Espera hasta recibir datos activos del panel antes de informar que terminó. Necesita Internet y puede tardar varios minutos. Si falla una dependencia o una comprobación, se detiene y muestra el error.

No es una imagen de la microSD ni una restauración probada en hardware desde este entorno. Conserva el sistema actual hasta probar esta instalación, preferiblemente en otra tarjeta. Los pesos y los paquetes se descargan: este repositorio por sí solo no permite instalar sin Internet.

## Consultar el conteo

```bash
hostname -I
```

Desde un celular en la misma red, abrir `http://IP_DE_LA_RASPBERRY:8080`. El panel muestra entradas, salidas, ocupación y FPS. El botón **Apagar Raspberry** solicita el apagado del sistema sin contraseña ni confirmación adicional. Esperar a que finalice antes de desconectar la corriente. Perder acceso a la página no demuestra por sí solo que haya terminado.

La página y la acción de apagado son para una red de confianza o Tailscale; cualquier dispositivo con acceso al panel puede solicitar el apagado. No reenviar el puerto 8080 hacia Internet.

## Acceso por Tailscale

```bash
bash instalar_tailscale.sh
```

Abrir el enlace de autenticación que aparezca, incorporar la Raspberry a tu cuenta y usar esa misma red Tailscale en el celular. Luego abrir `http://IP_TAILSCALE:8080`. La sesión y claves de Tailscale no se guardan en GitHub. Después de reinstalar hay que autenticar el equipo de nuevo. Tailscale no conecta por sí solo la Raspberry a una Wi-Fi desconocida.

## Arranque, diagnóstico y ejecución manual

El servicio inicia automáticamente al encender. Si el proceso falla, intenta recuperarse y empieza una nueva sesión en cero. Los eventos históricos permanecen en `registros/`, pero no restauran la ocupación.

```bash
systemctl status contadorbus.service --no-pager
journalctl -u contadorbus.service -n 60 --no-pager
```

Para ejecutar en la terminal y detener con Ctrl+C:

```bash
sudo systemctl stop contadorbus.service
bash iniciar_web.sh
```

Para volver al servicio automático:

```bash
sudo systemctl start contadorbus.service
```

Configuración inicial: `/dev/video0`, MJPG 640×480, modelo NCNN, inferencia 320 px, línea vertical x=320, entrada de izquierda a derecha. Cambiar los argumentos de `iniciar_web.sh` según el encuadre y reiniciar el servicio. No ejecutar dos contadores a la vez sobre la cámara.

## Archivos principales

- `codigo/contador_web.py`: cámara, detección, seguimiento, conteo y registros.
- `codigo/line_counter.py`: lógica del cruce de línea.
- `codigo/panel_bus.py`: servidor y panel móvil, con apagado.
- `codigo/probar_camara.py`: prueba de captura MJPG.
- `codigo/preparar_modelo.py`: exportación y comprobación del modelo.
- `instalar.sh`: instalación y servicio para el usuario y ruta actuales.
- `deploy/`: servicio y comando limitado de apagado.
- `pruebas/test_sistema.py`: pruebas sin cámara y sin apagar el equipo.

Los archivos de serial, ESP32 y `documentacion/README_ETAPA_ESP32.md` se conservan como historial del proyecto. La instalación web actual no los utiliza. Las notas antiguas dentro de `documentacion/` pueden describir aquella etapa.

## Qué está recuperado y qué es nuevo

El contador, la lógica de cruces, la prueba de cámara y la base del panel proceden de los archivos conservados del proyecto. El instalador y la integración de apagado de esta publicación se prepararon para facilitar una reinstalación. No se recuperó el archivo exacto del botón de apagado que estaba instalado en la Raspberry; esta integración es nueva y debe probarse físicamente.

Las versiones principales de `requirements.txt` proceden del entorno informado por el equipo; no equivalen a un bloqueo completo de todas las dependencias. El instalador guarda el entorno resuelto en `registros/requirements-instalados.txt`. El repositorio no incluye una copia de credenciales, redes Wi-Fi, configuración personal del sistema, pesos locales ni cambios que solo existan en la Raspberry.

La comprobación local de esta publicación cubre sintaxis y pruebas de conteo/HTTP con apagado simulado. No verifica cámara, inferencia ARM, permisos sudo, apagado físico ni restauración de una tarjeta real. Prueba antes de borrar el sistema original: acceso al panel, cruces conocidos, apagado, nuevo arranque sin periféricos y acceso remoto.

```bash
python3 -m unittest discover -s pruebas -v
```

## Resultados y alcance

Registros aportados: 3,98 FPS con PyTorch (240 fotogramas / 60,2 s) y 6,11 FPS con NCNN (2108 / 345,2 s). Son sesiones distintas, no un ensayo controlado. No hay referencia manual suficiente para afirmar un porcentaje de precisión. Se conservan valores negativos para detectar inconsistencias. La ocupación solo representa el total cuando la condición inicial y todos los accesos están controlados.

## Referencias

- [Ultralytics en Raspberry Pi](https://docs.ultralytics.com/guides/raspberry-pi/)
- [Exportación NCNN](https://docs.ultralytics.com/integrations/ncnn/)
- [Instalación de Tailscale](https://tailscale.com/download/linux)
- Licencias de modelos y dependencias: consultar `LICENSE_NOTES.md` y los proyectos originales.
