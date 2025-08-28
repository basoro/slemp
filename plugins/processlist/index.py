#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import psutil
import signal
from flask import request, jsonify

class ProcessListPlugin:
    def __init__(self):
        self.name = "Process List"
        self.version = "1.0.0"
    
    def get_processes(self):
        """Mendapatkan daftar semua proses yang sedang berjalan"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time', 'cmdline']):
                try:
                    proc_info = proc.info
                    # Format command line
                    cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else proc_info['name']
                    if len(cmdline) > 100:
                        cmdline = cmdline[:100] + '...'
                    
                    # Format waktu pembuatan
                    import datetime
                    create_time = datetime.datetime.fromtimestamp(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                    
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'username': proc_info['username'] or 'N/A',
                        'cpu_percent': round(proc_info['cpu_percent'] or 0, 2),
                        'memory_percent': round(proc_info['memory_percent'] or 0, 2),
                        'status': proc_info['status'],
                        'create_time': create_time,
                        'cmdline': cmdline
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Urutkan berdasarkan CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes
        except Exception as e:
            return {'error': str(e)}
    
    def kill_process(self, pid):
        """Menghentikan proses berdasarkan PID"""
        try:
            pid = int(pid)
            if pid <= 0:
                return {'success': False, 'message': 'PID tidak valid'}
            
            # Cek apakah proses ada
            if not psutil.pid_exists(pid):
                return {'success': False, 'message': f'Proses dengan PID {pid} tidak ditemukan'}
            
            # Dapatkan informasi proses
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            # Cegah kill proses sistem penting
            protected_processes = ['init', 'kernel', 'kthreadd', 'systemd', 'launchd']
            if proc_name.lower() in protected_processes or pid == 1:
                return {'success': False, 'message': f'Tidak dapat menghentikan proses sistem: {proc_name}'}
            
            # Kill proses
            proc.terminate()
            
            # Tunggu sebentar dan cek apakah proses masih ada
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Jika masih ada, paksa kill
                proc.kill()
            
            return {'success': True, 'message': f'Proses {proc_name} (PID: {pid}) berhasil dihentikan'}
        
        except psutil.NoSuchProcess:
            return {'success': False, 'message': f'Proses dengan PID {pid} tidak ditemukan'}
        except psutil.AccessDenied:
            return {'success': False, 'message': f'Akses ditolak untuk menghentikan proses PID {pid}'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_system_info(self):
        """Mendapatkan informasi sistem"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            boot_time = psutil.boot_time()
            
            import datetime
            boot_time_formatted = datetime.datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'cpu_count': cpu_count,
                'cpu_percent': round(cpu_percent, 2),
                'memory_total': round(memory.total / (1024**3), 2),  # GB
                'memory_used': round(memory.used / (1024**3), 2),    # GB
                'memory_percent': round(memory.percent, 2),
                'boot_time': boot_time_formatted,
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            return {'error': str(e)}

# Instance plugin
plugin = ProcessListPlugin()

def main():
    """Fungsi utama untuk menangani request"""
    try:
        action = request.form.get('action', '')
        
        if action == 'get_processes':
            return jsonify(plugin.get_processes())
        
        elif action == 'kill_process':
            pid = request.form.get('pid')
            if not pid:
                return jsonify({'success': False, 'message': 'PID tidak diberikan'})
            return jsonify(plugin.kill_process(pid))
        
        elif action == 'get_system_info':
            return jsonify(plugin.get_system_info())
        
        else:
            return jsonify({'success': False, 'message': 'Action tidak dikenali'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    main()