# Sistema inteligente de conteo de pasajeros en transporte público mediante visión por computador y sistemas embebidos

**Asignatura:** Sistemas Inteligentes para Electrónica  
**Docente:** Nazhir Amaya  
**Integrantes:** Mateo Peña, Daniel Ibáñez y Jesús Ramírez  
**Fecha de entrega:** 19 de noviembre de 2026  
**Entregable:** Corte 2 — Avance 2 del proyecto de aula  
**Estado:** Prototipo en desarrollo

> **Nota de alcance:** El algoritmo de detección de objetos YOLOv8 se ha probado inicialmente con la cámara de un computador portátil. Se ha seleccionado la arquitectura Raspberry Pi 4 (4 GB) + cámara USB + ESP32 + OLED, pero su integración final todavía no ha sido validada. La implementación autónoma, la precisión del conteo, la PCB fabricada y el gabinete aún requieren desarrollo y validación. No se presentan como resultados terminados.

## 1. Título y objetivos

### 1.1. Título

Sistema inteligente de conteo de pasajeros en transporte público mediante visión por computador y sistemas embebidos.

### 1.2. Objetivo general

Diseñar e implementar un prototipo de sistema inteligente capaz de estimar el número de pasajeros que ingresan y salen de un autobús mediante análisis de imágenes y seguimiento de personas, para presentar el conteo en una pantalla OLED a través de una plataforma electrónica embebida.

### 1.3. Objetivos específicos

1. Desarrollar y evaluar un algoritmo de visión por computador que identifique personas y determine el sentido de cruce de una línea virtual en una zona de acceso al autobús.
2. Seleccionar y diseñar la arquitectura electrónica que integre cámara, procesamiento, alimentación, microcontrolador y pantalla OLED, utilizando una Raspberry Pi 4 de 4 GB para procesar video, una ESP32 para visualizar datos y una interfaz de comunicación entre ambas.
3. Construir e integrar un prototipo con PCB y gabinete, y verificar experimentalmente su funcionamiento mediante pruebas de entradas, salidas, conteo acumulado y estabilidad del sistema.

## 2. Planteamiento del problema

El conocimiento del número de pasajeros dentro de un autobús puede contribuir al seguimiento de ocupación, al análisis de demanda y a la toma de decisiones operativas. Los conteos manuales requieren intervención humana y pueden presentar errores, especialmente cuando varias personas transitan por una puerta en intervalos cortos.

Se propone explorar un sistema de conteo automático basado en visión por computador. Una cámara observará la zona de acceso y un algoritmo identificará personas, seguirá su desplazamiento y determinará si cruzan una referencia virtual en sentido de entrada o salida. El conteo neto se visualizará localmente en una pantalla OLED.

El desafío técnico principal consiste en trasladar la prueba de concepto, realizada en un computador portátil con YOLOv8, a una Raspberry Pi 4 de 4 GB que funcione sin depender de la laptop. El conteo se transmitirá mediante USB serial a una ESP32 XH-32S N4XX, encargada de actualizar una pantalla OLED. La velocidad de inferencia, la robustez del seguimiento y la autonomía del sistema deben validarse experimentalmente.

**Pregunta de investigación:** ¿En qué condiciones una Raspberry Pi 4 de 4 GB, ejecutando YOLOv8 y seguimiento de personas, puede estimar entradas y salidas de pasajeros y transmitir la ocupación a una ESP32 para su visualización en una pantalla OLED?

## 3. Estado del arte y marco teórico

### 3.1. Estado del arte

Los sistemas de conteo automático de personas pueden emplear sensores infrarrojos, barreras ópticas, cámaras convencionales o cámaras de profundidad. Los sensores de barrera detectan interrupciones de un haz, pero pueden tener dificultades al diferenciar personas que transitan juntas o en sentidos opuestos. La visión por computador permite analizar posiciones y trayectorias, aunque su rendimiento depende de la iluminación, oclusiones, ángulo de cámara y capacidad de procesamiento.

YOLO (You Only Look Once) es una familia de modelos de detección de objetos que permite localizar objetos mediante cajas delimitadoras. La implementación Ultralytics de YOLOv8 proporciona modelos ligeros, como `yolov8n.pt`, y herramientas de seguimiento. ByteTrack es un método de asociación de detecciones entre fotogramas que ayuda a mantener identificadores temporales para objetos seguidos. Una solución de conteo por línea virtual puede comparar la trayectoria de cada identificador respecto a una frontera y registrar cruces según su dirección.

En sistemas embebidos, la selección del algoritmo debe ajustarse a la memoria, la velocidad de inferencia, el consumo energético y las interfaces de cámara disponibles. La Raspberry Pi 4 es un computador de placa única con Linux, capaz de ejecutar Python y modelos pequeños de detección, aunque con menor rendimiento que un PC moderno. La ESP32 no ejecutará YOLO: recibirá únicamente los contadores por USB serial. Se medirá la velocidad real de inferencia y se evaluarán optimizaciones, como disminuir el tamaño de entrada o convertir el modelo a NCNN.

### 3.2. Marco teórico

**Visión por computador:** conjunto de técnicas que permiten extraer información de imágenes o secuencias de vídeo.

**Detección de personas:** identificación de regiones de una imagen que corresponden a personas. En el conjunto de clases COCO empleado por el modelo de prueba, la clase `0` corresponde a `person`.

**Seguimiento de objetos (tracking):** asociación temporal de detecciones para estimar la trayectoria de cada persona y evitar contar cada fotograma como una persona distinta.

**Línea virtual de conteo:** referencia geométrica definida sobre la imagen. Se registra un evento cuando la trayectoria de una persona pasa de un lado al otro de la línea. La orientación de la línea y la interpretación entrada/salida deben calibrarse con la cámara instalada en la puerta.

**Ocupación estimada:** si el autobús comienza vacío, puede calcularse como `ocupación = entradas − salidas`. En una implementación real deben considerarse la ocupación inicial, errores de detección y la capacidad máxima del vehículo; no basta con truncar valores negativos para garantizar exactitud.

**Raspberry Pi 4 (4 GB):** computador de placa única que ejecutará Raspberry Pi OS, Python, OpenCV, YOLOv8n y el seguimiento de personas. Su rendimiento efectivo está pendiente de medición.

**ESP32 XH-32S N4XX:** placa de desarrollo destinada a recibir los contadores mediante comunicación serial y controlar la OLED; el modelo y distribución de pines deben comprobarse físicamente.

**USB serial:** enlace de datos entre la Raspberry Pi y la ESP32 a través del puerto USB de la placa de desarrollo. El nombre del puerto en Linux se verificará durante las pruebas.

**OLED:** pantalla de bajo consumo que puede mostrar los valores de entradas, salidas y ocupación. El modelo y el controlador exactos (por ejemplo, SSD1306) se confirmarán antes de cerrar el diseño eléctrico.

**PCB:** placa de circuito impreso que conecta mecánica y eléctricamente los componentes. Su diseño requiere verificar alimentación, niveles lógicos, pines, dimensiones y huellas reales antes de fabricar.

### 3.3. Referencias técnicas iniciales

1. Ultralytics. *YOLOv8 Documentation*. https://docs.ultralytics.com/models/yolov8/
2. Ultralytics. *Multi-Object Tracking*. https://docs.ultralytics.com/modes/track/
3. Zhang, Y. et al. (2022). *ByteTrack: Multi-Object Tracking by Associating Every Detection Box*. ECCV. https://arxiv.org/abs/2110.06864
4. Espressif Systems. *ESP32 Series Datasheet*. https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf
5. Raspberry Pi. *Documentation*. https://www.raspberrypi.com/documentation/
6. Raspberry Pi. *Raspberry Pi 4 product specifications*. https://www.raspberrypi.com/products/raspberry-pi-4-model-b/
7. Ultralytics. *NCNN Export*. https://docs.ultralytics.com/integrations/ncnn/

> Las referencias se incluyen como bases técnicas para el desarrollo; antes de la entrega final deben revisarse las fuentes consultadas, completarse los datos bibliográficos y citarse específicamente las afirmaciones sustentadas.

## 4. Introducción y materiales

### 4.1. Introducción

La automatización del conteo de pasajeros es una aplicación de los sistemas inteligentes que integra adquisición de imágenes, reconocimiento de patrones, electrónica digital y visualización de datos. Este proyecto propone un prototipo para registrar cruces de personas por la puerta de un autobús, clasificarlos como entradas o salidas y mostrar una estimación de ocupación en una pantalla OLED.

La primera fase ha consistido en probar YOLOv8 con la cámara integrada de un computador portátil. La siguiente fase comprende validar el seguimiento y el conteo direccional, trasladar el programa a una Raspberry Pi 4 de 4 GB, integrar la ESP32 y la OLED, desarrollar el hardware y fabricar el ensamble. El alcance académico se centra en demostrar el principio de funcionamiento y documentar sus limitaciones; no se considera todavía un sistema comercial certificado.

### 4.2. Tabla 1. Materiales y herramientas

| N.º | Elemento | Función | Estado |
|---|---|---|---|
| 1 | Computador con Python y VS Code | Desarrollo y prueba inicial de YOLO | Disponible; detección probada |
| 2 | Raspberry Pi 4, 4 GB | Procesamiento autónomo con Python, YOLO y OpenCV | Arquitectura seleccionada; adquisición/instalación por confirmar |
| 3 | Cámara USB | Captura de la zona de acceso del autobús | Disponible; integración con Raspberry Pi pendiente |
| 4 | ESP32 XH-32S N4XX | Recepción de contadores y control de pantalla | Disponible; pinout exacto por verificar |
| 5 | Pantalla OLED | Visualización de entradas, salidas y ocupación | Disponible; controlador e interfaz por verificar |
| 6 | microSD de 32–64 GB | Sistema operativo y software de Raspberry Pi | Por confirmar |
| 7 | Fuente USB-C 5,1 V / 3 A para Raspberry Pi 4 | Alimentación del procesador principal | Por confirmar |
| 8 | Refrigeración, cables USB de datos y conectores | Operación estable e interconexión | Por confirmar |
| 9 | PCB de integración, conectores y componentes auxiliares | Montaje y distribución eléctrica de la ESP32/OLED | Por diseñar y fabricar |
| 10 | Gabinete y elementos de fijación | Protección y montaje | Por diseñar y fabricar |
| 11 | Ultralytics YOLOv8n, OpenCV, ByteTrack, pyserial | Detección, seguimiento y transmisión de datos | Detección inicial probada; integración pendiente |

**Alcance de la PCB:** se diseñará una placa de integración para la ESP32, la OLED y los conectores auxiliares. La Raspberry Pi 4 y la cámara USB serán módulos comerciales conectados externamente; no se diseñará ni fabricará la electrónica interna de esos equipos. La alimentación y la geometría definitiva de la PCB se fijarán tras verificar los módulos reales.

## 5. Componente técnico

### 5.1. Arquitectura seleccionada

**Arquitectura de procesamiento distribuido:** cámara USB → Raspberry Pi 4 (4 GB) → comunicación USB serial → ESP32 XH-32S N4XX → interfaz de pantalla OLED.

La cámara captura fotogramas de la puerta del autobús. La Raspberry Pi ejecuta YOLOv8n para detectar personas, ByteTrack para asociar detecciones y una lógica de cruce para contar entradas y salidas. El software envía mensajes con los contadores a la ESP32, que los muestra en la OLED. El computador portátil se utiliza para desarrollar el software, pero no será necesario durante la operación final.

**Figura 1. Diagrama de bloques de la arquitectura seleccionada.** **[INSERTAR DIAGRAMA PROPIO, NO GENERADO CON IA]**

**Comunicación propuesta:** conexión USB entre Raspberry Pi y ESP32 con mensajes de texto JSON terminados en salto de línea, por ejemplo `{"entradas":3,"salidas":1,"ocupacion":2}`. La ESP32 comprobará la recepción de mensajes válidos antes de actualizar la OLED. La frecuencia de envío y el puerto serial se definirán durante las pruebas.

**Rendimiento:** no se presupone que la Raspberry Pi 4 alcance una tasa de fotogramas específica. Se medirá el tiempo de inferencia y la precisión de conteo con `yolov8n.pt`, y se estudiará una conversión a NCNN y un tamaño de inferencia menor si es necesario.

### 5.2. Algoritmo de conteo propuesto

1. Capturar cada fotograma de la cámara.
2. Detectar solamente personas (`classes=[0]`) con el modelo seleccionado.
3. Asignar y mantener identificadores mediante seguimiento temporal.
4. Definir una línea virtual y una zona de tolerancia para reducir oscilaciones cerca de la frontera.
5. Comparar el lado anterior y actual de cada trayectoria para identificar cruces completos.
6. Incrementar el contador de entradas o salidas según la dirección calibrada.
7. Calcular la ocupación estimada y actualizar la pantalla OLED.
8. Registrar fallos de seguimiento, cruces simultáneos y condiciones de iluminación como posibles fuentes de error.

**Tabla 2. Variables del algoritmo**

| Variable | Descripción | Unidad |
|---|---|---|
| `entradas` | Cruces clasificados como ingreso | personas |
| `salidas` | Cruces clasificados como salida | personas |
| `ocupacion_inicial` | Pasajeros presentes al iniciar | personas |
| `ocupacion_estimada` | `ocupacion_inicial + entradas - salidas` | personas |
| `linea_x` | Posición horizontal de la línea vertical en la imagen | píxeles |
| `id_persona` | Identificador temporal de seguimiento | sin unidad |

### 5.3. Prueba de concepto realizada

Se ha ejecutado un programa de detección basado en Python, OpenCV y `yolov8n.pt` utilizando la cámara de un computador portátil. Esta prueba confirma de manera preliminar la captura y detección visual de objetos. Se ha preparado una versión del algoritmo para filtrar personas, utilizar seguimiento y contar cruces sobre una línea vertical; su precisión y funcionamiento continuo todavía deben evaluarse experimentalmente.

**Figura 2.** Captura real de la detección de personas en el portátil. **[INSERTAR CAPTURA PROPIA]**

**Figura 3.** Captura real del conteo con línea vertical, entradas, salidas y ocupación. **[INSERTAR CAPTURA PROPIA TRAS VALIDACIÓN]**

### 5.4. Diseño electrónico y PCB

El esquemático y la PCB deben elaborarse en KiCad u otra herramienta de diseño electrónico, con símbolos y huellas correspondientes a componentes reales. Antes de realizar conexiones definitivas es necesario comprobar el pinout de la ESP32 XH-32S N4XX, el controlador y voltaje de la OLED, las dimensiones físicas de los módulos y el sistema de alimentación. La Raspberry Pi 4 y la cámara USB no se montarán como componentes soldados en esta PCB.

Se verificarán al menos: tensiones de alimentación, consumo máximo, masa común, interfaces de comunicación, pines disponibles, pines de arranque, acceso a programación, protección de alimentación, montaje y dimensiones. La placa podría actuar como tarjeta de interconexión para módulos comerciales; no se asumirá que todos los módulos deben soldarse directamente sin revisar sus requisitos.

**Figura 4.** Esquemático electrónico con referencias de componentes y conexiones verificadas. **[INSERTAR EXPORTACIÓN DE KICAD]**

**Figura 5.** Diseño de PCB: vista de pistas, serigrafía y disposición de componentes. **[INSERTAR EXPORTACIÓN DE KICAD]**

**Figura 6.** Gabinete, ubicación de cámara y pantalla, y sistema de montaje. **[INSERTAR DISEÑO O FOTOGRAFÍA PROPIA]**

> En cumplimiento de la rúbrica, las ilustraciones técnicas deben ser realizadas por el equipo y cada conexión, etiqueta y elemento debe poder justificarse durante la sustentación. No se usarán imágenes generadas por IA como evidencia de diseños realizados.

### 5.5. Plan de pruebas

**Tabla 3. Pruebas de validación previstas**

| Prueba | Procedimiento | Evidencia por registrar |
|---|---|---|
| Detección individual | Una persona permanece en el campo visual | Captura y tasa de detección |
| Entrada | Una persona cruza en el sentido definido como ingreso | Incremento de `entradas` |
| Salida | Una persona cruza en sentido contrario | Incremento de `salidas` |
| Cruces consecutivos | Varias personas cruzan por separado | Conteo automático frente al conteo manual |
| Cruces simultáneos | Dos personas cruzan con proximidad | Errores por oclusión y pérdida de ID |
| Iluminación variable | Repetir pruebas con diferentes condiciones | Errores observados |
| Reinicio del sistema | Apagar y encender el prototipo | Comportamiento del contador inicial |
| Integración OLED | Enviar valores desde el procesamiento | Correspondencia entre dato y pantalla |
| Autonomía | Ejecutar sin computador portátil | Tiempo de operación y estabilidad |

Para medir el rendimiento se propone comparar eventos detectados contra eventos reales, distinguiendo entradas, salidas, falsos conteos y omisiones. No se reportarán porcentajes de exactitud hasta contar con datos medidos.

### 5.6. Evidencia física requerida para el corte

**Tabla 4. Requisitos de prototipo según rúbrica**

| Requisito | Estado actual | Evidencia pendiente |
|---|---|---|
| Estructura o gabinete finalizado | Pendiente | Fotografías del gabinete terminado |
| PCB fabricada y componentes soldados | Pendiente | Fotografías de ambas caras y ensamble |
| Hardware integrado con microcontrolador | Pendiente | Fotografías y comprobación de alimentación |
| Prueba de resistencia «HardExplosion» | Pendiente de conocer protocolo docente | Registro de prueba conforme a indicaciones del profesor |

La programación final no es obligatoria para la evaluación física de este avance, de acuerdo con la rúbrica suministrada; sin embargo, se continuará desarrollando y documentando el algoritmo.

## 6. Metodología, cronograma y dificultades

### 6.1. Metodología

Se propone un desarrollo incremental: (1) definición de requisitos; (2) prueba de detección en PC; (3) implementación y evaluación del conteo; (4) selección de arquitectura autónoma; (5) esquemático y PCB; (6) fabricación y ensamble; (7) integración de OLED y cámara; (8) pruebas y documentación.

### 6.2. Tabla 5. Cronograma de actividades

| Periodo propuesto | Actividad | Estado al 13/10/2026 |
|---|---|---|
| Hasta el 13 de octubre | Configuración de Python, OpenCV y YOLO; prueba inicial de cámara | Avance preliminar realizado |
| 14–20 de octubre | Verificar seguimiento, línea virtual y conteo direccional | Pendiente de validación |
| 21–27 de octubre | Confirmar adquisición de Raspberry Pi 4, identificar OLED y ESP32; definir conexiones | Pendiente |
| 28 de octubre–3 de noviembre | Elaborar esquemático, huellas, PCB y gabinete | Pendiente |
| 4–10 de noviembre | Fabricar PCB, soldar e integrar componentes | Pendiente |
| 11–17 de noviembre | Realizar pruebas físicas, documentar resultados y corregir errores | Pendiente |
| 18 de noviembre | Revisar README, figuras, ortografía y evidencias | Pendiente |
| 19 de noviembre | Entregar repositorio y sustentar el avance | Programado |

Este cronograma es una propuesta de trabajo para la fecha de entrega indicada, no una afirmación de actividades ya ejecutadas.

### 6.3. Dificultades identificadas

1. **Capacidad de cómputo:** una ESP32 no es adecuada para ejecutar directamente el YOLOv8 de escritorio utilizado; se eligió una Raspberry Pi 4, cuyo rendimiento debe medirse y optimizarse.
2. **Compatibilidad de cámara:** se debe comprobar que la cámara USB sea reconocida por Raspberry Pi OS y OpenCV mediante Video4Linux2 (V4L2).
3. **Confiabilidad del seguimiento:** las oclusiones, los cambios de iluminación y la pérdida de identificadores pueden causar conteos incorrectos.
4. **Diseño eléctrico:** deben verificarse el pinout de la ESP32 XH-32S N4XX, la interfaz y tensión de la OLED y los conectores antes de justificar el esquemático y las conexiones.
5. **Integración mecánica:** es necesario definir la posición de cámara, gabinete y PCB para obtener una vista adecuada de la puerta.
6. **Plazo de fabricación:** la entrega exige una PCB fabricada y un gabinete finalizado, por lo que la elección de arquitectura debe resolverse pronto.

### 6.4. Verificación del cumplimiento

Hasta la fecha de elaboración se dispone de una prueba preliminar de detección de objetos con YOLO y cámara del portátil. El conteo direccional, la evaluación cuantitativa, la instalación y evaluación de la Raspberry Pi 4, el diseño eléctrico, la fabricación de PCB y el gabinete requieren evidencia adicional. El equipo actualizará esta sección con fechas, responsables, capturas, fotografías y resultados reales antes de entregar.

## 7. Organización del repositorio

```text
conteo-pasajeros-bus/
├── README.md
├── software/
│   ├── raspberry_pi/
│   │   ├── conteo_pasajeros.py
│   │   └── comunicacion_esp32.py
│   └── esp32/
│       └── pantalla_oled.ino
├── hardware/
│   ├── esquematico/
│   └── pcb/
├── imagenes/
│   ├── prueba_yolo.png
│   ├── conteo_linea.png
│   ├── diagrama_bloques.png
│   ├── esquematico.png
│   ├── pcb.png
│   └── gabinete.png
└── resultados/
    └── pruebas.md
```

Los nombres de archivos de imágenes son rutas previstas: no deben presentarse como evidencia hasta añadir los archivos reales. Los archivos de KiCad y el código fuente deben conservarse en el repositorio para facilitar su revisión y sustentación.

## 8. Conclusiones preliminares

La prueba inicial en un computador permite comprobar la detección visual de objetos y avanzar hacia la detección exclusiva de personas como base para un sistema de conteo de pasajeros. La arquitectura seleccionada utiliza una Raspberry Pi 4 de 4 GB para procesar video y una ESP32 para presentar los contadores en la OLED. Su desempeño autónomo todavía no se ha verificado. El avance siguiente se enfocará en validar el conteo direccional y convertir la propuesta en un ensamble electrónico documentado y comprobable.
