import socket
import json
import time
from typing import Callable

class WsjtxUdpListener:
    def __init__(self, ip: str = "127.0.0.1", port: int = 2237):
        self.ip = ip
        self.port = port
        self.sock = None
        self.running = False
        self.callbacks = []
        self.last_heartbeat = 0
        
    def register_callback(self, callback: Callable):
        self.callbacks.append(callback)

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(1.0)
        self.running = True
        
    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
            
    def listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                self._parse_packet(data)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"UDP Error: {e}")

    def _parse_packet(self, data: bytes):
        """
        Parses WSJT-X UDP packets.
        WSJT-X packets have a binary header. For a full implementation, 
        we would unpack the QDataStream format (Magic Number: 0xadbccbda).
        For this scaffold, we just identify Decode (Message Type 2) or Heartbeat (Message Type 0).
        """
        # Magic number check: \xad\xbc\xcb\xda
        if len(data) < 12 or data[:4] != b'\xad\xbc\xcb\xda':
            return
            
        # Extract message type (32-bit int at offset 8)
        msg_type = int.from_bytes(data[8:12], byteorder='big')
        
        if msg_type == 0:
            # Heartbeat
            self.last_heartbeat = time.time()
        elif msg_type == 2:
            # Decode message
            # A full implementation would unpack the QSO details (Target, Grid, SNR).
            # For now, we mock passing a decoded spot to callbacks.
            decoded_spot = {
                'timestamp': time.time(),
                'snr': 0, # Placeholder
                'message': 'CQ DX W1AW FN21' # Placeholder
            }
            
            for cb in self.callbacks:
                try:
                    cb(decoded_spot)
                except Exception:
                    pass
