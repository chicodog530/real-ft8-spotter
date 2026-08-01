from PySide6.QtCore import QThread, Signal
from phase1_poc import fetch_reports, grid_to_latlon, haversine_miles
from analyzer import freq_to_band, deduplicate_spots, filter_spots, score_dx
import xml.etree.ElementTree as ET

class ApiWorker(QThread):
    data_ready = Signal(list, dict) # spots, map_data
    error = Signal(str)

    def __init__(self, my_callsign, my_grid, exclude_callsign, radius, min_dx=1000):
        super().__init__()
        self.my_callsign = my_callsign
        self.my_grid = my_grid
        self.exclude_callsign = exclude_callsign
        self.radius = radius
        self.min_dx = min_dx

    def run(self):
        try:
            # For this prototype we fetch for my_callsign.
            # In a real app we might fetch for all callsigns in radius, but PSK reporter limits this.
            # We'll use the sample response or live fetch.
            xml_data = fetch_reports(self.my_callsign)
            if not xml_data:
                self.error.emit("Failed to fetch data from PSK Reporter.")
                return
            
            my_loc = grid_to_latlon(self.my_grid)
            if not my_loc:
                self.error.emit("Invalid Grid.")
                return

            root = ET.fromstring(xml_data)
            spots = []
            
            for report in root.findall('.//receptionReport'):
                rx_call = report.get('receiverCallsign')
                if self.exclude_callsign and rx_call.upper() == self.exclude_callsign.upper():
                    continue
                    
                rx_grid = report.get('receiverLocator')
                tx_call = report.get('senderCallsign')
                tx_grid = report.get('senderLocator')
                freq = report.get('frequency')
                snr = report.get('sNR')
                
                if not (rx_grid and tx_grid): continue
                rx_loc = grid_to_latlon(rx_grid)
                tx_loc = grid_to_latlon(tx_grid)
                if not (rx_loc and tx_loc): continue
                    
                dist_to_rx = haversine_miles(my_loc[0], my_loc[1], rx_loc[0], rx_loc[1])
                if dist_to_rx <= self.radius:
                    dist_to_tx = haversine_miles(rx_loc[0], rx_loc[1], tx_loc[0], tx_loc[1])
                    if dist_to_tx >= self.min_dx:
                        spots.append({
                            'tx_call': tx_call,
                            'rx_call': rx_call,
                            'band': freq_to_band(freq) if freq else 'Unknown',
                            'snr': snr or '0',
                            'dist_to_tx': dist_to_tx,
                            'rx_loc': rx_loc,
                            'tx_loc': tx_loc
                        })

            spots = deduplicate_spots(spots)
            scored = score_dx(spots)
            
            self.data_ready.emit(scored, {'my_loc': my_loc, 'spots': spots})
        except Exception as e:
            self.error.emit(str(e))
