"""Panel de consulta para red local de confianza. Apagado limitado a un comando fijo instalado por el administrador."""
import json
import subprocess
from urllib.parse import urlsplit
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTML = '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Contador del bus</title>
<style>body{font:17px system-ui;background:#edf3f7;color:#152e3d;margin:0;padding:24px}main{max-width:740px;margin:auto}h1{font-size:28px;margin-bottom:6px}.tag{color:#486173}section{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}article{background:white;border-radius:18px;padding:22px;box-shadow:0 3px 14px #1231}article:first-child{grid-column:1/-1;background:#123e50;color:white}strong{font-size:56px;display:block}.warn{color:#a32916;font-weight:600}small{color:#486173}footer{margin-top:24px;line-height:1.7}#estado{padding:12px;background:white;border-radius:10px}</style>
<main><p class="tag">MONITOREO LOCAL · RASPBERRY PI</p><h1>Contador de pasajeros</h1><p id="estado">Conectando…</p><section><article>Ocupación estimada<strong id="ocupacion">—</strong></article><article>Entradas<strong id="entradas">—</strong></article><article>Salidas<strong id="salidas">—</strong></article></section><p id="aviso" class="warn"></p><footer><div>Personas con seguimiento: <b id="personas">—</b></div><div>Procesamiento: <b id="fps">—</b> FPS</div><div>Último dato: <span id="fecha_hora">—</span></div><small>Se inicia en cero al iniciar el programa. La ocupación requiere validar los cruces y comenzar con el bus vacío. Este panel no transmite vídeo.</small></footer><p><button id="apagar" onclick="apagar()" style="padding:12px 20px;font-size:17px;background:#9d2424;color:white;border:0;border-radius:8px">Apagar Raspberry</button></p></main>
<script>let apagando=false;
async function apagar(){const boton=document.getElementById('apagar');boton.disabled=true;
try{const r=await fetch('/api/apagar',{method:'POST',headers:{'Content-Type':'application/json','X-ContadorBus':'apagar'},body:'{}',signal:AbortSignal.timeout(8000)});const d=await r.json();if(!r.ok)throw Error(d.error||'No se pudo apagar');apagando=true;document.getElementById('estado').textContent='Apagado solicitado. Espera a que la Raspberry termine antes de desconectar.';}
catch(e){document.getElementById('estado').textContent='No se confirmó el apagado: '+e.message;boton.disabled=false;}}
async function actualizar(){try{let r=await fetch('/api/estado',{cache:'no-store',signal:AbortSignal.timeout(2500)});if(!r.ok)throw Error();let d=await r.json();for(let k of ['ocupacion','entradas','salidas','personas','fps','fecha_hora'])document.getElementById(k).textContent=d[k]??'—';if(!apagando)document.getElementById('estado').textContent=d.activo?'● Conteo activo':d.edad_s===null?'Esperando la primera detección procesada…':'⚠ Sin datos recientes: revisar cámara o proceso';document.getElementById('aviso').textContent=d.ocupacion<0?'Ocupación negativa: revisar cruces y ocupación inicial.':'';}catch(e){if(!apagando)document.getElementById('estado').textContent='⚠ Sin conexión. Los valores visibles son los últimos recibidos.';}finally{if(!apagando)setTimeout(actualizar,1000)}}actualizar();</script></html>'''

class PanelBus:
    def __init__(self, host='0.0.0.0', port=8080, shutdown_action=None):
        self.lock = threading.Lock()
        self.shutdown_action = shutdown_action or self._apagar
        self.shutdown_requested = False
        self.data = dict(entradas=0, salidas=0, ocupacion=0)
        self.last = None
        self.server = None
        self.host, self.port = host, port

    @staticmethod
    def _apagar():
        subprocess.run(['/usr/bin/sudo', '-n', '/usr/local/sbin/contadorbus-apagar'],
                       check=True, timeout=5, capture_output=True)

    def solicitar_apagado(self):
        with self.lock:
            if self.shutdown_requested:
                return
            self.shutdown_action()
            self.shutdown_requested = True

    def actualizar(self, data):
        with self.lock:
            self.data = dict(data)
            self.last = time.monotonic()

    def estado(self):
        with self.lock:
            age = None if self.last is None else time.monotonic() - self.last
            return dict(self.data, edad_s=age, activo=age is not None and age < 5)

    def iniciar(self):
        panel = self
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup()
                self.connection.settimeout(5)
            def responder_json(self, status, data):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def do_POST(self):
                if self.path != '/api/apagar':
                    self.send_error(404)
                    return
                # No se aceptan formularios ni llamadas desde otro sitio. No requiere claves.
                origin = self.headers.get('Origin')
                try:
                    same_origin = origin is None or (urlsplit(origin).scheme in ('http', 'https')
                                  and urlsplit(origin).netloc == self.headers.get('Host'))
                except ValueError:
                    same_origin = False
                if (not same_origin or self.headers.get('X-ContadorBus') != 'apagar'
                        or self.headers.get('Content-Type', '').split(';')[0] != 'application/json'):
                    self.responder_json(403, {'error': 'Solicitud no permitida'})
                    return
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if length < 0 or length > 128:
                        raise ValueError('Tamaño inválido')
                    payload = json.loads(self.rfile.read(length))
                    if payload != {}:
                        raise ValueError('Solo se acepta un objeto vacío')
                except (ValueError, OSError):
                    self.responder_json(400, {'error': 'Solicitud inválida'})
                    return
                try:
                    panel.solicitar_apagado()
                except (OSError, subprocess.SubprocessError):
                    self.responder_json(503, {'error': 'No se pudo solicitar el apagado. Revisar instalación y permisos.'})
                    return
                self.responder_json(200, {'ok': True, 'mensaje': 'Apagado solicitado'})

            def do_GET(self):
                path = self.path.split('?', 1)[0]
                if path == '/':
                    body, mime = HTML.encode(), 'text/html; charset=utf-8'
                elif path == '/api/estado':
                    body, mime = json.dumps(panel.estado()).encode(), 'application/json'
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def cerrar(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
