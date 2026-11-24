import json
import sys
import unittest
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'codigo'))
from line_counter import ContadorLinea
from panel_bus import PanelBus


class ConteoTest(unittest.TestCase):
    def setUp(self):
        self.c = ContadorLinea('vertical', 320, 'left_to_right', margen_px=26)

    def test_entrada_salida_y_reinicio(self):
        self.assertIsNone(self.c.actualizar(1, (200, 100), 0))
        self.assertEqual(self.c.actualizar(1, (400, 100), 1).direccion, 'entrada')
        self.assertEqual(self.c.ocupacion, 1)
        self.assertEqual(self.c.actualizar(1, (200, 100), 2).direccion, 'salida')
        self.assertEqual(self.c.ocupacion, 0)
        self.c.reiniciar()
        self.assertEqual((self.c.entradas, self.c.salidas, self.c.tracks_activos), (0, 0, 0))

    def test_banda_sin_cruce(self):
        for t, x in enumerate([200, 310, 330, 320, 200]):
            self.assertIsNone(self.c.actualizar(1, (x, 100), t * .2))
        self.assertEqual(self.c.entradas, 0)

    def test_perdida_de_seguimiento_no_inventa_cruce(self):
        self.c.actualizar(1, (200, 100), 0)
        self.assertIsNone(self.c.actualizar(1, (400, 100), 3))
        self.assertEqual(self.c.entradas, 0)

    def test_salida_inicial_conserva_negativo(self):
        self.c.actualizar(1, (400, 100), 0)
        self.c.actualizar(1, (200, 100), 1)
        self.assertEqual(self.c.ocupacion, -1)


class PanelTest(unittest.TestCase):
    def setUp(self):
        self.actions = []
        self.panel = PanelBus('127.0.0.1', 0, shutdown_action=lambda: self.actions.append('apagado'))
        self.panel.iniciar()
        self.url = 'http://127.0.0.1:' + str(self.panel.server.server_port)

    def tearDown(self):
        self.panel.cerrar()

    def request(self, path, data=None, headers=None):
        req = Request(self.url + path, data=data, headers=headers or {})
        try:
            with urlopen(req, timeout=3) as r: return r.status, r.read()
        except HTTPError as e:
            return e.code, e.read()

    def headers(self):
        return {'Content-Type': 'application/json', 'X-ContadorBus': 'apagar', 'Origin': self.url}

    def test_estado_actualizado(self):
        self.assertFalse(json.loads(self.request('/api/estado')[1])['activo'])
        self.panel.actualizar({'entradas': 3, 'salidas': 1, 'ocupacion': 2})
        data = json.loads(self.request('/api/estado')[1])
        self.assertTrue(data['activo'])
        self.assertEqual(data['ocupacion'], 2)

    def test_pagina_y_get_no_apagan(self):
        status, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'Apagar Raspberry', body)
        self.assertEqual(self.request('/api/apagar')[0], 404)
        self.assertEqual(self.actions, [])

    def test_post_valido_una_sola_solicitud(self):
        for _ in range(2):
            self.assertEqual(self.request('/api/apagar', b'{}', self.headers())[0], 200)
        self.assertEqual(self.actions, ['apagado'])

    def test_otro_origen_rechazado(self):
        headers = self.headers(); headers['Origin'] = 'https://otro-sitio.invalid'
        self.assertEqual(self.request('/api/apagar', b'{}', headers)[0], 403)
        self.assertEqual(self.actions, [])

    def test_sin_cabecera_rechazado(self):
        self.assertEqual(self.request('/api/apagar', b'{}', {'Content-Type': 'application/json'})[0], 403)
        self.assertEqual(self.actions, [])

    def test_payload_no_permite_comandos(self):
        self.assertEqual(self.request('/api/apagar', b'{"cmd":"otra cosa"}', self.headers())[0], 400)
        self.assertEqual(self.actions, [])

    def test_fallo_privilegios_no_da_exito(self):
        def fallo(): raise subprocess.CalledProcessError(1, 'sudo')
        self.panel.shutdown_action = fallo
        self.assertEqual(self.request('/api/apagar', b'{}', self.headers())[0], 503)
        self.assertFalse(self.panel.shutdown_requested)
