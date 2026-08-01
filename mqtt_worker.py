import json
import time
from PySide6.QtCore import QThread, Signal
import paho.mqtt.client as mqtt
from phase1_poc import grid_to_latlon, haversine_miles
from analyzer import freq_to_band, score_dx

class MqttWorker(QThread):
    data_ready = Signal(list, dict) # scored_dx, map_data
    status_update = Signal(str)

    def __init__(self, my_callsign, my_grid, exclude_callsign, radius, min_dx=1000, pota_engine=None):
        super().__init__()
        self.my_callsign = my_callsign
        self.my_grid = my_grid
        self.my_loc = grid_to_latlon(my_grid)
        self.exclude_callsign = exclude_callsign
        self.radius = radius
        self.min_dx = min_dx
        self.pota_engine = pota_engine
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"FT8Spotter_{self.my_callsign}_{int(time.time())}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        from database import Database
        from likelihood_engine import LikelihoodEngineV2
        from need_engine import NeedEngine
        
        self.db = Database()
        self.likelihood_engine = LikelihoodEngineV2(self.db)
        self.need_engine = NeedEngine(self.db)
        
        self.rolling_spots = [] # Buffer for recent spots
        self.db_insert_queue = [] # Buffer for pending DB insertions
        self.running = True

    def on_connect(self, client, userdata, flags, reason_code, properties):
        self.status_update.emit("Connected to MQTT Stream")
        # Subscribe to all spots (Firehose) because we want anything heard by nearby receivers
        self.client.subscribe("pskr/filter/v2/#")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        if self.running:
            self.status_update.emit("MQTT Disconnected. Reconnecting...")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Extract fields using MQTT short keys
            rx_call = payload.get('rc', '')
            if self.exclude_callsign and rx_call.upper() == self.exclude_callsign.upper():
                return
                
            rx_grid = payload.get('rl', '')
            tx_call = payload.get('sc', '')
            tx_grid = payload.get('sl', '')
            freq = payload.get('f')
            snr = payload.get('rp')
            if snr is None:
                snr = 0
            
            if not (rx_grid and tx_grid and freq):
                return
                
            rx_loc = grid_to_latlon(rx_grid)
            tx_loc = grid_to_latlon(tx_grid)
            if not (rx_loc and tx_loc):
                return
                
            # Filter by radius
            dist_to_rx = haversine_miles(self.my_loc[0], self.my_loc[1], rx_loc[0], rx_loc[1])
            if dist_to_rx > self.radius:
                return # Receiver is too far
                
            # Filter by DX distance
            dist_to_tx = haversine_miles(rx_loc[0], rx_loc[1], tx_loc[0], tx_loc[1])
            if dist_to_tx < self.min_dx:
                return # DX is not far enough
                
            spot = {
                'tx_call': tx_call,
                'rx_call': rx_call,
                'tx_grid': tx_grid,
                'rx_grid': rx_grid,
                'band': freq_to_band(freq),
                'snr': snr,
                'dist_to_tx': dist_to_tx,
                'dist_to_rx': dist_to_rx,
                'rx_loc': rx_loc,
                'tx_loc': tx_loc,
                'timestamp': time.time()
            }
            self.rolling_spots.append(spot)
            self.db_insert_queue.append(spot)
            
            
        except Exception:
            pass # Ignore malformed json

    def run(self):
        if not self.my_loc:
            self.status_update.emit("Invalid Grid.")
            return

        self.status_update.emit("Connecting to mqtt.pskreporter.info...")
        try:
            self.client.connect("mqtt.pskreporter.info", 1883, 60)
            self.client.loop_start()
        except Exception as e:
            self.status_update.emit(f"MQTT Connect Error: {e}")
            return

        while self.running:
            time.sleep(5) # Push UI updates every 5 seconds
            current_time = time.time()
            
            # Flush pending DB insertions
            if self.db_insert_queue:
                spots_to_insert = self.db_insert_queue[:]
                self.db_insert_queue.clear()
                try:
                    self.db.batch_insert_spots(spots_to_insert)
                except Exception as e:
                    print(f"DB Insert Error: {e}")
            
            # Evict spots that are too old, or no longer match current filters
            valid_spots = []
            for s in self.rolling_spots:
                if current_time - s['timestamp'] >= 900:
                    continue
                if self.exclude_callsign and s['rx_call'].upper() == self.exclude_callsign.upper():
                    continue
                if s['dist_to_rx'] > self.radius:
                    continue
                valid_spots.append(s)
                
            self.rolling_spots = valid_spots
            
            # We don't deduplicate in the traditional sense, score_dx groups them anyway
            scored = score_dx(self.rolling_spots, likelihood_engine=self.likelihood_engine, need_engine=self.need_engine, pota_engine=self.pota_engine)
            self.data_ready.emit(scored, {'my_loc': self.my_loc, 'spots': self.rolling_spots})

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
