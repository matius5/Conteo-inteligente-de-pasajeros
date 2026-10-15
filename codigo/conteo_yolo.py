"""Prototipo de conteo por línea con tracking YOLO. Validar sobre videos reales."""
import argparse
import json
import cv2
from ultralytics import YOLO

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--camera', type=int, default=0)
    p.add_argument('--line-y', type=int, default=None, help='Línea horizontal (coordenada Y)')
    p.add_argument('--line-x', type=int, default=None, help='Línea vertical (coordenada X)')
    p.add_argument('--model', default='yolo11n.pt')
    p.add_argument('--serial-port', default=None)
    p.add_argument('--baud', type=int, default=115200)
    a = p.parse_args()
    if a.line_x is not None and a.line_y is not None:
        p.error('Utiliza solo --line-x o --line-y')
    horizontal = a.line_x is None
    ser = None
    if a.serial_port:
        import serial
        ser = serial.Serial(a.serial_port, a.baud, timeout=1)
    camera = cv2.VideoCapture(a.camera)
    if not camera.isOpened():
        raise RuntimeError('No se pudo abrir la cámara')
    model = YOLO(a.model)
    last_side = {}  # identificador -> lado previo de la línea
    entries, exits = 0, 0
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            line = min(max((a.line_y if a.line_y is not None else h//2) if horizontal else a.line_x, 0), (h-1 if horizontal else w-1))
            result = model.track(frame, persist=True, classes=[0], conf=0.35, verbose=False)[0]
            boxes = result.boxes
            if boxes is not None and boxes.id is not None:
                ids = boxes.id.int().cpu().tolist()
                xyxy = boxes.xyxy.cpu().tolist()
                for tid, (x1, y1, x2, y2) in zip(ids, xyxy):
                    center = (y1 + y2) / 2 if horizontal else (x1 + x2) / 2
                    side = -1 if center < line else 1
                    old = last_side.get(tid)
                    # Convención provisional: arriba->abajo o izquierda->derecha = entrada
                    if old is not None and old != side:
                        if old == -1 and side == 1:
                            entries += 1
                        else:
                            exits += 1
                        payload = {'entradas': entries, 'salidas': exits,
                                   'ocupacion': max(0, entries - exits)}
                        print(json.dumps(payload, ensure_ascii=False))
                        if ser:
                            ser.write((json.dumps(payload) + '\n').encode('utf-8'))
                    last_side[tid] = side
                    cv2.rectangle(frame, (int(x1),int(y1)), (int(x2),int(y2)), (0,255,0),2)
                    cv2.putText(frame, f'ID {tid}', (int(x1),max(20,int(y1)-5)),
                                cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,0),2)
            if horizontal:
                cv2.line(frame,(0,line),(w,line),(255,200,0),2)
            else:
                cv2.line(frame,(line,0),(line,h),(255,200,0),2)
            cv2.putText(frame, f'Ent: {entries} Sal: {exits} Ocup: {max(0,entries-exits)}',
                        (12,32), cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
            cv2.imshow('Conteo de pasajeros - prototipo',frame)
            if cv2.waitKey(1)&0xFF == ord('q'):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        if ser:
            ser.close()

if __name__ == '__main__':
    main()
