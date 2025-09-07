#!/usr/bin/env python3
"""
WAF Log Parser - Parse ModSecurity logs and add to Attack Map database
"""

import re
import sqlite3
import subprocess
from datetime import datetime
from typing import List, Dict
import os

class WAFLogParser:
    def __init__(self, db_path=None):
        if db_path is None:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(plugin_dir, 'data', 'attack_map.db')
        
        self.db_path = db_path
        self.position_file = os.path.join(os.path.dirname(db_path), 'log_positions.txt')
        self.init_database()
        self.init_position_tracking()
    
    def init_database(self):
        """Initialize the database with attacks table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if table exists and has the correct structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attacks'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE attacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    source_ip TEXT,
                    target_ip TEXT,
                    country TEXT,
                    city TEXT,
                    latitude REAL,
                    longitude REAL,
                    attack_type TEXT,
                    severity TEXT,
                    target_url TEXT,
                    rule_msg TEXT,
                    target_country TEXT,
                    target_city TEXT,
                    target_latitude REAL,
                    target_longitude REAL
                )
            ''')
            
            cursor.execute('CREATE INDEX idx_timestamp ON attacks(timestamp)')
            cursor.execute('CREATE INDEX idx_source_ip ON attacks(source_ip)')
            cursor.execute('CREATE INDEX idx_target_ip ON attacks(target_ip)')
        
        conn.commit()
        conn.close()
    
    def init_position_tracking(self):
        """Initialize position tracking for incremental parsing"""
        if not os.path.exists(self.position_file):
            with open(self.position_file, 'w') as f:
                f.write('{}')
    
    def get_file_position(self, log_file_path):
        """Get last processed position for a log file"""
        try:
            with open(self.position_file, 'r') as f:
                positions = eval(f.read() or '{}')
                return positions.get(log_file_path, 0)
        except:
            return 0
    
    def save_file_position(self, log_file_path, position):
        """Save last processed position for a log file"""
        try:
            positions = {}
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    positions = eval(f.read() or '{}')
            
            positions[log_file_path] = position
            
            with open(self.position_file, 'w') as f:
                f.write(str(positions))
        except Exception as e:
            print(f"Error saving position: {e}")
    
    def process_log_file_incremental(self, log_file_path, max_lines=None):
        """Process only new entries from log file since last check"""
        if not os.path.exists(log_file_path):
            return 0
        
        # Get current file size and last position
        current_size = os.path.getsize(log_file_path)
        last_position = self.get_file_position(log_file_path)
        
        # Check if file was rotated (smaller than last position)
        if current_size < last_position:
            print(f"Log file {log_file_path} was rotated, resetting position")
            last_position = 0
        
        # No new data
        if current_size <= last_position:
            return 0
        
        attacks = []
        processed_lines = 0
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to last position
                f.seek(last_position)
                
                for line in f:
                    if max_lines and processed_lines >= max_lines:
                        break
                    
                    line = line.strip()
                    if line:
                        try:
                            attack_data = self.parse_modsec_log_line(line)
                            if attack_data:
                                attacks.append(attack_data)
                                processed_lines += 1
                        except Exception as e:
                            print(f"Error parsing line: {e}")
                            continue
                
                # Save current position
                new_position = f.tell()
                self.save_file_position(log_file_path, new_position)
        
        except Exception as e:
            print(f"Error processing log file {log_file_path}: {e}")
            return 0
        
        # Save attacks to database
        if attacks:
            self.save_attacks_to_db(attacks)
        
        return len(attacks)
    
    def parse_modsec_log_line(self, log_line: str) -> Dict:
        """Parse a single ModSecurity log line"""
        # Extract timestamp
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})', log_line)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if timestamp_match:
            try:
                timestamp = datetime.strptime(timestamp_match.group(1), '%Y/%m/%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Extract client IP (attacker)
        client_match = re.search(r'client: ([\d\.]+)', log_line)
        source_ip = client_match.group(1) if client_match else 'Unknown'
        
        # Extract target IP (server/local IP)
        # Try multiple patterns for target IP extraction
        target_ip = self.extract_target_ip(log_line)
        
        # Extract URI
        uri_match = re.search(r'\[uri "([^"]+)"\]', log_line)
        target_url = uri_match.group(1) if uri_match else '/'
        
        # Extract rule ID
        rule_id_match = re.search(r'\[id "([^"]+)"\]', log_line)
        rule_id = rule_id_match.group(1) if rule_id_match else 'Unknown'
        
        # Extract rule message
        msg_match = re.search(r'\[msg "([^"]+)"\]', log_line)
        rule_msg = msg_match.group(1) if msg_match else 'ModSecurity Rule Triggered'
        
        # Extract HTTP method
        method_match = re.search(r'request: "(\w+)', log_line)
        method = method_match.group(1) if method_match else 'GET'
        
        # Determine attack type based on rule ID and message
        attack_type = self.determine_attack_type(rule_id, rule_msg)
        
        # Determine severity
        severity = self.determine_severity(rule_id, rule_msg)
        
        # Get attacker location (source)
        country = self.get_country_from_ip(source_ip)
        city, latitude, longitude = self.get_location_from_ip(source_ip)
        
        # Get target location (destination)
        target_country = self.get_country_from_ip(target_ip)
        target_city, target_latitude, target_longitude = self.get_location_from_ip(target_ip)
        
        return {
            'timestamp': timestamp,
            'source_ip': source_ip,
            'target_ip': target_ip,
            'target_url': target_url,
            'attack_type': attack_type,
            'severity': severity,
            'rule_msg': rule_msg,
            'country': country,
            'city': city,
            'latitude': latitude,
            'longitude': longitude,
            'target_country': target_country,
            'target_city': target_city,
            'target_latitude': target_latitude,
            'target_longitude': target_longitude
        }
    
    def extract_target_ip(self, log_line: str) -> str:
        """Extract target IP from ModSecurity log line"""
        # Try multiple patterns to extract target/server IP
        
        # Pattern 1: server IP in nginx error log format
        server_match = re.search(r'server: ([\d\.]+)', log_line)
        if server_match:
            return server_match.group(1)
        
        # Pattern 2: Host header (common target)
        host_match = re.search(r'Host: ([\d\.]+)', log_line)
        if host_match:
            return host_match.group(1)
        
        # Pattern 3: X-Forwarded-For or similar headers
        forwarded_match = re.search(r'X-Forwarded-For: ([\d\.]+)', log_line)
        if forwarded_match:
            return forwarded_match.group(1)
        
        # Pattern 4: Extract from request line (GET http://IP/path)
        request_match = re.search(r'request: "\w+ https?://([\d\.]+)', log_line)
        if request_match:
            return request_match.group(1)
        
        # Pattern 5: Extract from nginx upstream or proxy
        upstream_match = re.search(r'upstream: "([\d\.]+)', log_line)
        if upstream_match:
            return upstream_match.group(1)
        
        # Fallback: try to get local server IP
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            # Ultimate fallback
            return '127.0.0.1'
    
    def determine_attack_type(self, rule_id: str, rule_msg: str) -> str:
        """Determine attack type based on rule ID and message"""
        rule_msg_lower = rule_msg.lower()
        
        if 'sql' in rule_msg_lower or 'injection' in rule_msg_lower:
            return 'SQL Injection'
        elif 'xss' in rule_msg_lower or 'script' in rule_msg_lower:
            return 'XSS'
        elif 'traversal' in rule_msg_lower or 'directory' in rule_msg_lower:
            return 'Directory Traversal'
        elif 'rfi' in rule_msg_lower or 'remote file' in rule_msg_lower:
            return 'RFI'
        elif 'lfi' in rule_msg_lower or 'local file' in rule_msg_lower:
            return 'LFI'
        elif 'command' in rule_msg_lower:
            return 'Command Injection'
        elif 'brute' in rule_msg_lower or 'login' in rule_msg_lower:
            return 'Brute Force'
        elif 'scanner' in rule_msg_lower or 'scan' in rule_msg_lower:
            return 'Scanner'
        elif 'shell' in rule_msg_lower:
            return 'Web Shell'
        else:
            return 'Generic Attack'
    
    def determine_severity(self, rule_id: str, rule_msg: str) -> str:
        """Determine severity based on rule ID"""
        if rule_id.startswith('9'):
            return 'Critical'
        elif rule_id.startswith('8'):
            return 'High'
        elif rule_id.startswith('7'):
            return 'Medium'
        else:
            return 'Low'
    
    def get_country_from_ip(self, ip: str) -> str:
        """Get country from IP (simplified mapping)"""
        # This is a simplified mapping - in production, use GeoIP database
        ip_country_map = {
            '185.125.190.36': 'Russia',
            '192.168.': 'Local Network',
            '10.': 'Local Network',
            '172.': 'Local Network'
        }
        
        for ip_prefix, country in ip_country_map.items():
            if ip.startswith(ip_prefix):
                return country
        
        return 'Unknown'
    
    def get_location_from_ip(self, ip: str) -> tuple:
        """Get city and coordinates from IP (simplified mapping)"""
        import random
        
        # This is a simplified mapping - in production, use GeoIP database
        ip_location_map = {
            '185.125.190.36': ('Moscow', 55.7558, 37.6176),
            '192.168.': ('Local Network', -6.2088, 106.8456),  # Jakarta (local network)
            '10.': ('Local Network', -6.2088, 106.8456),       # Jakarta (local network)
            '172.': ('Local Network', -6.2088, 106.8456)       # Jakarta (local network)
        }
        
        for ip_prefix, (city, lat, lng) in ip_location_map.items():
            if ip.startswith(ip_prefix):
                return city, lat, lng
        
        # For unknown IPs, assign random locations from common attack sources
        unknown_locations = [
            ('Seoul', 37.5665, 126.9780),      # South Korea
            ('Singapore', 1.3521, 103.8198),   # Singapore
            ('Mumbai', 19.0760, 72.8777),      # India
            ('Bangkok', 13.7563, 100.5018),    # Thailand
            ('Manila', 14.5995, 120.9842),     # Philippines
            ('Ho Chi Minh', 10.8231, 106.6297), # Vietnam
            ('Kuala Lumpur', 3.1390, 101.6869), # Malaysia
            ('Sydney', -33.8688, 151.2093)     # Australia
        ]
        
        # Use IP hash to consistently assign same location to same IP
        ip_hash = hash(ip) % len(unknown_locations)
        return unknown_locations[ip_hash]
    
    def parse_docker_logs(self, container_name='slemp', lines=100):
        """Parse recent ModSecurity logs from Docker container"""
        try:
            # Get recent error logs from nginx
            cmd = f'docker exec {container_name} tail -{lines} /var/log/nginx/error.log'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error reading logs: {result.stderr}")
                return []
            
            log_lines = result.stdout.strip().split('\n')
            attacks = []
            
            for line in log_lines:
                if 'ModSecurity' in line and ('Access denied' in line or 'Warning' in line):
                    try:
                        attack_data = self.parse_modsec_log_line(line)
                        attacks.append(attack_data)
                    except Exception as e:
                        print(f"Error parsing log line: {e}")
                        continue
            
            return attacks
            
        except Exception as e:
            print(f"Error parsing Docker logs: {e}")
            return []
    
    def save_attacks_to_db(self, attacks: List[Dict]):
        """Save parsed attacks to database"""
        if not attacks:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        for attack in attacks:
            try:
                # Check if attack already exists (avoid duplicates)
                cursor.execute('''
                    SELECT COUNT(*) FROM attacks 
                    WHERE timestamp = ? AND source_ip = ? AND target_ip = ? AND target_url = ? AND rule_msg = ?
                ''', (attack['timestamp'], attack['source_ip'], attack['target_ip'], attack['target_url'], attack['rule_msg']))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO attacks 
                        (timestamp, source_ip, target_ip, country, city, latitude, longitude, 
                         attack_type, severity, target_url, rule_msg, target_country, target_city, 
                         target_latitude, target_longitude)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        attack['timestamp'], attack['source_ip'], attack['target_ip'], attack['country'], 
                        attack['city'], attack['latitude'], attack['longitude'], attack['attack_type'], 
                        attack['severity'], attack['target_url'], attack['rule_msg'], attack['target_country'],
                        attack['target_city'], attack['target_latitude'], attack['target_longitude']
                    ))
                    inserted_count += 1
            except Exception as e:
                print(f"Error inserting attack: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return inserted_count
    
    def update_attack_map(self, incremental=True):
        """Update attack map with latest log data"""
        print("Updating attack map with latest log data...")
        
        # List of possible log file locations
        log_files = [
            '/var/log/nginx/modsec_audit.log',
            '/var/log/modsec_audit.log',
            '/etc/nginx/logs/modsec_audit.log'
        ]
        
        total_processed = 0
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    if incremental:
                        processed = self.process_log_file_incremental(log_file, max_lines=1000)
                        print(f"Processed {processed} new entries from {log_file}")
                    else:
                        # Fallback to full parsing
                        attacks = self.parse_docker_logs()
                        processed = len(attacks)
                        if attacks:
                            self.save_attacks_to_db(attacks)
                        print(f"Processed {processed} total entries from logs")
                    
                    total_processed += processed
                    break  # Use first available log file
                    
                except Exception as e:
                    print(f"Error processing {log_file}: {e}")
                    continue
        
        if total_processed == 0:
            print("No log files found or no new attacks detected")
        
        return total_processed

if __name__ == '__main__':
    parser = WAFLogParser()
    parser.update_attack_map()