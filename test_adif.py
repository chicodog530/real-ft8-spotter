import unittest
from adif_parser import AdifParser

class TestAdifParser(unittest.TestCase):
    def setUp(self):
        self.parser = AdifParser()

    def test_basic_and_mixed_case(self):
        # Mixed uppercase/lowercase field names, Unknown fields
        adif_data = "<cAlL:4>W1AW <qso_date:8>20260801 <unknown_field:3>FOO <MODE:3>FT8 <EOR>"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        
        self.assertEqual(len(qsos), 1)
        self.assertEqual(qsos[0]['CALL'], 'W1AW')
        self.assertEqual(qsos[0]['QSO_DATE'], '20260801')
        self.assertEqual(qsos[0]['UNKNOWN_FIELD'], 'FOO')
        self.assertEqual(qsos[0]['MODE'], 'FT8')
        self.assertEqual(trailing, '')

    def test_multiple_records_one_line(self):
        adif_data = "<CALL:4>W1AW<MODE:3>FT8<EOR><CALL:4>K1ZZ<MODE:3>FT8<EOR>"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        
        self.assertEqual(len(qsos), 2)
        self.assertEqual(qsos[0]['CALL'], 'W1AW')
        self.assertEqual(qsos[1]['CALL'], 'K1ZZ')

    def test_records_split_across_lines(self):
        adif_data = "<CALL:4>W1\nAW\n<MODE:3>FT8\n<EOR>\n"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        
        self.assertEqual(len(qsos), 1)
        # Note: length 4 means "W1\nA". Let's use a better example.
        # Length includes newlines if they are within the length block!
        adif_data2 = "<CALL:4>W1AW\n<MODE:3>FT8\n<EOR>"
        qsos2, trailing2 = self.parser.parse_adif_chunk(adif_data2)
        self.assertEqual(qsos2[0]['CALL'], 'W1AW')
        self.assertEqual(qsos2[0]['MODE'], 'FT8')

    def test_incomplete_final_record(self):
        adif_data = "<CALL:4>W1AW<MODE:3>FT8<EOR><CALL:4>K1ZZ<MODE:3>FT"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        
        self.assertEqual(len(qsos), 1)
        self.assertEqual(qsos[0]['CALL'], 'W1AW')
        # The trailing data should be the incomplete portion
        self.assertTrue(trailing.startswith('<CALL:4>K1ZZ'))

    def test_mfsk_submode_normalization(self):
        adif_data = "<CALL:4>W1AW<MODE:4>MFSK<SUBMODE:3>FT8<EOR>"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        self.assertEqual(qsos[0]['MODE'], 'FT8')

    def test_missing_band_inference(self):
        adif_data = "<CALL:4>W1AW<FREQ:7>14.0740<MODE:3>FT8<EOR>"
        qsos, trailing = self.parser.parse_adif_chunk(adif_data)
        self.assertEqual(qsos[0]['BAND'], '20M')

if __name__ == '__main__':
    unittest.main()
