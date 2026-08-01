import sqlite3
import os
import shutil
import logging
from typing import List, Tuple, Any

logger = logging.getLogger(__name__)

# Define all migrations sequentially
MIGRATIONS = [
    # Version 1: Initial Baseline Schema
    """
    CREATE TABLE schema_migrations (
        version INTEGER PRIMARY KEY,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE adif_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_size INTEGER NOT NULL,
        mtime REAL NOT NULL,
        last_byte_offset INTEGER NOT NULL DEFAULT 0,
        begin_hash TEXT,
        checkpoint_hash TEXT,
        trailing_bytes BLOB,
        last_imported_at DATETIME,
        status TEXT
    );
    
    CREATE TABLE qsos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER REFERENCES adif_sources(id),
        fingerprint TEXT UNIQUE NOT NULL,
        callsign TEXT NOT NULL,
        qso_date TEXT NOT NULL,
        time_on TEXT,
        band TEXT NOT NULL,
        freq REAL,
        mode TEXT NOT NULL,
        dxcc INTEGER,
        country TEXT,
        gridsquare TEXT,
        state TEXT,
        county TEXT,
        cqz INTEGER,
        ituz INTEGER,
        iota TEXT,
        qsl_rcvd TEXT,
        lotw_qsl_rcvd TEXT,
        eqsl_qsl_rcvd TEXT
    );
    
    CREATE TABLE receiver_epochs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        callsign TEXT NOT NULL,
        locator TEXT NOT NULL,
        first_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        antenna_info TEXT,
        software_info TEXT,
        UNIQUE(callsign, locator)
    );
    
    CREATE TABLE receiver_raw_spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epoch_id INTEGER REFERENCES receiver_epochs(id),
        tx_call TEXT NOT NULL,
        tx_grid TEXT,
        band TEXT NOT NULL,
        freq REAL,
        snr INTEGER NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE receiver_hourly_stats (
        epoch_id INTEGER REFERENCES receiver_epochs(id),
        date_str TEXT NOT NULL,
        utc_hour INTEGER NOT NULL,
        band TEXT NOT NULL,
        unique_tx_count INTEGER NOT NULL DEFAULT 0,
        total_spots INTEGER NOT NULL DEFAULT 0,
        median_snr REAL,
        PRIMARY KEY(epoch_id, date_str, utc_hour, band)
    );
    """
]

class Database:
    def __init__(self, db_path="ft8spotter.db"):
        self.db_path = db_path
        self._initialize_db()

    def get_connection(self):
        """Returns a configured connection suitable for the current thread."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        # Return dict-like rows for convenience
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        """Creates the DB, checks current version, runs missing migrations."""
        if not os.path.exists(self.db_path):
            logger.info("Creating new database.")
            
        with self.get_connection() as conn:
            # Check if schema_migrations table exists
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            has_migrations = cur.fetchone() is not None
            
            current_version = 0
            if has_migrations:
                cur.execute("SELECT MAX(version) FROM schema_migrations")
                row = cur.fetchone()
                if row and row[0] is not None:
                    current_version = row[0]

            logger.info(f"Current DB Version: {current_version}")
            
            # Apply pending migrations
            for idx, sql_script in enumerate(MIGRATIONS):
                target_version = idx + 1
                if target_version > current_version:
                    self._apply_migration(conn, target_version, sql_script)

    def _apply_migration(self, conn, version: int, sql_script: str):
        """Applies a single migration within a transaction and backs up beforehand if not v1."""
        if version > 1:
            self._backup_db(f"v{version-1}_pre_migration")
            
        logger.info(f"Applying Migration v{version}...")
        try:
            with conn: # Transaction block
                conn.executescript(sql_script)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
            logger.info(f"Migration v{version} successful.")
        except Exception as e:
            logger.error(f"Migration v{version} failed! Rolling back.")
            raise e

    def _backup_db(self, tag: str):
        """Safely creates a backup copy of the database."""
        backup_path = f"{self.db_path}.{tag}.bak"
        logger.info(f"Backing up database to {backup_path}")
        try:
            # Since WAL mode is used, standard file copy is safe enough for backup
            # prior to migration (assuming no other active writers during startup).
            shutil.copy2(self.db_path, backup_path)
            # Copy WAL and SHM if they exist
            if os.path.exists(f"{self.db_path}-wal"):
                shutil.copy2(f"{self.db_path}-wal", f"{backup_path}-wal")
            if os.path.exists(f"{self.db_path}-shm"):
                shutil.copy2(f"{self.db_path}-shm", f"{backup_path}-shm")
        except Exception as e:
            logger.error(f"Backup failed: {e}")

    def batch_insert_spots(self, spots: List[Dict]):
        """Efficiently inserts a batch of spots, managing receiver epochs on the fly."""
        if not spots:
            return
            
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Upsert Epochs
            # We first try to select existing epochs, and insert those that don't exist.
            # Using IGNORE on conflict requires INSERT OR IGNORE, which is SQLite specific.
            epochs = {(s['rx_call'], s['rx_grid']) for s in spots if s.get('rx_grid')}
            
            for rx_call, locator in epochs:
                cur.execute('''
                    INSERT OR IGNORE INTO receiver_epochs (callsign, locator, first_seen, last_seen)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (rx_call, locator))
                
                # Update last_seen
                cur.execute('''
                    UPDATE receiver_epochs 
                    SET last_seen = CURRENT_TIMESTAMP 
                    WHERE callsign = ? AND locator = ?
                ''', (rx_call, locator))
                
            # Pre-fetch epoch IDs to avoid a query per spot
            cur.execute("SELECT id, callsign, locator FROM receiver_epochs")
            epoch_map = {(row['callsign'], row['locator']): row['id'] for row in cur.fetchall()}
            
            # 2. Insert Raw Spots
            spot_tuples = []
            for s in spots:
                if not s.get('rx_grid'): continue
                epoch_id = epoch_map.get((s['rx_call'], s['rx_grid']))
                if epoch_id:
                    spot_tuples.append((
                        epoch_id, s['tx_call'], s['tx_grid'], s['band'], s.get('freq'), s['snr']
                    ))
                    
            if spot_tuples:
                cur.executemany('''
                    INSERT INTO receiver_raw_spots (epoch_id, tx_call, tx_grid, band, freq, snr)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', spot_tuples)
