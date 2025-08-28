#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
import re
from flask import request, jsonify
from datetime import datetime

class CrontabPlugin:
    def __init__(self):
        self.name = "Crontab Manager"
        self.version = "1.0.0"
    
    def get_crontab_jobs(self):
        """Mendapatkan daftar semua crontab jobs"""
        try:
            # Check if crontab command exists
            check_result = subprocess.run(['which', 'crontab'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'error': 'Crontab command not found. Please install cron package.'}
            
            # Jalankan crontab -l untuk mendapatkan daftar jobs
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode != 0:
                if "no crontab" in result.stderr.lower():
                    return []
                else:
                    return {'error': f'Error getting crontab: {result.stderr}'}
            
            jobs = []
            lines = result.stdout.strip().split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse crontab line
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    minute, hour, day, month, weekday = parts[:5]
                    command = parts[5]
                    
                    # Determine status (enabled/disabled)
                    status = 'enabled'
                    
                    # Parse schedule untuk display yang lebih readable
                    schedule_desc = self._parse_schedule(minute, hour, day, month, weekday)
                    
                    jobs.append({
                        'id': i + 1,
                        'minute': minute,
                        'hour': hour,
                        'day': day,
                        'month': month,
                        'weekday': weekday,
                        'command': command,
                        'schedule': f"{minute} {hour} {day} {month} {weekday}",
                        'schedule_desc': schedule_desc,
                        'status': status,
                        'raw_line': line
                    })
            
            return jobs
        except Exception as e:
            return {'error': str(e)}
    
    def install_cron_package(self):
        """Install cron package using apt-get for Ubuntu Linux"""
        try:
            # Install cron package using apt-get with proper command structure
            # First update package list
            update_result = subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
            if update_result.returncode != 0:
                return {'error': f'Failed to update package list: {update_result.stderr}'}
            
            # Then install cron package
            install_result = subprocess.run(['apt-get', 'install', '-y', 'cron'], capture_output=True, text=True)
            result = install_result
            
            if result.returncode != 0:
                return {'error': f'Failed to install cron package: {result.stderr}'}
            
            # Add cron service to supervisord configuration
            supervisord_conf = '/etc/supervisor/conf.d/supervisord.conf'
            cron_config = '''

[program:cron]
command=/usr/sbin/cron -f
autostart=true
autorestart=true
stdout_logfile=/var/log/cron.log
stderr_logfile=/var/log/cron_error.log
'''
            
            try:
                # Check if cron program already exists in supervisord.conf
                with open(supervisord_conf, 'r') as f:
                    content = f.read()
                    if '[program:cron]' not in content:
                        with open(supervisord_conf, 'a') as f:
                            f.write(cron_config)
                
                # Reload supervisord configuration
                reload_result = subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                if reload_result.returncode != 0:
                    return {'error': f'Failed to reload supervisord config: {reload_result.stderr}'}
                
                update_result = subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                if update_result.returncode != 0:
                    return {'error': f'Failed to update supervisord: {update_result.stderr}'}
                
                # Start cron service
                start_result = subprocess.run(['supervisorctl', 'start', 'cron'], capture_output=True, text=True)
                if start_result.returncode != 0:
                    return {'error': f'Failed to start cron service: {start_result.stderr}'}
                
                return {'success': True, 'message': 'Cron package installed and started successfully'}
                
            except Exception as e:
                return {'error': f'Error configuring supervisord: {str(e)}'}
                
        except Exception as e:
            return {'error': f'Error installing cron package: {str(e)}'}
    
    def _parse_schedule(self, minute, hour, day, month, weekday):
        """Parse schedule menjadi deskripsi yang lebih readable"""
        try:
            desc_parts = []
            
            # Parse minute
            if minute == '*':
                desc_parts.append('every minute')
            elif '/' in minute:
                interval = minute.split('/')[1]
                desc_parts.append(f'every {interval} minutes')
            else:
                desc_parts.append(f'at minute {minute}')
            
            # Parse hour
            if hour != '*':
                if '/' in hour:
                    interval = hour.split('/')[1]
                    desc_parts.append(f'every {interval} hours')
                else:
                    desc_parts.append(f'at {hour}:00')
            
            # Parse day
            if day != '*':
                desc_parts.append(f'on day {day}')
            
            # Parse month
            if month != '*':
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                if month.isdigit() and 1 <= int(month) <= 12:
                    desc_parts.append(f'in {months[int(month)-1]}')
                else:
                    desc_parts.append(f'in month {month}')
            
            # Parse weekday
            if weekday != '*':
                weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
                if weekday.isdigit() and 0 <= int(weekday) <= 6:
                    desc_parts.append(f'on {weekdays[int(weekday)]}')
                else:
                    desc_parts.append(f'on weekday {weekday}')
            
            return ' '.join(desc_parts)
        except:
            return f"{minute} {hour} {day} {month} {weekday}"
    
    def add_crontab_job(self, minute, hour, day, month, weekday, command):
        """Menambahkan job baru ke crontab"""
        try:
            # Check if crontab command exists
            check_result = subprocess.run(['which', 'crontab'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Crontab command not found. Please install cron package.'}
            
            # Validasi input
            if not command.strip():
                return {'success': False, 'message': 'Command tidak boleh kosong'}
            
            # Format crontab line
            cron_line = f"{minute} {hour} {day} {month} {weekday} {command}"
            
            # Dapatkan crontab yang ada
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            existing_crontab = result.stdout if result.returncode == 0 else ""
            
            # Tambahkan job baru
            new_crontab = existing_crontab.rstrip() + "\n" + cron_line + "\n"
            
            # Tulis kembali ke crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                return {'success': True, 'message': 'Crontab job berhasil ditambahkan'}
            else:
                return {'success': False, 'message': 'Gagal menambahkan crontab job'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def delete_crontab_job(self, job_id):
        """Menghapus job dari crontab berdasarkan ID"""
        try:
            # Check if crontab command exists
            check_result = subprocess.run(['which', 'crontab'], capture_output=True, text=True)
            if check_result.returncode != 0:
                return {'success': False, 'message': 'Crontab command not found. Please install cron package.'}
            
            job_id = int(job_id)
            
            # Dapatkan crontab yang ada
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'success': False, 'message': 'Tidak ada crontab yang ditemukan'}
            
            lines = result.stdout.strip().split('\n')
            job_lines = [line for line in lines if line.strip() and not line.startswith('#')]
            
            if job_id < 1 or job_id > len(job_lines):
                return {'success': False, 'message': 'Job ID tidak valid'}
            
            # Hapus job yang dipilih
            job_to_remove = job_lines[job_id - 1]
            new_lines = [line for line in lines if line != job_to_remove]
            
            # Tulis kembali ke crontab
            new_crontab = '\n'.join(new_lines) + '\n' if new_lines else ''
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                return {'success': True, 'message': f'Crontab job berhasil dihapus'}
            else:
                return {'success': False, 'message': 'Gagal menghapus crontab job'}
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_system_info(self):
        """Mendapatkan informasi sistem terkait crontab"""
        try:
            # Hitung total jobs
            jobs = self.get_crontab_jobs()
            if isinstance(jobs, dict) and 'error' in jobs:
                total_jobs = 0
                enabled_jobs = 0
            else:
                total_jobs = len(jobs)
                enabled_jobs = len([job for job in jobs if job['status'] == 'enabled'])
            
            # Cek status cron service
            try:
                result = subprocess.run(['pgrep', 'cron'], capture_output=True)
                cron_running = result.returncode == 0
            except:
                cron_running = False
            
            # Dapatkan waktu terakhir crontab dimodifikasi
            try:
                result = subprocess.run(['stat', '-c', '%Y', '/var/spool/cron/crontabs/' + os.getenv('USER', 'root')], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    timestamp = int(result.stdout.strip())
                    last_modified = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    last_modified = 'N/A'
            except:
                last_modified = 'N/A'
            
            return {
                'total_jobs': total_jobs,
                'enabled_jobs': enabled_jobs,
                'disabled_jobs': total_jobs - enabled_jobs,
                'cron_service_status': 'Running' if cron_running else 'Stopped',
                'last_modified': last_modified
            }
        except Exception as e:
            return {'error': str(e)}

# Instance plugin
plugin = CrontabPlugin()

def main():
    """Fungsi utama untuk menangani request"""
    try:
        action = request.form.get('action', '')
        
        if action == 'get_crontab_jobs':
            return jsonify(plugin.get_crontab_jobs())
        
        elif action == 'add_crontab_job':
            minute = request.form.get('minute', '*')
            hour = request.form.get('hour', '*')
            day = request.form.get('day', '*')
            month = request.form.get('month', '*')
            weekday = request.form.get('weekday', '*')
            command = request.form.get('command', '')
            
            return jsonify(plugin.add_crontab_job(minute, hour, day, month, weekday, command))
        
        elif action == 'delete_crontab_job':
            job_id = request.form.get('job_id')
            if not job_id:
                return jsonify({'success': False, 'message': 'Job ID tidak diberikan'})
            return jsonify(plugin.delete_crontab_job(job_id))
        
        elif action == 'get_system_info':
            return jsonify(plugin.get_system_info())
        
        elif action == 'install_cron_package':
            return jsonify(plugin.install_cron_package())
        
        else:
            return jsonify({'success': False, 'message': 'Action tidak dikenali'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    main()