import json
import socket

from PyQt5.QtCore import QThread, pyqtSignal


class NetworkClient(QThread):
    message_received = pyqtSignal(dict)
    connection_error = pyqtSignal(str)

    def __init__(self, host: str, port: int, nickname: str, parent=None):
        super().__init__(parent)
        self._host     = host
        self._port     = port
        self._nickname = nickname
        self._sock: socket.socket | None = None
        self._running  = False

    def connect_to_server(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(10)
        self._sock.connect((self._host, self._port))
        self._sock.settimeout(None)
        self._send_raw({"type": "HELLO", "payload": {"name": self._nickname}})

    def run(self):
        self._running = True
        buf = b""
        try:
            while self._running:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if line.strip():
                        msg = json.loads(line.decode())
                        self.message_received.emit(msg)
        except Exception as e:
            if self._running:
                self.connection_error.emit(str(e))
        finally:
            self._running = False

    def send(self, msg: dict):
        self._send_raw(msg)

    def _send_raw(self, msg: dict):
        if self._sock:
            try:
                raw = json.dumps(msg) + "\n"
                self._sock.sendall(raw.encode())
            except Exception as e:
                self.connection_error.emit(str(e))

    def close(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
