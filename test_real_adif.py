import os
from adif_parser import AdifParser

def test_real_log():
    log_path = r"C:\Users\chico\AppData\Local\WSJT-X\wsjtx_log.adi"
    if not os.path.exists(log_path):
        print(f"File not found: {log_path}")
        return

    parser = AdifParser()
    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        data = f.read()

    qsos, trailing = parser.parse_adif_chunk(data)
    print(f"Successfully parsed {len(qsos)} QSOs.")
    if trailing:
        print(f"Trailing bytes length: {len(trailing)}")
    
    # Print a sample QSO
    if qsos:
        print("\nSample QSO:")
        for k, v in qsos[-1].items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    test_real_log()
