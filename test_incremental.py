import os
import shutil
import time
from database import Database
from adif_parser import AdifParser

def test_incremental():
    db = Database("test_incremental.db")
    parser = AdifParser(db_conn=db)
    
    test_file = "test_log.adi"
    
    # 1. First Import
    with open(test_file, "w") as f:
        f.write("<CALL:4>W1AW<MODE:3>FT8<EOR>")
    
    new_qsos = parser.import_incremental(test_file)
    print(f"First import: {new_qsos} new QSOs.")
    
    # 2. Unchanged Import
    new_qsos = parser.import_incremental(test_file)
    print(f"Unchanged import: {new_qsos} new QSOs.")
    
    # 3. Appended Import
    with open(test_file, "a") as f:
        f.write("<CALL:4>K1ZZ<MODE:3>FT8<EOR>")
        
    new_qsos = parser.import_incremental(test_file)
    print(f"Appended import: {new_qsos} new QSOs.")
    
    # 4. Truncated Import (Rewrite)
    with open(test_file, "w") as f:
        f.write("<CALL:4>N0AA<MODE:3>FT8<EOR>")
        
    new_qsos = parser.import_incremental(test_file)
    print(f"Truncated import (rewrite): {new_qsos} new QSOs.")
    
    # Clean up
    if os.path.exists("test_incremental.db"): os.remove("test_incremental.db")
    if os.path.exists("test_log.adi"): os.remove("test_log.adi")

if __name__ == "__main__":
    test_incremental()
