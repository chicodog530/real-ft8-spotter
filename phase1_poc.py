import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import math
import time

def grid_to_latlon(grid):
    grid = grid.upper()
    if len(grid) < 4:
        return None
    lon = (ord(grid[0]) - ord('A')) * 20 - 180
    lat = (ord(grid[1]) - ord('A')) * 10 - 90
    lon += (ord(grid[2]) - ord('0')) * 2
    lat += (ord(grid[3]) - ord('0')) * 1
    
    # Add center offset for 4-char grids
    if len(grid) == 4:
        lon += 1.0
        lat += 0.5
    elif len(grid) >= 6:
        lon += (ord(grid[4]) - ord('A')) * (5.0 / 60.0)
        lat += (ord(grid[5]) - ord('A')) * (2.5 / 60.0)
        # Center offset for 6-char grids
        lon += (2.5 / 60.0)
        lat += (1.25 / 60.0)
    
    return lat, lon

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def fetch_reports(callsign):
    url = f"https://retrieve.pskreporter.info/query?receiverCallsign={urllib.parse.quote(callsign)}&appcontact=test@example.com"
    req = urllib.request.Request(url, headers={'User-Agent': 'FT8LocalDXSpotter-PoC/0.1'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def process_reports(xml_data, my_grid, max_nearby_radius=100):
    my_loc = grid_to_latlon(my_grid)
    if not my_loc:
        print("Invalid grid.")
        return
        
    root = ET.fromstring(xml_data)
    
    print(f"My Location: {my_grid} -> {my_loc}")
    
    spots = []
    
    for report in root.findall('.//receptionReport'):
        rx_call = report.get('receiverCallsign')
        rx_grid = report.get('receiverLocator')
        tx_call = report.get('senderCallsign')
        tx_grid = report.get('senderLocator')
        freq = report.get('frequency')
        snr = report.get('sNR')
        
        if not (rx_grid and tx_grid):
            continue
            
        rx_loc = grid_to_latlon(rx_grid)
        tx_loc = grid_to_latlon(tx_grid)
        
        if not (rx_loc and tx_loc):
            continue
            
        dist_to_rx = haversine_miles(my_loc[0], my_loc[1], rx_loc[0], rx_loc[1])
        
        # Only care about nearby receivers
        if dist_to_rx <= max_nearby_radius:
            dist_to_tx = haversine_miles(my_loc[0], my_loc[1], tx_loc[0], tx_loc[1])
            spots.append({
                'rx_call': rx_call,
                'rx_grid': rx_grid,
                'tx_call': tx_call,
                'tx_grid': tx_grid,
                'freq': freq,
                'snr': snr,
                'dist_to_rx': dist_to_rx,
                'dist_to_tx': dist_to_tx
            })

    # Print interesting DX
    spots.sort(key=lambda x: x['dist_to_tx'], reverse=True)
    print(f"\nFound {len(spots)} reception reports from nearby receivers (<= {max_nearby_radius} miles).\n")
    for s in spots[:20]: # show top 20 furthest DX
        print(f"RX: {s['rx_call']} ({s['dist_to_rx']:.1f}mi away) heard TX: {s['tx_call']} ({s['dist_to_tx']:,.0f}mi away) on {s['freq']} Hz with SNR {s['snr']} dB")

if __name__ == "__main__":
    my_callsign = "KE0CGB"
    my_grid = "EM27XO" # Based on Jerico Springs MO approximate grid
    
    print("Fetching data...")
    xml_data = fetch_reports(my_callsign)
    if xml_data:
        # Save sample for offline testing
        with open("sample_response.xml", "wb") as f:
            f.write(xml_data)
        print("Saved sample_response.xml")
        
        process_reports(xml_data, my_grid, max_nearby_radius=100)
