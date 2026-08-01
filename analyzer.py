import math

def freq_to_band(frequency_hz):
    freq_mhz = int(frequency_hz) / 1000000.0
    if 1.8 <= freq_mhz <= 2.0: return "160m"
    if 3.5 <= freq_mhz <= 4.0: return "80m"
    if 5.33 <= freq_mhz <= 5.41: return "60m"
    if 7.0 <= freq_mhz <= 7.3: return "40m"
    if 10.1 <= freq_mhz <= 10.15: return "30m"
    if 14.0 <= freq_mhz <= 14.35: return "20m"
    if 18.068 <= freq_mhz <= 18.168: return "17m"
    if 21.0 <= freq_mhz <= 21.45: return "15m"
    if 24.89 <= freq_mhz <= 24.99: return "12m"
    if 28.0 <= freq_mhz <= 29.7: return "10m"
    if 50.0 <= freq_mhz <= 54.0: return "6m"
    return "Unknown"

def deduplicate_spots(spots):
    # deduplicate by tx_call, rx_call, and band
    # keeping the strongest SNR
    seen = {}
    for s in spots:
        key = (s['tx_call'], s['rx_call'], s['band'])
        if key not in seen:
            seen[key] = s
        else:
            if int(s['snr']) > int(seen[key]['snr']):
                seen[key] = s
    return list(seen.values())

def filter_spots(spots, min_dx_distance=1500, max_age_seconds=600, current_time=None):
    filtered = []
    for s in spots:
        if s['dist_to_tx'] >= min_dx_distance:
            filtered.append(s)
    return filtered

def score_dx(filtered_spots, likelihood_engine=None, need_engine=None, pota_engine=None):
    from callsign_resolver import CallsignResolver
    resolver = CallsignResolver()
    
    # Group spots by tx_call and band
    scoring = {}
    for s in filtered_spots:
        key = (s['tx_call'], s['band'])
        if key not in scoring:
            scoring[key] = {
                'tx_call': s['tx_call'],
                'band': s['band'],
                'receivers': set(),
                'spots': []
            }
        scoring[key]['receivers'].add(s['rx_call'])
        scoring[key]['spots'].append(s)
    
    results = []
    for key, data in scoring.items():
        if likelihood_engine and need_engine:
            # Use V2 Engines
            lik_result = likelihood_engine.calculate_hear_likelihood(data['tx_call'], data['band'], data['spots'])
            # Assuming grid is empty for now unless we look it up
            need_val, need_exp = need_engine.evaluate_need(data['tx_call'], 0, "", data['band'])
            priority = need_engine.calculate_opportunity_priority(lik_result['hear_score'], 50, need_val)
            
            data['likelihood'] = f"{lik_result['hear_score']}%"
            data['confidence'] = lik_result['confidence']
            data['need_val'] = need_val
            data['need_exp'] = need_exp
            data['priority'] = priority
            data['is_pota'] = pota_engine.is_pota(data['tx_call']) if pota_engine else False
            
            # Resolve additional flags
            grid_to_use = data['spots'][0].get('tx_grid', '')
            info = resolver.resolve(data['tx_call'], grid_to_use)
            data['state'] = info['state']
            data['country'] = info['country']
            
            data['is_new_state'] = need_engine.evaluate_state_need(info['state'], data['band']) if info['state'] else False
            data['is_new_country'] = need_engine.evaluate_country_need(info['country'], data['band']) if info['country'] else False
            
        else:
            # Fallback for tests
            rx_count = len(data['receivers'])
            avg_snr = sum(int(s['snr']) for s in data['spots']) / rx_count
            data['likelihood'] = f"{rx_count * 10}%"
            data['confidence'] = "Low"
            data['need_val'] = 0
            data['need_exp'] = "Fallback"
            data['priority'] = int(rx_count * 10 + avg_snr)
            data['is_pota'] = False
            
        data['rx_count'] = len(data['receivers'])
        results.append(data)
        
    results.sort(key=lambda x: x['priority'], reverse=True)
    return results
