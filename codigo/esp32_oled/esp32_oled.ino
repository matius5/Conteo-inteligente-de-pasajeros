// Firmware de ejemplo para ESP32 + OLED SSD1306 I2C 128x64.
//
// IMPORTANTE: adaptar y verificar antes de flashear.
// - Placa exacta de ESP32: pendiente de confirmar.
// - Pantalla: SSD1306 128x64, dirección I2C habitual 0x3C.
// - Pines de ejemplo: SDA=21, SCL=22. No son válidos en todas las placas.
// - Alimentación: 3.3 V y GND comunes con la Raspberry por USB.
//
// Protocolo: una línea JSON por puerto serial a 115200 baudios.
// {"entradas":10,"salidas":8,"ocupacion":2}
//
// Librerías Arduino: Adafruit GFX, Adafruit SSD1306, ArduinoJson 7.x.
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

constexpr int SCREEN_WIDTH = 128;
constexpr int SCREEN_HEIGHT = 64;
constexpr int OLED_RESET = -1;
constexpr uint8_t SCREEN_ADDRESS = 0x3C;  // Verificar con escáner I2C.
constexpr int PIN_SDA = 21;               // Verificar en la placa real.
constexpr int PIN_SCL = 22;
constexpr unsigned long TIMEOUT_MS = 5000;

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

int entradas = 0;
int salidas = 0;
int ocupacion = 0;
bool hayDatos = false;
unsigned long ultimoMensaje = 0;

void mostrarPantalla(bool conectado) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("CONTEO DE PASAJEROS");
  display.drawLine(0, 10, 127, 10, SSD1306_WHITE);

  display.setCursor(0, 15);
  display.print("Entradas: ");
  display.print(entradas);
  display.setCursor(0, 26);
  display.print("Salidas:  ");
  display.print(salidas);

  display.setTextSize(2);
  display.setCursor(0, 40);
  display.print("A bordo:");
  display.setCursor(84, 40);
  display.print(ocupacion);

  display.setTextSize(1);
  display.setCursor(0, 57);
  display.print(conectado ? "ESP32 conectado" : "Sin datos serial");
  display.display();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    // Si la pantalla no responde, no bloquear el puerto serial.
    Serial.println("ERROR: OLED SSD1306 no encontrada");
  } else {
    mostrarPantalla(false);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String linea = Serial.readStringUntil('\n');
    linea.trim();
    if (linea.length() > 0) {
      JsonDocument doc;
      DeserializationError error = deserializeJson(doc, linea);
      if (!error) {
        entradas = doc["entradas"] | entradas;
        salidas = doc["salidas"] | salidas;
        ocupacion = doc["ocupacion"] | ocupacion;
        hayDatos = true;
        ultimoMensaje = millis();
      }
    }
  }

  static unsigned long ultimaActualizacion = 0;
  if (millis() - ultimaActualizacion > 500) {
    bool conectado = hayDatos && (millis() - ultimoMensaje < TIMEOUT_MS);
    mostrarPantalla(conectado);
    ultimaActualizacion = millis();
  }
}
