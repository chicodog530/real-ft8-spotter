import math
from typing import List, Dict

class LikelihoodEngineV2:
    def __init__(self, db_conn):
        self.db = db_conn
        
        # Transparent weights based on Phase 2 specification
        self.weights = {
            'consensus': 0.25,
            'similarity': 0.20,
            'snr': 0.15,
            'recency': 0.12,
            'path': 0.10,
            'regional': 0.08,
            'user_history': 0.05,
            'context': 0.03,
            'terrain': 0.02
        }

    def calculate_hear_likelihood(self, target_call: str, band: str, raw_spots: List[Dict]) -> Dict:
        """
        Calculates the probability that the local user can decode target_call on the specified band.
        Returns a dictionary containing the score (0-100), confidence level, and a plain-text explanation.
        """
        score = 0.0
        explanations = []
        
        # 1. Receiver Consensus (25%)
        # Count independent unique reporting receivers
        unique_rx = {s['rx_call'] for s in raw_spots}
        rx_count = len(unique_rx)
        
        # Saturating curve for consensus: 1 rx = low, 5 rx = max
        consensus_score = min(1.0, rx_count / 5.0)
        score += consensus_score * self.weights['consensus']
        explanations.append(f"Heard by {rx_count} independent receivers near you.")
        
        # 2. Normalized SNR (15%)
        avg_snr = sum(s['snr'] for s in raw_spots) / len(raw_spots) if raw_spots else -30
        snr_score = max(0.0, min(1.0, (avg_snr + 25) / 25)) # Scale -25 (0%) to 0+ (100%)
        score += snr_score * self.weights['snr']
        
        # 3. Recency & Persistence (12%)
        # (Mock implementation for scaffolding)
        score += 1.0 * self.weights['recency']
        
        # 4. Path & Bearing Similarity (10%)
        # (Mock implementation for scaffolding)
        score += 0.8 * self.weights['path']
        
        # 5. User/Receiver Similarity (20%)
        # (Mock implementation - requires historical DB cross-referencing)
        score += 0.5 * self.weights['similarity']
        
        # Produce Final Values
        final_score = int(score * 100)
        
        confidence = "Low"
        if rx_count >= 3:
            confidence = "Medium"
        if rx_count >= 5 and final_score > 50:
            confidence = "High"
            
        return {
            'hear_score': final_score,
            'confidence': confidence,
            'explanation': " ".join(explanations)
        }
