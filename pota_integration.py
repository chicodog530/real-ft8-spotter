import threading
import time
import requests

class PotaIntegration:
    def __init__(self, polling_interval=300):
        self.polling_interval = polling_interval
        self.active_activators = set()
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._poll_loop)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            try:
                self._fetch_pota_spots()
            except Exception as e:
                print(f"Error fetching POTA API: {e}")
            
            # Sleep in chunks to allow quick exit
            for _ in range(self.polling_interval):
                if not self._running:
                    break
                time.sleep(1)

    def _fetch_pota_spots(self):
        """Fetches live spots from api.pota.app and updates the active set."""
        # POTA API for current spots
        url = "https://api.pota.app/spot/activator"
        headers = {"User-Agent": "RealFT8Spotter/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            new_activators = set()
            for spot in data:
                activator = spot.get("activator")
                if activator:
                    # Strip modifiers like /P just in case, though usually exact match is safer
                    base_call = activator.split('/')[0]
                    new_activators.add(base_call.upper())
            
            with self._lock:
                self.active_activators = new_activators
            print(f"[POTA] Updated active list: {len(self.active_activators)} activators.")

    def is_pota(self, callsign: str) -> bool:
        """Returns True if the callsign is currently activating a park."""
        with self._lock:
            # Check base callsign
            base_call = callsign.split('/')[0].upper()
            return base_call in self.active_activators
