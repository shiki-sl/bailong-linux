import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

import linux_support as linux


class LinuxIntegrationTests(unittest.TestCase):
    def test_startup_is_opt_in_and_uses_the_actual_venv(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}), patch.object(linux.sys, 'executable', '/tmp/example venv/bin/python'):
            path = linux.startup_path()
            self.assertFalse(path.exists())
            linux.register_startup(True)
            text = path.read_text()
            self.assertIn('"/tmp/example venv/bin/python"', text)
            self.assertNotIn('pythonw.exe', text)
            linux.register_startup(False)
            self.assertFalse(path.exists())

    def test_chat_key_is_sent_over_stdin_to_secret_service(self):
        with patch.object(linux.shutil, 'which', return_value='/usr/bin/secret-tool'), patch.object(linux.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            linux.SecretStore('/tmp/chat-keys.json').put('example', 'test-only-key')
            args, options = run.call_args
            self.assertNotIn('test-only-key', repr(args))
            self.assertEqual(options['input'], 'test-only-key')
            self.assertIn('store', args[0])

    def test_missing_keyring_never_falls_back_to_plaintext(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(linux.shutil, 'which', return_value=None):
            path = Path(folder) / 'keys.json'
            with self.assertRaises(OSError):
                linux.SecretStore(path).put('example', 'test-only-key')
            self.assertFalse(path.exists())

    def test_unix_transport_reads_and_writes_the_framed_stream(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            path = home / 'ipc/ipc.sock'
            path.parent.mkdir()
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(path))
            server.listen(1)
            received = []
            def serve():
                with server.accept()[0] as client:
                    received.append(client.recv(2))
                    client.sendall(b'ok')
            worker = threading.Thread(target=serve)
            worker.start()
            class Reader:
                stop_event = threading.Event()
                connected = False
                def _listen(self, stream, available):
                    stream.write(b'hi')
                    received.append(stream.read(2))
                    self.stop_event.set()
                def set_health(self, *args):
                    raise AssertionError(args)
            with patch('codex_connection.data_home', return_value=home):
                linux.ipc_listen(Reader())
            worker.join(2)
            server.close()
            self.assertEqual(received, [b'hi', b'ok'])


if __name__ == '__main__':
    unittest.main()
