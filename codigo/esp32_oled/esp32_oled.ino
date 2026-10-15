// EJEMPLO por adaptar: pantalla SSD1306 I2C 128x64 y ESP32 (SDA=21, SCL=22).
// No confirmar pines hasta verificar placa ESP32 concreta.
// Librerías Arduino: Adafruit GFX, Adafruit SSD1306, ArduinoJson (v7).
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
Adafruit_SSD1306 display(128, 64, &Wire, -1);
void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { while (true) delay(100); }
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.println("Esperando datos...");
  display.display();
}
void loop() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) return;
  int entradas = doc["entradas"] | 0;
  int salidas = doc["salidas"] | 0;
  int ocupacion = doc["ocupacion"] | 0;
  display.clearDisplay();
  display.setCursor(0,0);
  display.print("Entradas: "); display.println(entradas);
  display.print("Salidas: "); display.println(salidas);
  display.print("A bordo: "); display.println(ocupacion);
  display.display();
}
