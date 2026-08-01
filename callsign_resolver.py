class CallsignResolver:
    def __init__(self):
        pass

    def get_us_state_from_grid(self, grid: str) -> str:
        """
        A very coarse estimation of US states based on Maidenhead Grid Squares.
        Because grids span across state lines, this is not 100% accurate without an API.
        """
        if not grid or len(grid) < 4:
            return ""
            
        grid4 = grid[:4].upper()
        
        # Extremely coarse mapping for demonstration
        # True implementations use coordinate bounding boxes
        state_map = {
            'FN44': 'ME', 'FN54': 'ME', 'FN34': 'NH', 'FN43': 'NH',
            'FN33': 'MA', 'FN41': 'MA', 'FN31': 'CT', 'FN32': 'CT',
            'FN21': 'NY', 'FN22': 'NY', 'FN23': 'NY', 'FN30': 'NY',
            'FM29': 'NJ', 'FN20': 'NJ', 'FM19': 'MD', 'FM28': 'MD',
            'FM18': 'VA', 'FM08': 'VA', 'EM96': 'NC', 'FM05': 'NC',
            'EM83': 'SC', 'EM93': 'SC', 'EM73': 'GA', 'EM83': 'GA',
            'EM90': 'FL', 'EL99': 'FL', 'EL98': 'FL', 'EL89': 'FL',
            'EM78': 'KY', 'EM87': 'KY', 'EM65': 'TN', 'EM75': 'TN',
            'EM63': 'AL', 'EM64': 'AL', 'EM52': 'MS', 'EM53': 'MS',
            'EM44': 'AR', 'EM45': 'AR', 'EM31': 'LA', 'EM41': 'LA',
            'EM20': 'TX', 'EM10': 'TX', 'EM00': 'TX', 'DM90': 'TX',
            'EM25': 'OK', 'EM15': 'OK', 'EM27': 'KS', 'EM17': 'KS',
            'EM28': 'NE', 'EM18': 'NE', 'EN21': 'SD', 'EN11': 'SD',
            'EN23': 'ND', 'EN13': 'ND', 'EN34': 'MN', 'EN24': 'MN',
            'EN42': 'WI', 'EN52': 'WI', 'EN41': 'IL', 'EN51': 'IL',
            'EN62': 'MI', 'EN72': 'MI', 'EN70': 'IN', 'EN60': 'IN',
            'EN80': 'OH', 'EN90': 'OH', 'EN91': 'PA', 'FN01': 'PA',
            'DM43': 'AZ', 'DM33': 'AZ', 'DM65': 'NM', 'DM55': 'NM',
            'DM69': 'CO', 'DM79': 'CO', 'DN71': 'WY', 'DN61': 'WY',
            'DN35': 'ID', 'DN45': 'ID', 'DN40': 'UT', 'DN30': 'UT',
            'DM14': 'CA', 'DM04': 'CA', 'CM97': 'CA', 'CM87': 'CA',
            'CN84': 'OR', 'CN94': 'OR', 'CN87': 'WA', 'CN97': 'WA',
        }
        return state_map.get(grid4, "")
        
    def resolve(self, callsign: str, grid: str) -> dict:
        info = {
            'state': self.get_us_state_from_grid(grid),
            'country': 'Unknown'
        }
        
        # Basic Prefix Country mapping
        call_upper = callsign.upper()
        if call_upper.startswith('K') or call_upper.startswith('W') or call_upper.startswith('N') or call_upper.startswith('A'):
            info['country'] = 'United States'
        elif call_upper.startswith('VE') or call_upper.startswith('VA') or call_upper.startswith('VY'):
            info['country'] = 'Canada'
        elif call_upper.startswith('M') or call_upper.startswith('G') or call_upper.startswith('2E'):
            info['country'] = 'England'
        elif call_upper.startswith('VK'):
            info['country'] = 'Australia'
        elif call_upper.startswith('ZL'):
            info['country'] = 'New Zealand'
        elif call_upper.startswith('JA') or call_upper.startswith('JH') or call_upper.startswith('JR'):
            info['country'] = 'Japan'
        elif call_upper.startswith('PY') or call_upper.startswith('PR') or call_upper.startswith('PP') or call_upper.startswith('PU'):
            info['country'] = 'Brazil'
        elif call_upper.startswith('LU') or call_upper.startswith('LW'):
            info['country'] = 'Argentina'
        elif call_upper.startswith('CE') or call_upper.startswith('CA'):
            info['country'] = 'Chile'
        elif call_upper.startswith('EA') or call_upper.startswith('EB') or call_upper.startswith('EC'):
            info['country'] = 'Spain'
        elif call_upper.startswith('I') or call_upper.startswith('IK') or call_upper.startswith('IZ'):
            info['country'] = 'Italy'
        elif call_upper.startswith('F') or call_upper.startswith('TM'):
            info['country'] = 'France'
        elif call_upper.startswith('D'):
            info['country'] = 'Fed. Rep. of Germany'
        elif call_upper.startswith('PA') or call_upper.startswith('PB') or call_upper.startswith('PD'):
            info['country'] = 'Netherlands'
        elif call_upper.startswith('ZS') or call_upper.startswith('ZR'):
            info['country'] = 'South Africa'
        elif call_upper.startswith('VU'):
            info['country'] = 'India'
        elif call_upper.startswith('XE'):
            info['country'] = 'Mexico'
            
        return info
