#!/usr/bin/env python3
"""
ModSecurity Attack Map Parser
Parses ModSecurity audit logs and extracts attack data for visualization
"""

import re
import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttackMapParser:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use absolute path in plugin directory
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(plugin_dir, "data", "attack_map.db")
        self.db_path = db_path
        self.init_database()
        
        # Common attack patterns
        self.attack_patterns = {
            'sql_injection': [r'union.*select', r'or.*1=1', r'drop.*table', r'insert.*into'],
            'xss': [r'<script', r'javascript:', r'onerror=', r'onload='],
            'lfi': [r'\.\./\.\./\.\./etc/passwd', r'file://', r'php://'],
            'rfi': [r'http://.*\.(txt|php)', r'https://.*\.(txt|php)'],
            'command_injection': [r';.*cat', r'\|.*ls', r'&&.*whoami', r'`.*id`'],
            'directory_traversal': [r'\.\./\.\./\.\./'],
            'brute_force': [r'wp-login\.php', r'admin/login', r'/login'],
            'scanner': [r'nikto', r'nmap', r'sqlmap', r'dirb']
        }
    
    def init_database(self):
        """Initialize SQLite database for storing attack data"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                source_ip TEXT,
                country TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                attack_type TEXT,
                severity TEXT,
                target_url TEXT,
                user_agent TEXT,
                rule_id TEXT,
                rule_msg TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON attacks(timestamp);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_ip ON attacks(source_ip);
        ''')
        
        conn.commit()
        conn.close()
    
    def get_geolocation(self, ip: str) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
        """Get geolocation data for IP address using free API"""
        try:
            # Using ip-api.com (free tier: 1000 requests/month)
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return data.get('country'), data.get('city'), data.get('lat'), data.get('lon')
        except Exception as e:
            logger.warning(f"Failed to get geolocation for {ip}: {e}")
        
        return None, None, None, None
    
    def classify_attack(self, request_data: str, rule_msg: str = "") -> str:
        """Classify attack type based on request data and rule message"""
        request_lower = request_data.lower()
        rule_lower = rule_msg.lower()
        
        # Check rule message first (more accurate)
        if any(keyword in rule_lower for keyword in ['sql', 'injection']):
            return 'sql_injection'
        elif any(keyword in rule_lower for keyword in ['xss', 'script', 'javascript']):
            return 'xss'
        elif any(keyword in rule_lower for keyword in ['file', 'inclusion', 'traversal']):
            return 'lfi'
        elif any(keyword in rule_lower for keyword in ['command', 'execution']):
            return 'command_injection'
        elif any(keyword in rule_lower for keyword in ['scanner', 'bot']):
            return 'scanner'
        
        # Fallback to pattern matching
        for attack_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request_lower, re.IGNORECASE):
                    return attack_type
        
        return 'unknown'
    
    def parse_modsec_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single ModSecurity audit log line"""
        try:
            # ModSecurity audit log format parsing
            # Look for key components: timestamp, IP, rule info
            
            # Extract timestamp
            timestamp_match = re.search(r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})', line)
            if not timestamp_match:
                return None
            
            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S')
            
            # Extract source IP
            ip_match = re.search(r'client: ([\d\.]+)', line)
            if not ip_match:
                ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', line)
            
            if not ip_match:
                return None
            
            source_ip = ip_match.group(1)
            
            # Extract rule information
            rule_id_match = re.search(r'\[id "(\d+)"\]', line)
            rule_id = rule_id_match.group(1) if rule_id_match else 'unknown'
            
            rule_msg_match = re.search(r'\[msg "([^"]+)"\]', line)
            rule_msg = rule_msg_match.group(1) if rule_msg_match else ''
            
            # Extract target URL
            url_match = re.search(r'"(?:GET|POST|PUT|DELETE) ([^"\s]+)', line)
            target_url = url_match.group(1) if url_match else '/'
            
            # Extract User-Agent
            ua_match = re.search(r'User-Agent: ([^\r\n]+)', line)
            user_agent = ua_match.group(1) if ua_match else ''
            
            # Determine severity based on rule ID ranges (common ModSecurity convention)
            severity = 'medium'
            if rule_id.isdigit():
                rule_num = int(rule_id)
                if rule_num >= 950000 and rule_num < 960000:
                    severity = 'high'  # Protocol violations
                elif rule_num >= 960000 and rule_num < 970000:
                    severity = 'critical'  # Application attacks
                elif rule_num >= 970000 and rule_num < 980000:
                    severity = 'high'  # Data leakages
            
            # Classify attack type
            attack_type = self.classify_attack(line, rule_msg)
            
            return {
                'timestamp': timestamp,
                'source_ip': source_ip,
                'attack_type': attack_type,
                'severity': severity,
                'target_url': target_url,
                'user_agent': user_agent,
                'rule_id': rule_id,
                'rule_msg': rule_msg
            }
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None
    
    def process_log_file(self, log_file_path: str, max_lines: int = 1000):
        """Process ModSecurity log file and extract attack data"""
        if not Path(log_file_path).exists():
            logger.error(f"Log file not found: {log_file_path}")
            return
        
        processed_count = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    if processed_count >= max_lines:
                        break
                    
                    attack_data = self.parse_modsec_log_line(line.strip())
                    if attack_data:
                        # Get geolocation data
                        country, city, lat, lon = self.get_geolocation(attack_data['source_ip'])
                        
                        # Insert into database
                        cursor.execute('''
                            INSERT INTO attacks 
                            (timestamp, source_ip, country, city, latitude, longitude, 
                             attack_type, severity, target_url, user_agent, rule_id, rule_msg)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            attack_data['timestamp'],
                            attack_data['source_ip'],
                            country,
                            city,
                            lat,
                            lon,
                            attack_data['attack_type'],
                            attack_data['severity'],
                            attack_data['target_url'],
                            attack_data['user_agent'],
                            attack_data['rule_id'],
                            attack_data['rule_msg']
                        ))
                        
                        processed_count += 1
                        
                        if processed_count % 100 == 0:
                            conn.commit()
                            logger.info(f"Processed {processed_count} attacks")
            
            conn.commit()
            logger.info(f"Successfully processed {processed_count} attacks from {log_file_path}")
            
        except Exception as e:
            logger.error(f"Error processing log file: {e}")
        finally:
            conn.close()
    
    def get_recent_attacks(self, hours: int = 24, limit: int = 1000) -> List[Dict]:
        """Get recent attacks from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT timestamp, source_ip, country, city, latitude, longitude,
                   attack_type, severity, target_url, rule_msg,
                   target_ip, target_country, target_city, target_latitude, target_longitude
            FROM attacks 
            WHERE timestamp >= ? AND latitude IS NOT NULL AND longitude IS NOT NULL
                  AND target_ip IS NOT NULL AND target_latitude IS NOT NULL AND target_longitude IS NOT NULL
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (since, limit))
        
        attacks = []
        for row in cursor.fetchall():
            attacks.append({
                'timestamp': row[0],
                'source_ip': row[1],
                'country': row[2],
                'city': row[3],
                'latitude': row[4],
                'longitude': row[5],
                'attack_type': row[6],
                'severity': row[7],
                'target_url': row[8],
                'rule_msg': row[9],
                'target_ip': row[10],
                'target_country': row[11],
                'target_city': row[12],
                'target_latitude': row[13],
                'target_longitude': row[14]
            })
        
        conn.close()
        return attacks
    
    def get_attack_stats(self, hours: int = 24) -> Dict:
        """Get attack statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        # Total attacks
        cursor.execute('SELECT COUNT(*) FROM attacks WHERE timestamp >= ?', (since,))
        total_attacks = cursor.fetchone()[0]
        
        # Attacks by type
        cursor.execute('''
            SELECT attack_type, COUNT(*) 
            FROM attacks 
            WHERE timestamp >= ? 
            GROUP BY attack_type 
            ORDER BY COUNT(*) DESC
        ''', (since,))
        attacks_by_type = dict(cursor.fetchall())
        
        # Attacks by country
        cursor.execute('''
            SELECT country, COUNT(*) 
            FROM attacks 
            WHERE timestamp >= ? AND country IS NOT NULL 
            GROUP BY country 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''', (since,))
        attacks_by_country = dict(cursor.fetchall())
        
        # Top attacking IPs
        cursor.execute('''
            SELECT source_ip, COUNT(*) 
            FROM attacks 
            WHERE timestamp >= ? 
            GROUP BY source_ip 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''', (since,))
        top_ips = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_attacks': total_attacks,
            'attacks_by_type': attacks_by_type,
            'attacks_by_country': attacks_by_country,
            'top_attacking_ips': top_ips,
            'period_hours': hours
        }

if __name__ == '__main__':
    # Example usage
    parser = AttackMapParser()
    
    # Process sample log file if it exists
    log_files = [
        '/var/log/nginx/modsec_audit.log',
        '/var/log/modsec_audit.log',
        '/etc/nginx/logs/modsec_audit.log'
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            print(f"Processing {log_file}...")
            parser.process_log_file(log_file, max_lines=500)
            break
    else:
        print("No ModSecurity log files found. Creating sample data...")
        # Create some sample data for testing
        conn = sqlite3.connect(parser.db_path)
        cursor = conn.cursor()
        
        sample_attacks = [
            ('2024-01-15 10:30:00', '192.168.1.100', 'Indonesia', 'Jakarta', -6.2088, 106.8456, 'sql_injection', 'high', '/admin/login.php', 'SQL Injection Attempt'),
            ('2024-01-15 10:31:00', '203.0.113.1', 'United States', 'New York', 40.7128, -74.0060, 'xss', 'medium', '/search.php', 'XSS Attack Detected'),
            ('2024-01-15 10:32:00', '198.51.100.1', 'Russia', 'Moscow', 55.7558, 37.6176, 'scanner', 'low', '/', 'Automated Scanner Detected')
        ]
        
        for attack in sample_attacks:
            cursor.execute('''
                INSERT INTO attacks 
                (timestamp, source_ip, country, city, latitude, longitude, attack_type, severity, target_url, rule_msg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', attack)
        
        conn.commit()
        conn.close()
        print("Sample data created.")
    
    # Show statistics
    stats = parser.get_attack_stats(24)
    print(f"\nAttack Statistics (last 24 hours):")
    print(f"Total attacks: {stats['total_attacks']}")
    print(f"Attacks by type: {stats['attacks_by_type']}")
    print(f"Top countries: {stats['attacks_by_country']}")