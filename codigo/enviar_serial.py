"""Prueba de conexión: envía UN mensaje de ejemplo a la ESP32."""
import argparse, json
import serial

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('port',help='Ej.: COM3 o /dev/ttyUSB0')
    args=p.parse_args()
    with serial.Serial(args.port,115200,timeout=2) as esp:
        msg={'entradas': 3, 'salidas': 1, 'ocupacion': 2}
        esp.write((json.dumps(msg)+'\n').encode())
        print('Enviado:',msg)
