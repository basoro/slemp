#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import psutil
import platform
from datetime import datetime, timedelta
from flask import request, jsonify

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SystemMonitorPlugin:
    def __init__(self):
        self.last_network_io = None
        self.last_network_time = None
    
    def get_system_info(self):
        """Get comprehensive system information"""
        try:
            # CPU Information
            cpu_usage = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # Memory Information
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_total = memory.total
            memory_available = memory.available
            memory_used = memory.used
            
            # Disk Information
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            disk_total = disk.total
            disk_used = disk.used
            disk_free = disk.free
            
            # Network Information
            network_info = self.get_network_info()
            
            # System Information
            system_info = {
                'os': f"{platform.system()} {platform.release()}",
                'hostname': platform.node(),
                'uptime': self.get_uptime(),
                'cpu_model': self.get_cpu_model(),
                'cpu_cores': cpu_count,
                'cpu_logical_cores': cpu_count_logical,
                'total_memory': memory_total,
                'architecture': platform.architecture()[0]
            }
            
            # Load Average (Unix-like systems only)
            load_average = self.get_load_average()
            
            return {
                'success': True,
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'disk_usage': round(disk_usage, 2),
                'memory_info': {
                    'total': memory_total,
                    'available': memory_available,
                    'used': memory_used,
                    'percent': memory_usage
                },
                'disk_info': {
                    'total': disk_total,
                    'used': disk_used,
                    'free': disk_free,
                    'percent': disk_usage
                },
                'network': network_info,
                'system_info': system_info,
                'load_average': load_average,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get system information: {str(e)}'
            }
    
    def get_network_info(self):
        """Get network I/O statistics with rate calculation"""
        try:
            current_time = time.time()
            current_io = psutil.net_io_counters()
            
            network_info = {
                'bytes_sent': current_io.bytes_sent,
                'bytes_recv': current_io.bytes_recv,
                'packets_sent': current_io.packets_sent,
                'packets_recv': current_io.packets_recv,
                'bytes_sent_per_sec': 0,
                'bytes_recv_per_sec': 0
            }
            
            # Calculate rates if we have previous data
            if self.last_network_io and self.last_network_time:
                time_diff = current_time - self.last_network_time
                if time_diff > 0:
                    bytes_sent_diff = current_io.bytes_sent - self.last_network_io.bytes_sent
                    bytes_recv_diff = current_io.bytes_recv - self.last_network_io.bytes_recv
                    
                    network_info['bytes_sent_per_sec'] = max(0, bytes_sent_diff / time_diff)
                    network_info['bytes_recv_per_sec'] = max(0, bytes_recv_diff / time_diff)
            
            # Store current values for next calculation
            self.last_network_io = current_io
            self.last_network_time = current_time
            
            return network_info
            
        except Exception as e:
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'bytes_sent_per_sec': 0,
                'bytes_recv_per_sec': 0,
                'error': str(e)
            }
    
    def get_uptime(self):
        """Get system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_delta = timedelta(seconds=uptime_seconds)
            
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception as e:
            return "Unknown"
    
    def get_cpu_model(self):
        """Get CPU model information"""
        try:
            if platform.system() == "Darwin":  # macOS
                import subprocess
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            elif platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            return line.split(':')[1].strip()
            elif platform.system() == "Windows":
                import subprocess
                result = subprocess.run(['wmic', 'cpu', 'get', 'name'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        return lines[1].strip()
            
            return f"{platform.processor()} ({psutil.cpu_count()} cores)"
            
        except Exception as e:
            return f"Unknown CPU ({psutil.cpu_count()} cores)"
    
    def get_load_average(self):
        """Get system load average (Unix-like systems)"""
        try:
            if hasattr(os, 'getloadavg'):
                load1, load5, load15 = os.getloadavg()
                return {
                    'load_1min': round(load1, 2),
                    'load_5min': round(load5, 2),
                    'load_15min': round(load15, 2)
                }
            else:
                # Windows doesn't have load average, use CPU usage as approximation
                cpu_usage = psutil.cpu_percent()
                approx_load = cpu_usage / 100.0 * psutil.cpu_count()
                return {
                    'load_1min': round(approx_load, 2),
                    'load_5min': round(approx_load, 2),
                    'load_15min': round(approx_load, 2)
                }
        except Exception as e:
            return {
                'load_1min': 0.0,
                'load_5min': 0.0,
                'load_15min': 0.0,
                'error': str(e)
            }
    
    def get_process_list(self, limit=10):
        """Get list of top processes by CPU usage"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    proc_info = proc.info
                    proc_info['cpu_percent'] = proc.cpu_percent()
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and limit results
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return {
                'success': True,
                'processes': processes[:limit]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get process list: {str(e)}'
            }

# Instance plugin
plugin = SystemMonitorPlugin()

def main():
    """Main function to handle API requests"""
    try:
        # Get action from form data
        action = request.form.get('action', '')
        
        if action == 'get_system_info':
            result = plugin.get_system_info()
            return jsonify(result)
        
        elif action == 'get_process_list':
            limit = int(request.form.get('limit', 10))
            result = plugin.get_process_list(limit)
            return jsonify(result)
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action specified'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'API Error: {str(e)}'
        })

if __name__ == '__main__':
    main()