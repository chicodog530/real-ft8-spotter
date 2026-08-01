import unittest
import xml.etree.ElementTree as ET
from analyzer import freq_to_band, deduplicate_spots, filter_spots, score_dx
from phase1_poc import grid_to_latlon, haversine_miles

class TestAnalyzer(unittest.TestCase):
    def test_freq_to_band(self):
        self.assertEqual(freq_to_band(14074000), "20m")
        self.assertEqual(freq_to_band(7074000), "40m")
        self.assertEqual(freq_to_band(28074000), "10m")
        
    def test_deduplicate(self):
        spots = [
            {'tx_call': 'DX1', 'rx_call': 'ME1', 'band': '20m', 'snr': '-10'},
            {'tx_call': 'DX1', 'rx_call': 'ME1', 'band': '20m', 'snr': '-5'}, # Stronger
            {'tx_call': 'DX2', 'rx_call': 'ME1', 'band': '20m', 'snr': '0'},
        ]
        deduped = deduplicate_spots(spots)
        self.assertEqual(len(deduped), 2)
        
        # Check that the stronger one was kept
        dx1_spot = next(s for s in deduped if s['tx_call'] == 'DX1')
        self.assertEqual(dx1_spot['snr'], '-5')
        
    def test_score_dx(self):
        spots = [
            {'tx_call': 'DX1', 'rx_call': 'ME1', 'band': '20m', 'snr': '-10', 'dist_to_tx': 5000},
            {'tx_call': 'DX1', 'rx_call': 'ME2', 'band': '20m', 'snr': '-5', 'dist_to_tx': 5100},
            {'tx_call': 'DX2', 'rx_call': 'ME1', 'band': '20m', 'snr': '0', 'dist_to_tx': 2000},
        ]
        scored = score_dx(spots)
        self.assertEqual(len(scored), 2)
        
        dx1_score = next(s for s in scored if s['tx_call'] == 'DX1')
        self.assertEqual(dx1_score['rx_count'], 2)
        self.assertEqual(dx1_score['avg_snr'], -7.5) # (-10 + -5) / 2

if __name__ == '__main__':
    unittest.main()
