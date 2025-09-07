#!/usr/bin/env python3
"""
Attack Map API Class
Provides API methods for attack map data visualization
"""

from attack_map_parser import AttackMapParser
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)













class AttackMapAPI:
    """Attack Map API class for direct access to attack data"""
    
    def __init__(self):
        self.parser = AttackMapParser()
    
    def get_attacks(self, time_range=24, attack_type=None, severity=None, country=None):
        """Get attacks with filters"""
        try:
            attacks = self.parser.get_recent_attacks(hours=time_range, limit=1000)
            
            # Apply filters
            if attack_type:
                attacks = [a for a in attacks if a.get('attack_type') == attack_type]
            if severity:
                attacks = [a for a in attacks if a.get('severity') == severity]
            if country:
                attacks = [a for a in attacks if a.get('country') == country]
            
            return attacks
        except Exception as e:
            logger.error(f"Error getting attacks: {e}")
            return []
    
    def get_latest_attacks(self, limit=10):
        """Get latest attacks"""
        try:
            return self.parser.get_recent_attacks(hours=1, limit=limit)
        except Exception as e:
            logger.error(f"Error getting latest attacks: {e}")
            return []
    
    def get_attack_statistics(self, time_range=24):
        """Get attack statistics"""
        try:
            attacks = self.parser.get_recent_attacks(hours=time_range, limit=5000)
            
            # Calculate statistics
            total_attacks = len(attacks)
            attack_types = {}
            severities = {}
            countries = {}
            
            for attack in attacks:
                # Count attack types
                attack_type = attack.get('attack_type', 'Unknown')
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
                
                # Count severities
                severity = attack.get('severity', 'Unknown')
                severities[severity] = severities.get(severity, 0) + 1
                
                # Count countries
                country = attack.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
            
            return {
                'total_attacks': total_attacks,
                'attack_types': attack_types,
                'severities': severities,
                'top_countries': dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        except Exception as e:
            logger.error(f"Error getting attack statistics: {e}")
            return {
                'total_attacks': 0,
                'attack_types': {},
                'severities': {},
                'top_countries': {}
            }
    
    def get_country_statistics(self, time_range=24):
        """Get country-specific statistics"""
        try:
            attacks = self.parser.get_recent_attacks(hours=time_range, limit=5000)
            
            countries = {}
            for attack in attacks:
                country = attack.get('country', 'Unknown')
                if country not in countries:
                    countries[country] = {
                        'count': 0,
                        'severities': {},
                        'attack_types': {}
                    }
                
                countries[country]['count'] += 1
                
                severity = attack.get('severity', 'Unknown')
                countries[country]['severities'][severity] = countries[country]['severities'].get(severity, 0) + 1
                
                attack_type = attack.get('attack_type', 'Unknown')
                countries[country]['attack_types'][attack_type] = countries[country]['attack_types'].get(attack_type, 0) + 1
            
            return countries
        except Exception as e:
            logger.error(f"Error getting country statistics: {e}")
            return {}
    
    def get_recent_attacks(self, limit=50, since_timestamp=None):
        """Get recent attacks for arrow animation"""
        try:
            if since_timestamp:
                # Convert timestamp string to datetime for filtering
                from datetime import datetime
                since_dt = datetime.strptime(since_timestamp, '%Y-%m-%d %H:%M:%S')
                hours_back = (datetime.now() - since_dt).total_seconds() / 3600
                attacks = self.parser.get_recent_attacks(hours=max(1, hours_back), limit=limit)
                
                # Filter by timestamp
                filtered_attacks = []
                for attack in attacks:
                    attack_dt = datetime.strptime(attack['timestamp'], '%Y-%m-%d %H:%M:%S')
                    if attack_dt >= since_dt:
                        filtered_attacks.append(attack)
                
                return filtered_attacks[:limit]
            else:
                # Get recent attacks from last hour
                return self.parser.get_recent_attacks(hours=1, limit=limit)
                
        except Exception as e:
            logger.error(f"Error getting recent attacks: {e}")
            return []