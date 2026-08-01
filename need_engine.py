from typing import Dict, Tuple

class NeedEngine:
    def __init__(self, db_conn):
        self.db = db_conn

    def evaluate_need(self, callsign: str, dxcc: int, grid: str, band: str, mode: str = 'FT8') -> Tuple[int, str]:
        """
        Cross-references a target against the ADIF logbook to determine its Need Value.
        Returns a tuple of (Need Value 0-100, Plain English Explanation).
        """
        # Scaffold: In a full implementation, this queries the SQLite `qsos` table.
        # It would check for Worked All States (WAS), DXCC, VUCC (Grids), etc.
        
        need_score = 0
        explanation = ""
        
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Check if completely new Callsign
            cur.execute("SELECT COUNT(*) FROM qsos WHERE callsign = ?", (callsign,))
            if cur.fetchone()[0] == 0:
                need_score = max(need_score, 80)
                explanation = f"New Callsign {callsign}"
                
            # 2. Check DXCC
            if dxcc:
                cur.execute("SELECT COUNT(*) FROM qsos WHERE dxcc = ?", (dxcc,))
                if cur.fetchone()[0] == 0:
                    need_score = max(need_score, 100)
                    explanation = f"All-Time New DXCC Entity!"
                else:
                    cur.execute("SELECT COUNT(*) FROM qsos WHERE dxcc = ? AND band = ?", (dxcc, band))
                    if cur.fetchone()[0] == 0:
                        need_score = max(need_score, 90)
                        explanation = f"New DXCC on {band}"

            # 3. Check Grid (VUCC)
            if grid and len(grid) >= 4:
                grid4 = grid[:4].upper()
                cur.execute("SELECT COUNT(*) FROM qsos WHERE gridsquare LIKE ?", (f"{grid4}%",))
                if cur.fetchone()[0] == 0:
                    need_score = max(need_score, 65)
                    if not explanation:
                        explanation = f"New Grid Square {grid4}"

        if need_score == 0:
            explanation = "Previously Worked"
            
        return need_score, explanation

    def evaluate_state_need(self, state: str, band: str) -> bool:
        if not state:
            return False
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM qsos WHERE state = ?", (state,))
            if cur.fetchone()[0] == 0:
                return True
            cur.execute("SELECT COUNT(*) FROM qsos WHERE state = ? AND band = ?", (state, band))
            return cur.fetchone()[0] == 0
            
    def evaluate_country_need(self, country: str, band: str) -> bool:
        if not country or country == 'Unknown':
            return False
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM qsos WHERE country = ?", (country,))
            if cur.fetchone()[0] == 0:
                return True
            cur.execute("SELECT COUNT(*) FROM qsos WHERE country = ? AND band = ?", (country, band))
            return cur.fetchone()[0] == 0

    def calculate_opportunity_priority(self, hear_likelihood: int, work_likelihood: int, need_value: int) -> int:
        """
        Combines propagation likelihood with logbook need into a single ranking value.
        Opportunity Priority = Hear Likelihood × Work Likelihood × Need Value
        """
        # Normalize weights
        # If work_likelihood is unknown, we weight hear_likelihood heavier
        wl = work_likelihood if work_likelihood > 0 else 50
        
        priority = (hear_likelihood / 100.0) * (wl / 100.0) * (need_value / 100.0)
        return int(priority * 100)
