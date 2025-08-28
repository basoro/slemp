#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import re
from flask import request, jsonify
from datetime import datetime

class Fail2banPlugin:
    def __init__(self):
        self.name = "Fail2ban Manager"
        self.version = "1.0.0"
    
    def get_fail2ban_status(self):
        """Mendapatkan status service fail2ban"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'error': 'Fail2ban not installed. Please install fail2ban package.'}
            
            # Check fail2ban service status
            result = subprocess.run(['fail2ban-client', 'status'], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'error': f'Error getting fail2ban status: {result.stderr}'}
            
            # Parse output
            output = result.stdout.strip()
            lines = output.split('\n')
            
            status_info = {
                'service_status': 'running',
                'jails': [],
                'total_jails': 0,
                'active_jails': 0
            }
            
            # Extract jail list
            for line in lines:
                if 'Jail list:' in line:
                    jail_list = line.split('Jail list:')[1].strip()
                    if jail_list:
                        jails = [jail.strip() for jail in jail_list.split(',')]
                        status_info['jails'] = jails
                        status_info['total_jails'] = len(jails)
                        status_info['active_jails'] = len(jails)
                elif '`- Jail list:' in line:
                    # Handle different format: `- Jail list:   sshd
                    jail_list = line.split('`- Jail list:')[1].strip()
                    if jail_list:
                        jails = [jail.strip() for jail in jail_list.split(',') if jail.strip()]
                        status_info['jails'] = jails
                        status_info['total_jails'] = len(jails)
                        status_info['active_jails'] = len(jails)
            
            return status_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_all_available_jails(self):
        """Mendapatkan semua jail yang tersedia dari konfigurasi fail2ban"""
        try:
            available_jails = []
            config_files = ['/etc/fail2ban/jail.conf', '/etc/fail2ban/jail.local']
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()
                        
                    # Find all jail sections [jail_name]
                    import re
                    jail_pattern = r'\[([^\]]+)\]'
                    matches = re.findall(jail_pattern, content)
                    
                    for match in matches:
                        if match not in ['DEFAULT', 'INCLUDES'] and not match.startswith('Definition'):
                            if match not in available_jails:
                                available_jails.append(match)
            
            # Also check jail.d directory
            jail_d_path = '/etc/fail2ban/jail.d/'
            if os.path.exists(jail_d_path):
                for filename in os.listdir(jail_d_path):
                    if filename.endswith('.conf') or filename.endswith('.local'):
                        jail_name = filename.replace('.conf', '').replace('.local', '')
                        if jail_name not in available_jails:
                            available_jails.append(jail_name)
            
            return sorted(available_jails)
        except Exception as e:
            return []
    
    def get_jail_status(self, jail_name=None):
        """Mendapatkan status jail tertentu atau semua jail"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'error': 'Fail2ban not installed. Please install fail2ban package.'}
            
            if jail_name:
                # Get specific jail status
                result = subprocess.run(['fail2ban-client', 'status', jail_name], capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {'error': f'Error getting jail status: {result.stderr}'}
                
                return self._parse_jail_status(result.stdout, jail_name)
            else:
                # Get all jails status (both active and available)
                active_status = self.get_fail2ban_status()
                active_jails = active_status.get('jails', []) if 'error' not in active_status else []
                available_jails = self.get_all_available_jails()
                
                jails_info = []
                
                # Process active jails
                for jail in active_jails:
                    jail_result = subprocess.run(['fail2ban-client', 'status', jail], capture_output=True, text=True)
                    if jail_result.returncode == 0:
                        jail_info = self._parse_jail_status(jail_result.stdout, jail)
                        jail_info['is_active'] = True
                        jails_info.append(jail_info)
                
                # Process inactive jails
                for jail in available_jails:
                    if jail not in active_jails:
                        jail_info = {
                            'name': jail,
                            'status': 'inactive',
                            'is_active': False,
                            'filter': '',
                            'actions': [],
                            'currently_failed': 0,
                            'total_failed': 0,
                            'currently_banned': 0,
                            'total_banned': 0,
                            'banned_ips': []
                        }
                        jails_info.append(jail_info)
                
                return jails_info
        except Exception as e:
            return {'error': str(e)}
    
    def _parse_jail_status(self, output, jail_name):
        """Parse output status jail"""
        try:
            lines = output.strip().split('\n')
            jail_info = {
                'name': jail_name,
                'status': 'active',
                'filter': '',
                'actions': [],
                'currently_failed': 0,
                'total_failed': 0,
                'currently_banned': 0,
                'total_banned': 0,
                'banned_ips': []
            }
            
            for line in lines:
                line = line.strip()
                # Handle new format: |  |- Currently failed: 0
                if '|- Currently failed:' in line:
                    jail_info['currently_failed'] = int(line.split(':')[1].strip())
                elif '|- Total failed:' in line:
                    jail_info['total_failed'] = int(line.split(':')[1].strip())
                elif '|- Currently banned:' in line:
                    jail_info['currently_banned'] = int(line.split(':')[1].strip())
                elif '|- Total banned:' in line:
                    jail_info['total_banned'] = int(line.split(':')[1].strip())
                elif '`- File list:' in line:
                    file_list = line.split(':')[1].strip()
                    jail_info['filter'] = file_list
                elif '`- Banned IP list:' in line:
                    banned_ips = line.split(':')[1].strip()
                    if banned_ips:
                        jail_info['banned_ips'] = [ip.strip() for ip in banned_ips.split() if ip.strip()]
                # Handle old format for backward compatibility
                elif 'Filter' in line and ':' in line:
                    jail_info['filter'] = line.split(':')[1].strip()
                elif 'Actions' in line and ':' in line:
                    actions = line.split(':')[1].strip()
                    jail_info['actions'] = [action.strip() for action in actions.split(',') if action.strip()]
                elif 'Currently failed:' in line:
                    jail_info['currently_failed'] = int(line.split(':')[1].strip())
                elif 'Total failed:' in line:
                    jail_info['total_failed'] = int(line.split(':')[1].strip())
                elif 'Currently banned:' in line:
                    jail_info['currently_banned'] = int(line.split(':')[1].strip())
                elif 'Total banned:' in line:
                    jail_info['total_banned'] = int(line.split(':')[1].strip())
                elif 'Banned IP list:' in line:
                    banned_ips = line.split(':')[1].strip()
                    if banned_ips:
                        jail_info['banned_ips'] = [ip.strip() for ip in banned_ips.split() if ip.strip()]
            
            return jail_info
        except Exception as e:
            return {'error': f'Error parsing jail status: {str(e)}'}
    
    def manage_jail(self, action, jail_name):
        """Mengelola jail (start, stop, restart)"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Fail2ban not installed. Please install fail2ban package.'}
            
            valid_actions = ['start', 'stop', 'restart']
            if action not in valid_actions:
                return {'success': False, 'message': f'Invalid action. Valid actions: {valid_actions}'}
            
            if not jail_name:
                return {'success': False, 'message': 'Jail name is required'}
            
            # Create jail.local to enable the jail
            subprocess.run(['sh', '-c', f'echo "[{jail_name}]" >> /etc/fail2ban/jail.local'], capture_output=True, text=True)
            subprocess.run(['sh', '-c', 'echo "enabled = true" >> /etc/fail2ban/jail.local'], capture_output=True, text=True)
            subprocess.run(['supervisorctl', 'restart', 'fail2ban'], capture_output=True, text=True)
            
            # Execute action
            result = subprocess.run(['fail2ban-client', action, jail_name], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'Jail {jail_name} {action}ed successfully'}
            else:
                return {'success': False, 'message': f'Error {action}ing jail: {result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def unban_ip(self, jail_name, ip_address):
        """Unban IP address dari jail tertentu"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Fail2ban not installed. Please install fail2ban package.'}
            
            if not jail_name or not ip_address:
                return {'success': False, 'message': 'Jail name and IP address are required'}
            
            # Unban IP
            result = subprocess.run(['fail2ban-client', 'set', jail_name, 'unbanip', ip_address], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'IP {ip_address} unbanned from {jail_name} successfully'}
            else:
                return {'success': False, 'message': f'Error unbanning IP: {result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def ban_ip(self, jail_name, ip_address):
        """Ban IP address di jail tertentu"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Fail2ban not installed. Please install fail2ban package.'}
            
            if not jail_name or not ip_address:
                return {'success': False, 'message': 'Jail name and IP address are required'}
            
            # Ban IP
            result = subprocess.run(['fail2ban-client', 'set', jail_name, 'banip', ip_address], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'success': True, 'message': f'IP {ip_address} banned in {jail_name} successfully'}
            else:
                return {'success': False, 'message': f'Error banning IP: {result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_fail2ban_logs(self, lines=100):
        """Mendapatkan log fail2ban"""
        try:
            log_files = ['/var/log/fail2ban.log', '/var/log/fail2ban/fail2ban.log']
            log_file = None
            
            # Find existing log file
            for file_path in log_files:
                if os.path.exists(file_path):
                    log_file = file_path
                    break
            
            if not log_file:
                return {'error': 'Fail2ban log file not found'}
            
            # Read last N lines
            result = subprocess.run(['tail', '-n', str(lines), log_file], capture_output=True, text=True)
            
            if result.returncode == 0:
                log_lines = result.stdout.strip().split('\n')
                return {'logs': log_lines}
            else:
                return {'error': f'Error reading log file: {result.stderr}'}
        
        except Exception as e:
            return {'error': str(e)}
    
    def configure_auto_jail(self, jail_name, enabled=True, maxretry=5, findtime=600, bantime=3600, banaction='ufw'):
        """Mengonfigurasi jail untuk otomatis aktif ketika mendeteksi serangan"""
        try:
            # Check if fail2ban-client command exists
            check_result = subprocess.run(['which', 'fail2ban-client'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Fail2ban not installed. Please install fail2ban package.'}
            
            if not jail_name:
                return {'success': False, 'message': 'Jail name is required'}
            
            # Create jail configuration directory if not exists
            jail_dir = '/etc/fail2ban/jail.d'
            if not os.path.exists(jail_dir):
                os.makedirs(jail_dir, exist_ok=True)
            
            # Create auto-configuration file for the jail
            config_file = f'{jail_dir}/{jail_name}-auto.conf'
            
            config_content = f"""# Auto-generated configuration for {jail_name} jail
# Configured for automatic activation on attack detection

[{jail_name}]
enabled = {str(enabled).lower()}
maxretry = {maxretry}
findtime = {findtime}
bantime = {bantime}
banaction = {banaction}

# Auto-enable settings
# This jail will automatically start when fail2ban service starts
# and will monitor for attacks based on the configured thresholds
# Uses UFW (Uncomplicated Firewall) as the ban action
"""
            
            # Write configuration
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            # Reload fail2ban configuration
            reload_result = subprocess.run(['fail2ban-client', 'reload'], capture_output=True, text=True)
            
            if reload_result.returncode == 0:
                # Start the jail if enabled
                if enabled:
                    start_result = subprocess.run(['fail2ban-client', 'start', jail_name], capture_output=True, text=True)
                    if start_result.returncode == 0:
                        return {
                            'success': True, 
                            'message': f'Jail {jail_name} configured for auto-activation and started successfully. '
                                     f'Settings: maxretry={maxretry}, findtime={findtime}s, bantime={bantime}s'
                        }
                    else:
                        return {
                            'success': True, 
                            'message': f'Jail {jail_name} configured but failed to start: {start_result.stderr}'
                        }
                else:
                    return {
                        'success': True, 
                        'message': f'Jail {jail_name} configured but disabled. '
                                 f'Settings: maxretry={maxretry}, findtime={findtime}s, bantime={bantime}s'
                    }
            else:
                return {'success': False, 'message': f'Error reloading fail2ban configuration: {reload_result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error configuring auto jail: {str(e)}'}
    
    def get_auto_jail_config(self, jail_name):
        """Mendapatkan konfigurasi auto jail"""
        try:
            config_file = f'/etc/fail2ban/jail.d/{jail_name}-auto.conf'
            
            if not os.path.exists(config_file):
                return {
                    'success': False, 
                    'message': f'Auto configuration for jail {jail_name} not found',
                    'config': {
                        'enabled': False,
                        'maxretry': 5,
                        'findtime': 600,
                        'bantime': 3600,
                        'banaction': 'ufw'
                    }
                }
            
            # Read configuration
            config = {
                'enabled': False,
                'maxretry': 5,
                'findtime': 600,
                'bantime': 3600,
                'banaction': 'ufw'
            }
            
            with open(config_file, 'r') as f:
                content = f.read()
                
                # Parse configuration values
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('enabled ='):
                        config['enabled'] = 'true' in line.lower()
                    elif line.startswith('maxretry ='):
                        config['maxretry'] = int(line.split('=')[1].strip())
                    elif line.startswith('findtime ='):
                        config['findtime'] = int(line.split('=')[1].strip())
                    elif line.startswith('bantime ='):
                        config['bantime'] = int(line.split('=')[1].strip())
                    elif line.startswith('banaction ='):
                        config['banaction'] = line.split('=')[1].strip()
            
            return {
                'success': True,
                'config': config
            }
        
        except Exception as e:
            return {'success': False, 'message': f'Error reading auto jail config: {str(e)}'}
    
    def monitor_and_auto_activate_jails(self):
        """Monitor jails and auto-activate if attack detected"""
        try:
            # Get all available jails
            status_result = subprocess.run(['fail2ban-client', 'status'], capture_output=True, text=True)
            if status_result.returncode != 0:
                return {'success': False, 'message': 'Failed to get fail2ban status'}
            
            # Parse available jails
            lines = status_result.stdout.split('\n')
            jail_list_line = None
            for line in lines:
                if 'Jail list:' in line:
                    jail_list_line = line
                    break
            
            if not jail_list_line:
                return {'success': False, 'message': 'No jails found'}
            
            # Extract jail names
            jail_names = jail_list_line.split('Jail list:')[1].strip().split(', ')
            jail_names = [name.strip() for name in jail_names if name.strip()]
            
            activated_jails = []
            
            for jail_name in jail_names:
                 # Check if auto config is enabled for this jail
                 auto_config = self.get_auto_jail_config(jail_name)
                 if not auto_config.get('enabled', False):
                     continue
                 
                 # Check jail status
                 jail_status = self.get_jail_status(jail_name)
                 if not jail_status.get('success', False):
                     continue
                 
                 jail_data = jail_status.get('jail', {})
                 currently_failed = jail_data.get('currently_failed', 0)
                 total_failed = jail_data.get('total_failed', 0)
                 
                 # Check if jail is inactive and has failures
                 if jail_data.get('status', '').lower() != 'active':
                     # Check if there are recent failures that exceed threshold
                     maxretry = auto_config.get('maxretry', 5)
                     
                     if currently_failed >= maxretry or total_failed >= maxretry * 2:
                         # Activate the jail
                         try:
                             activate_result = subprocess.run(
                                 ['fail2ban-client', 'start', jail_name], 
                                 capture_output=True, text=True
                             )
                             
                             if activate_result.returncode == 0:
                                 activated_jails.append({
                                     'jail': jail_name,
                                     'reason': f'Auto-activated due to {currently_failed} current failures and {total_failed} total failures (threshold: {maxretry})'
                                 })
                             
                         except Exception as e:
                             continue
                 
                 # Also check if jail is active but needs parameter updates
                 elif jail_data.get('status', '').lower() == 'active':
                     # Update jail parameters if needed
                     try:
                         # Set maxretry
                         subprocess.run(
                             ['fail2ban-client', 'set', jail_name, 'maxretry', str(auto_config.get('maxretry', 5))],
                             capture_output=True, text=True
                         )
                         # Set findtime
                         subprocess.run(
                             ['fail2ban-client', 'set', jail_name, 'findtime', str(auto_config.get('findtime', 600))],
                             capture_output=True, text=True
                         )
                         # Set bantime
                         subprocess.run(
                             ['fail2ban-client', 'set', jail_name, 'bantime', str(auto_config.get('bantime', 3600))],
                             capture_output=True, text=True
                         )
                     except Exception as e:
                         continue
            
            if activated_jails:
                return {
                    'success': True, 
                    'message': f'Auto-activated {len(activated_jails)} jail(s)',
                    'activated_jails': activated_jails
                }
            else:
                return {
                    'success': True, 
                    'message': 'No jails needed activation',
                    'activated_jails': []
                }
                
        except Exception as e:
            return {'success': False, 'message': f'Error in auto monitoring: {str(e)}'}
    
    def start_auto_monitoring(self):
        """Start automatic monitoring service using supervisord"""
        try:
            # Create a simple monitoring script
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            monitor_script = f'''#!/bin/bash
# Fail2ban Auto Monitor Script

while true; do
    # Call the monitoring function every 60 seconds
    cd {plugin_dir}
    python3 -c "
import sys
sys.path.append('{plugin_dir}')
from index import Fail2banPlugin
plugin = Fail2banPlugin()
result = plugin.monitor_and_auto_activate_jails()
print(f'Monitor result: {{result}}')
" >> /var/log/fail2ban-auto-monitor.log 2>&1
    
    sleep 60
done
'''
            
            script_path = '/usr/local/bin/fail2ban-auto-monitor.sh'
            with open(script_path, 'w') as f:
                f.write(monitor_script)
            
            # Make script executable
            subprocess.run(['chmod', '+x', script_path], capture_output=True, text=True)
            
            # Create supervisord configuration
            supervisor_config = f'''
[program:fail2ban-auto-monitor]
command={script_path}
autostart=true
autorestart=true
user=root
stdout_logfile=/var/log/fail2ban-auto-monitor.log
stderr_logfile=/var/log/fail2ban-auto-monitor-error.log
'''
            
            # Add configuration to supervisord.conf
            config_path = '/etc/supervisor/conf.d/supervisord.conf'
            
            # Check if fail2ban-auto-monitor already exists in config
            config_exists = False
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                    if '[program:fail2ban-auto-monitor]' in content:
                        config_exists = True
            
            if not config_exists:
                with open(config_path, 'a') as f:
                    f.write(supervisor_config)
            
            # Reload supervisor configuration and start service
            subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
            subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
            subprocess.run(['supervisorctl', 'start', 'fail2ban-auto-monitor'], capture_output=True, text=True)
            
            return {'success': True, 'message': 'Auto monitoring service started successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to start auto monitoring: {str(e)}'}
    
    def stop_auto_monitoring(self):
        """Stop automatic monitoring service using supervisord"""
        try:
            subprocess.run(['supervisorctl', 'stop', 'fail2ban-auto-monitor'], capture_output=True, text=True)
            
            return {'success': True, 'message': 'Auto monitoring service stopped successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Failed to stop auto monitoring: {str(e)}'}
    
    def get_auto_monitoring_status(self):
        """Get auto monitoring service status using supervisord"""
        try:
            # Check if supervisord config exists
            config_path = '/etc/supervisor/conf.d/supervisord.conf'
            config_exists = False
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                    config_exists = '[program:fail2ban-auto-monitor]' in content
            
            if not config_exists:
                return {
                    'success': True,
                    'active': False,
                    'enabled': False,
                    'status': 'stopped',
                    'message': 'Service not configured'
                }
            
            # Check supervisor status
            result = subprocess.run(['supervisorctl', 'status', 'fail2ban-auto-monitor'], capture_output=True, text=True)
            status_output = result.stdout.strip()
            
            # Parse supervisorctl status output
            is_running = 'RUNNING' in status_output
            is_enabled = config_exists  # If config exists, it's considered enabled
            
            # Additional check: see if the monitoring script is running
            script_running = False
            try:
                pgrep_result = subprocess.run(['pgrep', '-f', 'fail2ban-auto-monitor.sh'], capture_output=True, text=True)
                script_running = pgrep_result.returncode == 0
            except:
                pass
            
            return {
                'success': True,
                'active': is_running or script_running,
                'enabled': is_enabled,
                'status': 'running' if (is_running or script_running) else 'stopped',
                'supervisor_status': status_output,
                'script_running': script_running
            }
            
        except Exception as e:
            return {
                'success': False,
                'active': False,
                'enabled': False,
                'status': 'unknown',
                'message': f'Error checking status: {str(e)}'
            }
    
    def install_fail2ban(self):
        """Install fail2ban package"""
        try:
            # Install fail2ban package using apt-get
            update_result = subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
            if update_result.returncode != 0:
                return {'error': f'Failed to update package list: {update_result.stderr}'}
            
            install_result = subprocess.run(['apt-get', 'install', '-y', 'fail2ban'], capture_output=True, text=True)
            
            if install_result.returncode != 0:
                return {'error': f'Failed to install fail2ban: {install_result.stderr}'}

            # Stop and disable fail2ban service
            start_result = subprocess.run(['systemctl', 'stop', 'fail2ban'], capture_output=True, text=True)
            enable_result = subprocess.run(['systemctl', 'disable', 'fail2ban'], capture_output=True, text=True)
            
            # Fix nginx log permissions for fail2ban access
            subprocess.run(['chmod', '644', '/var/log/nginx/access.log'], capture_output=True, text=True)
            subprocess.run(['chmod', '644', '/var/log/nginx/error.log'], capture_output=True, text=True)
                        
            # Create and configure auth.log file
            subprocess.run(['touch', '/var/log/auth.log'], capture_output=True, text=True)
            subprocess.run(['chown', 'root:adm', '/var/log/auth.log'], capture_output=True, text=True)
            subprocess.run(['chmod', '640', '/var/log/auth.log'], capture_output=True, text=True)
            
            # Configure rsyslog to write auth logs to /var/log/auth.log
            rsyslog_config = '\nauth,authpriv.*   /var/log/auth.log\n'
            with open('/etc/rsyslog.conf', 'a') as f:
                f.write(rsyslog_config)
            
            # Configure supervisord for fail2ban service
            supervisord_conf = '/etc/supervisor/conf.d/supervisord.conf'
            fail2ban_conf = '''
[program:fail2ban]
command=/usr/bin/fail2ban-server -f
autorestart=true
user=root
stdout_logfile=/var/log/fail2ban.log
stderr_logfile=/var/log/fail2ban.log
startretries=3
'''
            
            try:
                # Check if supervisord config exists
                if os.path.exists(supervisord_conf):
                    with open(supervisord_conf, 'r') as f:
                        existing_conf = f.read()
                    
                    # Check if fail2ban config already exists
                    if '[program:fail2ban]' not in existing_conf:
                        with open(supervisord_conf, 'a') as f:
                            f.write(fail2ban_conf)
                        
                        # Reload supervisord configuration
                        subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                        subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                        subprocess.run(['supervisorctl', 'start', 'fail2ban'], capture_output=True, text=True)
                else:
                    # Create supervisord config directory if it doesn't exist
                    os.makedirs('/etc/supervisor/conf.d', exist_ok=True)
                    
                    # Create basic supervisord config with fail2ban
                    with open(supervisord_conf, 'w') as f:
                        f.write(fail2ban_conf)
                        
            except Exception as e:
                # If supervisord configuration fails, fallback to systemctl
                pass
            
            
            return {'success': True, 'message': 'Fail2ban installed and started successfully'}
        
        except Exception as e:
            return {'error': f'Error installing fail2ban: {str(e)}'}
    
    def get_system_info(self):
        """Mendapatkan informasi sistem terkait fail2ban"""
        try:
            # Get fail2ban status
            status = self.get_fail2ban_status()
            
            if 'error' in status:
                return {
                    'service_status': 'Not installed',
                    'total_jails': 0,
                    'active_jails': 0,
                    'total_banned': 0,
                    'version': 'N/A'
                }
            
            # Get version
            try:
                version_result = subprocess.run(['fail2ban-client', 'version'], capture_output=True, text=True)
                version = version_result.stdout.strip() if version_result.returncode == 0 else 'Unknown'
            except:
                version = 'Unknown'
            
            # Count total banned IPs
            total_banned = 0
            jails_status = self.get_jail_status()
            if isinstance(jails_status, list):
                for jail in jails_status:
                    if 'currently_banned' in jail:
                        total_banned += jail['currently_banned']
            
            return {
                'service_status': status.get('service_status', 'unknown'),
                'total_jails': status.get('total_jails', 0),
                'active_jails': status.get('active_jails', 0),
                'total_banned': total_banned,
                'version': version
            }
        except Exception as e:
            return {'error': str(e)}

# Instance plugin
plugin = Fail2banPlugin()

def main():
    """Fungsi utama untuk menangani request"""
    try:
        action = request.form.get('action', '')
        
        if action == 'get_fail2ban_status':
            return jsonify(plugin.get_fail2ban_status())
        
        elif action == 'get_jail_status':
            jail_name = request.form.get('jail_name')
            return jsonify(plugin.get_jail_status(jail_name))
        
        elif action == 'manage_jail':
            jail_action = request.form.get('jail_action')
            jail_name = request.form.get('jail_name')
            return jsonify(plugin.manage_jail(jail_action, jail_name))
        
        elif action == 'unban_ip':
            jail_name = request.form.get('jail_name')
            ip_address = request.form.get('ip_address')
            return jsonify(plugin.unban_ip(jail_name, ip_address))
        
        elif action == 'ban_ip':
            jail_name = request.form.get('jail_name')
            ip_address = request.form.get('ip_address')
            return jsonify(plugin.ban_ip(jail_name, ip_address))
        
        elif action == 'get_fail2ban_logs':
            lines = int(request.form.get('lines', 100))
            return jsonify(plugin.get_fail2ban_logs(lines))
        
        elif action == 'get_system_info':
            return jsonify(plugin.get_system_info())
        
        elif action == 'install_fail2ban':
            return jsonify(plugin.install_fail2ban())
        
        elif action == 'configure_auto_jail':
            jail_name = request.form.get('jail_name')
            enabled = request.form.get('enabled', 'true').lower() == 'true'
            maxretry = int(request.form.get('maxretry', 5))
            findtime = int(request.form.get('findtime', 600))
            bantime = int(request.form.get('bantime', 3600))
            banaction = request.form.get('banaction', 'ufw')
            return jsonify(plugin.configure_auto_jail(jail_name, enabled, maxretry, findtime, bantime, banaction))
        
        elif action == 'get_auto_jail_config':
            jail_name = request.form.get('jail_name')
            return jsonify(plugin.get_auto_jail_config(jail_name))
        
        elif action == 'monitor_and_auto_activate_jails':
            return jsonify(plugin.monitor_and_auto_activate_jails())
        
        elif action == 'start_auto_monitoring':
            return jsonify(plugin.start_auto_monitoring())
        
        elif action == 'stop_auto_monitoring':
            return jsonify(plugin.stop_auto_monitoring())
        
        elif action == 'get_auto_monitoring_status':
            return jsonify(plugin.get_auto_monitoring_status())
        
        else:
            return jsonify({'success': False, 'message': 'Action tidak dikenali'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    main()