#!/usr/bin/env python3
"""Testes do ADB Connection Manager (stdlib unittest, sem dependências).

Executa:  python scripts/test_adb_connection_manager.py
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

import adb_connection_manager as m


def _fake_devices_output(*lines):
    return 'List of devices attached\n' + '\n'.join(lines) + '\n'


class TestParseDevices(unittest.TestCase):
    def test_vazio(self):
        self.assertEqual(m.parse_devices('List of devices attached\n'), [])

    def test_multiplos(self):
        out = _fake_devices_output('emulator-5554\tdevice', '192.168.1.5:5555\tdevice')
        devs = m.parse_devices(out)
        self.assertEqual(len(devs), 2)
        self.assertEqual(devs[0]['state'], 'device')

    def test_unauthorized(self):
        out = _fake_devices_output('XX123\tunauthorized')
        self.assertEqual(m.parse_devices(out)[0]['state'], 'unauthorized')


class TestBackoff(unittest.TestCase):
    def setUp(self):
        self.cm = m.ConnectionManager(adb='fake/adb')

    def test_escala_e_teto(self):
        # backoff_idx cresce até o teto
        self.assertEqual(m.BACKOFF_SCHEDULE[-1], 300)
        self.cm.backoff_idx = len(m.BACKOFF_SCHEDULE) - 1
        delay = self.cm._backoff_delay()
        # base 300, jitter ±25% -> 225..375
        self.assertGreaterEqual(delay, 225)
        self.assertLessEqual(delay, 375)

    def test_reset(self):
        self.cm.backoff_idx = 3
        self.cm._reset_backoff()
        self.assertEqual(self.cm.backoff_idx, 0)
        self.assertEqual(self.cm.attempts, 0)


class TestTransportes(unittest.TestCase):
    def setUp(self):
        self.cm = m.ConnectionManager(adb='fake/adb')

    def test_prioridade(self):
        self.assertEqual([t.name for t in self.cm.transports],
                         ['usb', 'wifi', 'mdns', 'tailscale'])

    def test_transporte_registro(self):
        self.assertIn('usb', m.TRANSPORT_CLASSES)
        self.assertIn('tailscale', m.TRANSPORT_CLASSES)

    def test_usb_detect_ignora_tcp(self):
        with mock.patch.object(self.cm, '_devices', return_value=[
            {'id': 'emulator-5554', 'state': 'device'},
            {'id': '192.168.1.5:5555', 'state': 'device'},
        ]):
            usb = self.cm.transports[0]
            det = usb.detect()
            self.assertEqual(len(det), 1)
            self.assertEqual(det[0]['id'], 'emulator-5554')


class TestConnectionFlow(unittest.TestCase):
    def test_connect_preserva_saudavel(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[
                {'id': 'emulator-5554', 'state': 'device'}]):
            # health() já mockado para reportar saudável
            with mock.patch.object(cm, 'health', return_value={
                    'status': m.HEALTH_OK, 'serial': 'emulator-5554',
                    'devices': [], 'latency_ms': 1}):
                res = cm.connect()
                self.assertTrue(res['success'])
                self.assertEqual(res['device'], 'emulator-5554')

    def test_connect_tenta_transportes_em_falha(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[]):
            with mock.patch.object(cm, 'health', return_value={
                    'status': m.HEALTH_DISCONNECTED, 'devices': []}):
                # Força falha em todos os transportes
                for tr in cm.transports:
                    tr.connect = mock.Mock(return_value={
                        'success': False, 'error': 'x', 'transport': tr.name})
                res = cm.connect(force=True)
                self.assertFalse(res['success'])
                self.assertEqual(res['state'], m.FAILED)

    def test_connect_sucesso_tailscale(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[]):
            with mock.patch.object(cm, 'health', return_value={
                    'status': m.HEALTH_DISCONNECTED, 'devices': []}):
                for tr in cm.transports:
                    if tr.name == 'tailscale':
                        tr.connect = mock.Mock(return_value={
                            'success': True, 'serial': '100.64.71.9:5555',
                            'transport': 'tailscale'})
                    else:
                        tr.connect = mock.Mock(return_value={
                            'success': False, 'error': 'x', 'transport': tr.name})
                res = cm.connect(force=True)
                self.assertTrue(res['success'])
                self.assertEqual(res['device'], '100.64.71.9:5555')
                self.assertEqual(res['transport'], 'tailscale')


class TestHealth(unittest.TestCase):
    def test_health_responsivo(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[
                {'id': 'emulator-5554', 'state': 'device'}]):
            with mock.patch.object(m, '_run', return_value=mock.Mock(
                    returncode=0, stdout='ok')):
                h = cm.health()
                self.assertEqual(h['status'], m.HEALTH_OK)
                self.assertEqual(h['state'], m.CONNECTED)

    def test_health_nao_responsivo(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[
                {'id': 'emulator-5554', 'state': 'device'}]):
            def _raise(*a, **k):
                raise Exception('timeout')
            with mock.patch.object(m, '_run', side_effect=_raise):
                h = cm.health()
                self.assertEqual(h['status'], m.HEALTH_UNRESPONSIVE)
                self.assertEqual(h['state'], m.DEGRADED)

    def test_health_desconectado(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[]):
            h = cm.health()
            self.assertEqual(h['status'], m.HEALTH_DISCONNECTED)


class TestExecuteValida(unittest.TestCase):
    def test_rejeita_comando_arbitrario(self):
        cm = m.ConnectionManager(adb='fake/adb')
        res = cm.execute('rm', ['-rf', '/'])
        self.assertFalse(res['success'])
        self.assertIn('não permitido', res['error'])

    def test_permite_comando_valido(self):
        cm = m.ConnectionManager(adb='fake/adb')
        cm.device = 'emulator-5554'
        with mock.patch.object(m, '_run', return_value=mock.Mock(
                returncode=0, stdout='ok', stderr='')):
            res = cm.execute('shell', ['echo', 'hi'])
            self.assertTrue(res['success'])


class TestDiagnose(unittest.TestCase):
    def test_diagnose_estrutura(self):
        cm = m.ConnectionManager(adb='fake/adb')
        with mock.patch.object(cm, '_devices', return_value=[]):
            with mock.patch.object(m, '_run', return_value=mock.Mock(
                    returncode=0, stdout='ok', stderr='')):
                d = cm.diagnose()
                for key in ('adbd', 'server', 'authorization', 'transport',
                            'state', 'health', 'timestamp'):
                    self.assertIn(key, d)


class TestLock(unittest.TestCase):
    def test_lock_libera(self):
        with m.ConnectionLock():
            pass
        self.assertFalse(m._LOCK_FILE.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
