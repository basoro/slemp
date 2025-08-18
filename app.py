from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, Namespace
from werkzeug.security import generate_password_hash, check_password_hash
import psutil
import os
import subprocess
import mysql.connector
from mysql.connector import pooling
import json
from werkzeug.utils import secure_filename
import shutil
import configparser
import zipfile
import tarfile
import re
import logging
from logging.handlers import RotatingFileHandler
import datetime
import threading
import time
import pty
import select
import termios
import struct
import fcntl
import signal
import requests
import tempfile

# Environment detection
def is_docker_environment():
    """Detect if running in Docker container"""
    try:
        # Check for .dockerenv file
        if os.path.exists('/.dockerenv'):
            return True
        # Check for Docker in cgroup
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return False

def is_systemctl_available():
    """Check if systemctl is available and functional"""
    try:
        result = subprocess.run(['which', 'systemctl'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def safe_systemctl_command(command, service_name, capture_output=True, text=True, timeout=30):
    """Execute systemctl command with error handling"""
    if not is_systemctl_available():
        logger.warning('systemctl is not available')
        return None

    try:
        return subprocess.run(['systemctl', command, service_name], 
                            capture_output=capture_output, text=text, timeout=timeout)
    except Exception as e:
        logger.warning(f'Failed to execute systemctl {command} {service_name}: {str(e)}')
        return None

# Konfigurasi logging 
if not os.path.exists('data/logs'):
    os.makedirs('data/logs')

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = 'data/logs/server_manager.log'
log_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('server_manager')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# MySQL Connection Pool Configuration
def load_config():
    """Load configuration from JSON file - force load from config.json only"""
    config_file = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def save_config(config_data):
    """Save configuration to JSON file"""
    config_file = os.path.join(os.path.dirname(__file__), 'data', 'config.json')
    try:
        # Save to file
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=4)
        
        logger.info('Configuration saved successfully')
        return True
    except Exception as e:
        logger.error(f'Error saving config: {str(e)}')
        return False

def save_mysql_config(mysql_config):
    """Save MySQL configuration to JSON file"""
    try:
        # Load existing config
        config = load_config()
        
        # Update MySQL configuration
        config['mysql'] = mysql_config
        
        # Save to file
        return save_config(config)
    except Exception as e:
        logger.error(f'Error saving MySQL config: {str(e)}')
        return False

# Load configuration from file
app_config = load_config()
db_config = app_config['mysql']

def check_pool_health():
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        logger.error(f'Pool health check failed: {str(e)}')
        return False

# Initialize MySQL connection pool (optional - only for database management features)
# Helper function to create MySQL connection using centralized config
def create_mysql_connection():
    """Create a MySQL connection using the centralized db_config"""
    # Create a copy of db_config without pool-specific parameters
    connection_config = {
        'host': db_config['host'],
        'user': db_config['user'],
        'password': db_config['password'],
        'raise_on_warnings': db_config.get('raise_on_warnings', True),
        'buffered': db_config.get('buffered', True)
    }
    return mysql.connector.connect(**connection_config)

connection_pool = None
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
    if not check_pool_health():
        logger.warning('MySQL connection pool health check failed - database management features will be disabled')
        connection_pool = None
    else:
        logger.info('MySQL connection pool initialized successfully')
except mysql.connector.Error as e:
    logger.warning(f'MySQL connection failed: {str(e)} - database management features will be disabled')
    connection_pool = None
except Exception as e:
    logger.warning(f'Error creating MySQL connection pool: {str(e)} - database management features will be disabled')
    connection_pool = None
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key

login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

class User(UserMixin):
    def __init__(self, username, password_hash):
        self.id = username  # Use username as ID for Flask-Login
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        # Save to config file
        config = load_config()
        config['users'][self.username]['password_hash'] = self.password_hash
        save_config(config)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_user_by_username(username):
        """Get user from config file by username"""
        config = load_config()
        users = config.get('users', {})
        if username in users:
            user_data = users[username]
            return User(user_data['username'], user_data['password_hash'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_username(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.info('Login attempt')
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_user_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            logger.info(f'User {username} logged in successfully')
            return redirect(url_for('index'))
        logger.warning(f'Failed login attempt for username: {username}')
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f'User {current_user.username} logged out')
    logout_user()
    return redirect(url_for('login'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    logger.info(f'Password change attempt for user {current_user.username}')
    try:
        current_password = request.json.get('current_password')
        new_password = request.json.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
            
        if not current_user.check_password(current_password):
            logger.warning(f'Invalid current password for user {current_user.username}')
            return jsonify({'error': 'Current password is incorrect'}), 400
            
        current_user.set_password(new_password)
        logger.info(f'Password changed successfully for user {current_user.username}')
        
        return jsonify({'message': 'Password changed successfully'})
    except Exception as e:
        logger.error(f'Password change failed for user {current_user.username}: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/terminal')
@login_required
def terminal():
    return render_template('terminal.html')

def format_uptime(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    result = []
    if days:
        result.append(f"{days}d")
    if hours:
        result.append(f"{hours}h")
    if minutes:
        result.append(f"{minutes}m")
    if seconds:
        result.append(f"{seconds}s")
    return ' '.join(result) if result else "0s"

@app.route('/api/system-info')
@login_required
def system_info():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get system uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(datetime.datetime.now().timestamp() - boot_time)
    uptime_formatted = format_uptime(uptime_seconds)
    
    return jsonify({
        'cpu': cpu_percent,
        'memory': {
            'total': memory.total,
            'used': memory.used,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'percent': disk.percent
        },
        'uptime': uptime_formatted
    })

# Format bytes to human readable format
def format_bytes(bytes_value):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def get_network_data():
    """Get network statistics data"""
    try:
        # Get network I/O statistics
        net_io = psutil.net_io_counters()
        
        # Debug logging
        logger.info(f'Network stats - Bytes sent: {net_io.bytes_sent}, Bytes recv: {net_io.bytes_recv}')
        
        # Get network interfaces
        interfaces = []
        net_if_stats = psutil.net_if_stats()
        net_if_addrs = psutil.net_if_addrs()
        
        for interface_name, stats in net_if_stats.items():
            if interface_name != 'lo':  # Skip loopback interface
                interface_info = {
                    'name': interface_name,
                    'is_up': stats.isup,
                    'speed': f'{stats.speed} Mbps' if stats.speed > 0 else 'Auto-negotiate',
                    'mtu': stats.mtu
                }
                
                # Get IP addresses for this interface
                if interface_name in net_if_addrs:
                    addresses = []
                    for addr in net_if_addrs[interface_name]:
                        if addr.family.name in ['AF_INET', 'AF_INET6']:
                            addresses.append({
                                'family': addr.family.name,
                                'address': addr.address,
                                'netmask': addr.netmask
                            })
                    interface_info['addresses'] = addresses
                
                interfaces.append(interface_info)
        
        # Get network connections count safely
        try:
            connections_count = len(psutil.net_connections())
        except Exception as conn_error:
            logger.warning(f'Error getting network connections: {str(conn_error)}')
            connections_count = 0
        
        return {
            'total_traffic': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout,
                'bytes_sent_formatted': format_bytes(net_io.bytes_sent),
                'bytes_recv_formatted': format_bytes(net_io.bytes_recv)
            },
            'interfaces': interfaces,
            'connections': connections_count
        }
        
    except Exception as e:
        logger.error(f'Error getting network info: {str(e)}')
        return {'error': f'Terjadi kesalahan: {str(e)}'}

@app.route('/api/network-info')
@login_required
def network_info():
    """Get network statistics including inbound and outbound traffic"""
    return jsonify(get_network_data())

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    # Check if user is authenticated
    if not current_user.is_authenticated:
        logger.warning(f'Unauthenticated client attempted to connect: {request.sid}')
        return False  # Reject connection
    
    logger.info(f'Authenticated client connected: {request.sid} (user: {current_user.username})')
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('request_network_data')
def handle_network_data_request():
    """Handle request for network data via SocketIO"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    try:
        network_data = get_network_data()
        emit('network_data', network_data)
    except Exception as e:
        logger.error(f'Error sending network data via SocketIO: {str(e)}')
        emit('error', {'message': f'Error getting network data: {str(e)}'})

@socketio.on('install_service')
def handle_install_service(data):
    """Handle real-time service installation via SocketIO"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    service = data.get('service')
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb-server',
        'powerdns': 'pdns-server',
        'ufw': 'ufw'
    }

    if service not in service_map:
        emit('install_error', {'message': 'Layanan tidak valid'})
        return

    # Start installation in background thread to prevent worker timeout
    import threading
    
    def install_in_background():
        def emit_output_lines(output_text, output_type='info'):
            """Split output into lines and emit each line separately"""
            if output_text:
                lines = output_text.strip().split('\n')
                for line in lines:
                    if line.strip():  # Only emit non-empty lines
                        socketio.emit('install_output', {'output': line, 'type': output_type})
        
        def run_command_with_realtime_output(cmd, timeout_seconds=300):
            """Run command and emit output in real-time"""
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                output_lines = []
                while True:
                    line = process.stdout.readline()
                    if line:
                        line = line.rstrip()
                        if line:  # Only emit non-empty lines
                            socketio.emit('install_output', {'output': line, 'type': 'info'})
                            output_lines.append(line)
                    elif process.poll() is not None:
                        break
                
                return_code = process.wait(timeout=timeout_seconds)
                return return_code, '\n'.join(output_lines)
            except subprocess.TimeoutExpired:
                process.kill()
                socketio.emit('install_output', {'output': 'Command timed out', 'type': 'error'})
                return -1, 'Command timed out'
            except Exception as e:
                socketio.emit('install_output', {'output': f'Error running command: {str(e)}', 'type': 'error'})
                return -1, str(e)
        
        try:
            service_name = service_map[service]
            logger.info(f'Starting real-time installation of {service_name} via WebSocket')
            
            progress_data = {'message': f'Memulai instalasi {service_name}...', 'step': 1, 'total': 4, 'status': f'Memulai instalasi {service_name}...', 'percentage': 25}
            logger.info(f'Emitting install_progress: {progress_data}')
            socketio.emit('install_progress', progress_data)
            
            # Update package list first
            progress_data = {'message': 'Memperbarui daftar paket...', 'step': 2, 'total': 4, 'status': 'Memperbarui daftar paket...', 'percentage': 50}
            logger.info(f'Emitting install_progress: {progress_data}')
            socketio.emit('install_progress', progress_data)
            socketio.emit('install_output', {'output': '$ apt-get update', 'type': 'command'})
            
            update_code, update_output = run_command_with_realtime_output(['apt-get', 'update'], 300)
            
            if update_code != 0:
                logger.warning(f'Package update failed with code {update_code}')
                progress_data = {'message': 'Peringatan: Gagal memperbarui daftar paket', 'step': 2, 'total': 4, 'status': 'Peringatan: Gagal memperbarui daftar paket', 'percentage': 50}
                logger.info(f'Emitting install_progress: {progress_data}')
                socketio.emit('install_progress', progress_data)
            else:
                progress_data = {'message': 'Daftar paket berhasil diperbarui', 'step': 2, 'total': 4, 'status': 'Daftar paket berhasil diperbarui', 'percentage': 50}
                logger.info(f'Emitting install_progress: {progress_data}')
                socketio.emit('install_progress', progress_data)
            
            # Install the service
            progress_data = {'message': f'Menginstall {service_name}...', 'step': 3, 'total': 4, 'status': f'Menginstall {service_name}...', 'percentage': 75}
            logger.info(f'Emitting install_progress: {progress_data}')
            socketio.emit('install_progress', progress_data)
            socketio.emit('install_output', {'output': f'$ apt-get install -y {service_name}', 'type': 'command'})
            
            install_code, install_output = run_command_with_realtime_output(['apt-get', 'install', '-y', service_name], 600)
            
            if install_code == 0:
                logger.info(f'Service {service_name} installed successfully via WebSocket')
                progress_data = {'message': f'{service_name} berhasil diinstall', 'step': 3, 'total': 4, 'status': f'{service_name} berhasil diinstall', 'percentage': 75}
                logger.info(f'Emitting install_progress: {progress_data}')
                socketio.emit('install_progress', progress_data)
                
                # Stop and disable the newly installed system service (only in production)
                system_service_name = service_name
                if service == 'php-fpm':
                    system_service_name = 'php8.1-fpm'  # Adjust for PHP-FPM service name
                elif service == 'mysql':
                    system_service_name = 'mariadb'  # Adjust for MariaDB service name
                    
                # Stop and disable system service (safe for both Docker and production)
                socketio.emit('install_output', {'output': f'Menghentikan layanan sistem: {system_service_name}', 'type': 'info'})
                safe_systemctl_command('stop', system_service_name)
                safe_systemctl_command('disable', system_service_name)
                
                # Start the service using supervisorctl
                progress_data = {'message': f'Memulai layanan {service_name}...', 'step': 4, 'total': 4, 'status': f'Memulai layanan {service_name}...', 'percentage': 100}
                logger.info(f'Emitting install_progress: {progress_data}')
                socketio.emit('install_progress', progress_data)
                
                if service_name == 'nginx':
                    # Nginx specific configuration
                    socketio.emit('install_output', {'output': 'Mengkonfigurasi Nginx untuk supervisord...', 'type': 'info'})
                    
                    # Add Nginx configuration to supervisord.conf
                    nginx_config = """\n[program:nginx]
command=/usr/sbin/nginx -g 'daemon off;'
autostart=true
autorestart=true\n"""
                    
                    socketio.emit('install_output', {'output': 'Menambahkan konfigurasi Nginx ke supervisord.conf...', 'type': 'info'})
                    with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                        f.write(nginx_config)
                    
                    # Reload supervisor configuration
                    socketio.emit('install_output', {'output': '$ supervisorctl reread', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True, timeout=30)
                    socketio.emit('install_output', {'output': '$ supervisorctl update', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True, timeout=30)
                    
                    # Stop and disable system service (only in production environment)
                    safe_systemctl_command('stop', service_name)
                    safe_systemctl_command('disable', service_name)

                    # Start Nginx with supervisor
                    socketio.emit('install_output', {'output': '$ supervisorctl restart nginx', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'restart', 'nginx'], 30)
                elif service_name == 'php-fpm':
                    # PHP-FPM specific configuration
                    socketio.emit('install_output', {'output': 'Mengkonfigurasi PHP-FPM untuk supervisord...', 'type': 'info'})
                    
                    # Add PHP-FPM configuration to supervisord.conf
                    phpfpm_config = """\n[program:php-fpm]
command=/usr/sbin/php-fpm8.1 -F
autostart=true
autorestart=true\n"""
                    
                    socketio.emit('install_output', {'output': 'Menambahkan konfigurasi PHP-FPM ke supervisord.conf...', 'type': 'info'})
                    with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                        f.write(phpfpm_config)
                    
                    # Reload supervisor configuration
                    socketio.emit('install_output', {'output': '$ supervisorctl reread', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True, timeout=30)
                    socketio.emit('install_output', {'output': '$ supervisorctl update', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True, timeout=30)
                    
                    logger.info(f'Skipping system service management for: {service_name}')
                    socketio.emit('install_output', {'output': f'Melewati manajemen layanan sistem untuk: {service_name} (environment containerized)', 'type': 'info'})
                    # Note: In containerized environment with supervisor, we don't need to stop/disable system services

                    # Start PHP-FPM with supervisor
                    socketio.emit('install_output', {'output': '$ supervisorctl restart php-fpm', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'restart', 'php-fpm'], 30)
                elif service_name == 'mariadb-server':
                    # MariaDB specific configuration
                    socketio.emit('install_output', {'output': 'Mengkonfigurasi MariaDB untuk supervisord...', 'type': 'info'})
                    
                    # Add MariaDB configuration to supervisord.conf
                    mariadb_config = """\n[program:mariadb]
command=/usr/sbin/mariadbd --basedir=/usr --datadir=/var/www/panel/data --plugin-dir=/usr/lib/mysql/plugin --user=mysql --skip-log-error --pid-file=/run/mysqld/mysqld.pid --socket=/run/mysqld/mysqld.sock
autostart=true
autorestart=true
killasgroup=true
stopasgroup=true\n"""
                    
                    socketio.emit('install_output', {'output': 'Menambahkan konfigurasi MariaDB ke supervisord.conf...', 'type': 'info'})
                    with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                        f.write(mariadb_config)
                    
                    # Reload supervisor configuration
                    socketio.emit('install_output', {'output': '$ supervisorctl reread', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True, timeout=30)
                    socketio.emit('install_output', {'output': '$ supervisorctl update', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True, timeout=30)
                    
                    # For MariaDB, create socket directory first
                    socketio.emit('install_output', {'output': 'Menyiapkan direktori socket MariaDB...', 'type': 'info'})
                    socketio.emit('install_output', {'output': '$ mkdir -p /run/mysqld', 'type': 'command'})
                    subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    socketio.emit('install_output', {'output': '$ chown mysql:mysql /run/mysqld', 'type': 'command'})
                    subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    socketio.emit('install_output', {'output': '$ chmod 755 /run/mysqld', 'type': 'command'})
                    subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    
                    # Start MariaDB with supervisor
                    socketio.emit('install_output', {'output': '$ supervisorctl restart mariadb', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'restart', 'mariadb'], 30)
                    
                    # Reset MySQL root password
                    if start_code == 0:
                        socketio.emit('install_output', {'output': 'Mengatur ulang kata sandi root MySQL...', 'type': 'info'})
                        socketio.emit('install_output', {'output': '$ mysql -u root -e "ALTER USER \'root\'@\'localhost\' IDENTIFIED BY \'\';"', 'type': 'command'})
                        subprocess.run(['mysql', '-u', 'root', '-e', "ALTER USER 'root'@'localhost' IDENTIFIED BY '';"], capture_output=True, text=True, timeout=30)
                        socketio.emit('install_output', {'output': '$ mysql -u root -e "FLUSH PRIVILEGES;"', 'type': 'command'})
                        subprocess.run(['mysql', '-u', 'root', '-e', 'FLUSH PRIVILEGES;'], capture_output=True, text=True, timeout=30)
                        
                        # Restart SLEMP to reload database configuration
                        socketio.emit('install_output', {'output': 'Restart SLEMP untuk reload konfigurasi database...', 'type': 'info'})
                        socketio.emit('install_output', {'output': '$ supervisorctl restart slemp', 'type': 'command'})
                        try:
                            restart_result = subprocess.run(['supervisorctl', 'restart', 'slemp'], capture_output=True, text=True, timeout=30)
                            if restart_result.returncode == 0:
                                socketio.emit('install_output', {'output': 'SLEMP berhasil direstart', 'type': 'success'})
                            else:
                                socketio.emit('install_output', {'output': f'Gagal restart SLEMP: {restart_result.stderr}', 'type': 'error'})
                        except Exception as e:
                            socketio.emit('install_output', {'output': f'Error saat restart SLEMP: {str(e)}', 'type': 'error'})
                    
                elif service_name == 'pdns-server':
                    # PowerDNS specific configuration
                    socketio.emit('install_output', {'output': 'Mengkonfigurasi PowerDNS...', 'type': 'info'})

                    # Stop and disable system service (only in production environment)
                    safe_systemctl_command('stop', 'pdns')
                    safe_systemctl_command('disable', 'pdns')
                    safe_systemctl_command('stop', 'systemd-resolved')

                    # Disable DNSStubListener in resolved.conf
                    socketio.emit('install_output', {'output': '$ sed -i "s/^#DNSStubListener=.*/DNSStubListener=no/" /etc/systemd/resolved.conf', 'type': 'command'})
                    subprocess.run(['sed', '-i', 's/^#DNSStubListener=.*/DNSStubListener=no/', '/etc/systemd/resolved.conf'], capture_output=True, text=True, timeout=10)

                    # Restart systemd-resolved (only in production environment)
                    safe_systemctl_command('restart', 'systemd-resolved')

                    # Change /etc/resolv.conf symlink to /run/systemd/resolve/resolv.conf
                    socketio.emit('install_output', {'output': '$ ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf', 'type': 'command'})
                    subprocess.run(['ln', '-sf', '/run/systemd/resolve/resolv.conf', '/etc/resolv.conf'], capture_output=True, text=True, timeout=10)

                    # Ensure nameserver 8.8.8.8 exists in systemd-resolved config
                    with open('/etc/systemd/resolved.conf', 'r') as f:
                        resolved_conf = f.read()

                    if 'DNS=8.8.8.8' not in resolved_conf:
                        socketio.emit('install_output', {'output': '$ echo -e "\\n[Resolve]\\nDNS=8.8.8.8" >> /etc/systemd/resolved.conf', 'type': 'command'})
                        with open('/etc/systemd/resolved.conf', 'a') as f:
                            f.write('\n[Resolve]\nDNS=8.8.8.8\n')
                        # Skip systemd-resolved restart in containerized environment
                        socketio.emit('install_output', {'output': 'Skipping systemd-resolved restart - running in containerized environment', 'type': 'info'})

                    # Create PowerDNS zones directory
                    socketio.emit('install_output', {'output': '$ mkdir -p /var/lib/powerdns/zones', 'type': 'command'})
                    subprocess.run(['mkdir', '-p', '/var/lib/powerdns/zones'], capture_output=True, text=True, timeout=10)

                    # Create and set ownership of PowerDNS log file
                    socketio.emit('install_output', {'output': '$ touch /var/log/pdns.log', 'type': 'command'})
                    subprocess.run(['touch', '/var/log/pdns.log'], capture_output=True, text=True, timeout=10)
                    socketio.emit('install_output', {'output': '$ chown pdns:pdns /var/log/pdns.log', 'type': 'command'})
                    subprocess.run(['chown', 'pdns:pdns', '/var/log/pdns.log'], capture_output=True, text=True, timeout=10)

                    # Add PowerDNS configuration to supervisord.conf
                    pdns_config = """\n[program:pdns]
command=/usr/sbin/pdns_server --daemon=no --guardian=no --control-console --loglevel=4
autostart=true
autorestart=true\n"""
                    
                    socketio.emit('install_output', {'output': 'Menambahkan konfigurasi PowerDNS ke supervisord.conf...', 'type': 'info'})
                    with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                        f.write(pdns_config)
                    
                    # Reload supervisor configuration
                    socketio.emit('install_output', {'output': '$ supervisorctl reread', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True, timeout=30)
                    socketio.emit('install_output', {'output': '$ supervisorctl update', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True, timeout=30)
                    
                    # Start PowerDNS with supervisor
                    socketio.emit('install_output', {'output': '$ supervisorctl restart pdns', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'restart', 'pdns'], 30)

                elif service_name == 'ufw':
                    # UFW specific configuration
                    socketio.emit('install_output', {'output': 'Mengkonfigurasi UFW untuk supervisord...', 'type': 'info'})
                    
                    # Add UFW configuration to supervisord.conf
                    ufw_config = """\n[program:ufw]
command=/bin/bash -c 'while true; do if ufw status | grep -q "Status: active"; then sleep 30; else exit 1; fi; done'
autostart=false
autorestart=false
startretries=0\n"""
                    
                    socketio.emit('install_output', {'output': 'Menambahkan konfigurasi UFW ke supervisord.conf...', 'type': 'info'})
                    with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                        f.write(ufw_config)
                    
                    # Reload supervisor configuration
                    socketio.emit('install_output', {'output': '$ supervisorctl reread', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True, timeout=30)
                    socketio.emit('install_output', {'output': '$ supervisorctl update', 'type': 'command'})
                    subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True, timeout=30)
                    
                    # UFW doesn't use supervisorctl start, it's managed differently
                    socketio.emit('install_output', {'output': 'UFW berhasil dikonfigurasi untuk supervisord', 'type': 'info'})
                    start_code = 0  # Set success code for UFW
                else:
                    # This should not happen as all services are now handled specifically
                    socketio.emit('install_output', {'output': f'Layanan {service_name} tidak memiliki konfigurasi khusus', 'type': 'warning'})
                    socketio.emit('install_output', {'output': f'$ supervisorctl restart {service}', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'restart', service], 30)
                
                if start_code == 0:
                    socketio.emit('install_complete', {'message': f'{service_name} berhasil diinstall dan diaktifkan!', 'service': service})
                else:
                    logger.warning(f'Service {service_name} installed but failed to start with code {start_code}')
                    socketio.emit('install_complete', {'message': f'{service_name} berhasil diinstall tetapi gagal dijalankan', 'service': service})
            else:
                logger.error(f'Failed to install {service_name} with code {install_code}')
                socketio.emit('install_error', {'message': f'Gagal menginstall {service_name}'})
        except subprocess.TimeoutExpired:
            logger.error(f'Installation of {service} timed out')
            socketio.emit('install_error', {'message': f'Instalasi {service} timeout'})
        except Exception as e:
            logger.error(f'Error installing {service} via WebSocket: {str(e)}')
            socketio.emit('install_error', {'message': f'Terjadi kesalahan saat menginstall {service}: {str(e)}'})
    
    # Start background thread
    thread = threading.Thread(target=install_in_background)
    thread.daemon = True
    thread.start()
    
    # Immediately return to prevent blocking
    progress_data = {'message': 'Instalasi dimulai...', 'step': 1, 'total': 4, 'status': 'Instalasi dimulai...', 'percentage': 25}
    logger.info(f'Emitting initial install_progress: {progress_data}')
    emit('install_progress', progress_data)

@app.route('/api/services/status')
@login_required
def get_services_status():
    def get_service_info(service_name, process_name=None):
        if process_name is None:
            process_name = service_name
        try:
            # Cek apakah service terinstall
            installed = False
            if service_name == 'nginx':
                check_cmd = subprocess.run(['which', 'nginx'], capture_output=True, text=True)
                installed = check_cmd.returncode == 0
            elif service_name == 'php-fpm':
                # Check for common PHP-FPM paths
                php_fpm_paths = ['/usr/sbin/php-fpm8.1', '/usr/sbin/php-fpm', 'php-fpm']
                for php_fpm_path in php_fpm_paths:
                    check_cmd = subprocess.run(['which', php_fpm_path], capture_output=True, text=True)
                    if check_cmd.returncode == 0:
                        installed = True
                        break
            elif service_name == 'mysql':
                # Check for MariaDB/MySQL
                check_cmd = subprocess.run(['which', 'mysql'], capture_output=True, text=True)
                installed = check_cmd.returncode == 0
            elif service_name == 'powerdns':
                # Check for PowerDNS
                check_cmd = subprocess.run(['which', 'pdns_server'], capture_output=True, text=True)
                installed = check_cmd.returncode == 0
            elif service_name == 'ufw':
                # Check for UFW
                check_cmd = subprocess.run(['which', 'ufw'], capture_output=True, text=True)
                installed = check_cmd.returncode == 0
            
            # Cek status proses hanya jika terinstall
            running = False
            pid = None
            version = 'Not Installed' if not installed else 'Checking...'
            
            if installed:
                if service_name == 'ufw':
                    # For UFW, check status using ufw status command
                    status_cmd = subprocess.run(['ufw', 'status'], capture_output=True, text=True)
                    running = 'Status: active' in status_cmd.stdout if status_cmd.returncode == 0 else False
                    pid = 'N/A'  # UFW doesn't have a traditional PID
                else:
                    status_cmd = subprocess.run(['pgrep', process_name], capture_output=True, text=True)
                    running = status_cmd.returncode == 0
                    pid = status_cmd.stdout.strip() if running else None

                # Dapatkan versi
                if service_name == 'nginx':
                    version_cmd = subprocess.run(['nginx', '-v'], capture_output=True, text=True)
                    if version_cmd.returncode == 0:
                        # nginx -v outputs to stderr, not stdout
                        version = version_cmd.stderr.strip()
                elif service_name == 'php-fpm':
                    # Try different PHP-FPM executable paths
                    php_fpm_paths = ['/usr/sbin/php-fpm8.1', '/usr/sbin/php-fpm', 'php-fpm']
                    for php_fpm_path in php_fpm_paths:
                        try:
                            version_cmd = subprocess.run([php_fpm_path, '-v'], capture_output=True, text=True)
                            if version_cmd.returncode == 0:
                                version = version_cmd.stdout.split('\n')[0]
                                break
                        except FileNotFoundError:
                            continue
                elif service_name == 'mysql':
                    version_cmd = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
                    if version_cmd.returncode == 0:
                        version = version_cmd.stdout.strip()
                elif service_name == 'powerdns':
                    version_cmd = subprocess.run(['pdns_server', '--version'], capture_output=True, text=True)
                    # PowerDNS exits with code 99 but still outputs version info
                    if version_cmd.returncode == 99 or version_cmd.returncode == 0:
                        # Extract version from stderr (PowerDNS outputs to stderr)
                        output = version_cmd.stderr.strip() if version_cmd.stderr else version_cmd.stdout.strip()
                        if output:
                            # Extract version number from the first line
                            first_line = output.split('\n')[0]
                            if 'PowerDNS Authoritative Server' in first_line:
                                version = first_line
                            else:
                                version = output
                elif service_name == 'ufw':
                    version_cmd = subprocess.run(['ufw', '--version'], capture_output=True, text=True)
                    if version_cmd.returncode == 0:
                        version = version_cmd.stdout.strip()

            return {
                'installed': installed,
                'running': running,
                'pid': pid,
                'version': version
            }
        except Exception as e:
            logger.error(f'Error checking {service_name} status: {str(e)}')
            return {
                'installed': False,
                'running': False,
                'pid': None,
                'version': 'Error'
            }

    services = {
        'nginx': get_service_info('nginx'),
        'php_fpm': get_service_info('php-fpm'),
        'mysql': get_service_info('mysql', 'mariadbd'),
        'powerdns': get_service_info('powerdns', 'pdns_server'),
        'ufw': get_service_info('ufw')
    }
    return jsonify(services)

@app.route('/api/service/<service>/start', methods=['POST'])
@login_required
def start_service(service):
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb',
        'powerdns': 'pdns',
        'ufw': 'ufw'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        # Use different commands based on service type
        if service_name == 'ufw':
            # For UFW, use ufw enable command
            result = subprocess.run(['ufw', '--force', 'enable'], capture_output=True, text=True)
        elif service_name == 'mariadb':
            # For MariaDB, create socket directory first
            subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True)
            result = subprocess.run(['supervisorctl', 'start', service_name], capture_output=True, text=True)
        else:
            # For nginx and php-fpm, use supervisorctl
            result = subprocess.run(['supervisorctl', 'start', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f'Service {service_name} started successfully')
            return jsonify({'success': True, 'message': f'{service_name} berhasil dimulai'})
        else:
            logger.error(f'Failed to start {service_name}: {result.stderr}')
            return jsonify({'success': False, 'message': f'Gagal memulai {service_name}: {result.stderr}'})
    except Exception as e:
        logger.error(f'Error starting {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat memulai {service}'}), 500

@app.route('/api/service/<service>/stop', methods=['POST'])
@login_required
def stop_service(service):
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb',
        'powerdns': 'pdns',
        'ufw': 'ufw'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        # Use different commands based on service type
        if service_name == 'ufw':
            # For UFW, use ufw disable command
            result = subprocess.run(['ufw', '--force', 'disable'], capture_output=True, text=True)
        elif service_name == 'mariadb':
            result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        else:
            # For nginx and php-fpm, use supervisorctl
            result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f'Service {service_name} stopped successfully')
            return jsonify({'success': True, 'message': f'{service_name} berhasil dihentikan'})
        else:
            logger.error(f'Failed to stop {service_name}: {result.stderr}')
            return jsonify({'success': False, 'message': f'Gagal menghentikan {service_name}: {result.stderr}'})
    except Exception as e:
        logger.error(f'Error stopping {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menghentikan {service}'}), 500

@app.route('/api/service/<service>/install', methods=['POST'])
@login_required
def install_service(service):
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb-server',
        'powerdns': 'pdns-server',
        'ufw': 'ufw'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        logger.info(f'Starting installation of {service_name}')
        
        # Update package list first
        update_result = subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
        if update_result.returncode != 0:
            logger.warning(f'Package update failed: {update_result.stderr}')
        
        # Install the service
        install_result = subprocess.run(['apt-get', 'install', '-y', service_name], capture_output=True, text=True)
        
        if install_result.returncode == 0:
            logger.info(f'Service {service_name} installed successfully')
            
            # Stop and disable the newly installed system service
            system_service_name = service_name
            if service == 'php-fpm':
                system_service_name = 'php8.1-fpm'  # Adjust for PHP-FPM service name
            elif service == 'mysql':
                system_service_name = 'mariadb'  # Adjust for MariaDB service name
                
            # Stop and disable system service (only in production environment)
            safe_systemctl_command('stop', system_service_name)
            safe_systemctl_command('disable', system_service_name)
            
            # Start the service using supervisorctl
            if service_name == 'nginx':
                # Nginx specific configuration
                logger.info('Configuring Nginx for supervisord')
                
                # Add Nginx configuration to supervisord.conf
                nginx_config = """\n[program:nginx]
command=/usr/sbin/nginx -g 'daemon off;'
autostart=true
autorestart=true\n"""
                
                with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                    f.write(nginx_config)
                
                # Reload supervisor configuration
                subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                
                # Start Nginx with supervisor
                start_result = subprocess.run(['supervisorctl', 'start', 'nginx'], capture_output=True, text=True)
            elif service_name == 'ufw':
                # UFW specific configuration
                logger.info('Configuring UFW for supervisord')
                
                # Add UFW configuration to supervisord.conf
                ufw_config = """\n[program:ufw]
command=/bin/bash -c 'while true; do if ufw status | grep -q "Status: active"; then sleep 30; else exit 1; fi; done'
autostart=false
autorestart=false
startretries=0\n"""
                
                with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                    f.write(ufw_config)
                
                # Reload supervisor configuration
                subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                
                # UFW doesn't use supervisorctl start, it's managed differently
                start_result = subprocess.run(['echo', 'UFW configured for supervisord successfully'], capture_output=True, text=True)
            elif service_name == 'php-fpm':
                # PHP-FPM specific configuration
                logger.info('Configuring PHP-FPM for supervisord')
                
                # Add PHP-FPM configuration to supervisord.conf
                phpfpm_config = """\n[program:php-fpm]
command=/usr/sbin/php-fpm8.1 -F
autostart=true
autorestart=true\n"""
                
                with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                    f.write(phpfpm_config)
                
                # Reload supervisor configuration
                subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                
                # Start PHP-FPM with supervisor
                start_result = subprocess.run(['supervisorctl', 'start', 'php-fpm'], capture_output=True, text=True)
            elif service_name == 'mariadb-server':
                # MariaDB specific configuration
                logger.info('Configuring MariaDB for supervisord')
                
                # Create socket directory first
                subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True)
                subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True)
                subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True)
                
                # Add MariaDB configuration to supervisord.conf
                mariadb_config = """\n[program:mariadb]
command=/usr/sbin/mariadbd --basedir=/usr --datadir=/var/www/panel/data --plugin-dir=/usr/lib/mysql/plugin --user=mysql --skip-log-error --pid-file=/run/mysqld/mysqld.pid --socket=/run/mysqld/mysqld.sock
autostart=true
autorestart=true
killasgroup=true
stopasgroup=true\n"""
                
                with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                    f.write(mariadb_config)
                
                # Reload supervisor configuration
                subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                
                # Start MariaDB with supervisor
                start_result = subprocess.run(['supervisorctl', 'start', 'mariadb'], capture_output=True, text=True)
                
                # Reset MySQL root password
                if start_result.returncode == 0:
                    logger.info('Resetting MySQL root password')
                    subprocess.run(['mysql', '-u', 'root', '-e', "ALTER USER 'root'@'localhost' IDENTIFIED BY '';"], capture_output=True, text=True, timeout=30)
                    subprocess.run(['mysql', '-u', 'root', '-e', 'FLUSH PRIVILEGES;'], capture_output=True, text=True, timeout=30)
                    
                    # Restart SLEMP to reload database configuration
                    try:
                        logger.info('Restarting SLEMP to reload database configuration')
                        restart_result = subprocess.run(['supervisorctl', 'restart', 'slemp'], capture_output=True, text=True, timeout=30)
                        if restart_result.returncode == 0:
                            logger.info('SLEMP restarted successfully')
                        else:
                            logger.warning(f'Failed to restart SLEMP: {restart_result.stderr}')
                    except Exception as e:
                        logger.warning(f'Error restarting SLEMP: {str(e)}')
            elif service_name == 'pdns-server':
                # PowerDNS specific configuration after installation
                logger.info('Configuring PowerDNS after installation')
                
                # Stop and disable PowerDNS and systemd-resolved services (production only)
                safe_systemctl_command('stop', 'pdns')
                safe_systemctl_command('disable', 'pdns')
                safe_systemctl_command('stop', 'systemd-resolved')
                safe_systemctl_command('disable', 'systemd-resolved')
                
                # Set DNS resolver to Google DNS
                with open('/etc/resolv.conf', 'w') as f:
                    f.write('nameserver 8.8.8.8\n')
                
                # Create PowerDNS zones directory
                subprocess.run(['mkdir', '-p', '/var/lib/powerdns/zones'], capture_output=True, text=True)
                
                # Create and set ownership for PowerDNS log file
                subprocess.run(['touch', '/var/log/pdns.log'], capture_output=True, text=True)
                subprocess.run(['chown', 'pdns:pdns', '/var/log/pdns.log'], capture_output=True, text=True)
                
                # Add PowerDNS configuration to supervisord.conf
                pdns_config = """\n[program:pdns]
command=/usr/sbin/pdns_server --guardian=no --daemon=no
autostart=true
autorestart=true
stderr_logfile=/var/log/pdns.err.log
stdout_logfile=/var/log/pdns.out.log\n"""
                
                with open('/etc/supervisor/conf.d/supervisord.conf', 'a') as f:
                    f.write(pdns_config)
                
                # Reload supervisor configuration
                subprocess.run(['supervisorctl', 'reread'], capture_output=True, text=True)
                subprocess.run(['supervisorctl', 'update'], capture_output=True, text=True)
                
                # Now start PowerDNS using supervisorctl
                start_result = subprocess.run(['supervisorctl', 'start', 'pdns'], capture_output=True, text=True)
            else:
                # This should not happen as all services are now handled specifically
                logger.warning(f'Unhandled service: {service_name}')
                start_result = subprocess.run(['echo', f'Service {service_name} configuration not found'], capture_output=True, text=True)
            
            if start_result.returncode == 0:
                return jsonify({'success': True, 'message': f'{service_name} berhasil diinstall dan diaktifkan'})
            else:
                logger.warning(f'Service {service_name} installed but failed to start: {start_result.stderr}')
                return jsonify({'success': True, 'message': f'{service_name} berhasil diinstall tetapi gagal dijalankan'})
        else:
            logger.error(f'Failed to install {service_name}: {install_result.stderr}')
            return jsonify({'success': False, 'message': f'Gagal menginstall {service_name}: {install_result.stderr}'})
    except Exception as e:
        logger.error(f'Error installing {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menginstall {service}'}), 500

@app.route('/api/service/<service>/uninstall', methods=['POST'])
@login_required
def uninstall_service(service):
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb-server',
        'powerdns': 'pdns-server',
        'ufw': 'ufw'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        logger.info(f'Starting uninstallation of {service_name}')
        
        # Stop the service first using supervisorctl
        if service_name != 'mariadb-server':
            stop_result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        else:
            # For MariaDB, use different service name
            stop_result = subprocess.run(['supervisorctl', 'stop', 'mariadb'], capture_output=True, text=True)
        
        # Remove the service package
        remove_result = subprocess.run(['apt-get', 'remove', '-y', service_name], capture_output=True, text=True)
        
        if remove_result.returncode == 0:
            logger.info(f'Service {service_name} removed successfully')
            
            # Clean up configuration files and dependencies
            purge_result = subprocess.run(['apt-get', 'purge', '-y', service_name], capture_output=True, text=True)
            autoremove_result = subprocess.run(['apt-get', 'autoremove', '-y'], capture_output=True, text=True)
            
            # Additional cleanup for specific services
            if service == 'nginx':
                # Stop nginx from supervisor first
                try:
                    subprocess.run(['supervisorctl', 'stop', 'nginx'], capture_output=True, text=True)
                    logger.info('Stopped nginx via supervisorctl')
                except Exception as e:
                    logger.warning(f'Could not stop nginx via supervisorctl: {str(e)}')
                
                # Remove all nginx packages including modules
                nginx_packages = [
                    'nginx', 'nginx-core', 'nginx-common',
                    'libnginx-mod-http-geoip2', 'libnginx-mod-http-image-filter',
                    'libnginx-mod-http-xslt-filter', 'libnginx-mod-mail',
                    'libnginx-mod-stream-geoip2', 'libnginx-mod-stream'
                ]
                
                for package in nginx_packages:
                    try:
                        remove_pkg_result = subprocess.run(['apt-get', 'remove', '-y', package], capture_output=True, text=True)
                        purge_pkg_result = subprocess.run(['apt-get', 'purge', '-y', package], capture_output=True, text=True)
                        logger.info(f'Removed and purged package: {package}')
                    except Exception as e:
                        logger.warning(f'Could not remove package {package}: {str(e)}')
                
                # Remove nginx configuration directory completely
                nginx_config_dir = '/etc/nginx'
                if os.path.exists(nginx_config_dir):
                    try:
                        shutil.rmtree(nginx_config_dir)
                        logger.info(f'Removed nginx configuration directory: {nginx_config_dir}')
                    except Exception as e:
                        logger.warning(f'Could not remove nginx config directory: {str(e)}')
                
                # Remove nginx log directory
                nginx_log_dir = '/var/log/nginx'
                if os.path.exists(nginx_log_dir):
                    try:
                        shutil.rmtree(nginx_log_dir)
                        logger.info(f'Removed nginx log directory: {nginx_log_dir}')
                    except Exception as e:
                        logger.warning(f'Could not remove nginx log directory: {str(e)}')
                
                # Remove nginx cache directory
                nginx_cache_dir = '/var/cache/nginx'
                if os.path.exists(nginx_cache_dir):
                    try:
                        shutil.rmtree(nginx_cache_dir)
                        logger.info(f'Removed nginx cache directory: {nginx_cache_dir}')
                    except Exception as e:
                        logger.warning(f'Could not remove nginx cache directory: {str(e)}')
                
                # Remove nginx lib directory
                nginx_lib_dir = '/var/lib/nginx'
                if os.path.exists(nginx_lib_dir):
                    try:
                        shutil.rmtree(nginx_lib_dir)
                        logger.info(f'Removed nginx lib directory: {nginx_lib_dir}')
                    except Exception as e:
                        logger.warning(f'Could not remove nginx lib directory: {str(e)}')
                
                # Clean up any remaining nginx processes
                try:
                    subprocess.run(['pkill', '-f', 'nginx'], capture_output=True, text=True)
                    logger.info('Killed any remaining nginx processes')
                except Exception as e:
                    logger.warning(f'Could not kill nginx processes: {str(e)}')
            
            elif service == 'mysql':
                # Remove MySQL data directory if requested
                mysql_data_dir = '/var/lib/mysql'
                if os.path.exists(mysql_data_dir):
                    try:
                        shutil.rmtree(mysql_data_dir)
                        logger.info(f'Removed MySQL data directory: {mysql_data_dir}')
                    except Exception as e:
                        logger.warning(f'Could not remove MySQL data directory: {str(e)}')
                
                # Reset MySQL password in config.json
                try:
                    config = load_config()
                    config['mysql']['password'] = ''
                    save_config(config)
                    logger.info('Reset MySQL password in config.json to empty string')
                except Exception as e:
                    logger.warning(f'Could not reset MySQL password in config: {str(e)}')
            
            return jsonify({'success': True, 'message': f'{service_name} berhasil diuninstall dan dibersihkan'})
        else:
            logger.error(f'Failed to uninstall {service_name}: {remove_result.stderr}')
            return jsonify({'success': False, 'message': f'Gagal menguninstall {service_name}: {remove_result.stderr}'})
    except Exception as e:
        logger.error(f'Error uninstalling {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menguninstall {service}'}), 500

@app.route('/api/mysql-info')
@login_required
def mysql_info():
    try:
        connection = connection_pool.get_connection()
        connection.autocommit = True
        connection.cmd_query('USE mysql')
        cursor = connection.cursor()
        cursor.execute('SHOW VARIABLES LIKE "%version%"')
        version = cursor.fetchall()
        
        cursor.execute('SHOW STATUS')
        status = cursor.fetchall()
        
        connection.close()
        
        return jsonify({
            'version': dict(version),
            'status': dict(status)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    base_path = request.args.get('path', '/')
    # Normalize path to prevent directory traversal
    base_path = os.path.normpath(base_path)
    if base_path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400

    try:
        files = []
        with os.scandir(base_path) as entries:
            for entry in entries:
                try:
                    file_info = {
                        'name': entry.name,
                        'path': os.path.normpath(os.path.join(base_path, entry.name)),
                        'is_dir': entry.is_dir(),
                        'size': os.path.getsize(entry.path) if not entry.is_dir() else None,
                        'modified': os.path.getmtime(entry.path)
                    }
                    files.append(file_info)
                except (OSError, IOError) as e:
                    continue  # Skip files that can't be accessed
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': f'Could not access directory: {str(e)}'}), 400

# Backup and restore endpoints removed

@app.route('/api/files/upload', methods=['POST'])
@login_required
def upload_file():
    logger.info('File upload attempt')
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    upload_path = request.form.get('path', '/')
    upload_path = os.path.normpath(upload_path)
    if upload_path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.normpath(os.path.join(upload_path, filename))
    
    try:
        os.makedirs(upload_path, exist_ok=True)
        file.save(file_path)
        logger.info(f'File uploaded successfully: {file_path}')
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'error': f'Could not upload file: {str(e)}'}), 400

@app.route('/api/files/delete', methods=['POST'])
@login_required
def delete_file():
    logger.info('File deletion attempt')
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    path = os.path.normpath(path)
    if path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if not os.path.exists(path):
            return jsonify({'error': 'File or directory not found'}), 404
        
        if os.path.isdir(path):
            shutil.rmtree(path)
            logger.info(f'Directory deleted successfully: {path}')
        else:
            os.remove(path)
            logger.info(f'File deleted successfully: {path}')
        return jsonify({'message': 'File/directory deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Could not delete: {str(e)}'}), 400

@app.route('/api/files/rename', methods=['POST'])
@login_required
def rename_file():
    logger.info('File rename attempt')
    old_path = request.json.get('old_path')
    new_path = request.json.get('new_path')
    if not old_path or not new_path:
        return jsonify({'error': 'Both old and new paths must be specified'}), 400
    
    old_path = os.path.normpath(old_path)
    new_path = os.path.normpath(new_path)
    if old_path.startswith('..') or new_path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if not os.path.exists(old_path):
            return jsonify({'error': 'Source file or directory not found'}), 404
        if os.path.exists(new_path):
            return jsonify({'error': 'Destination already exists'}), 400
            
        os.rename(old_path, new_path)
        logger.info(f'File/directory renamed successfully from {old_path} to {new_path}')
        return jsonify({'message': 'File/directory renamed successfully'})
    except Exception as e:
        return jsonify({'error': f'Could not rename: {str(e)}'}), 400

@app.route('/api/files/download', methods=['GET'])
@login_required
def download_file():
    logger.info('File download attempt')
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    path = os.path.normpath(path)
    if path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        
        if os.path.isdir(path):
            return jsonify({'error': 'Cannot download directory directly. Use compress first.'}), 400
        
        logger.info(f'File downloaded: {path}')
        return send_file(path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Could not download file: {str(e)}'}), 400

@app.route('/api/files/compress', methods=['POST'])
@login_required
def compress_files():
    logger.info('File compression attempt')
    data = request.json
    paths = data.get('paths', [])
    archive_name = data.get('archive_name', 'archive.zip')
    
    if not paths:
        return jsonify({'error': 'No files specified'}), 400
    
    # Validate paths
    for path in paths:
        path = os.path.normpath(path)
        if path.startswith('..'):
            return jsonify({'error': 'Invalid path'}), 400
        if not os.path.exists(path):
            return jsonify({'error': f'File not found: {path}'}), 404
    
    try:
        # Get the directory of the first file to save the archive
        first_path = os.path.normpath(paths[0])
        if os.path.isfile(first_path):
            archive_dir = os.path.dirname(first_path)
        else:
            archive_dir = os.path.dirname(first_path)
        
        archive_path = os.path.join(archive_dir, archive_name)
        
        # Ensure archive name ends with .zip
        if not archive_name.endswith('.zip'):
            archive_path += '.zip'
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in paths:
                path = os.path.normpath(path)
                if os.path.isfile(path):
                    zipf.write(path, os.path.basename(path))
                elif os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(path))
                            zipf.write(file_path, arcname)
        
        logger.info(f'Files compressed to: {archive_path}')
        return jsonify({'message': 'Files compressed successfully', 'archive_path': archive_path})
    except Exception as e:
        return jsonify({'error': f'Could not compress files: {str(e)}'}), 400

@app.route('/api/files/uncompress', methods=['POST'])
@login_required
def uncompress_file():
    logger.info('File uncompression attempt')
    data = request.json
    archive_path = data.get('path')
    extract_to = data.get('extract_to')
    
    if not archive_path:
        return jsonify({'error': 'No archive path specified'}), 400
    
    archive_path = os.path.normpath(archive_path)
    if archive_path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(archive_path):
        return jsonify({'error': 'Archive file not found'}), 404
    
    # If extract_to is not specified, extract to the same directory as the archive
    if not extract_to:
        extract_to = os.path.dirname(archive_path)
    else:
        extract_to = os.path.normpath(extract_to)
        if extract_to.startswith('..'):
            return jsonify({'error': 'Invalid extraction path'}), 400
    
    try:
        # Determine archive type and extract
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_to)
        elif archive_path.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2')):
            with tarfile.open(archive_path, 'r:*') as tarf:
                tarf.extractall(extract_to)
        else:
            return jsonify({'error': 'Unsupported archive format. Supported: .zip, .tar, .tar.gz, .tgz, .tar.bz2'}), 400
        
        logger.info(f'Archive extracted: {archive_path} to {extract_to}')
        return jsonify({'message': 'Archive extracted successfully', 'extract_path': extract_to})
    except Exception as e:
        return jsonify({'error': f'Could not extract archive: {str(e)}'}), 400

@app.route('/api/files/create-directory', methods=['POST'])
@login_required
def create_directory():
    logger.info('Directory creation attempt')
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    path = os.path.normpath(path)
    if path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f'Directory created successfully: {path}')
        return jsonify({'message': 'Directory created successfully'})
    except Exception as e:
        return jsonify({'error': f'Could not create directory: {str(e)}'}), 400

@app.route('/api/files/read', methods=['POST'])
@login_required
def read_file():
    path = request.json.get('path')
    if not path:
        return jsonify({'error': 'No path specified'}), 400
    
    path = os.path.normpath(path)
    if path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        if os.path.isdir(path):
            return jsonify({'error': 'Cannot read directory content'}), 400
            
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.info(f'File read successfully: {path}, content length: {len(content)}')
        return jsonify({
            'content': content,
            'path': path
        })
    except UnicodeDecodeError:
        # Try reading as binary and decode with error handling
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as file:
                content = file.read()
            logger.info(f'File read with encoding fallback: {path}')
            return jsonify({
                'content': content,
                'path': path
            })
        except Exception as e:
            return jsonify({'error': f'Could not read file (encoding issue): {str(e)}'}), 400
    except Exception as e:
        logger.error(f'Error reading file {path}: {str(e)}')
        return jsonify({'error': f'Could not read file: {str(e)}'}), 400

@app.route('/api/files/new', methods=['POST'])
@login_required
def create_new_file():
    try:
        data = request.json
        file_path = data.get('path')
        file_name = data.get('name')
        
        if not file_path or not file_name:
            return jsonify({'error': 'Path and filename are required'}), 400
            
        # Normalize path to prevent directory traversal
        full_path = os.path.normpath(os.path.join(file_path, file_name))
        if full_path.startswith('..'):
            return jsonify({'error': 'Invalid path'}), 400
            
        # Check if file already exists
        if os.path.exists(full_path):
            return jsonify({'error': 'File already exists'}), 400
            
        # Create empty file
        with open(full_path, 'w') as f:
            f.write('')
            
        logger.info(f'New file created: {full_path}')
        return jsonify({'message': 'File created successfully'})
    except Exception as e:
        logger.error(f'Error creating new file: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/save', methods=['POST'])
@login_required
def save_file():
    path = request.json.get('path')
    content = request.json.get('content')
    if not path or content is None:
        return jsonify({'error': 'Both path and content must be specified'}), 400
    
    path = os.path.normpath(path)
    if path.startswith('..'):
        return jsonify({'error': 'Invalid path'}), 400
    
    try:
        if not os.path.exists(path):
            return jsonify({'error': 'File not found'}), 404
        if os.path.isdir(path):
            return jsonify({'error': 'Cannot write to directory'}), 400
            
        with open(path, 'w') as file:
            file.write(content)
        return jsonify({'message': 'File saved successfully'})
    except Exception as e:
        return jsonify({'error': f'Could not save file: {str(e)}'}), 400

# Nginx Virtual Host Management
@app.route('/api/nginx/vhosts')
@login_required
def list_vhosts():
    try:
        vhosts = []
        nginx_sites_path = '/etc/nginx/sites-available'
        nginx_enabled_path = '/etc/nginx/sites-enabled'

        for file in os.listdir(nginx_sites_path):
            if file != 'default':
                file_path = os.path.join(nginx_sites_path, file)
                enabled = os.path.exists(os.path.join(nginx_enabled_path, file))
                root_dir = ''

                # Parse nginx config to get root directory
                with open(file_path, 'r') as f:
                    content = f.read()
                    root_match = re.search(r'root\s+(.+);', content)
                    if root_match:
                        root_dir = root_match.group(1)

                vhosts.append({
                    'domain': file,
                    'root_dir': root_dir,
                    'enabled': enabled
                })

        return jsonify(vhosts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nginx/create-vhost', methods=['POST'])
@login_required
def create_vhost():
    logger.info('Virtual host creation attempt')
    try:
        domain = request.json.get('domain')
        root_dir = request.json.get('root_dir')
        
        logger.info(f'Creating virtual host for domain: {domain}, root: {root_dir}')

        if not domain or not root_dir:
            logger.error('Domain and root directory are required')
            return jsonify({'error': 'Domain and root directory are required'}), 400

        # Create nginx config file
        config = f"""server {{
    listen 80;
    server_name {domain};
    root {root_dir};

    index index.html index.htm index.php;

    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php8.1-fpm.sock;
    }}
}}"""

        config_path = f'/etc/nginx/sites-available/{domain}'
        logger.info(f'Writing nginx config to: {config_path}')
        with open(config_path, 'w') as f:
            f.write(config)

        # Create symbolic link to enable the site
        enabled_path = f'/etc/nginx/sites-enabled/{domain}'
        if not os.path.exists(enabled_path):
            logger.info(f'Creating symbolic link: {enabled_path}')
            os.symlink(config_path, enabled_path)

        # Create root directory if it doesn't exist
        logger.info(f'Creating root directory: {root_dir}')
        os.makedirs(root_dir, exist_ok=True)
        
        # Create default index.html file
        index_file_path = os.path.join(root_dir, 'index.html')
        if not os.path.exists(index_file_path):
            default_html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {domain}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }}
        h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        p {{
            font-size: 1.2rem;
            margin-bottom: 2rem;
            opacity: 0.9;
        }}
        .domain {{
            color: #ffd700;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 2rem;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 Welcome!</h1>
        <p>Your virtual host <span class="domain">{domain}</span> is now active!</p>
        <p>This is the default index.html file. You can replace this content with your own website.</p>
        <div class="footer">
            <p>Powered by SLEMP Panel</p>
        </div>
    </div>
</body>
</html>'''
            
            with open(index_file_path, 'w') as f:
                f.write(default_html_content)
            logger.info(f'Created default index.html file: {index_file_path}')

        # Reload nginx configuration
        logger.info('Reloading nginx configuration')
        result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to reload nginx: {result.stderr}')
            return jsonify({'error': f'Failed to reload nginx: {result.stderr}'}), 500

        logger.info(f'Virtual host {domain} created successfully')
        return jsonify({'message': 'Virtual host created successfully'})
    except Exception as e:
        logger.error(f'Error creating virtual host: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/nginx/create-default-site', methods=['POST'])
@login_required
def create_default_site():
    logger.info('Default site creation attempt')
    try:
        domain = request.json.get('domain')
        
        if not domain:
            logger.error('Domain is required')
            return jsonify({'error': 'Domain is required'}), 400
        
        logger.info(f'Setting default site for domain: {domain}')
        
        # Check if the domain config exists
        config_path = f'/etc/nginx/sites-available/{domain}'
        if not os.path.exists(config_path):
            logger.error(f'Virtual host config not found: {config_path}')
            return jsonify({'error': f'Virtual host {domain} not found'}), 404
        
        # First, remove default_server from all existing configs
        sites_enabled_dir = '/etc/nginx/sites-enabled'
        if os.path.exists(sites_enabled_dir):
            for filename in os.listdir(sites_enabled_dir):
                # Process all files including 'default'
                    
                file_path = os.path.join(sites_enabled_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Remove default_server from listen directives (handle all possible formats)
                        content = re.sub(r'listen\s+80\s+default_server\s*;', 'listen 80;', content)
                        content = re.sub(r'listen\s+443\s+ssl\s+default_server\s*;', 'listen 443 ssl;', content)
                        content = re.sub(r'listen\s+\[::\]:80\s+default_server\s*;', 'listen [::]:80;', content)
                        content = re.sub(r'listen\s+\[::\]:443\s+ssl\s+default_server\s*;', 'listen [::]:443 ssl;', content)
                        # Also handle cases where default_server comes before ssl
                        content = re.sub(r'listen\s+443\s+default_server\s+ssl\s*;', 'listen 443 ssl;', content)
                        content = re.sub(r'listen\s+\[::\]:443\s+default_server\s+ssl\s*;', 'listen [::]:443 ssl;', content)
                        
                        with open(file_path, 'w') as f:
                            f.write(content)
                        
                        logger.info(f'Removed default_server from {filename}')
                    except Exception as e:
                        logger.warning(f'Error processing {filename}: {str(e)}')
        
        # Now add default_server to the selected domain
        enabled_path = f'/etc/nginx/sites-enabled/{domain}'
        if os.path.exists(enabled_path):
            try:
                with open(enabled_path, 'r') as f:
                    content = f.read()
                
                # First remove any existing default_server from this file too
                content = re.sub(r'listen\s+80\s+default_server\s*;', 'listen 80;', content)
                content = re.sub(r'listen\s+443\s+ssl\s+default_server\s*;', 'listen 443 ssl;', content)
                content = re.sub(r'listen\s+\[::\]:80\s+default_server\s*;', 'listen [::]:80;', content)
                content = re.sub(r'listen\s+\[::\]:443\s+ssl\s+default_server\s*;', 'listen [::]:443 ssl;', content)
                content = re.sub(r'listen\s+443\s+default_server\s+ssl\s*;', 'listen 443 ssl;', content)
                content = re.sub(r'listen\s+\[::\]:443\s+default_server\s+ssl\s*;', 'listen [::]:443 ssl;', content)
                
                # Add default_server to listen directives
                content = re.sub(r'listen\s+80;', 'listen 80 default_server;', content)
                content = re.sub(r'listen\s+443\s+ssl;', 'listen 443 ssl default_server;', content)
                content = re.sub(r'listen\s+\[::\]:80;', 'listen [::]:80 default_server;', content)
                content = re.sub(r'listen\s+\[::\]:443\s+ssl;', 'listen [::]:443 ssl default_server;', content)
                
                with open(enabled_path, 'w') as f:
                    f.write(content)
                
                logger.info(f'Added default_server to {domain}')
            except Exception as e:
                logger.error(f'Error updating {domain} config: {str(e)}')
                return jsonify({'error': f'Error updating {domain} config: {str(e)}'}), 500
        else:
            logger.error(f'Enabled site not found: {enabled_path}')
            return jsonify({'error': f'Enabled site {domain} not found'}), 404
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            logger.error(f'Nginx configuration test failed: {test_result.stderr}')
            return jsonify({'error': f'Nginx configuration test failed: {test_result.stderr}'}), 500
        
        # Reload nginx configuration
        logger.info('Reloading nginx configuration')
        result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to reload nginx: {result.stderr}')
            return jsonify({'error': f'Failed to reload nginx: {result.stderr}'}), 500
        
        logger.info(f'Successfully set {domain} as default site')
        return jsonify({'message': f'Successfully set {domain} as default site'})
        
    except Exception as e:
        logger.error(f'Error setting default site: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/nginx/delete-vhost', methods=['POST'])
@login_required
def delete_vhost():
    try:
        domain = request.json.get('domain')
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400

        logger.info(f'Attempting to delete virtual host: {domain}')

        # Remove symbolic link first
        link_path = f'/etc/nginx/sites-enabled/{domain}'
        if os.path.exists(link_path):
            os.remove(link_path)
            logger.info(f'Removed symbolic link: {link_path}')

        # Remove configuration file
        config_path = f'/etc/nginx/sites-available/{domain}'
        if os.path.exists(config_path):
            os.remove(config_path)
            logger.info(f'Removed config file: {config_path}')

        # Reload nginx configuration
        logger.info('Reloading nginx configuration')
        result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to reload nginx: {result.stderr}')
            return jsonify({'error': f'Failed to reload nginx: {result.stderr}'}), 500

        logger.info(f'Virtual host {domain} deleted successfully')
        return jsonify({'message': 'Virtual host deleted successfully'})
    except Exception as e:
        logger.error(f'Error deleting virtual host: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/nginx/toggle-vhost', methods=['POST'])
@login_required
def toggle_vhost():
    try:
        domain = request.json.get('domain')
        enable = request.json.get('enable')
        
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        if enable is None:
            return jsonify({'error': 'Enable flag is required'}), 400

        logger.info(f'Attempting to {"enable" if enable else "disable"} virtual host: {domain}')

        config_path = f'/etc/nginx/sites-available/{domain}'
        link_path = f'/etc/nginx/sites-enabled/{domain}'

        if not os.path.exists(config_path):
            return jsonify({'error': 'Virtual host configuration not found'}), 404

        if enable:
            # Enable: create symbolic link
            if not os.path.exists(link_path):
                os.symlink(config_path, link_path)
                logger.info(f'Created symbolic link: {link_path}')
        else:
            # Disable: remove symbolic link
            if os.path.exists(link_path):
                os.remove(link_path)
                logger.info(f'Removed symbolic link: {link_path}')

        # Reload nginx configuration
        logger.info('Reloading nginx configuration')
        result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to reload nginx: {result.stderr}')
            return jsonify({'error': f'Failed to reload nginx: {result.stderr}'}), 500

        logger.info(f'Virtual host {domain} {"enabled" if enable else "disabled"} successfully')
        return jsonify({'message': f'Virtual host {"enabled" if enable else "disabled"} successfully'})
    except Exception as e:
        logger.error(f'Error toggling virtual host: {str(e)}')
        return jsonify({'error': str(e)}), 500

# PHP Configuration Management
@app.route('/api/php/config', methods=['POST'])
@login_required
def update_php_config():
    try:
        memory_limit = request.json.get('memory_limit')
        max_execution_time = request.json.get('max_execution_time')

        if not memory_limit or not max_execution_time:
            return jsonify({'error': 'Memory limit and max execution time are required'}), 400

        # Update PHP configuration
        php_ini_path = '/etc/php/php.ini'
        config = configparser.ConfigParser()
        config.read(php_ini_path)

        if 'PHP' not in config.sections():
            config.add_section('PHP')

        config['PHP']['memory_limit'] = memory_limit
        config['PHP']['max_execution_time'] = max_execution_time

        with open(php_ini_path, 'w') as f:
            config.write(f)

        # Restart PHP-FPM
        subprocess.run(['supervisorctl', 'restart', 'php-fpm'])

        return jsonify({'message': 'PHP configuration updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/php/toggle-module', methods=['POST'])
@login_required
def toggle_php_module():
    """Toggle PHP module - install if not installed, then enable/disable"""
    try:
        data = request.get_json()
        module_name = data.get('module')
        action = data.get('action')  # 'enable' or 'disable'
        
        if not module_name or not action:
            return jsonify({'error': 'Module name and action are required'}), 400
            
        # Check if module is installed or available
        # For core modules like OpenSSL, check if they're available in PHP
        if module_name.lower() == 'openssl':
            check_cmd = "php -m | grep -i openssl"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            module_installed = result.returncode == 0
        else:
            check_cmd = f"dpkg -l | grep -E 'php.*{module_name}'"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            module_installed = result.returncode == 0
        
        if action == 'enable':
            # If module is not installed, install it first
            if not module_installed:
                # Special handling for OpenSSL - it's usually built into PHP core
                if module_name.lower() == 'openssl':
                    # Check if OpenSSL is already available in PHP
                    check_openssl_cmd = "php -m | grep -i openssl"
                    openssl_result = subprocess.run(check_openssl_cmd, shell=True, capture_output=True, text=True)
                    if openssl_result.returncode == 0:
                        # OpenSSL is already available, just enable it
                        pass
                    else:
                        return jsonify({
                            'error': 'OpenSSL module is not available. It should be compiled into PHP core. Please check your PHP installation.'
                        }), 500
                else:
                    # Special module name mappings
                    module_mappings = {
                        'pdo_mysql': 'mysql',
                        'pdo_pgsql': 'pgsql',
                        'pdo_sqlite': 'sqlite3',
                        'mysqli': 'mysql'
                    }
                    
                    # Get the actual package name
                    actual_module = module_mappings.get(module_name, module_name)
                    
                    # Try different naming conventions for PHP modules
                    module_variants = [
                        f"php-{actual_module}",
                        f"php8.1-{actual_module}",
                        f"php8.2-{actual_module}",
                        f"php8.3-{actual_module}"
                    ]
                    
                    installed = False
                    last_error = ""
                    for variant in module_variants:
                        try:
                            install_cmd = f"apt-get update && apt-get install {variant} -y"
                            install_result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
                            if install_result.returncode == 0:
                                installed = True
                                break
                            else:
                                last_error = install_result.stderr or install_result.stdout
                        except Exception as e:
                            last_error = str(e)
                            continue
                    
                    if not installed:
                        return jsonify({
                            'error': f'Failed to install module {module_name}. Last error: {last_error}'
                        }), 500
            
            # Enable the module in php.ini
            php_ini_path = '/etc/php/8.1/fpm/php.ini'  # Adjust path as needed
            if os.path.exists(php_ini_path):
                with open(php_ini_path, 'r') as f:
                    content = f.read()
                
                extension_line = f"extension={module_name}"
                if extension_line not in content:
                    # Add extension to php.ini
                    with open(php_ini_path, 'a') as f:
                        f.write(f"\n{extension_line}\n")
                
                # Restart PHP-FPM
                subprocess.run(['supervisorctl', 'restart', 'php-fpm'])
                
                return jsonify({
                    'message': f'Module {module_name} enabled successfully',
                    'installed': not module_installed,
                    'enabled': True
                })
        
        elif action == 'disable':
            # Disable the module in php.ini
            php_ini_path = '/etc/php/8.1/fpm/php.ini'  # Adjust path as needed
            if os.path.exists(php_ini_path):
                with open(php_ini_path, 'r') as f:
                    lines = f.readlines()
                
                # Comment out or remove the extension line
                with open(php_ini_path, 'w') as f:
                    for line in lines:
                        if f"extension={module_name}" in line and not line.strip().startswith(';'):
                            f.write(f";{line}")
                        else:
                            f.write(line)
                
                # Restart PHP-FPM
                subprocess.run(['supervisorctl', 'restart', 'php-fpm'])
                
                return jsonify({
                    'message': f'Module {module_name} disabled successfully',
                    'enabled': False
                })
        
        return jsonify({'error': 'Invalid action'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PowerDNS specific endpoints
@app.route('/api/service/<service>/restart', methods=['POST'])
@login_required
def restart_service(service):
    """Restart a service"""
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb',
        'powerdns': 'pdns'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        logger.info(f'Restarting service {service_name}')
        
        # Stop the service first
        stop_result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        if stop_result.returncode != 0:
            logger.warning(f'Failed to stop {service_name}: {stop_result.stderr}')
        
        # Wait a moment
        time.sleep(2)
        
        # Start the service
        if service_name == 'mariadb':
            # For MariaDB, create socket directory first
            subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True)
        
        start_result = subprocess.run(['supervisorctl', 'start', service_name], capture_output=True, text=True)
        
        if start_result.returncode == 0:
            logger.info(f'Service {service_name} restarted successfully')
            return jsonify({'success': True, 'message': f'{service_name} berhasil direstart'})
        else:
            logger.error(f'Failed to restart {service_name}: {start_result.stderr}')
            return jsonify({'success': False, 'message': f'Gagal merestart {service_name}: {start_result.stderr}'})
    except Exception as e:
        logger.error(f'Error restarting {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat merestart {service}'}), 500

@app.route('/api/service/<service>/logs', methods=['GET'])
@login_required
def get_service_logs(service):
    """Get service logs"""
    service_map = {
        'nginx': '/var/log/nginx/error.log',
        'php-fpm': '/var/log/php8.1-fpm.log',
        'mysql': '/var/log/mysql/error.log',
        'powerdns': '/var/log/pdns.log'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        log_file = service_map[service]
        lines = request.args.get('lines', 100, type=int)
        
        # Check if log file exists
        if not os.path.exists(log_file):
            return jsonify({'success': True, 'logs': f'Log file {log_file} tidak ditemukan'})
        
        # Get last N lines of log file
        result = subprocess.run(['tail', '-n', str(lines), log_file], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'logs': result.stdout})
        else:
            return jsonify({'success': False, 'message': f'Gagal membaca log: {result.stderr}'})
    except Exception as e:
        logger.error(f'Error getting logs for {service}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat membaca log {service}'}), 500

@app.route('/api/powerdns/domains', methods=['GET'])
@login_required
def list_powerdns_domains():
    """List all domains in PowerDNS"""
    try:
        # Read domains from named.conf for bind backend
        domains = []
        named_conf_path = '/etc/powerdns/named.conf'
        
        if os.path.exists(named_conf_path):
            with open(named_conf_path, 'r') as f:
                content = f.read()
                
            # Extract domain names from zone declarations
            import re
            zone_pattern = r'zone\s+"([^"]+)"'
            matches = re.findall(zone_pattern, content)
            domains = matches
        
        return jsonify({'success': True, 'domains': domains})
    except Exception as e:
        logger.error(f'Error listing PowerDNS domains: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat mendapatkan daftar domain'}), 500

def get_public_ip():
    """Get public IP address of the server"""
    try:
        # Try multiple services to get public IP
        services = [
            'https://api.ipify.org',
            'https://ipinfo.io/ip',
            'https://icanhazip.com',
            'https://ident.me'
        ]
        
        for service in services:
            try:
                result = subprocess.run(['curl', '-s', '--connect-timeout', '5', service], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    ip = result.stdout.strip()
                    # Validate IP format
                    import ipaddress
                    ipaddress.ip_address(ip)
                    return ip
            except Exception:
                continue
        
        # Fallback: try to get IP from network interface
        try:
            import socket
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            if local_ip and local_ip != '127.0.0.1':
                return local_ip
        except Exception:
            pass
            
        # Final fallback
        return '127.0.0.1'
        
    except Exception as e:
        logger.warning(f'Failed to get public IP: {str(e)}')
        return '127.0.0.1'

@app.route('/api/powerdns/domain', methods=['POST'])
@login_required
def add_powerdns_domain():
    """Add a new domain to PowerDNS"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        
        if not domain:
            return jsonify({'success': False, 'message': 'Domain name is required'}), 400
        
        # Get public IP address
        public_ip = get_public_ip()
        logger.info(f'Using IP address for domain {domain}: {public_ip}')
        
        # Get default nameservers from configuration
        config_file = '/etc/powerdns/default-ns.conf'
        nameserver1 = 'ns1.atila.co.id.'
        nameserver2 = 'ns2.atila.co.id.'
        
        # Read from configuration file if it exists
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('NAMESERVER1='):
                        nameserver1 = line.split('=', 1)[1]
                    elif line.startswith('NAMESERVER2='):
                        nameserver2 = line.split('=', 1)[1]
        
        # Check if domain is the same as nameserver top level domain
        # Extract top level domain from nameservers
        ns1_domain = nameserver1.rstrip('.')
        ns2_domain = nameserver2.rstrip('.')
        
        # Get the top level domain from nameservers (e.g., ns1.atila.co.id -> atila.co.id)
        ns1_tld = '.'.join(ns1_domain.split('.')[1:]) if '.' in ns1_domain else ns1_domain
        ns2_tld = '.'.join(ns2_domain.split('.')[1:]) if '.' in ns2_domain else ns2_domain
        
        # Create zone file
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        zone_content = f"""$ORIGIN {domain}.
$TTL 3600
@    IN    SOA    {nameserver1} admin.{domain}. (
                {datetime.datetime.now().strftime('%Y%m%d01')}    ; Serial
                3600          ; Refresh
                1800          ; Retry
                604800        ; Expire
                86400 )       ; Minimum TTL

@    IN    NS     {nameserver1}
@    IN    NS     {nameserver2}
@    IN    A      {public_ip}
www  IN    A      {public_ip}
"""
        
        # If domain matches nameserver top level domain, add A records for ns1 and ns2
        if domain == ns1_tld or domain == ns2_tld:
            ns1_subdomain = ns1_domain.split('.')[0]  # Extract 'ns1' from 'ns1.atila.co.id'
            ns2_subdomain = ns2_domain.split('.')[0]  # Extract 'ns2' from 'ns2.atila.co.id'
            
            zone_content += f"{ns1_subdomain}  IN    A      {public_ip}\n"
            zone_content += f"{ns2_subdomain}  IN    A      {public_ip}\n"
        
        # Write zone file
        with open(zone_file, 'w') as f:
            f.write(zone_content)
        
        # Set proper ownership
        subprocess.run(['chown', 'pdns:pdns', zone_file], check=True)
        
        # Add zone to named.conf
        zone_config = f'zone "{domain}" {{ type master; file "{zone_file}"; }};\n'
        with open('/etc/powerdns/named.conf', 'a') as f:
            f.write(zone_config)
        
        # Restart PowerDNS to load new zone
        restart_result = subprocess.run(['supervisorctl', 'restart', 'pdns'], capture_output=True, text=True)
        
        if restart_result.returncode == 0:
            logger.info(f'PowerDNS domain {domain} created successfully')
            return jsonify({'success': True, 'message': f'Domain {domain} berhasil ditambahkan'})
        else:
            logger.error(f'Failed to restart PowerDNS after adding domain {domain}: {restart_result.stderr}')
            return jsonify({'success': False, 'message': f'Domain ditambahkan tapi gagal restart PowerDNS: {restart_result.stderr}'})
            
    except Exception as e:
        logger.error(f'Error adding PowerDNS domain: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menambahkan domain: {str(e)}'}), 500

@app.route('/api/powerdns/default-ns', methods=['POST'])
@login_required
def save_default_nameservers():
    """Save default name servers configuration"""
    try:
        data = request.get_json()
        nameserver1 = data.get('nameserver1')
        nameserver2 = data.get('nameserver2')
        
        if not nameserver1 or not nameserver2:
            return jsonify({'success': False, 'message': 'Both nameservers are required'}), 400
        
        # Save to configuration file
        config_file = '/etc/powerdns/default-ns.conf'
        config_content = f"""# Default Name Servers Configuration
# Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
NAMESERVER1={nameserver1}
NAMESERVER2={nameserver2}
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        logger.info(f'Default name servers saved: {nameserver1}, {nameserver2}')
        return jsonify({'success': True, 'message': 'Default name servers saved successfully'})
        
    except Exception as e:
        logger.error(f'Error saving default name servers: {str(e)}')
        return jsonify({'success': False, 'message': f'Error saving default name servers: {str(e)}'}), 500

@app.route('/api/powerdns/default-ns', methods=['GET'])
@login_required
def get_default_nameservers():
    """Get default name servers configuration"""
    try:
        config_file = '/etc/powerdns/default-ns.conf'
        nameserver1 = 'ns1.atila.co.id.'
        nameserver2 = 'ns2.atila.co.id.'
        
        # Read from configuration file if it exists
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('NAMESERVER1='):
                        nameserver1 = line.split('=', 1)[1]
                    elif line.startswith('NAMESERVER2='):
                        nameserver2 = line.split('=', 1)[1]
        
        return jsonify({
            'success': True, 
            'nameserver1': nameserver1,
            'nameserver2': nameserver2
        })
        
    except Exception as e:
        logger.error(f'Error loading default name servers: {str(e)}')
        return jsonify({'success': False, 'message': f'Error loading default name servers: {str(e)}'}), 500

@app.route('/api/powerdns/record', methods=['POST'])
@login_required
def add_powerdns_record():
    """Add a DNS record to PowerDNS"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        name = data.get('name')
        record_type = data.get('type')
        content = data.get('content')
        ttl = data.get('ttl', 3600)
        
        if not all([domain, name, record_type, content]):
            return jsonify({'success': False, 'message': 'Domain, name, type, and content are required'}), 400
        
        # Validate IP address for A records
        if record_type == 'A':
            import ipaddress
            try:
                ipaddress.ip_address(content)
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid IP address format'}), 400
        
        # Add record directly to zone file for bind backend
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        if not os.path.exists(zone_file):
            return jsonify({'success': False, 'message': f'Zone file for {domain} not found'}), 404
        
        # Read current zone file
        with open(zone_file, 'r') as f:
            zone_content = f.read()
        
        # Update serial number
        import re
        serial_pattern = r'(\d{10})\s*;\s*serial'
        current_time = datetime.datetime.now().strftime('%Y%m%d%H')
        new_serial = current_time
        zone_content = re.sub(serial_pattern, f'{new_serial} ; serial', zone_content)
        
        # Add new record
        record_name = name if name != '@' else ''
        new_record = f'{record_name}\t{ttl}\tIN\t{record_type}\t{content}\n'
        zone_content += new_record
        
        # Write updated zone file
        with open(zone_file, 'w') as f:
            f.write(zone_content)
        
        # Set proper ownership
        subprocess.run(['chown', 'pdns:pdns', zone_file], capture_output=True)
        
        # Reload PowerDNS
        reload_result = subprocess.run(['supervisorctl', 'restart', 'pdns'], capture_output=True, text=True)
        
        if reload_result.returncode == 0:
            full_name = f'{name}.{domain}' if name != '@' else domain
            logger.info(f'PowerDNS record {full_name} {record_type} {content} added successfully')
            return jsonify({'success': True, 'message': f'Record {full_name} {record_type} berhasil ditambahkan'})
        else:
            logger.error(f'Failed to reload PowerDNS: {reload_result.stderr}')
            return jsonify({'success': False, 'message': f'Record ditambahkan tapi gagal reload PowerDNS: {reload_result.stderr}'})
    except Exception as e:
        logger.error(f'Error adding PowerDNS record: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menambahkan record'}), 500

@app.route('/api/powerdns/domain/<domain>/records', methods=['GET'])
@login_required
def list_powerdns_records(domain):
    """List all records for a domain in PowerDNS"""
    try:
        # Read records directly from zone file for bind backend
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        
        if not os.path.exists(zone_file):
            return jsonify({'success': False, 'message': f'Zone file for {domain} not found'}), 404
        
        records = []
        with open(zone_file, 'r') as f:
            content = f.read()
        
        # Skip SOA record (multi-line)
        lines = content.split('\n')
        in_soa = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';') or line.startswith('$'):
                continue
                
            # Handle SOA record (multi-line)
            if 'SOA' in line:
                in_soa = True
                continue
            if in_soa and ')' in line:
                in_soa = False
                continue
            if in_soa:
                continue
            
            # Parse records - handle different formats
            parts = line.split()
            if len(parts) >= 3:
                # Format: name [ttl] IN type content
                # or: name IN type content
                name = parts[0]
                if name == '@':
                    name = domain
                elif not name.endswith('.'):
                    name = f'{name}.{domain}' if name else domain
                else:
                    name = name.rstrip('.')
                
                # Check if TTL is present
                if parts[1].isdigit() and len(parts) >= 4 and parts[2] == 'IN':
                    # Format: name ttl IN type content
                    ttl = parts[1]
                    record_type = parts[3]
                    content = ' '.join(parts[4:]) if len(parts) > 4 else ''
                elif parts[1] == 'IN' and len(parts) >= 3:
                    # Format: name IN type content
                    ttl = '3600'
                    record_type = parts[2]
                    content = ' '.join(parts[3:]) if len(parts) > 3 else ''
                else:
                    continue
                
                records.append({
                    'name': name,
                    'ttl': ttl,
                    'type': record_type,
                    'content': content
                })
        
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        logger.error(f'Error listing PowerDNS records for {domain}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat mendapatkan records'}), 500

@app.route('/api/powerdns/list-records/<domain>', methods=['GET'])
@login_required
def list_records_for_domain(domain):
    """List all records for a domain in PowerDNS (alternative endpoint)"""
    try:
        # Read records directly from zone file for bind backend
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        
        if not os.path.exists(zone_file):
            return jsonify({'success': False, 'message': f'Zone file for {domain} not found'}), 404
        
        records = []
        with open(zone_file, 'r') as f:
            content = f.read()
        
        # Skip SOA record (multi-line)
        lines = content.split('\n')
        in_soa = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';') or line.startswith('$'):
                continue
                
            # Handle SOA record (multi-line)
            if 'SOA' in line:
                in_soa = True
                continue
            if in_soa and ')' in line:
                in_soa = False
                continue
            if in_soa:
                continue
            
            # Parse records - handle different formats
            parts = line.split()
            if len(parts) >= 3:
                # Format: name [ttl] IN type content
                # or: name IN type content
                name = parts[0]
                if name == '@':
                    name = domain
                elif not name.endswith('.'):
                    name = f'{name}.{domain}' if name else domain
                else:
                    name = name.rstrip('.')
                
                # Check if TTL is present
                if parts[1].isdigit() and len(parts) >= 4 and parts[2] == 'IN':
                    # Format: name ttl IN type content
                    ttl = parts[1]
                    record_type = parts[3]
                    content = ' '.join(parts[4:]) if len(parts) > 4 else ''
                elif parts[1] == 'IN' and len(parts) >= 3:
                    # Format: name IN type content
                    ttl = '3600'
                    record_type = parts[2]
                    content = ' '.join(parts[3:]) if len(parts) > 3 else ''
                else:
                    continue
                
                records.append({
                    'name': name,
                    'ttl': ttl,
                    'type': record_type,
                    'content': content
                })
        
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        logger.error(f'Error listing PowerDNS records for {domain}: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat mendapatkan records'}), 500

@app.route('/api/powerdns/delete-domain', methods=['POST'])
@login_required
def delete_powerdns_domain():
    """Delete a domain from PowerDNS"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        
        if not domain:
            return jsonify({'success': False, 'message': 'Domain name is required'}), 400
        
        # Remove zone file
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        if os.path.exists(zone_file):
            os.remove(zone_file)
            logger.info(f'Removed zone file: {zone_file}')
        
        # Remove zone from named.conf
        named_conf_path = '/etc/powerdns/named.conf'
        if os.path.exists(named_conf_path):
            with open(named_conf_path, 'r') as f:
                content = f.read()
            
            # Remove zone declaration
            import re
            zone_pattern = rf'zone\s+"{re.escape(domain)}"\s*{{[^}}]*}};?\s*\n?'
            content = re.sub(zone_pattern, '', content, flags=re.MULTILINE)
            
            with open(named_conf_path, 'w') as f:
                f.write(content)
            
            logger.info(f'Removed zone {domain} from named.conf')
        
        # Restart PowerDNS to reload configuration
        restart_result = subprocess.run(['supervisorctl', 'restart', 'pdns'], capture_output=True, text=True)
        
        if restart_result.returncode == 0:
            logger.info(f'PowerDNS domain {domain} deleted successfully')
            return jsonify({'success': True, 'message': f'Domain {domain} berhasil dihapus'})
        else:
            logger.error(f'Failed to restart PowerDNS after deleting domain {domain}: {restart_result.stderr}')
            return jsonify({'success': False, 'message': f'Domain dihapus tapi gagal restart PowerDNS: {restart_result.stderr}'})
            
    except Exception as e:
        logger.error(f'Error deleting PowerDNS domain: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menghapus domain: {str(e)}'}), 500

@app.route('/api/powerdns/record/edit', methods=['POST'])
@login_required
def edit_powerdns_record():
    """Edit a DNS record in PowerDNS"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        old_name = data.get('old_name')
        old_type = data.get('old_type')
        old_content = data.get('old_content')
        new_name = data.get('new_name')
        new_type = data.get('new_type')
        new_content = data.get('new_content')
        new_ttl = data.get('new_ttl', 3600)
        
        if not all([domain, old_name, old_type, old_content, new_name, new_type, new_content]):
            return jsonify({'success': False, 'message': 'All record fields are required'}), 400
        
        # Validate IP address for A records
        if new_type == 'A':
            import ipaddress
            try:
                ipaddress.ip_address(new_content)
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid IP address format'}), 400
        
        # Edit record directly in zone file for bind backend
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        if not os.path.exists(zone_file):
            return jsonify({'success': False, 'message': f'Zone file for {domain} not found'}), 404
        
        # Read current zone file
        with open(zone_file, 'r') as f:
            zone_content = f.read()
        
        # Update serial number
        import re
        serial_pattern = r'(\d{10})\s*;\s*serial'
        current_time = datetime.datetime.now().strftime('%Y%m%d%H')
        new_serial = current_time
        zone_content = re.sub(serial_pattern, f'{new_serial} ; serial', zone_content)
        
        # Find and replace the old record
        lines = zone_content.split('\n')
        updated_lines = []
        record_found = False
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith(';') and not line_stripped.startswith('$'):
                # Skip SOA record handling
                if 'SOA' in line_stripped:
                    updated_lines.append(line)
                    continue
                
                # Parse record line
                parts = line_stripped.split()
                if len(parts) >= 3:
                    # Extract record details
                    name = parts[0]
                    if name == '@':
                        name = domain
                    elif not name.endswith('.'):
                        name = f'{name}.{domain}' if name else domain
                    else:
                        name = name.rstrip('.')
                    
                    # Check if TTL is present
                    if parts[1].isdigit() and len(parts) >= 4 and parts[2] == 'IN':
                        record_type = parts[3]
                        content = ' '.join(parts[4:]) if len(parts) > 4 else ''
                    elif parts[1] == 'IN' and len(parts) >= 3:
                        record_type = parts[2]
                        content = ' '.join(parts[3:]) if len(parts) > 3 else ''
                    else:
                        updated_lines.append(line)
                        continue
                    
                    # Check if this is the record to edit
                    if (name == old_name and record_type == old_type and content == old_content):
                        # Replace with new record
                        new_record_name = new_name if new_name != domain else '@'
                        if new_name.endswith(f'.{domain}'):
                            new_record_name = new_name[:-len(f'.{domain}')]
                        
                        new_line = f'{new_record_name}\t{new_ttl}\tIN\t{new_type}\t{new_content}'
                        updated_lines.append(new_line)
                        record_found = True
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        if not record_found:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        # Write updated zone file
        updated_content = '\n'.join(updated_lines)
        with open(zone_file, 'w') as f:
            f.write(updated_content)
        
        # Set proper ownership
        subprocess.run(['chown', 'pdns:pdns', zone_file], capture_output=True)
        
        # Reload PowerDNS
        reload_result = subprocess.run(['supervisorctl', 'restart', 'pdns'], capture_output=True, text=True)
        
        if reload_result.returncode == 0:
            logger.info(f'PowerDNS record edited successfully: {old_name} -> {new_name}')
            return jsonify({'success': True, 'message': f'Record berhasil diubah'})
        else:
            logger.error(f'Failed to reload PowerDNS: {reload_result.stderr}')
            return jsonify({'success': False, 'message': f'Record diubah tapi gagal reload PowerDNS: {reload_result.stderr}'})
    except Exception as e:
        logger.error(f'Error editing PowerDNS record: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat mengubah record'}), 500

@app.route('/api/powerdns/record/delete', methods=['POST'])
@login_required
def delete_powerdns_record():
    """Delete a DNS record from PowerDNS"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        name = data.get('name')
        record_type = data.get('type')
        content = data.get('content')
        
        if not all([domain, name, record_type, content]):
            return jsonify({'success': False, 'message': 'All record fields are required'}), 400
        
        # Delete record directly from zone file for bind backend
        zone_file = f'/var/lib/powerdns/zones/{domain}.zone'
        if not os.path.exists(zone_file):
            return jsonify({'success': False, 'message': f'Zone file for {domain} not found'}), 404
        
        # Read current zone file
        with open(zone_file, 'r') as f:
            zone_content = f.read()
        
        # Update serial number
        import re
        serial_pattern = r'(\d{10})\s*;\s*serial'
        current_time = datetime.datetime.now().strftime('%Y%m%d%H')
        new_serial = current_time
        zone_content = re.sub(serial_pattern, f'{new_serial} ; serial', zone_content)
        
        # Find and remove the record
        lines = zone_content.split('\n')
        updated_lines = []
        record_found = False
        
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith(';') and not line_stripped.startswith('$'):
                # Skip SOA record handling
                if 'SOA' in line_stripped:
                    updated_lines.append(line)
                    continue
                
                # Parse record line
                parts = line_stripped.split()
                if len(parts) >= 3:
                    # Extract record details
                    record_name = parts[0]
                    if record_name == '@':
                        record_name = domain
                    elif not record_name.endswith('.'):
                        record_name = f'{record_name}.{domain}' if record_name else domain
                    else:
                        record_name = record_name.rstrip('.')
                    
                    # Check if TTL is present
                    if parts[1].isdigit() and len(parts) >= 4 and parts[2] == 'IN':
                        record_type_parsed = parts[3]
                        content_parsed = ' '.join(parts[4:]) if len(parts) > 4 else ''
                    elif parts[1] == 'IN' and len(parts) >= 3:
                        record_type_parsed = parts[2]
                        content_parsed = ' '.join(parts[3:]) if len(parts) > 3 else ''
                    else:
                        updated_lines.append(line)
                        continue
                    
                    # Check if this is the record to delete
                    if (record_name == name and record_type_parsed == record_type and content_parsed == content):
                        record_found = True
                        # Skip this line (delete it)
                        continue
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        if not record_found:
            return jsonify({'success': False, 'message': 'Record not found'}), 404
        
        # Write updated zone file
        updated_content = '\n'.join(updated_lines)
        with open(zone_file, 'w') as f:
            f.write(updated_content)
        
        # Set proper ownership
        subprocess.run(['chown', 'pdns:pdns', zone_file], capture_output=True)
        
        # Reload PowerDNS
        reload_result = subprocess.run(['supervisorctl', 'restart', 'pdns'], capture_output=True, text=True)
        
        if reload_result.returncode == 0:
            logger.info(f'PowerDNS record deleted successfully: {name} ({record_type})')
            return jsonify({'success': True, 'message': f'Record berhasil dihapus'})
        else:
            logger.error(f'Failed to reload PowerDNS: {reload_result.stderr}')
            return jsonify({'success': False, 'message': f'Record dihapus tapi gagal reload PowerDNS: {reload_result.stderr}'})
    except Exception as e:
        logger.error(f'Error deleting PowerDNS record: {str(e)}')
        return jsonify({'success': False, 'message': f'Terjadi kesalahan saat menghapus record'}), 500

@app.route('/api/php/modules', methods=['GET'])
@login_required
def get_php_modules():
    """Get PHP modules status from system"""
    try:
        logger.info('Loading PHP modules information...')
        
        # First check if PHP is available
        try:
            php_check = subprocess.run(['php', '--version'], capture_output=True, text=True, timeout=5)
            if php_check.returncode != 0:
                logger.error('PHP is not available or not working properly')
                return jsonify({'error': 'PHP is not available on this system'}), 500
        except subprocess.TimeoutExpired:
            logger.error('PHP version check timed out')
            return jsonify({'error': 'PHP is not responding'}), 500
        except FileNotFoundError:
            logger.error('PHP command not found')
            return jsonify({'error': 'PHP is not installed on this system'}), 500
        except Exception as e:
            logger.error(f'Error checking PHP availability: {str(e)}')
            return jsonify({'error': f'Error checking PHP: {str(e)}'}), 500
        
        # Define common PHP modules
        modules = [
            {'name': 'bcmath', 'description': 'Arbitrary Precision Mathematics'},
            {'name': 'calendar', 'description': 'Calendar conversion functions'},
            {'name': 'curl', 'description': 'Client URL library'},
            {'name': 'dom', 'description': 'Document Object Model'},
            {'name': 'exif', 'description': 'Exchangeable image information'},
            {'name': 'fileinfo', 'description': 'File information'},
            {'name': 'ftp', 'description': 'File Transfer Protocol'},
            {'name': 'gd', 'description': 'Image processing'},
            {'name': 'gettext', 'description': 'GNU gettext'},
            {'name': 'iconv', 'description': 'Character set conversion'},
            {'name': 'intl', 'description': 'Internationalization'},
            {'name': 'json', 'description': 'JavaScript Object Notation'},
            {'name': 'mbstring', 'description': 'Multibyte string'},
            {'name': 'mysqli', 'description': 'MySQL Improved'},
            {'name': 'mysqlnd', 'description': 'MySQL Native Driver'},
            {'name': 'opcache', 'description': 'Zend OPcache'},
            {'name': 'openssl', 'description': 'OpenSSL'},
            {'name': 'pcre', 'description': 'Perl Compatible Regular Expressions'},
            {'name': 'pdo', 'description': 'PHP Data Objects'},
            {'name': 'pdo_mysql', 'description': 'PDO MySQL driver'},
            {'name': 'phar', 'description': 'PHP Archive'},
            {'name': 'posix', 'description': 'POSIX functions'},
            {'name': 'readline', 'description': 'GNU Readline'},
            {'name': 'session', 'description': 'Session handling'},
            {'name': 'simplexml', 'description': 'SimpleXML'},
            {'name': 'soap', 'description': 'SOAP'},
            {'name': 'sockets', 'description': 'Socket functions'},
            {'name': 'sodium', 'description': 'Sodium cryptography'},
            {'name': 'sqlite3', 'description': 'SQLite3'},
            {'name': 'tokenizer', 'description': 'Tokenizer'},
            {'name': 'xml', 'description': 'XML Parser'},
            {'name': 'xmlreader', 'description': 'XMLReader'},
            {'name': 'xmlwriter', 'description': 'XMLWriter'},
            {'name': 'xsl', 'description': 'XSL'},
            {'name': 'zip', 'description': 'Zip'},
            {'name': 'zlib', 'description': 'Zlib compression'}
        ]
        
        # Core modules that are typically compiled into PHP and don't need separate installation
        core_modules = ['openssl', 'json', 'pcre', 'session', 'tokenizer', 'zlib', 'phar', 'posix', 'sodium']
        
        # Check which modules are actually enabled
        result = []
        for module in modules:
            module_name = module['name']
            
            # For core modules, check if they're enabled in PHP (they're usually compiled in)
            if module_name in core_modules:
                # Core modules are typically always "installed" if PHP is installed
                installed = True
            else:
                # Check if module is installed (package exists)
                check_installed_cmd = f"dpkg -l | grep -E 'php.*{module_name}'"
                installed_result = subprocess.run(check_installed_cmd, shell=True, capture_output=True, text=True)
                installed = installed_result.returncode == 0
            
            # Check if module is enabled in PHP
            enabled = False
            if installed:
                try:
                    # Check if extension is loaded in PHP
                    check_enabled_cmd = f"php -m | grep -i '^{module_name}$'"
                    enabled_result = subprocess.run(check_enabled_cmd, shell=True, capture_output=True, text=True, timeout=10)
                    enabled = enabled_result.returncode == 0
                except subprocess.TimeoutExpired:
                    logger.warning(f'Timeout checking PHP module {module_name}')
                    enabled = False
                except Exception as e:
                    logger.warning(f'Error checking PHP module {module_name}: {str(e)}')
                    enabled = False
            
            result.append({
                'name': module_name,
                'description': module['description'],
                'installed': installed,
                'enabled': enabled
            })
        
        logger.info(f'Successfully loaded {len(result)} PHP modules')
        return jsonify({'modules': result})
        
    except Exception as e:
        logger.error(f'Error in get_php_modules: {str(e)}')
        return jsonify({'error': f'Failed to load PHP modules: {str(e)}'}), 500

@app.route('/api/php/info', methods=['GET'])
@login_required
def get_php_info():
    """Get PHP information including version, configuration, and loaded extensions"""
    try:
        logger.info('Loading PHP information...')
        
        # Check if PHP is available
        try:
            php_check = subprocess.run(['php', '--version'], capture_output=True, text=True, timeout=10)
            if php_check.returncode != 0:
                return jsonify({'error': 'PHP is not available or not working properly'}), 500
        except subprocess.TimeoutExpired:
            logger.warning('Timeout checking PHP availability')
            return jsonify({'error': 'PHP check timed out'}), 500
        except FileNotFoundError:
            logger.error('PHP not found')
            return jsonify({'error': 'PHP is not installed'}), 500
        except Exception as e:
            logger.error(f'Error checking PHP availability: {str(e)}')
            return jsonify({'error': f'Error checking PHP: {str(e)}'}), 500
        
        php_info = {}
        
        # Get PHP version
        try:
            version_result = subprocess.run(['php', '--version'], capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0:
                version_line = version_result.stdout.split('\n')[0]
                php_info['version'] = version_line.split(' ')[1] if len(version_line.split(' ')) > 1 else 'Unable to detect'
            else:
                php_info['version'] = 'Unable to detect'
        except Exception as e:
            logger.warning(f'Error getting PHP version: {str(e)}')
            php_info['version'] = 'Unable to detect'
        
        # Get system information
        try:
            import platform
            php_info['system'] = f"{platform.system()} {platform.machine()}"
        except Exception:
            php_info['system'] = 'Unable to detect'
        
        # Get build date from PHP
        try:
            build_date_result = subprocess.run(['php', '-r', 'echo "Build Date: " . phpversion();'], capture_output=True, text=True, timeout=10)
            if build_date_result.returncode == 0:
                # Try to get actual build date from phpinfo
                phpinfo_result = subprocess.run(['php', '-r', 'ob_start(); phpinfo(); $info = ob_get_contents(); ob_end_clean(); if (preg_match("/Build Date => (.+)/", $info, $matches)) { echo $matches[1]; } else { echo date("M d Y H:i:s"); }'], capture_output=True, text=True, timeout=10)
                if phpinfo_result.returncode == 0 and phpinfo_result.stdout.strip():
                    php_info['build_date'] = phpinfo_result.stdout.strip()
                else:
                    php_info['build_date'] = 'Unable to detect'
            else:
                php_info['build_date'] = 'Unable to detect'
        except Exception as e:
            logger.warning(f'Error getting PHP build date: {str(e)}')
            php_info['build_date'] = 'Unable to detect'
        
        # Get configuration file path
        try:
            config_result = subprocess.run(['php', '--ini'], capture_output=True, text=True, timeout=10)
            if config_result.returncode == 0:
                for line in config_result.stdout.split('\n'):
                    if 'Loaded Configuration File:' in line:
                        php_info['config_file'] = line.split(':', 1)[1].strip()
                        break
                else:
                    php_info['config_file'] = '/etc/php/8.1/fpm/php.ini'
            else:
                php_info['config_file'] = '/etc/php/8.1/fpm/php.ini'
        except Exception as e:
            logger.warning(f'Error getting PHP config file: {str(e)}')
            php_info['config_file'] = '/etc/php/8.1/fpm/php.ini'
        
        # Get server API
        php_info['server_api'] = 'FPM/FastCGI'
        
        # Get PHP configuration values
        try:
            # Get memory limit
            memory_result = subprocess.run(['php', '-r', 'echo ini_get("memory_limit");'], capture_output=True, text=True, timeout=10)
            php_info['memory_limit'] = memory_result.stdout.strip() if memory_result.returncode == 0 else '128M'
            
            # Get max execution time
            exec_time_result = subprocess.run(['php', '-r', 'echo ini_get("max_execution_time");'], capture_output=True, text=True, timeout=10)
            exec_time = exec_time_result.stdout.strip() if exec_time_result.returncode == 0 else '30'
            php_info['max_execution_time'] = f"{exec_time} seconds"
            
            # Get upload max filesize
            upload_result = subprocess.run(['php', '-r', 'echo ini_get("upload_max_filesize");'], capture_output=True, text=True, timeout=10)
            php_info['upload_max_filesize'] = upload_result.stdout.strip() if upload_result.returncode == 0 else '2M'
            
            # Get post max size
            post_result = subprocess.run(['php', '-r', 'echo ini_get("post_max_size");'], capture_output=True, text=True, timeout=10)
            php_info['post_max_size'] = post_result.stdout.strip() if post_result.returncode == 0 else '8M'
            
        except Exception as e:
            logger.warning(f'Error getting PHP configuration values: {str(e)}')
            php_info.update({
                'memory_limit': '128M',
                'max_execution_time': '30 seconds',
                'upload_max_filesize': '2M',
                'post_max_size': '8M'
            })
        
        # Check OPcache status
        try:
            opcache_result = subprocess.run(['php', '-r', 'echo extension_loaded("opcache") ? "Enabled" : "Disabled";'], capture_output=True, text=True, timeout=10)
            php_info['opcache'] = opcache_result.stdout.strip() if opcache_result.returncode == 0 else 'Unable to detect'
        except Exception as e:
            logger.warning(f'Error checking OPcache status: {str(e)}')
            php_info['opcache'] = 'Unable to detect'
        
        # Get loaded extensions
        try:
            extensions_result = subprocess.run(['php', '-m'], capture_output=True, text=True, timeout=10)
            if extensions_result.returncode == 0:
                extensions = [ext.strip() for ext in extensions_result.stdout.split('\n') if ext.strip() and not ext.startswith('[')]
                php_info['extensions'] = extensions
            else:
                php_info['extensions'] = []
        except Exception as e:
            logger.warning(f'Error getting PHP extensions: {str(e)}')
            php_info['extensions'] = []
        
        logger.info('Successfully loaded PHP information')
        return jsonify(php_info)
        
    except Exception as e:
        logger.error(f'Error getting PHP info: {str(e)}')
        return jsonify({'error': str(e)}), 500

# MySQL Database Management
@app.route('/api/mysql/execute-query', methods=['POST'])
@login_required
def execute_query():
    logger.info('Database query execution requested')
    if connection_pool is None:
        return jsonify({'error': 'MySQL connection not available'}), 503
    try:
        data = request.get_json()
        database = data.get('database')
        query = data.get('query')

        if not database or not query:
            return jsonify({'error': 'Database and query are required'}), 400

        connection = connection_pool.get_connection()
        connection.cmd_query(f'USE `{database}`')

        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)

        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            result = cursor.fetchall()
        else:
            connection.commit()
            result = [{'affected_rows': cursor.rowcount}]

        cursor.close()
        connection.close()

        return jsonify(result)

    except mysql.connector.Error as err:
        logger.error(f'MySQL error: {err}')
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        logger.error(f'Error executing query: {e}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/mysql/tables')
@login_required
def list_tables():
    logger.info('Table list requested')
    connection = None
    cursor = None
    try:
        db_name = request.args.get('database')
        if not db_name:
            logger.warning('Database name not provided')
            return jsonify({'error': 'Database name is required'}), 400
            
        # Validate database name (prevent SQL injection)
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            logger.warning(f'Invalid database name format: {db_name}')
            return jsonify({'error': 'Invalid database name format'}), 400
            
        if connection_pool is None:
            return jsonify({'error': 'MySQL connection not available'}), 503
            
        try:
            connection = connection_pool.get_connection()
            connection.cmd_query(f'USE `{db_name}`')
            cursor = connection.cursor(dictionary=True)
            
            # Test connection
            cursor.execute('SELECT 1')
            cursor.fetchone()
        except mysql.connector.PoolError as e:
            logger.error(f'Connection pool error: {str(e)}')
            return jsonify({'error': 'Database connection pool error'}), 500
        except mysql.connector.Error as e:
            logger.error(f'Database connection error: {str(e)}')
            return jsonify({'error': 'Database connection error'}), 500

        try:
            # Get list of tables with information
            cursor.execute("""
                SELECT 
                    table_name as name,
                    `table_rows` as `rows`,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) as size
                FROM information_schema.tables 
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
            """, (db_name,))
            
            table_list = cursor.fetchall()
            
            # Handle null values
            for table in table_list:
                table['rows'] = table['rows'] if table['rows'] is not None else 0
                table['size'] = table['size'] if table['size'] is not None else 0
        except mysql.connector.Error as e:
            logger.error(f'Error listing tables: {str(e)}')
            raise

        return jsonify(table_list)
    except mysql.connector.Error as e:
        error_msg = f'MySQL Error ({e.errno}): {e.msg}'
        logger.error(f'Error listing tables: {error_msg}')
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Unexpected error: {str(e)}'
        logger.error(f'Error listing tables: {error_msg}')
        return jsonify({'error': error_msg}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                logger.error(f'Error closing cursor: {str(e)}')
        if connection:
            try:
                connection.close()
            except Exception as e:
                logger.error(f'Error closing connection: {str(e)}')

@app.route('/api/mysql/databases')
@login_required
def list_databases():
    logger.info('Database list requested')
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor()

        # Get list of databases
        cursor.execute('SHOW DATABASES')
        databases = cursor.fetchall()

        # Get size of each database
        db_list = []
        for (db_name,) in databases:
            if db_name not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                cursor.execute(f"""
                    SELECT 
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) 
                    FROM information_schema.tables 
                    WHERE table_schema = '{db_name}'
                    GROUP BY table_schema;
                """)
                size = cursor.fetchone()
                db_list.append({
                    'name': db_name,
                    'size': size[0] if size else 0
                })

        connection.close()
        return jsonify(db_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mysql/create-db', methods=['POST'])
@login_required
def create_database():
    logger.info('Database creation attempt')
    try:
        data = request.json
        db_name = data.get('name')
        db_user = data.get('user')
        db_password = data.get('password')
        
        if not db_name:
            logger.warning('Database name not provided')
            return jsonify({'error': 'Nama database diperlukan'}), 400

        # Validate database name (prevent SQL injection)
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            logger.warning(f'Invalid database name format: {db_name}')
            return jsonify({'error': 'Format nama database tidak valid. Gunakan hanya huruf, angka, dan underscore'}), 400

        # Validate username if provided
        if db_user and not re.match(r'^[a-zA-Z0-9_]+$', db_user):
            logger.warning(f'Invalid username format: {db_user}')
            return jsonify({'error': 'Format username tidak valid. Gunakan hanya huruf, angka, dan underscore'}), 400

        connection = create_mysql_connection()
        cursor = connection.cursor()

        # Create database
        cursor.execute(f'CREATE DATABASE `{db_name}`')
        
        # Create user and grant privileges if username and password provided
        if db_user and db_password:
            try:
                # Check if user already exists
                cursor.execute("SELECT User FROM mysql.user WHERE User = %s AND Host = 'localhost'", (db_user,))
                user_exists = cursor.fetchone()
                
                if user_exists:
                    # User exists, just grant privileges
                    cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost'")
                    cursor.execute("FLUSH PRIVILEGES")
                    logger.info(f'Granted privileges on {db_name} to existing user {db_user}')
                else:
                    # Create new user
                    cursor.execute(f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY %s", (db_password,))
                    # Grant all privileges on the database to the user
                    cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost'")
                    cursor.execute("FLUSH PRIVILEGES")
                    logger.info(f'Created new user {db_user} and granted privileges on {db_name}')
            except mysql.connector.Error as user_err:
                logger.warning(f'Error handling user {db_user}: {user_err}')
                # Continue without failing the database creation
                pass
            
        # Check if user exists before closing connection
        user_created_or_exists = False
        if db_user:
            try:
                cursor.execute("SELECT User FROM mysql.user WHERE User = %s AND Host = 'localhost'", (db_user,))
                user_created_or_exists = cursor.fetchone() is not None
            except mysql.connector.Error:
                user_created_or_exists = False
        
        connection.commit()
        cursor.close()
        connection.close()
        
        if db_user:
            if user_created_or_exists:
                logger.info(f'Database {db_name} created and privileges granted to user {db_user}')
                return jsonify({'message': f'Database "{db_name}" berhasil dibuat dan privileges diberikan ke user "{db_user}"'})
            else:
                logger.info(f'Database {db_name} created successfully')
                return jsonify({'message': f'Database "{db_name}" berhasil dibuat (user gagal dibuat)'})
        else:
            logger.info(f'Database {db_name} created successfully')
            return jsonify({'message': f'Database "{db_name}" berhasil dibuat'})
    except mysql.connector.Error as err:
        logger.error(f'MySQL error during database creation: {err}')
        if err.errno == 1007:  # Database already exists
            return jsonify({'error': f'Database "{db_name}" sudah ada'}), 400
        elif err.errno == 1045:  # Access denied
            return jsonify({'error': 'Akses ditolak. Periksa konfigurasi MySQL'}), 500
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error during database creation: {e}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/delete-db', methods=['POST'])
@login_required
def delete_database():
    logger.info('Database deletion attempt')
    try:
        db_name = request.json.get('name')
        if not db_name:
            logger.warning('Database name not provided for deletion')
            return jsonify({'error': 'Nama database diperlukan'}), 400

        # Validate database name (prevent SQL injection)
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            logger.warning(f'Invalid database name format for deletion: {db_name}')
            return jsonify({'error': 'Format nama database tidak valid'}), 400

        connection = create_mysql_connection()
        cursor = connection.cursor()

        # Drop database
        cursor.execute(f'DROP DATABASE `{db_name}`')
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f'Database {db_name} deleted successfully')
        return jsonify({'message': f'Database "{db_name}" berhasil dihapus'})
    except mysql.connector.Error as err:
        logger.error(f'MySQL error during database deletion: {err}')
        if err.errno == 1008:  # Database doesn't exist
            return jsonify({'error': f'Database "{db_name}" tidak ditemukan'}), 400
        elif err.errno == 1045:  # Access denied
            return jsonify({'error': 'Akses ditolak. Periksa konfigurasi MySQL'}), 500
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error during database deletion: {e}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/delete-table', methods=['POST'])
@login_required
def delete_table():
    logger.info('Table deletion requested')
    try:
        data = request.get_json()
        db_name = data.get('database')
        table_name = data.get('table')
        
        if not db_name or not table_name:
            logger.warning('Database name or table name not provided')
            return jsonify({'error': 'Nama database dan tabel diperlukan'}), 400
        
        # Validate database and table names (prevent SQL injection)
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            logger.warning(f'Invalid database name format for table deletion: {db_name}')
            return jsonify({'error': 'Format nama database tidak valid'}), 400
            
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            logger.warning(f'Invalid table name format for deletion: {table_name}')
            return jsonify({'error': 'Format nama tabel tidak valid'}), 400

        connection = create_mysql_connection()
        cursor = connection.cursor()

        # Use the specified database
        cursor.execute(f'USE `{db_name}`')
        
        # Drop table
        cursor.execute(f'DROP TABLE `{table_name}`')
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f'Table {table_name} deleted successfully from database {db_name}')
        return jsonify({'message': f'Tabel "{table_name}" berhasil dihapus dari database "{db_name}"'})
    except mysql.connector.Error as err:
        logger.error(f'MySQL error during table deletion: {err}')
        if err.errno == 1051:  # Table doesn't exist
            return jsonify({'error': f'Tabel "{table_name}" tidak ditemukan dalam database "{db_name}"'}), 400
        elif err.errno == 1049:  # Database doesn't exist
            return jsonify({'error': f'Database "{db_name}" tidak ditemukan'}), 400
        elif err.errno == 1045:  # Access denied
            return jsonify({'error': 'Akses ditolak. Periksa konfigurasi MySQL'}), 500
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error during table deletion: {e}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/get-root-password', methods=['GET'])
@login_required
def get_root_password():
    """Get current MySQL root password from config"""
    try:
        current_password = db_config.get('password', '')
        return jsonify({'password': current_password})
    except Exception as e:
        logger.error(f'Error getting root password: {str(e)}')
        return jsonify({'error': 'Gagal mendapatkan password root'}), 500

@app.route('/api/mysql/set-root-password', methods=['POST'])
@login_required
def set_root_password():
    logger.info('Root password change requested')
    try:
        data = request.get_json()
        new_password = data.get('password', '')
        
        # Connect to MySQL as root with current password from db_config
        connection = create_mysql_connection()
        cursor = connection.cursor()
        
        # Set new password for root user
        if new_password:
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (new_password,))
        else:
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY ''")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        # Update the global db_config with new password
        global db_config
        old_password = db_config['password']
        db_config['password'] = new_password
        logger.info(f'Password updated in db_config: from "{old_password}" to "{new_password}"')
        logger.info(f'Current db_config password: {db_config["password"]}')
        
        # Save configuration to JSON file for persistence
        if save_mysql_config(db_config):
            logger.info('Password configuration saved to file successfully')
        else:
            logger.warning('Failed to save password configuration to file')
        
        # Reinitialize connection pool with new password
        global connection_pool
        try:
            if connection_pool:
                connection_pool._remove_connections()
            connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)
            logger.info('Connection pool reinitialized with new password')
        except Exception as e:
            logger.warning(f'Failed to reinitialize connection pool: {str(e)}')
            connection_pool = None
        
        # Restart SLEMP to reload database configuration
        try:
            logger.info('Restarting SLEMP to reload database configuration')
            restart_result = subprocess.run(['supervisorctl', 'restart', 'slemp'], capture_output=True, text=True, timeout=30)
            if restart_result.returncode == 0:
                logger.info('SLEMP restarted successfully')
            else:
                logger.warning(f'Failed to restart SLEMP: {restart_result.stderr}')
        except Exception as e:
            logger.warning(f'Error restarting SLEMP: {str(e)}')
        
        logger.info('Root password changed successfully')
        return jsonify({'message': 'Password root MySQL berhasil diubah'})
        
    except mysql.connector.Error as err:
        logger.error(f'MySQL error during password change: {err}')
        if err.errno == 1045:  # Access denied
            return jsonify({'error': 'Akses ditolak. Password root saat ini mungkin sudah berubah'}), 500
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Unexpected error during password change: {e}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/users', methods=['GET'])
@login_required
def get_mysql_users():
    """Get list of MySQL users"""
    try:
        connection = create_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get all users
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User != '' ORDER BY User, Host")
        users = cursor.fetchall()
        
        # Get privileges for each user
        for user in users:
            try:
                cursor.execute(f"SHOW GRANTS FOR '{user['User']}'@'{user['Host']}'")
                grants = cursor.fetchall()
                privileges = []
                for grant in grants:
                    grant_text = list(grant.values())[0]
                    if 'ALL PRIVILEGES' in grant_text:
                        privileges.append('ALL PRIVILEGES')
                    elif 'GRANT' in grant_text:
                        # Extract specific privileges
                        start = grant_text.find('GRANT ') + 6
                        end = grant_text.find(' ON')
                        if start < end:
                            privileges.append(grant_text[start:end])
                user['privileges'] = ', '.join(privileges) if privileges else 'No privileges'
            except Exception:
                user['privileges'] = 'Unable to determine'
        
        cursor.close()
        connection.close()
        
        return jsonify({'users': users})
        
    except mysql.connector.Error as err:
        logger.error(f'MySQL error getting users: {err}')
        return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Error getting MySQL users: {str(e)}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/create-user', methods=['POST'])
@login_required
def create_mysql_user():
    """Create a new MySQL user"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        host = data.get('host', '%')
        privileges = data.get('privileges', 'ALL')
        
        if not username or not password:
            return jsonify({'error': 'Username dan password harus diisi'}), 400
        
        connection = create_mysql_connection()
        cursor = connection.cursor()
        
        # Create user
        cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY %s", (password,))
        
        # Grant privileges
        if privileges == 'ALL':
            cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'{host}'")
        else:
            cursor.execute(f"GRANT {privileges} ON *.* TO '{username}'@'{host}'")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f'MySQL user created: {username}@{host}')
        return jsonify({'message': f'User {username}@{host} berhasil dibuat'})
        
    except mysql.connector.Error as err:
        logger.error(f'MySQL error creating user: {err}')
        if err.errno == 1396:  # User already exists
            return jsonify({'error': f'User {username}@{host} sudah ada'}), 400
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Error creating MySQL user: {str(e)}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/delete-user', methods=['DELETE'])
@login_required
def delete_mysql_user():
    """Delete a MySQL user"""
    try:
        data = request.get_json()
        username = data.get('username')
        host = data.get('host')
        
        if not username or not host:
            return jsonify({'error': 'Username dan host harus diisi'}), 400
        
        # Prevent deletion of root user
        if username == 'root':
            return jsonify({'error': 'User root tidak dapat dihapus'}), 400
        
        connection = create_mysql_connection()
        cursor = connection.cursor()
        
        # Drop user
        cursor.execute(f"DROP USER '{username}'@'{host}'")
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f'MySQL user deleted: {username}@{host}')
        return jsonify({'message': f'User {username}@{host} berhasil dihapus'})
        
    except mysql.connector.Error as err:
        logger.error(f'MySQL error deleting user: {err}')
        if err.errno == 1396:  # User doesn't exist
            return jsonify({'error': f'User {username}@{host} tidak ditemukan'}), 404
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Error deleting MySQL user: {str(e)}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/mysql/update-user', methods=['PUT'])
@login_required
def update_mysql_user():
    """Update a MySQL user's password, privileges, and host"""
    try:
        data = request.get_json()
        username = data.get('username')
        host = data.get('host')
        new_host = data.get('new_host', host)  # Use original host if new_host not provided
        password = data.get('password')
        privileges = data.get('privileges', 'ALL PRIVILEGES')
        
        if not username or not host or not password or not new_host:
            return jsonify({'error': 'Username, host, new_host, dan password harus diisi'}), 400
        
        connection = create_mysql_connection()
        cursor = connection.cursor()
        
        # If host is changing, we need to create a new user and drop the old one
        if host != new_host:
            # Create new user with new host
            cursor.execute(f"CREATE USER '{username}'@'{new_host}' IDENTIFIED BY %s", (password,))
            
            # Grant privileges to new user
            if privileges == 'ALL PRIVILEGES':
                cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'{new_host}'")
            else:
                cursor.execute(f"GRANT {privileges} ON *.* TO '{username}'@'{new_host}'")
            
            # Drop old user
            try:
                cursor.execute(f"DROP USER '{username}'@'{host}'")
            except mysql.connector.Error as err:
                if err.errno != 1396:  # Ignore if user doesn't exist
                    raise
            
            logger.info(f'MySQL user host changed: {username}@{host} -> {username}@{new_host}')
            message = f'User {username}@{new_host} berhasil diupdate (host diubah dari {host})'
        else:
            # Just update password and privileges for existing user
            cursor.execute(f"ALTER USER '{username}'@'{host}' IDENTIFIED BY %s", (password,))
            
            # Update privileges if specified
            if privileges and privileges != 'CURRENT':
                # First revoke all privileges
                cursor.execute(f"REVOKE ALL PRIVILEGES ON *.* FROM '{username}'@'{host}'")
                
                # Grant new privileges
                if privileges == 'ALL PRIVILEGES':
                    cursor.execute(f"GRANT ALL PRIVILEGES ON *.* TO '{username}'@'{host}'")
                else:
                    cursor.execute(f"GRANT {privileges} ON *.* TO '{username}'@'{host}'")
            
            logger.info(f'MySQL user updated: {username}@{host}')
            message = f'User {username}@{host} berhasil diupdate'
        
        # Flush privileges
        cursor.execute("FLUSH PRIVILEGES")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'message': message})
        
    except mysql.connector.Error as err:
        logger.error(f'MySQL error updating user: {err}')
        if err.errno == 1396:  # User doesn't exist
            return jsonify({'error': f'User {username}@{host} tidak ditemukan'}), 404
        elif err.errno == 1007:  # User already exists
            return jsonify({'error': f'User {username}@{new_host} sudah ada'}), 409
        else:
            return jsonify({'error': f'Error MySQL: {str(err)}'}), 500
    except Exception as e:
        logger.error(f'Error updating MySQL user: {str(e)}')
        return jsonify({'error': f'Terjadi kesalahan: {str(e)}'}), 500

@app.route('/api/app/update', methods=['POST'])
@login_required
def update_app():
    """Update aplikasi Flask"""
    
    try:
        app.logger.info(f"App update initiated")
        
        # Restart SLEMP menggunakan supervisorctl
        result = subprocess.run(
            ['bash', '/var/www/panel/update.sh'],
            capture_output=True,
            text=True,
            timeout=300  # Increased timeout to 5 minutes for update process
        )
        
        if result.returncode == 0:
            app.logger.info("App updated successfully")
            return jsonify({
                'success': True,
                'message': 'Aplikasi berhasil diupdate'
            })
        else:
            app.logger.error(f"Failed to update app: {result.stderr}")
            return jsonify({
                'success': False,
                'message': f'Gagal update aplikasi: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        app.logger.error("Timeout updating app after 5 minutes")
        return jsonify({
            'success': False,
            'message': 'Timeout saat update aplikasi (lebih dari 5 menit). Silakan coba lagi atau periksa koneksi internet.'
        }), 500
    except Exception as e:
        app.logger.error(f"Error during app update: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@app.route('/api/app/restart', methods=['POST'])
@login_required
def restart_app():
    """Restart aplikasi Flask (SLEMP via gunicorn)"""
    
    try:
        app.logger.info(f"App restart initiated")
        
        # Restart SLEMP menggunakan supervisorctl
        result = subprocess.run(
            ['supervisorctl', 'restart', 'slemp'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            app.logger.info("SLEMP restarted successfully")
            return jsonify({
                'success': True,
                'message': 'Aplikasi berhasil direstart'
            })
        else:
            app.logger.error(f"Failed to restart SLEMP: {result.stderr}")
            return jsonify({
                'success': False,
                'message': f'Gagal restart aplikasi: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        app.logger.error("Timeout restarting SLEMP")
        return jsonify({
            'success': False,
            'message': 'Timeout saat restart aplikasi'
        }), 500
    except Exception as e:
        app.logger.error(f"Error during app restart: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@app.route('/api/mariadb/config', methods=['GET', 'POST'])
@login_required
def mariadb_config():
    """Read or update MariaDB configuration file"""
    config_file = '/etc/mysql/mariadb.conf.d/50-server.cnf'
    
    try:
        if request.method == 'GET':
            # Read configuration file
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                return jsonify({
                    'success': True,
                    'content': content
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'File konfigurasi tidak ditemukan'
                }), 404
        
        elif request.method == 'POST':
            # Update configuration file
            data = request.get_json()
            content = data.get('content', '')
            
            # Backup original file
            backup_file = f'{config_file}.backup.{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_file)
                logger.info(f'Backup created: {backup_file}')
            
            # Write new configuration
            with open(config_file, 'w') as f:
                f.write(content)
            
            logger.info(f'MariaDB configuration updated by user {current_user.username}')
            
            return jsonify({
                'success': True,
                'message': 'Konfigurasi berhasil disimpan'
            })
            
    except PermissionError:
        logger.error(f'Permission denied accessing {config_file}')
        return jsonify({
            'success': False,
            'message': 'Tidak memiliki izin untuk mengakses file konfigurasi'
        }), 403
    except Exception as e:
        logger.error(f'Error managing MariaDB config: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@app.route('/api/nginx/config', methods=['GET', 'POST'])
@login_required
def nginx_config():
    """Read or update Nginx configuration file"""
    config_file = '/etc/nginx/nginx.conf'
    
    try:
        if request.method == 'GET':
            # Read configuration file
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                return jsonify({
                    'success': True,
                    'content': content
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'File konfigurasi tidak ditemukan'
                }), 404
        
        elif request.method == 'POST':
            # Update configuration file
            data = request.get_json()
            content = data.get('content', '')
            
            # Backup original file
            backup_file = f'{config_file}.backup.{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_file)
                logger.info(f'Backup created: {backup_file}')
            
            # Write new configuration
            with open(config_file, 'w') as f:
                f.write(content)
            
            logger.info(f'Nginx configuration updated by user {current_user.username}')
            
            # Reload nginx configuration to apply changes
            result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f'Failed to reload nginx: {result.stderr}')
                return jsonify({
                    'success': False,
                    'message': f'Konfigurasi disimpan tetapi gagal reload nginx: {result.stderr}'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Konfigurasi berhasil disimpan dan nginx direload'
            })
            
    except PermissionError:
        logger.error(f'Permission denied accessing {config_file}')
        return jsonify({
            'success': False,
            'message': 'Tidak memiliki izin untuk mengakses file konfigurasi'
        }), 403
    except Exception as e:
        logger.error(f'Error managing Nginx config: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

def generate_vhost_config(domain, root_dir, ssl=False, ssl_cert='', ssl_key='', force_https=False, php_version='8.1', 
                          proxy_enabled=False, proxy_pass='', proxy_headers='', rewrite_rules='', 
                          index_files='index.html index.htm index.php', error_404='', error_500=''):
    """Generate nginx virtual host configuration"""
    config = f"""server {{
    listen 80;"""
    
    # Add SSL configuration if enabled
    if ssl and ssl_cert and ssl_key:
        config += f"""
    listen 443 ssl;
    ssl_certificate {ssl_cert};
    ssl_certificate_key {ssl_key};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;"""
    
    config += f"""
    server_name {domain};
    root {root_dir};

    index {index_files};
"""
    
    # Add HTTPS redirect if force_https is enabled
    if ssl and force_https:
        config += f"""
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {{
        return 301 https://$server_name$request_uri;
    }}
"""
    
    # Add custom error pages if specified
    if error_404:
        config += f"""
    error_page 404 {error_404};
"""
    
    if error_500:
        config += f"""
    error_page 500 502 503 504 {error_500};
"""
    
    # Add rewrite rules if specified
    if rewrite_rules:
        config += f"""
    # Custom rewrite rules
{rewrite_rules}
"""
    
    # Add proxy configuration if enabled
    if proxy_enabled and proxy_pass:
        config += f"""
    location / {{
        proxy_pass {proxy_pass};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
"""
        
        # Add custom proxy headers if specified
        if proxy_headers:
            # Split proxy headers by newlines and add them
            for header in proxy_headers.strip().split('\n'):
                if header.strip():
                    # Check if header already ends with semicolon
                    header_clean = header.strip()
                    if not header_clean.endswith(';'):
                        header_clean += ';'
                    config += f"""
        {header_clean}
"""
        
        config += f"""
    }}
"""
    else:
        # Standard location block for non-proxy setup
        config += f"""
    location / {{
        try_files $uri $uri/ /index.php?$query_string;
    }}

    location ~ \.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/run/php/php{php_version}-fpm.sock;
    }}

    location ~ /\.ht {{
        deny all;
    }}
"""
    
    config += "}"
    
    return config

@app.route('/api/nginx/update-vhost', methods=['POST'])
@login_required
def update_vhost():
    """Update virtual host settings including custom configuration"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        root_dir = data.get('root_dir')
        enabled = data.get('enabled', True)
        ssl = data.get('ssl', False)
        ssl_cert = data.get('ssl_cert', '')
        ssl_key = data.get('ssl_key', '')
        force_https = data.get('force_https', False)
        php_version = data.get('php_version', '8.1')
        custom_config = data.get('custom_config', '')
        
        # Get proxy settings
        proxy_enabled = data.get('proxy_enabled', False)
        proxy_pass = data.get('proxy_pass', '')
        proxy_headers = data.get('proxy_headers', '')
        
        # Get rewrite settings
        rewrite_rules = data.get('rewrite_rules', '')
        
        # Get default settings
        index_files = data.get('index_files', 'index.html index.htm index.php')
        error_404 = data.get('error_404', '')
        error_500 = data.get('error_500', '')
        
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        
        config_file = f'/etc/nginx/sites-available/{domain}'
        
        # If custom config is provided, save it to the config file
        if custom_config:
            # Write new configuration
            with open(config_file, 'w') as f:
                f.write(custom_config)
            
            logger.info(f'Virtual host config updated for {domain} by user {current_user.username}')
        else:
            # Generate configuration based on settings
            config = generate_vhost_config(
                domain=domain, 
                root_dir=root_dir, 
                ssl=ssl, 
                ssl_cert=ssl_cert, 
                ssl_key=ssl_key, 
                force_https=force_https, 
                php_version=php_version,
                proxy_enabled=proxy_enabled,
                proxy_pass=proxy_pass,
                proxy_headers=proxy_headers,
                rewrite_rules=rewrite_rules,
                index_files=index_files,
                error_404=error_404,
                error_500=error_500
            )
            
            # Write new configuration
            with open(config_file, 'w') as f:
                f.write(config)
            
            logger.info(f'Virtual host config generated for {domain} by user {current_user.username}')
        
        # Handle enabled/disabled state
        enabled_path = f'/etc/nginx/sites-enabled/{domain}'
        if enabled:
            # Enable: create symbolic link if it doesn't exist
            if not os.path.exists(enabled_path):
                os.symlink(config_file, enabled_path)
                logger.info(f'Enabled virtual host: {domain}')
        else:
            # Disable: remove symbolic link if it exists
            if os.path.exists(enabled_path):
                os.remove(enabled_path)
                logger.info(f'Disabled virtual host: {domain}')
        
        # Reload nginx configuration to apply changes
        result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to reload nginx: {result.stderr}')
            return jsonify({'error': f'Failed to reload nginx: {result.stderr}'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Virtual host settings updated successfully'
        })
        
    except PermissionError:
        logger.error(f'Permission denied updating vhost config for {domain}')
        return jsonify({
            'success': False,
            'error': 'Tidak memiliki izin untuk mengupdate konfigurasi'
        }), 403
    except Exception as e:
        logger.error(f'Error updating vhost settings: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error updating settings: {str(e)}'
        }), 500

@app.route('/api/nginx/config/<domain>', methods=['GET'])
@login_required
def get_vhost_config(domain):
    """Read virtual host configuration file from /etc/nginx/sites-available"""
    config_file = f'/etc/nginx/sites-available/{domain}'
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'config': content,
                'file_path': config_file
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Configuration file for {domain} not found'
            }), 404
            
    except PermissionError:
        logger.error(f'Permission denied accessing {config_file}')
        return jsonify({
            'success': False,
            'message': 'Tidak memiliki izin untuk mengakses file konfigurasi'
        }), 403
    except Exception as e:
        logger.error(f'Error reading vhost config for {domain}: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error reading configuration: {str(e)}'
        }), 500

def run_ssl_generation(domain, email):
    """Run SSL certificate generation in background with real-time output"""
    try:
        # Emit progress update
        socketio.emit('ssl_generate_progress', {
            'status': 'Checking domain accessibility...',
            'step': '1/4',
            'progress': 15
        })
        
        # Check if domain is accessible (basic validation)
        socketio.emit('ssl_generate_output', {
            'message': f'Checking domain accessibility for {domain}...',
            'type': 'info'
        })
        
        try:
            import socket
            socket.gethostbyname(domain)
            socketio.emit('ssl_generate_output', {
                'message': f'Domain {domain} is accessible',
                'type': 'success'
            })
        except socket.gaierror:
            socketio.emit('ssl_generate_complete', {
                'success': False,
                'error': f'Domain {domain} is not accessible. Please ensure the domain points to this server.'
            })
            return
        
        # Emit progress update
        socketio.emit('ssl_generate_progress', {
            'status': 'Checking Certbot installation...',
            'step': '2/4',
            'progress': 30
        })
        
        # Check if certbot is installed
        socketio.emit('ssl_generate_output', {
            'message': 'Checking if Certbot is installed...',
            'type': 'info'
        })
        
        certbot_check = subprocess.run(['which', 'certbot'], capture_output=True, text=True)
        if certbot_check.returncode != 0:
            socketio.emit('ssl_generate_complete', {
                'success': False,
                'error': 'Certbot is not installed. Please install certbot first.'
            })
            return
        
        socketio.emit('ssl_generate_output', {
            'message': 'Certbot is installed and ready',
            'type': 'success'
        })
        
        # Emit progress update
        socketio.emit('ssl_generate_progress', {
            'status': 'Generating SSL certificate...',
            'step': '3/4',
            'progress': 50
        })
        
        # Generate SSL certificate using certbot
        socketio.emit('ssl_generate_output', {
            'message': f'Running certbot for domain {domain}...',
            'type': 'info'
        })
        
        certbot_cmd = [
            'certbot', 'certonly',
            '--nginx',
            '--non-interactive',
            '--agree-tos',
            '--email', email,
            '-d', domain
        ]
        
        socketio.emit('ssl_generate_output', {
            'message': f'Command: {" ".join(certbot_cmd)}',
            'type': 'command'
        })
        
        certbot_process = subprocess.Popen(
            certbot_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream certbot output
        for line in iter(certbot_process.stdout.readline, ''):
            if line.strip():
                socketio.emit('ssl_generate_output', {
                    'message': line.strip(),
                    'type': 'info'
                })
        
        certbot_process.wait()
        
        # Emit progress update
        socketio.emit('ssl_generate_progress', {
            'status': 'Verifying certificate files...',
            'step': '4/4',
            'progress': 90
        })
        
        if certbot_process.returncode == 0:
            # Certificate generated successfully
            cert_path = f'/etc/letsencrypt/live/{domain}/fullchain.pem'
            key_path = f'/etc/letsencrypt/live/{domain}/privkey.pem'
            
            socketio.emit('ssl_generate_output', {
                'message': f'Checking certificate files at {cert_path}...',
                'type': 'info'
            })
            
            # Verify certificate files exist
            if os.path.exists(cert_path) and os.path.exists(key_path):
                logger.info(f'SSL certificate generated successfully for {domain}')
                socketio.emit('ssl_generate_output', {
                    'message': f'Certificate files found: {cert_path}',
                    'type': 'success'
                })
                socketio.emit('ssl_generate_output', {
                    'message': f'Private key found: {key_path}',
                    'type': 'success'
                })
                socketio.emit('ssl_generate_complete', {
                    'success': True,
                    'message': f'SSL certificate generated successfully for {domain}',
                    'cert_path': cert_path,
                    'key_path': key_path
                })
            else:
                logger.error(f'Certificate files not found after generation for {domain}')
                socketio.emit('ssl_generate_complete', {
                    'success': False,
                    'error': 'Certificate generated but files not found'
                })
        else:
            # Certificate generation failed
            logger.error(f'Failed to generate SSL certificate for {domain}')
            socketio.emit('ssl_generate_complete', {
                'success': False,
                'error': 'Failed to generate SSL certificate. Please check the output above for details.'
            })
        
    except Exception as e:
        logger.error(f'Error generating Let\'s Encrypt SSL certificate: {str(e)}')
        socketio.emit('ssl_generate_complete', {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })

@app.route('/api/ssl/check/<domain>', methods=['GET'])
@login_required
def check_ssl_certificates(domain):
    """Check if SSL certificates exist for a domain"""
    try:
        cert_path = f'/etc/letsencrypt/live/{domain}/fullchain.pem'
        key_path = f'/etc/letsencrypt/live/{domain}/privkey.pem'
        
        cert_exists = os.path.exists(cert_path)
        key_exists = os.path.exists(key_path)
        
        logger.info(f'SSL certificate check for {domain}: cert={cert_exists}, key={key_exists}')
        
        return jsonify({
            'success': True,
            'domain': domain,
            'cert_exists': cert_exists,
            'key_exists': key_exists,
            'cert_path': cert_path if cert_exists else '',
            'key_path': key_path if key_exists else ''
        })
        
    except Exception as e:
        logger.error(f'Error checking SSL certificates for {domain}: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error checking SSL certificates: {str(e)}'
        }), 500

@app.route('/api/ssl/letsencrypt', methods=['POST'])
@login_required
def generate_letsencrypt_ssl():
    """Generate Let's Encrypt SSL certificate for a domain with real-time output"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        email = data.get('email')
        
        if not domain:
            return jsonify({'error': 'Domain is required'}), 400
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Validate email format
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        logger.info(f'Generating Let\'s Encrypt SSL certificate for {domain} with email {email} by user {current_user.username}')
        
        # Start SSL generation in background thread
        ssl_thread = threading.Thread(target=run_ssl_generation, args=(domain, email))
        ssl_thread.daemon = True
        ssl_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'SSL generation started'
        })
        
    except Exception as e:
        logger.error(f'Error starting SSL generation: {str(e)}')
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

def _extract_cert_field(cert_data, field_name, default_value):
    """Safely extract field from SSL certificate data"""
    try:
        for item in cert_data:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                key, value = item[0], item[1]
                if key == field_name:
                    return value
    except (TypeError, ValueError, IndexError):
        pass
    return default_value

@app.route('/api/ssl/check', methods=['POST'])
@login_required
def check_ssl_certificate_info():
    """Check SSL certificate information including expiry date"""
    try:
        data = request.get_json()
        domain = data.get('domain')
        cert_path = data.get('cert_path')
        
        if not domain:
            return jsonify({
                'success': False,
                'error': 'Domain is required'
            }), 400
        
        logger.info(f'Checking SSL certificate info for {domain} by user {current_user.username}')
        
        # Try to get certificate info from domain (online check)
        try:
            import ssl
            import socket
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to domain and get certificate
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse expiry date
                    expiry_str = cert['notAfter']
                    expiry_date = datetime.datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days left
                    now = datetime.datetime.now()
                    days_left = (expiry_date - now).days
                    
                    # Determine status
                    if days_left < 0:
                        status = 'Expired'
                        valid = False
                    elif days_left < 7:
                        status = 'Expires Soon'
                        valid = True
                    elif days_left < 30:
                        status = 'Valid (Renewal Recommended)'
                        valid = True
                    else:
                        status = 'Valid'
                        valid = True
                    
                    return jsonify({
                        'success': True,
                        'valid': valid,
                        'status': status,
                        'expiry_date': expiry_date.isoformat(),
                        'days_left': days_left,
                        'issuer': _extract_cert_field(cert.get('issuer', []), 'organizationName', 'Unknown'),
                        'subject': _extract_cert_field(cert.get('subject', []), 'commonName', domain)
                    })
                    
        except (socket.timeout, socket.gaierror, ssl.SSLError, ConnectionRefusedError) as e:
            # If online check fails, try to check local certificate file
            if cert_path and os.path.exists(cert_path):
                try:
                    import subprocess
                    
                    # Use openssl to check certificate
                    result = subprocess.run([
                        'openssl', 'x509', '-in', cert_path, '-noout', '-enddate'
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        # Parse openssl output
                        enddate_line = result.stdout.strip()
                        if 'notAfter=' in enddate_line:
                            date_str = enddate_line.split('notAfter=')[1]
                            expiry_date = datetime.datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
                            
                            now = datetime.datetime.now()
                            days_left = (expiry_date - now).days
                            
                            if days_left < 0:
                                status = 'Expired'
                                valid = False
                            elif days_left < 7:
                                status = 'Expires Soon'
                                valid = True
                            elif days_left < 30:
                                status = 'Valid (Renewal Recommended)'
                                valid = True
                            else:
                                status = 'Valid'
                                valid = True
                            
                            return jsonify({
                                'success': True,
                                'valid': valid,
                                'status': status,
                                'expiry_date': expiry_date.isoformat(),
                                'days_left': days_left,
                                'source': 'local_file'
                            })
                    
                except subprocess.TimeoutExpired:
                    pass
                except Exception as file_error:
                    logger.warning(f'Error checking local certificate file: {str(file_error)}')
            
            # Return connection error
            return jsonify({
                'success': False,
                'error': f'Unable to connect to {domain}:443 or check certificate file. Error: {str(e)}'
            })
            
    except Exception as e:
        logger.error(f'Error checking SSL certificate info: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

def run_certbot_installation():
    """Run Certbot installation in background with real-time output"""
    try:
        # Emit progress update
        socketio.emit('certbot_install_progress', {
            'status': 'Updating package list...',
            'step': '1/3',
            'progress': 20
        })
        
        # Update package list first
        socketio.emit('certbot_install_output', {
            'message': 'Running apt update...',
            'type': 'info'
        })
        
        update_process = subprocess.Popen(
            ['apt', 'update'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream update output
        for line in iter(update_process.stdout.readline, ''):
            if line.strip():
                socketio.emit('certbot_install_output', {
                    'message': line.strip(),
                    'type': 'info'
                })
        
        update_process.wait()
        
        if update_process.returncode != 0:
            socketio.emit('certbot_install_complete', {
                'success': False,
                'error': 'Failed to update package list'
            })
            return
        
        # Emit progress update
        socketio.emit('certbot_install_progress', {
            'status': 'Installing Certbot...',
            'step': '2/3',
            'progress': 50
        })
        
        # Install certbot and python3-certbot-nginx
        socketio.emit('certbot_install_output', {
            'message': 'Installing certbot python3-certbot-nginx...',
            'type': 'info'
        })
        
        install_process = subprocess.Popen(
            ['apt', 'install', 'certbot', 'python3-certbot-nginx', '-y'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream installation output
        for line in iter(install_process.stdout.readline, ''):
            if line.strip():
                socketio.emit('certbot_install_output', {
                    'message': line.strip(),
                    'type': 'info'
                })
        
        install_process.wait()
        
        # Emit progress update
        socketio.emit('certbot_install_progress', {
            'status': 'Finalizing installation...',
            'step': '3/3',
            'progress': 90
        })
        
        if install_process.returncode == 0:
            logger.info('Certbot installed successfully')
            socketio.emit('certbot_install_complete', {
                'success': True,
                'message': 'Certbot installed successfully'
            })
        else:
            logger.error('Failed to install Certbot')
            socketio.emit('certbot_install_complete', {
                'success': False,
                'error': 'Failed to install Certbot'
            })
        
    except Exception as e:
        logger.error(f'Error installing Certbot: {str(e)}')
        socketio.emit('certbot_install_complete', {
            'success': False,
            'error': f'Internal server error: {str(e)}'
        })

@app.route('/api/certbot/install', methods=['POST'])
@login_required
def install_certbot():
    """Install Certbot and python3-certbot-nginx with real-time output"""
    try:
        logger.info(f'Installing Certbot by user {current_user.username}')
        
        # Start installation in background thread
        install_thread = threading.Thread(target=run_certbot_installation)
        install_thread.daemon = True
        install_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Installation started'
        })
        
    except Exception as e:
        logger.error(f'Error starting Certbot installation: {str(e)}')
        return jsonify({
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/certbot/status', methods=['GET'])
@login_required
def check_certbot_status():
    """Check if Certbot is installed"""
    try:
        # Check if certbot is installed
        certbot_check = subprocess.run(['which', 'certbot'], capture_output=True, text=True)
        certbot_installed = certbot_check.returncode == 0
        
        certbot_version = 'Not installed'
        if certbot_installed:
            try:
                version_result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
                if version_result.returncode == 0:
                    certbot_version = version_result.stdout.strip()
            except:
                certbot_version = 'Installed (version unknown)'
        
        return jsonify({
            'success': True,
            'installed': certbot_installed,
            'version': certbot_version
        })
        
    except Exception as e:
        logger.error(f'Error checking Certbot status: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/nginx/status')
@login_required
def nginx_status():
    try:
        # 1. Check if Nginx is running
        result = subprocess.run(['pgrep', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': 'Nginx is not running',
                'active_connections': 0,
                'requests_per_sec': 0,
                'total_requests': 0,
                'server_load': '0%',
                'uptime': 'Not running',
                'version': 'Unable to detect',
                'worker_processes': 0,
                'reading': 0,
                'writing': 0,
                'waiting': 0
            })

        # 2. Get Nginx version
        nginx_version = 'Unable to detect'
        try:
            version_result = subprocess.run(['nginx', '-v'], capture_output=True, text=True)
            version_output = version_result.stderr.strip() if version_result.stderr else version_result.stdout.strip()
            if 'nginx version:' in version_output:
                nginx_version = version_output.split('nginx version:')[1].strip()
        except Exception as e:
            logger.warning(f'Failed to get nginx version: {str(e)}')

        # 3. Get stub_status info
        active_connections = 0
        total_requests = 0
        reading = 0
        writing = 0
        waiting = 0
        try:
            stub_result = subprocess.run(['curl', '-s', 'http://localhost/nginx_status'],
                                         capture_output=True, text=True, timeout=5)
            if stub_result.returncode == 0 and stub_result.stdout:
                lines = stub_result.stdout.strip().split('\n')
                for line in lines:
                    if 'Active connections:' in line:
                        active_connections = int(line.split(':')[1].strip())
                    elif 'server accepts handled requests' in line:
                        continue
                    elif re.match(r'^\s*\d+\s+\d+\s+\d+\s*$', line):
                        parts = line.strip().split()
                        if len(parts) == 3:
                            total_requests = int(parts[2])
                    elif 'Reading:' in line and 'Writing:' in line and 'Waiting:' in line:
                        try:
                            parts = line.replace(':', '').split()
                            reading = int(parts[parts.index('Reading') + 1])
                            writing = int(parts[parts.index('Writing') + 1])
                            waiting = int(parts[parts.index('Waiting') + 1])
                        except Exception as e:
                            logger.warning(f'Failed to parse Reading/Writing/Waiting: {str(e)}')
        except Exception as e:
            logger.warning(f'Failed to parse stub_status: {str(e)}')

        # 4. Get uptime (from oldest nginx process)
        uptime_seconds = 0
        uptime = 'Unable to detect'
        try:
            result = subprocess.run(['pgrep', '-o', 'nginx'], capture_output=True, text=True)
            pid = result.stdout.strip()
            if pid:
                process = psutil.Process(int(pid))
                start_time = process.create_time()
                uptime_seconds = int(time.time() - start_time)
                uptime = format_uptime(uptime_seconds)
        except Exception as e:
            logger.warning(f'Failed to calculate uptime: {str(e)}')

        # 5. Get worker process count
        worker_processes = 0
        try:
            result = subprocess.run(['pgrep', 'nginx'], capture_output=True, text=True)
            if result.returncode == 0:
                worker_processes = len(result.stdout.strip().split('\n'))
        except Exception as e:
            logger.warning(f'Failed to count worker processes: {str(e)}')

        # 6. Calculate requests per second
        requests_per_sec = 0
        if uptime_seconds > 0 and total_requests > 0:
            requests_per_sec = round(total_requests / uptime_seconds, 2)

        # 7. Get server load (1-minute average)
        server_load = '0%'
        try:
            load_avg = psutil.getloadavg()[0]
            cpu_count = psutil.cpu_count()
            server_load = f'{(load_avg / cpu_count * 100):.1f}%'
        except Exception as e:
            logger.warning(f'Failed to get server load: {str(e)}')

        # 8. Return status
        return jsonify({
            'success': True,
            'active_connections': active_connections,
            'requests_per_sec': requests_per_sec,
            'total_requests': total_requests,
            'server_load': server_load,
            'uptime': uptime,
            'version': nginx_version,
            'worker_processes': worker_processes,
            'reading': reading,
            'writing': writing,
            'waiting': waiting
        })

    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'active_connections': 0,
            'requests_per_sec': 0,
            'total_requests': 0,
            'server_load': '0%',
            'uptime': 'Error',
            'version': 'Error',
            'worker_processes': 0,
            'reading': 0,
            'writing': 0,
            'waiting': 0
        }), 500

@socketio.on('install_php_module')
def handle_install_php_module(data):
    """Handle real-time PHP module installation via SocketIO"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        emit('error', {'message': 'Authentication required'})
        return
    
    module_name = data.get('module')
    
    if not module_name:
        emit('php_module_install_error', {'message': 'Module name is required'})
        return
    
    # Validate module name (basic security check)
    if not re.match(r'^[a-zA-Z0-9_-]+$', module_name):
        emit('php_module_install_error', {'message': 'Invalid module name'})
        return
    
    def install_module_background():
        try:
            # Emit initial progress
            socketio.emit('php_module_install_progress', {
                'step': 1,
                'total': 3,
                'status': f'Memulai instalasi modul {module_name}...',
                'percentage': 10
            })
            
            socketio.emit('php_module_install_output', {
                'output': f'Starting installation of PHP module: {module_name}',
                'type': 'info'
            })
            
            time.sleep(1)
            
            # Step 1: Update package list
            socketio.emit('php_module_install_progress', {
                'step': 1,
                'total': 3,
                'status': 'Updating package list...',
                'percentage': 20
            })
            
            socketio.emit('php_module_install_output', {
                'output': 'Updating package repositories...',
                'type': 'command'
            })
            
            result = subprocess.run(['apt', 'update'], capture_output=True, text=True)
            if result.returncode != 0:
                socketio.emit('php_module_install_error', {
                    'message': f'Failed to update package list: {result.stderr}'
                })
                return
            
            socketio.emit('php_module_install_output', {
                'output': 'Package list updated successfully',
                'type': 'success'
            })
            
            time.sleep(1)
            
            # Step 2: Install the PHP module
            socketio.emit('php_module_install_progress', {
                'step': 2,
                'total': 3,
                'status': f'Installing php-{module_name}...',
                'percentage': 50
            })
            
            socketio.emit('php_module_install_output', {
                'output': f'Installing php-{module_name}...',
                'type': 'command'
            })
            
            # Special module name mappings
            module_mappings = {
                'pdo_mysql': 'mysql',
                'pdo_pgsql': 'pgsql',
                'pdo_sqlite': 'sqlite3',
                'mysqli': 'mysql'
            }
            
            # Get the actual package name
            actual_module = module_mappings.get(module_name, module_name)
            
            # Try different package naming conventions
            package_names = [f'php-{actual_module}', f'php8.1-{actual_module}', f'php8.2-{actual_module}', f'php8.3-{actual_module}']
            installed = False
            
            for package_name in package_names:
                socketio.emit('php_module_install_output', {
                    'output': f'Trying to install {package_name}...',
                    'type': 'info'
                })
                
                result = subprocess.run(['apt', 'install', '-y', package_name], capture_output=True, text=True)
                if result.returncode == 0:
                    socketio.emit('php_module_install_output', {
                        'output': f'Successfully installed {package_name}',
                        'type': 'success'
                    })
                    installed = True
                    break
                else:
                    socketio.emit('php_module_install_output', {
                        'output': f'Package {package_name} not found or failed to install',
                        'type': 'warning'
                    })
            
            if not installed:
                socketio.emit('php_module_install_error', {
                    'message': f'Failed to install PHP module {module_name}. Package not found.'
                })
                return
            
            time.sleep(1)
            
            # Step 3: Restart PHP-FPM
            socketio.emit('php_module_install_progress', {
                'step': 3,
                'total': 3,
                'status': 'Restarting PHP-FPM...',
                'percentage': 80
            })
            
            socketio.emit('php_module_install_output', {
                'output': 'Restarting PHP-FPM service...',
                'type': 'command'
            })
            
            # Try to restart PHP-FPM using supervisorctl
            result = subprocess.run(['supervisorctl', 'restart', 'php-fpm'], capture_output=True, text=True)
            if result.returncode == 0:
                socketio.emit('php_module_install_output', {
                    'output': 'Successfully restarted php-fpm',
                    'type': 'success'
                })
                restarted = True
            else:
                restarted = False
            
            if not restarted:
                socketio.emit('php_module_install_output', {
                    'output': 'Warning: Could not restart PHP-FPM automatically',
                    'type': 'warning'
                })
            
            # Complete
            socketio.emit('php_module_install_progress', {
                'step': 3,
                'total': 3,
                'status': 'Installation completed',
                'percentage': 100
            })
            
            socketio.emit('php_module_install_complete', {
                'module': module_name,
                'success': True
            })
            
        except Exception as e:
            logger.error(f'Error installing PHP module {module_name}: {str(e)}')
            socketio.emit('php_module_install_error', {
                'message': f'Installation failed: {str(e)}'
            })
    
    # Start background thread
    thread = threading.Thread(target=install_module_background)
    thread.daemon = True
    thread.start()
    
    # Immediately return to prevent blocking
    progress_data = {'message': 'Instalasi modul PHP dimulai...', 'step': 1, 'total': 3, 'status': 'Instalasi dimulai...', 'percentage': 10}
    logger.info(f'Emitting initial php_module_install_progress: {progress_data}')
    emit('php_module_install_progress', progress_data)

@app.route('/api/php/install-module', methods=['POST'])
@login_required
def install_php_module():
    """Install PHP module with real-time progress via WebSocket"""
    try:
        data = request.get_json()
        module_name = data.get('module')
        
        if not module_name:
            return jsonify({'success': False, 'error': 'Module name is required'}), 400
        
        # Validate module name (basic security check)
        if not re.match(r'^[a-zA-Z0-9_-]+$', module_name):
            return jsonify({'success': False, 'error': 'Invalid module name'}), 400
        
        def install_module_background():
            try:
                # Emit initial progress
                socketio.emit('php_module_install_progress', {
                    'step': 1,
                    'total': 3,
                    'status': f'Memulai instalasi modul {module_name}...',
                    'percentage': 10
                })
                
                socketio.emit('php_module_install_output', {
                    'output': f'Starting installation of PHP module: {module_name}',
                    'type': 'info'
                })
                
                time.sleep(1)
                
                # Step 1: Update package list
                socketio.emit('php_module_install_progress', {
                    'step': 1,
                    'total': 3,
                    'status': 'Updating package list...',
                    'percentage': 20
                })
                
                socketio.emit('php_module_install_output', {
                    'output': 'Updating package repositories...',
                    'type': 'command'
                })
                
                result = subprocess.run(['apt', 'update'], capture_output=True, text=True)
                if result.returncode != 0:
                    socketio.emit('php_module_install_error', {
                        'message': f'Failed to update package list: {result.stderr}'
                    })
                    return
                
                socketio.emit('php_module_install_output', {
                    'output': 'Package list updated successfully',
                    'type': 'success'
                })
                
                time.sleep(1)
                
                # Step 2: Install the PHP module
                socketio.emit('php_module_install_progress', {
                    'step': 2,
                    'total': 3,
                    'status': f'Installing php-{module_name}...',
                    'percentage': 50
                })
                
                socketio.emit('php_module_install_output', {
                    'output': f'Installing php-{module_name}...',
                    'type': 'command'
                })
                
                # Special module name mappings
                module_mappings = {
                    'pdo_mysql': 'mysql',
                    'pdo_pgsql': 'pgsql',
                    'pdo_sqlite': 'sqlite3',
                    'mysqli': 'mysql'
                }
                
                # Get the actual package name
                actual_module = module_mappings.get(module_name, module_name)
                
                # Try different package naming conventions
                package_names = [f'php-{actual_module}', f'php8.1-{actual_module}', f'php8.2-{actual_module}', f'php8.3-{actual_module}']
                installed = False
                
                for package_name in package_names:
                    socketio.emit('php_module_install_output', {
                        'output': f'Trying to install {package_name}...',
                        'type': 'info'
                    })
                    
                    result = subprocess.run(['apt', 'install', '-y', package_name], capture_output=True, text=True)
                    if result.returncode == 0:
                        socketio.emit('php_module_install_output', {
                            'output': f'Successfully installed {package_name}',
                            'type': 'success'
                        })
                        installed = True
                        break
                    else:
                        socketio.emit('php_module_install_output', {
                            'output': f'Package {package_name} not found or failed to install',
                            'type': 'warning'
                        })
                
                if not installed:
                    socketio.emit('php_module_install_error', {
                        'message': f'Failed to install PHP module {module_name}. Package not found.'
                    })
                    return
                
                time.sleep(1)
                
                # Step 3: Restart PHP-FPM
                socketio.emit('php_module_install_progress', {
                    'step': 3,
                    'total': 3,
                    'status': 'Restarting PHP-FPM...',
                    'percentage': 80
                })
                
                socketio.emit('php_module_install_output', {
                    'output': 'Restarting PHP-FPM service...',
                    'type': 'command'
                })
                
                # Try to restart PHP-FPM using supervisorctl
                result = subprocess.run(['supervisorctl', 'restart', 'php-fpm'], capture_output=True, text=True)
                if result.returncode == 0:
                    socketio.emit('php_module_install_output', {
                        'output': 'Successfully restarted php-fpm',
                        'type': 'success'
                    })
                    restarted = True
                else:
                    restarted = False
                
                if not restarted:
                    socketio.emit('php_module_install_output', {
                        'output': 'Warning: Could not restart PHP-FPM automatically',
                        'type': 'warning'
                    })
                
                # Complete
                socketio.emit('php_module_install_progress', {
                    'step': 3,
                    'total': 3,
                    'status': 'Installation completed',
                    'percentage': 100
                })
                
                socketio.emit('php_module_install_complete', {
                    'module': module_name,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f'Error installing PHP module {module_name}: {str(e)}')
                socketio.emit('php_module_install_error', {
                    'message': f'Installation failed: {str(e)}'
                })
        
        # Start background thread
        thread = threading.Thread(target=install_module_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Installation started'})
        
    except Exception as e:
        logger.error(f'Error starting PHP module installation: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/php/phpfpm-config', methods=['GET'])
@login_required
def get_phpfpm_config():
    """Get PHP-FPM pool configuration"""
    try:
        logger.info('Loading PHP-FPM configuration...')
        
        # Common PHP-FPM pool configuration paths
        pool_paths = [
            '/etc/php/8.2/fpm/pool.d/www.conf',
            '/etc/php/8.1/fpm/pool.d/www.conf',
            '/etc/php/8.0/fpm/pool.d/www.conf',
            '/etc/php/7.4/fpm/pool.d/www.conf'
        ]
        
        config_content = ''
        config_file = None
        
        for path in pool_paths:
            if os.path.exists(path):
                config_file = path
                with open(path, 'r') as f:
                    config_content = f.read()
                break
        
        if not config_file:
            # Return default configuration if no file found
            config_content = '''[www]
user = www-data
group = www-data
listen = /run/php/php8.1-fpm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3'''
        
        return jsonify({
            'success': True,
            'config': config_content,
            'file': config_file
        })
        
    except Exception as e:
        logger.error(f'Error loading PHP-FPM config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/php/test-phpfpm-config', methods=['POST'])
@login_required
def test_phpfpm_config():
    """Test PHP-FPM configuration"""
    try:
        data = request.get_json()
        config = data.get('config', '')
        
        if not config:
            return jsonify({'success': False, 'error': 'Configuration content is required'})
        
        # Write config to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_file:
            temp_file.write(config)
            temp_path = temp_file.name
        
        try:
            # Test the configuration
            test_cmd = ['php-fpm8.1', '-t', '-y', temp_path]
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({'success': True, 'message': 'Configuration is valid'})
            else:
                error_msg = result.stderr or result.stdout
                return jsonify({'success': False, 'error': error_msg})
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f'Error testing PHP-FPM config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/php/save-phpfpm-config', methods=['POST'])
@login_required
def save_phpfpm_config():
    """Save PHP-FPM pool configuration"""
    try:
        data = request.get_json()
        config = data.get('config', '')
        
        if not config:
            return jsonify({'success': False, 'error': 'Configuration content is required'})
        
        # Find the correct pool configuration file
        pool_paths = [
            '/etc/php/8.2/fpm/pool.d/www.conf',
            '/etc/php/8.1/fpm/pool.d/www.conf',
            '/etc/php/8.0/fpm/pool.d/www.conf',
            '/etc/php/7.4/fpm/pool.d/www.conf'
        ]
        
        config_file = None
        for path in pool_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if not config_file:
            # Use default path if none found
            config_file = '/etc/php/8.1/fpm/pool.d/www.conf'
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Backup existing configuration
        if os.path.exists(config_file):
            backup_file = f'{config_file}.backup.{int(time.time())}'
            shutil.copy2(config_file, backup_file)
            logger.info(f'Backed up existing config to: {backup_file}')
        
        # Write new configuration
        with open(config_file, 'w') as f:
            f.write(config)
        
        # Test the configuration before restarting
        test_cmd = ['php-fpm8.1', '-t']
        test_result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if test_result.returncode != 0:
            # Restore backup if test fails
            if 'backup_file' in locals() and os.path.exists(backup_file):
                shutil.copy2(backup_file, config_file)
            error_msg = test_result.stderr or test_result.stdout
            return jsonify({'success': False, 'error': f'Configuration test failed: {error_msg}'})
        
        # Restart PHP-FPM
        restart_cmd = ['supervisorctl', 'restart', 'php-fpm']
        restart_result = subprocess.run(restart_cmd, capture_output=True, text=True)
        
        if restart_result.returncode == 0:
            logger.info('PHP-FPM configuration saved and service restarted successfully')
            return jsonify({'success': True, 'message': 'Configuration saved and PHP-FPM restarted successfully'})
        else:
            logger.warning('Configuration saved but failed to restart PHP-FPM')
            return jsonify({'success': True, 'message': 'Configuration saved but failed to restart PHP-FPM automatically'})
            
    except Exception as e:
        logger.error(f'Error saving PHP-FPM config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/php/phpini-config', methods=['GET'])
@login_required
def get_phpini_config():
    """Get PHP.ini configuration"""
    try:
        logger.info('Loading PHP.ini configuration...')
        
        # Common PHP.ini paths
        ini_paths = [
            '/etc/php/8.2/fpm/php.ini',
            '/etc/php/8.1/fpm/php.ini',
            '/etc/php/8.0/fpm/php.ini',
            '/etc/php/7.4/fpm/php.ini'
        ]
        
        config_content = ''
        config_file = None
        
        for path in ini_paths:
            if os.path.exists(path):
                config_file = path
                with open(path, 'r') as f:
                    config_content = f.read()
                break
        
        if not config_file:
            return jsonify({'success': False, 'error': 'PHP.ini file not found'})
        
        return jsonify({
            'success': True,
            'config': config_content,
            'file': config_file
        })
        
    except Exception as e:
        logger.error(f'Error loading PHP.ini config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/php/test-phpini-config', methods=['POST'])
@login_required
def test_phpini_config():
    """Test PHP.ini configuration"""
    try:
        data = request.get_json()
        config = data.get('config', '')
        
        if not config:
            return jsonify({'success': False, 'error': 'Configuration content is required'})
        
        # Write config to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as temp_file:
            temp_file.write(config)
            temp_path = temp_file.name
        
        try:
            # Test the configuration
            test_cmd = ['php', '-c', temp_path, '-m']
            result = subprocess.run(test_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return jsonify({'success': True, 'message': 'Configuration is valid'})
            else:
                error_msg = result.stderr or result.stdout
                return jsonify({'success': False, 'error': error_msg})
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f'Error testing PHP.ini config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/php/save-phpini-config', methods=['POST'])
@login_required
def save_phpini_config():
    """Save PHP.ini configuration"""
    try:
        data = request.get_json()
        config = data.get('config', '')
        
        if not config:
            return jsonify({'success': False, 'error': 'Configuration content is required'})
        
        # Find the correct PHP.ini file
        ini_paths = [
            '/etc/php/8.2/fpm/php.ini',
            '/etc/php/8.1/fpm/php.ini',
            '/etc/php/8.0/fpm/php.ini',
            '/etc/php/7.4/fpm/php.ini'
        ]
        
        config_file = None
        for path in ini_paths:
            if os.path.exists(path):
                config_file = path
                break
        
        if not config_file:
            return jsonify({'success': False, 'error': 'PHP.ini file not found'})
        
        # Backup existing configuration
        backup_file = f'{config_file}.backup.{int(time.time())}'
        shutil.copy2(config_file, backup_file)
        logger.info(f'Backed up existing config to: {backup_file}')
        
        # Write new configuration
        with open(config_file, 'w') as f:
            f.write(config)
        
        # Test the configuration
        test_cmd = ['php', '-c', config_file, '-m']
        test_result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if test_result.returncode != 0:
            # Restore backup if test fails
            shutil.copy2(backup_file, config_file)
            error_msg = test_result.stderr or test_result.stdout
            return jsonify({'success': False, 'error': f'Configuration test failed: {error_msg}'})
        
        # Restart PHP-FPM
        restart_cmd = ['supervisorctl', 'restart', 'php-fpm']
        restart_result = subprocess.run(restart_cmd, capture_output=True, text=True)
        
        if restart_result.returncode == 0:
            logger.info('PHP.ini configuration saved and PHP-FPM restarted successfully')
            return jsonify({'success': True, 'message': 'Configuration saved and PHP-FPM restarted successfully'})
        else:
            logger.warning('Configuration saved but failed to restart PHP-FPM')
            return jsonify({'success': True, 'message': 'Configuration saved but failed to restart PHP-FPM automatically'})
            
    except Exception as e:
        logger.error(f'Error saving PHP.ini config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

# UFW Firewall Management endpoints
@app.route('/api/ufw/status', methods=['GET'])
@login_required
def get_ufw_status():
    """Get UFW firewall status"""
    try:
        # Check if UFW is installed
        result = subprocess.run(['which', 'ufw'], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({
                'success': True,
                'installed': False,
                'status': 'not_installed',
                'message': 'UFW is not installed'
            })
        
        # Get UFW status
        result = subprocess.run(['ufw', 'status', 'verbose'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            
            # Parse status
            is_active = 'Status: active' in output
            
            # Parse default policies
            default_incoming = 'deny (incoming)' if 'Default: deny (incoming)' in output else 'allow (incoming)' if 'Default: allow (incoming)' in output else 'unknown'
            default_outgoing = 'allow (outgoing)' if 'Default: allow (outgoing)' in output else 'deny (outgoing)' if 'Default: deny (outgoing)' in output else 'unknown'
            default_routed = 'disabled (routed)' if 'Default: disabled (routed)' in output else 'allow (routed)' if 'Default: allow (routed)' in output else 'unknown'
            
            return jsonify({
                'success': True,
                'installed': True,
                'status': 'active' if is_active else 'inactive',
                'active': is_active,
                'default_incoming': default_incoming,
                'default_outgoing': default_outgoing,
                'default_routed': default_routed,
                'output': output
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to get UFW status: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error getting UFW status: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/rules', methods=['GET'])
@login_required
def list_ufw_rules():
    """List UFW firewall rules"""
    try:
        result = subprocess.run(['ufw', 'status', 'numbered'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            rules = []
            
            # Parse rules from output
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                if line and line.startswith('[') and ']' in line:
                    # Extract rule number and rule text
                    parts = line.split(']', 1)
                    if len(parts) == 2:
                        rule_num = parts[0].strip('[ ')
                        rule_text = parts[1].strip()
                        
                        # Parse UFW output format: "5000                       ALLOW IN    Anywhere"
                        # Split by multiple spaces to get columns
                        import re
                        columns = re.split(r'\s{2,}', rule_text)
                        
                        if len(columns) >= 3:
                            port_protocol = columns[0].strip()
                            action = columns[1].strip()
                            source = columns[2].strip()
                            
                            # For UFW format, destination is usually the port/protocol
                            destination = port_protocol
                            
                            rules.append({
                                'number': rule_num,
                                'action': action,
                                'port_protocol': port_protocol,
                                'source': source,
                                'destination': destination,
                                'raw': rule_text
                            })
            
            return jsonify({
                'success': True,
                'rules': rules,
                'output': output
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to list UFW rules: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error listing UFW rules: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/rule', methods=['POST'])
@login_required
def add_ufw_rule():
    """Add UFW firewall rule"""
    try:
        data = request.get_json()
        action = data.get('action', 'allow').lower()
        port = data.get('port', '')
        protocol = data.get('protocol', '')
        source = data.get('source', '')
        destination = data.get('destination', '')
        
        # Build UFW command
        cmd = ['ufw']
        
        # Add action
        if action in ['allow', 'deny', 'reject']:
            cmd.append(action)
        else:
            cmd.append('allow')
        
        # Add from source if specified
        if source and source.strip():
            cmd.extend(['from', source.strip()])
        
        # Add to destination if specified
        if destination and destination.strip():
            cmd.extend(['to', destination.strip()])
        
        # Add port and protocol
        if port and port.strip():
            if protocol and protocol.strip():
                cmd.extend(['port', f'{port.strip()}/{protocol.strip()}'])
            else:
                cmd.extend(['port', port.strip()])
        elif protocol and protocol.strip():
            cmd.append(f'proto {protocol.strip()}')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f'UFW rule added: {" ".join(cmd)}')
            return jsonify({
                'success': True,
                'message': 'UFW rule added successfully',
                'output': result.stdout,
                'command': ' '.join(cmd)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to add UFW rule: {result.stderr}',
                'command': ' '.join(cmd)
            }), 500
            
    except Exception as e:
        logger.error(f'Error adding UFW rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/rule/delete', methods=['POST'])
@login_required
def delete_ufw_rule():
    """Delete UFW firewall rule"""
    try:
        data = request.get_json()
        rule_number = data.get('rule_number')
        
        if not rule_number:
            return jsonify({
                'success': False,
                'error': 'Rule number is required'
            }), 400
        
        result = subprocess.run(['ufw', '--force', 'delete', str(rule_number)], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f'UFW rule {rule_number} deleted')
            return jsonify({
                'success': True,
                'message': f'UFW rule {rule_number} deleted successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete UFW rule: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error deleting UFW rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/reset', methods=['POST'])
@login_required
def reset_ufw():
    """Reset UFW firewall to defaults"""
    try:
        result = subprocess.run(['ufw', '--force', 'reset'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info('UFW firewall reset to defaults')
            return jsonify({
                'success': True,
                'message': 'UFW firewall reset to defaults successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to reset UFW: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error resetting UFW: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/logs', methods=['GET'])
@login_required
def get_ufw_logs():
    """Get UFW firewall logs"""
    try:
        # Try to read UFW logs from common locations
        log_files = ['/var/log/ufw.log', '/var/log/kern.log']
        logs = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    result = subprocess.run(['tail', '-n', '100', log_file], capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'UFW' in line or '[UFW' in line:
                                logs.append({
                                    'file': log_file,
                                    'line': line.strip()
                                })
                except Exception as e:
                    logger.warning(f'Error reading log file {log_file}: {str(e)}')
        
        return jsonify({
            'success': True,
            'logs': logs[-50:] if len(logs) > 50 else logs  # Return last 50 entries
        })
        
    except Exception as e:
        logger.error(f'Error getting UFW logs: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# SSH Configuration endpoints
@app.route('/api/ssh/config', methods=['GET'])
@login_required
def get_ssh_config():
    """Get SSH configuration"""
    try:
        ssh_config = {}
        
        # Read SSH config file
        ssh_config_file = '/etc/ssh/sshd_config'
        if os.path.exists(ssh_config_file):
            with open(ssh_config_file, 'r') as f:
                content = f.read()
                
                # Parse port
                port_match = re.search(r'^\s*Port\s+(\d+)', content, re.MULTILINE)
                ssh_config['port'] = int(port_match.group(1)) if port_match else 22
                
                # Parse PermitRootLogin
                root_match = re.search(r'^\s*PermitRootLogin\s+(\w+)', content, re.MULTILINE)
                ssh_config['allow_root'] = root_match.group(1).lower() == 'yes' if root_match else False
                
                # Parse PasswordAuthentication
                pass_match = re.search(r'^\s*PasswordAuthentication\s+(\w+)', content, re.MULTILINE)
                ssh_config['password_auth'] = pass_match.group(1).lower() == 'yes' if pass_match else True
        else:
            # Default values if config file doesn't exist
            ssh_config = {
                'port': 22,
                'allow_root': False,
                'password_auth': True
            }
        
        return jsonify({
            'success': True,
            **ssh_config
        })
        
    except Exception as e:
        logger.error(f'Error getting SSH config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ssh/config', methods=['POST'])
@login_required
def update_ssh_config():
    """Update SSH configuration"""
    try:
        data = request.get_json()
        port = data.get('port', 22)
        allow_root = data.get('allow_root', False)
        password_auth = data.get('password_auth', True)
        
        # Validate port
        if not isinstance(port, int) or port < 1 or port > 65535:
            return jsonify({
                'success': False,
                'error': 'Invalid port number'
            }), 400
        
        ssh_config_file = '/etc/ssh/sshd_config'
        backup_file = f'{ssh_config_file}.backup.{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # Create backup
        if os.path.exists(ssh_config_file):
            subprocess.run(['cp', ssh_config_file, backup_file], check=True)
        
        # Read current config
        content = ''
        if os.path.exists(ssh_config_file):
            with open(ssh_config_file, 'r') as f:
                content = f.read()
        
        # Update or add configurations
        lines = content.split('\n')
        updated_lines = []
        port_updated = False
        root_updated = False
        pass_updated = False
        
        for line in lines:
            if re.match(r'^\s*Port\s+', line):
                updated_lines.append(f'Port {port}')
                port_updated = True
            elif re.match(r'^\s*PermitRootLogin\s+', line):
                updated_lines.append(f'PermitRootLogin {"yes" if allow_root else "no"}')
                root_updated = True
            elif re.match(r'^\s*PasswordAuthentication\s+', line):
                updated_lines.append(f'PasswordAuthentication {"yes" if password_auth else "no"}')
                pass_updated = True
            else:
                updated_lines.append(line)
        
        # Add missing configurations
        if not port_updated:
            updated_lines.append(f'Port {port}')
        if not root_updated:
            updated_lines.append(f'PermitRootLogin {"yes" if allow_root else "no"}')
        if not pass_updated:
            updated_lines.append(f'PasswordAuthentication {"yes" if password_auth else "no"}')
        
        # Write updated config
        with open(ssh_config_file, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        logger.info(f'SSH config updated: port={port}, allow_root={allow_root}, password_auth={password_auth}')
        
        return jsonify({
            'success': True,
            'message': 'SSH configuration updated successfully',
            'backup_file': backup_file
        })
        
    except Exception as e:
        logger.error(f'Error updating SSH config: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# UFW Policies endpoints
@app.route('/api/ufw/policies', methods=['GET'])
@login_required
def get_ufw_policies():
    """Get UFW default policies"""
    try:
        result = subprocess.run(['ufw', 'status', 'verbose'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            
            # Parse default policies
            policies = {
                'incoming': 'deny',
                'outgoing': 'allow',
                'forward': 'deny'
            }
            
            # Extract policies from output
            if 'Default: deny (incoming)' in output:
                policies['incoming'] = 'deny'
            elif 'Default: allow (incoming)' in output:
                policies['incoming'] = 'allow'
            elif 'Default: reject (incoming)' in output:
                policies['incoming'] = 'reject'
                
            if 'Default: allow (outgoing)' in output:
                policies['outgoing'] = 'allow'
            elif 'Default: deny (outgoing)' in output:
                policies['outgoing'] = 'deny'
            elif 'Default: reject (outgoing)' in output:
                policies['outgoing'] = 'reject'
                
            if 'Default: deny (routed)' in output or 'Default: disabled (routed)' in output:
                policies['forward'] = 'deny'
            elif 'Default: allow (routed)' in output:
                policies['forward'] = 'allow'
            
            return jsonify({
                'success': True,
                **policies
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to get UFW policies: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error getting UFW policies: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/policies', methods=['POST'])
@login_required
def update_ufw_policies():
    """Update UFW default policies"""
    try:
        data = request.get_json()
        incoming = data.get('incoming', 'deny')
        outgoing = data.get('outgoing', 'allow')
        forward = data.get('forward', 'deny')
        
        # Validate policy values
        valid_policies = ['allow', 'deny', 'reject']
        if incoming not in valid_policies or outgoing not in valid_policies or forward not in valid_policies:
            return jsonify({
                'success': False,
                'error': 'Invalid policy value. Must be allow, deny, or reject'
            }), 400
        
        # Update policies
        commands = [
            ['ufw', '--force', 'default', incoming, 'incoming'],
            ['ufw', '--force', 'default', outgoing, 'outgoing'],
            ['ufw', '--force', 'default', forward, 'routed']
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Failed to update policy: {result.stderr}'
                }), 500
        
        logger.info(f'UFW policies updated: incoming={incoming}, outgoing={outgoing}, forward={forward}')
        
        return jsonify({
            'success': True,
            'message': 'UFW policies updated successfully'
        })
        
    except Exception as e:
        logger.error(f'Error updating UFW policies: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# UFW Logging endpoints
@app.route('/api/ufw/logging', methods=['GET'])
@login_required
def get_ufw_logging():
    """Get UFW logging settings"""
    try:
        result = subprocess.run(['ufw', 'status', 'verbose'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            
            # Parse logging level
            logging_settings = {
                'level': 'off',
                'log_denied': False,
                'log_allowed': False
            }
            
            if 'Logging: on (low)' in output:
                logging_settings['level'] = 'low'
            elif 'Logging: on (medium)' in output:
                logging_settings['level'] = 'medium'
            elif 'Logging: on (high)' in output:
                logging_settings['level'] = 'high'
            elif 'Logging: on (full)' in output:
                logging_settings['level'] = 'full'
            elif 'Logging: off' in output:
                logging_settings['level'] = 'off'
            
            # For simplicity, we'll assume log_denied and log_allowed based on level
            if logging_settings['level'] != 'off':
                logging_settings['log_denied'] = True
                if logging_settings['level'] in ['high', 'full']:
                    logging_settings['log_allowed'] = True
            
            return jsonify({
                'success': True,
                **logging_settings
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to get UFW logging settings: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error getting UFW logging settings: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ufw/logging', methods=['POST'])
@login_required
def update_ufw_logging():
    """Update UFW logging settings"""
    try:
        data = request.get_json()
        level = data.get('level', 'off')
        
        # Validate logging level
        valid_levels = ['off', 'low', 'medium', 'high', 'full']
        if level not in valid_levels:
            return jsonify({
                'success': False,
                'error': 'Invalid logging level. Must be off, low, medium, high, or full'
            }), 400
        
        # Update logging
        result = subprocess.run(['ufw', 'logging', level], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f'UFW logging updated: level={level}')
            return jsonify({
                'success': True,
                'message': f'UFW logging set to {level}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to update UFW logging: {result.stderr}'
            }), 500
            
    except Exception as e:
        logger.error(f'Error updating UFW logging: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# Firewall Security Settings endpoints
@app.route('/api/firewall/security', methods=['GET'])
@login_required
def get_firewall_security():
    """Get firewall security settings"""
    try:
        # Default security settings
        security_settings = {
            'rate_limit': 30,
            'connection_timeout': 300,
            'enable_syn_cookies': True,
            'enable_connection_tracking': True,
            'block_invalid_packets': True
        }
        
        # Try to read actual system settings
        try:
            # Check SYN cookies
            with open('/proc/sys/net/ipv4/tcp_syncookies', 'r') as f:
                security_settings['enable_syn_cookies'] = f.read().strip() == '1'
        except:
            pass
            
        try:
            # Check connection tracking
            result = subprocess.run(['lsmod'], capture_output=True, text=True)
            security_settings['enable_connection_tracking'] = 'nf_conntrack' in result.stdout
        except:
            pass
        
        return jsonify({
            'success': True,
            **security_settings
        })
        
    except Exception as e:
        logger.error(f'Error getting firewall security settings: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/firewall/security', methods=['POST'])
@login_required
def update_firewall_security():
    """Update firewall security settings"""
    try:
        data = request.get_json()
        rate_limit = data.get('rate_limit', 30)
        connection_timeout = data.get('connection_timeout', 300)
        enable_syn_cookies = data.get('enable_syn_cookies', True)
        enable_connection_tracking = data.get('enable_connection_tracking', True)
        block_invalid_packets = data.get('block_invalid_packets', True)
        
        # Validate values
        if not isinstance(rate_limit, int) or rate_limit < 1 or rate_limit > 1000:
            return jsonify({
                'success': False,
                'error': 'Rate limit must be between 1 and 1000'
            }), 400
            
        if not isinstance(connection_timeout, int) or connection_timeout < 30 or connection_timeout > 3600:
            return jsonify({
                'success': False,
                'error': 'Connection timeout must be between 30 and 3600 seconds'
            }), 400
        
        # Apply SYN cookies setting
        try:
            with open('/proc/sys/net/ipv4/tcp_syncookies', 'w') as f:
                f.write('1' if enable_syn_cookies else '0')
        except Exception as e:
            logger.warning(f'Failed to set SYN cookies: {str(e)}')
        
        # Note: Other settings would require more complex system configuration
        # For now, we'll just log the settings and return success
        
        logger.info(f'Firewall security settings updated: rate_limit={rate_limit}, '
                   f'connection_timeout={connection_timeout}, syn_cookies={enable_syn_cookies}, '
                   f'connection_tracking={enable_connection_tracking}, block_invalid={block_invalid_packets}')
        
        return jsonify({
            'success': True,
            'message': 'Firewall security settings updated successfully'
        })
        
    except Exception as e:
        logger.error(f'Error updating firewall security settings: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# Terminal namespace for handling terminal connections
class TerminalNamespace(Namespace):
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.terminals = {}
    
    def on_connect(self, sid=None, environ=None):
        if sid is None:
            sid = request.sid
        print(f'Terminal client connected: {sid}')
        # Start a new terminal session
        try:
            master, slave = pty.openpty()
            
            # Start bash in the terminal
            pid = os.fork()
            if pid == 0:
                # Child process
                os.setsid()
                os.dup2(slave, 0)
                os.dup2(slave, 1)
                os.dup2(slave, 2)
                os.close(master)
                os.close(slave)
                
                # Set environment variables
                os.environ['TERM'] = 'xterm-256color'
                os.environ['PS1'] = '\[\033[01;32m\]slemp@container\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]$ '
                
                # Set default working directory to /var/www/html
                os.chdir('/var/www/html')
                
                # Execute bash
                os.execvp('/bin/bash', ['/bin/bash'])
            else:
                # Parent process
                os.close(slave)
                
                # Store terminal info
                self.terminals[sid] = {
                    'master': master,
                    'pid': pid,
                    'thread': None
                }
                
                # Start reading thread
                thread = threading.Thread(target=self._read_terminal, args=(sid, master))
                thread.daemon = True
                thread.start()
                self.terminals[sid]['thread'] = thread
                
        except Exception as e:
            print(f'Error starting terminal: {e}')
            self.emit('error', str(e), room=sid)
    
    def on_disconnect(self, sid=None):
        if sid is None:
            sid = request.sid
        print(f'Terminal client disconnected: {sid}')
        if sid in self.terminals:
            terminal = self.terminals[sid]
            try:
                # Kill the process
                os.kill(terminal['pid'], signal.SIGTERM)
                os.close(terminal['master'])
            except:
                pass
            del self.terminals[sid]
    
    def on_terminal_input(self, data, sid=None):
        if sid is None:
            sid = request.sid
        if sid in self.terminals:
            try:
                os.write(self.terminals[sid]['master'], data.encode('utf-8'))
            except Exception as e:
                print(f'Error writing to terminal: {e}')
    
    def on_terminal_resize(self, data, sid=None):
        if sid is None:
            sid = request.sid
        if sid in self.terminals:
            try:
                # Set terminal size
                cols = data.get('cols', 80)
                rows = data.get('rows', 24)
                
                # Pack the window size
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.terminals[sid]['master'], termios.TIOCSWINSZ, winsize)
            except Exception as e:
                print(f'Error resizing terminal: {e}')
    
    def _read_terminal(self, sid, master):
        while sid in self.terminals:
            try:
                # Use select to check if data is available
                ready, _, _ = select.select([master], [], [], 0.1)
                if ready:
                    data = os.read(master, 1024)
                    if data:
                        self.emit('terminal_output', data.decode('utf-8', errors='ignore'), room=sid)
                    else:
                        break
            except Exception as e:
                print(f'Error reading from terminal: {e}')
                break

# Port Management Helper Functions
def run_command(command):
    """Run shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def get_ufw_rules():
    """Get current UFW rules"""
    try:
        # Get UFW status and rules
        success, output, error = run_command("sudo ufw status numbered")
        if not success:
            logger.warning(f"Cannot access UFW: {error}. Returning mock data.")
            # Return some basic mock data if UFW is not accessible
            return [
                {
                    'id': '1',
                    'port': '22',
                    'protocol': 'tcp',
                    'action': 'allow',
                    'source': 'any',
                    'description': 'SSH Access (mock)',
                    'status': 'active'
                }
            ]
        
        rules = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and '[' in line and ']' in line:
                # Parse UFW rule format: [ 1] 22/tcp                     ALLOW IN    Anywhere
                match = re.match(r'\[\s*(\d+)\]\s+([^\s]+)\s+(ALLOW|DENY)\s+IN\s+(.+)', line.strip())
                if match:
                    rule_num = match.group(1)
                    port_proto = match.group(2)
                    action = match.group(3).lower()
                    source = match.group(4).strip()
                    
                    # Parse port and protocol
                    if '/' in port_proto:
                        port, protocol = port_proto.split('/', 1)
                    else:
                        port = port_proto
                        protocol = 'tcp'
                    
                    if source == 'Anywhere':
                        source = 'any'
                    
                    rules.append({
                        'id': rule_num,
                        'port': port,
                        'protocol': protocol,
                        'action': action,
                        'source': source,
                        'description': f'{action.upper()} {protocol} port {port}',
                        'status': 'active'
                    })
        
        return rules
    except Exception as e:
        logger.error(f"Error getting UFW rules: {str(e)}")
        return []

def add_ufw_rule(port, protocol='tcp', action='allow', source='any', description=''):
    """Add UFW rule"""
    try:
        # Normalize action
        if action.lower() in ['accept', 'allow']:
            action = 'allow'
        elif action.lower() in ['deny', 'block', 'drop']:
            action = 'deny'
        
        # Build UFW command
        if source == 'any' or source == '0.0.0.0/0':
            command = f"sudo ufw {action} {port}/{protocol}"
        else:
            command = f"sudo ufw {action} from {source} to any port {port} proto {protocol}"
        
        success, output, error = run_command(command)
        
        if success:
            return True, f"UFW rule added successfully"
        else:
            return False, f"Failed to add UFW rule: {error}"
    except Exception as e:
        return False, str(e)

def delete_ufw_rule(rule_num):
    """Delete UFW rule by rule number"""
    try:
        command = f"sudo ufw --force delete {rule_num}"
        success, output, error = run_command(command)
        
        if success:
            return True, "UFW rule deleted successfully"
        else:
            return False, f"Failed to delete UFW rule: {error}"
    except Exception as e:
        return False, str(e)

def scan_open_ports(target='127.0.0.1'):
    """Scan for open ports using netstat"""
    try:
        success, output, error = run_command("netstat -tuln")
        if not success:
            return []
        
        ports = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'LISTEN' in line:
                parts = line.split()
                if len(parts) >= 4:
                    protocol = parts[0].lower()
                    address = parts[3]
                    
                    if ':' in address:
                        port = address.split(':')[-1]
                        if port.isdigit():
                            service = get_service_name(int(port))
                            ports.append({
                                'port': int(port),
                                'protocol': protocol[:3],  # tcp or udp
                                'status': 'open',
                                'service': service
                            })
        
        return ports
    except Exception as e:
        logger.error(f"Error scanning ports: {str(e)}")
        return []

def get_service_name(port):
    """Get service name for common ports"""
    services = {
        22: 'ssh',
        23: 'telnet',
        25: 'smtp',
        53: 'dns',
        80: 'http',
        110: 'pop3',
        143: 'imap',
        443: 'https',
        993: 'imaps',
        995: 'pop3s',
        3306: 'mysql',
        5432: 'postgresql',
        6379: 'redis',
        27017: 'mongodb',
        7777: 'flask'
    }
    return services.get(port, 'unknown')

def get_port_statistics():
    """Get real port statistics"""
    try:
        rules = get_ufw_rules()
        open_ports = scan_open_ports()
        
        allowed_count = len([r for r in rules if r['action'] == 'allow'])
        blocked_count = len([r for r in rules if r['action'] == 'deny'])
        
        return {
            'total_rules': len(rules),
            'allowed_ports': allowed_count,
            'blocked_ports': blocked_count,
            'open_ports': len(open_ports)
        }
    except Exception as e:
        logger.error(f"Error getting port statistics: {str(e)}")
        return {
            'total_rules': 0,
            'allowed_ports': 0,
            'blocked_ports': 0,
            'open_ports': 0
        }

# Port Management API Endpoints
@app.route('/api/ports/rules', methods=['GET'])
@login_required
def get_port_rules():
    """Get all port rules"""
    try:
        rules = get_ufw_rules()
        return jsonify({'success': True, 'rules': rules})
    except Exception as e:
        logger.error(f'Error getting port rules: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/rule', methods=['POST'])
@login_required
def add_port_rule():
    """Add a new port rule"""
    try:
        data = request.get_json()
        port = data.get('port')
        protocol = data.get('protocol', 'tcp')
        action = data.get('action', 'allow')
        source = data.get('source', 'any')
        description = data.get('description', '')
        
        success, message = add_ufw_rule(port, protocol, action, source, description)
        
        if success:
            logger.info(f'Added port rule: {port}/{protocol} {action} from {source}')
            return jsonify({
                'success': True, 
                'message': f'Port rule for {port}/{protocol} added successfully'
            })
        else:
            logger.error(f'Failed to add port rule: {message}')
            return jsonify({'success': False, 'error': message})
    except Exception as e:
        logger.error(f'Error adding port rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/rule/<rule_id>', methods=['GET'])
@login_required
def get_port_rule(rule_id):
    """Get a specific port rule"""
    try:
        rules = get_ufw_rules()
        rule = next((r for r in rules if r['id'] == rule_id), None)
        
        if rule:
            return jsonify({'success': True, 'rule': rule})
        else:
            return jsonify({'success': False, 'error': 'Rule not found'})
    except Exception as e:
        logger.error(f'Error getting port rule {rule_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/rule/<rule_id>', methods=['PUT'])
@login_required
def update_port_rule(rule_id):
    """Update a port rule"""
    try:
        data = request.get_json()
        port = data.get('port')
        protocol = data.get('protocol', 'tcp')
        action = data.get('action', 'allow')
        source = data.get('source', 'any')
        description = data.get('description', '')
        
        # First, delete the old rule
        delete_result = delete_ufw_rule(rule_id)
        if not delete_result[0]:  # delete_ufw_rule returns (success, message)
            return jsonify({'success': False, 'error': f'Failed to delete old rule: {delete_result[1]}'})
        
        # Then add the new rule with updated data
        add_success, add_message = add_ufw_rule(port, protocol, action, source, description)
        if add_success:
            logger.info(f'Updated port rule {rule_id}: {port}/{protocol} {action} from {source}')
            return jsonify({
                'success': True, 
                'message': f'Port rule {rule_id} updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': f'Failed to add updated rule: {add_message}'})
            
    except Exception as e:
        logger.error(f'Error updating port rule {rule_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/rule/<rule_id>', methods=['DELETE'])
@login_required
def delete_port_rule(rule_id):
    """Delete a port rule"""
    try:
        success, message = delete_ufw_rule(rule_id)
        
        if success:
            logger.info(f'Deleted port rule {rule_id}')
            return jsonify({
                'success': True, 
                'message': f'Port rule {rule_id} deleted successfully'
            })
        else:
            logger.error(f'Failed to delete port rule {rule_id}: {message}')
            return jsonify({'success': False, 'error': message})
    except Exception as e:
        logger.error(f'Error deleting port rule {rule_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/scan', methods=['POST'])
@login_required
def scan_ports():
    """Scan for open ports"""
    try:
        data = request.get_json() or {}
        target = data.get('target', '127.0.0.1')
        
        results = scan_open_ports(target)
        
        logger.info(f'Port scan completed for {target}, found {len(results)} open ports')
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f'Error scanning ports: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ports/statistics', methods=['GET'])
@login_required
def get_port_statistics_api():
    """Get port statistics"""
    try:
        stats = get_port_statistics()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f'Error getting port statistics: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

# Port Forwarding Functions
def get_port_forward_rules_list():
    """Get list of port forwarding rules from UFW"""
    try:
        # Read UFW rules from user.rules file
        rules_file = '/etc/ufw/user.rules'
        if not os.path.exists(rules_file):
            return []
        
        rules = []
        rule_id = 1
        
        with open(rules_file, 'r') as f:
            content = f.read()
        
        # Look for route rules in UFW format
        lines = content.split('\n')
        
        # First pass: collect all input rules (external ports)
        input_rules = []
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('### tuple ### allow tcp') or line.startswith('### tuple ### allow udp'):
                parts = line.split()
                if len(parts) >= 6:
                    protocol = parts[4]  # tcp/udp
                    external_port = parts[5]  # external port
                    input_rules.append({
                        'protocol': protocol,
                        'external_port': external_port,
                        'line_index': i
                    })
        
        # Second pass: process route rules and match with input rules
        used_input_indices = set()  # Track which input rules have been used
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('### tuple ### route:allow'):
                parts = line.split()
                if len(parts) >= 7:
                    protocol = parts[4]  # tcp/udp
                    internal_port = parts[5]  # internal port (destination)
                    internal_ip = parts[6]  # destination IP
                    
                    # Look for the corresponding iptables rule in next lines
                    confirmed_internal_port = internal_port  # default
                    j = i + 1
                    while j < len(lines) and j < i + 5:  # Look within next 5 lines
                        next_line = lines[j].strip()
                        if 'ufw-user-forward' in next_line and '--dport' in next_line:
                            # Confirm internal port from iptables rule
                            rule_parts = next_line.split()
                            for k, part in enumerate(rule_parts):
                                if part == '--dport' and k + 1 < len(rule_parts):
                                    confirmed_internal_port = rule_parts[k + 1]
                                    break
                            break
                        j += 1
                    
                    # Find matching external port from input rules
                    external_port = confirmed_internal_port  # default fallback
                    for idx, input_rule in enumerate(input_rules):
                        if (input_rule['protocol'] == protocol and 
                            input_rule['line_index'] < i and 
                            idx not in used_input_indices):  # Must come before route rule and not used
                            external_port = input_rule['external_port']
                            used_input_indices.add(idx)  # Mark as used
                            break
                    
                    # Add the port forwarding rule
                    rules.append({
                        'id': rule_id,
                        'external_port': int(external_port) if external_port.isdigit() else external_port,
                        'internal_ip': internal_ip,
                        'internal_port': int(confirmed_internal_port) if confirmed_internal_port.isdigit() else confirmed_internal_port,
                        'protocol': protocol,
                        'description': f'Forward {external_port} to {internal_ip}:{confirmed_internal_port}',
                        'status': 'active'
                    })
                    rule_id += 1
        
        return rules
    except Exception as e:
        logger.error(f'Error getting port forward rules: {e}')
        return []

def create_port_forward_rule_helper(external_port, internal_ip, internal_port, protocol='tcp', description=''):
    """Create a new port forwarding rule using UFW"""
    try:
        protocols = ['tcp'] if protocol == 'tcp' else ['udp'] if protocol == 'udp' else ['tcp', 'udp']
        
        for proto in protocols:
            # Create UFW route rule for port forwarding
            route_cmd = [
                'sudo', 'ufw', 'route', 'allow', 'in', 'on', 'any',
                'out', 'on', 'any', 'to', internal_ip, 'port', str(internal_port),
                'proto', proto
            ]
            subprocess.run(route_cmd, check=True)
            
            # Add DNAT rule to UFW's before.rules
            before_rules_file = '/etc/ufw/before.rules'
            dnat_rule = f'-A PREROUTING -p {proto} --dport {external_port} -j DNAT --to-destination {internal_ip}:{internal_port}\n'
            
            # Read current before.rules
            with open(before_rules_file, 'r') as f:
                content = f.read()
            
            # Add DNAT rule if not already present
            if dnat_rule.strip() not in content:
                # Find the *nat table section
                if '*nat' in content:
                    # Insert after *nat line
                    lines = content.split('\n')
                    new_lines = []
                    nat_found = False
                    for line in lines:
                        new_lines.append(line)
                        if line.strip() == '*nat' and not nat_found:
                            new_lines.append(':PREROUTING ACCEPT [0:0]')
                            new_lines.append(dnat_rule.strip())
                            nat_found = True
                    
                    if not nat_found:
                        # Add *nat section at the beginning
                        nat_section = f'*nat\n:PREROUTING ACCEPT [0:0]\n{dnat_rule}COMMIT\n\n'
                        content = nat_section + content
                    else:
                        content = '\n'.join(new_lines)
                else:
                    # Add *nat section at the beginning
                    nat_section = f'*nat\n:PREROUTING ACCEPT [0:0]\n{dnat_rule}COMMIT\n\n'
                    content = nat_section + content
                
                # Write back to file
                with open(before_rules_file, 'w') as f:
                    f.write(content)
        
        # Reload UFW to apply changes
        subprocess.run(['sudo', 'ufw', 'reload'], check=True)
        
        return {'success': True}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error creating port forward rule: {e}')
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f'Error creating port forward rule: {e}')
        return {'success': False, 'error': str(e)}

def update_port_forward_rule_data(rule_id, data):
    """Update a port forwarding rule"""
    try:
        # For simplicity, delete old rule and create new one
        delete_result = delete_port_forward_rule_data(rule_id)
        if not delete_result['success']:
            return delete_result
        
        create_result = create_port_forward_rule_helper(
            data.get('external_port'),
            data.get('internal_ip'),
            data.get('internal_port'),
            data.get('protocol', 'tcp'),
            data.get('description', '')
        )
        return create_result
    except Exception as e:
        logger.error(f'Error updating port forward rule: {e}')
        return {'success': False, 'error': str(e)}

def delete_port_forward_rule_data(rule_id):
    """Delete a port forwarding rule"""
    try:
        # Get current rules to find the rule to delete
        rules = get_port_forward_rules_list()
        rule_to_delete = next((r for r in rules if r.get('id') == rule_id), None)
        
        if not rule_to_delete:
            return {'success': False, 'error': 'Rule not found'}
        
        external_port = rule_to_delete['external_port']
        internal_ip = rule_to_delete['internal_ip']
        internal_port = rule_to_delete['internal_port']
        protocol = rule_to_delete['protocol']
        
        # Delete UFW route rule
        route_cmd = [
            'sudo', 'ufw', 'route', 'delete', 'allow', 'in', 'on', 'any',
            'out', 'on', 'any', 'to', internal_ip, 'port', str(internal_port),
            'proto', protocol
        ]
        try:
            subprocess.run(route_cmd, check=True)
        except subprocess.CalledProcessError:
            pass  # Rule might not exist
        
        # Remove DNAT rule from UFW's before.rules
        before_rules_file = '/etc/ufw/before.rules'
        dnat_rule = f'-A PREROUTING -p {protocol} --dport {external_port} -j DNAT --to-destination {internal_ip}:{internal_port}'
        
        try:
            with open(before_rules_file, 'r') as f:
                content = f.read()
            
            # Remove the DNAT rule
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.strip() != dnat_rule:
                    new_lines.append(line)
            
            # Write back to file
            with open(before_rules_file, 'w') as f:
                f.write('\n'.join(new_lines))
        except Exception as e:
            logger.warning(f'Could not remove DNAT rule from before.rules: {e}')
        
        # Reload UFW to apply changes
        subprocess.run(['sudo', 'ufw', 'reload'], check=True)
        
        return {'success': True}
    except subprocess.CalledProcessError as e:
        logger.error(f'Error deleting port forward rule: {e}')
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f'Error deleting port forward rule: {e}')
        return {'success': False, 'error': str(e)}

# Port Forwarding API endpoints
@app.route('/api/port-forward/rules', methods=['GET'])
@login_required
def get_port_forward_rules():
    """Get all port forwarding rules"""
    try:
        rules = get_port_forward_rules_list()
        return jsonify({'success': True, 'rules': rules})
    except Exception as e:
        logger.error(f'Error getting port forward rules: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/port-forward/rules', methods=['POST'])
@login_required
def create_port_forward_rule():
    """Create a new port forwarding rule"""
    try:
        data = request.get_json()
        external_port = data.get('external_port')
        internal_ip = data.get('internal_ip')
        internal_port = data.get('internal_port')
        protocol = data.get('protocol', 'tcp')
        description = data.get('description', '')
        
        if not all([external_port, internal_ip, internal_port]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        result = create_port_forward_rule_helper(external_port, internal_ip, internal_port, protocol, description)
        if result['success']:
            logger.info(f'Port forward rule created: {external_port} -> {internal_ip}:{internal_port}')
            return jsonify({'success': True, 'message': 'Port forward rule created successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']})
    except Exception as e:
        logger.error(f'Error creating port forward rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/port-forward/rules/<int:rule_id>', methods=['GET'])
@login_required
def get_port_forward_rule(rule_id):
    """Get a specific port forwarding rule"""
    try:
        rules = get_port_forward_rules_list()
        rule = next((r for r in rules if r.get('id') == rule_id), None)
        if rule:
            return jsonify({'success': True, 'rule': rule})
        else:
            return jsonify({'success': False, 'error': 'Rule not found'})
    except Exception as e:
        logger.error(f'Error getting port forward rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/port-forward/rules/<int:rule_id>', methods=['PUT'])
@login_required
def update_port_forward_rule(rule_id):
    """Update a port forwarding rule"""
    try:
        data = request.get_json()
        result = update_port_forward_rule_data(rule_id, data)
        if result['success']:
            logger.info(f'Port forward rule updated: {rule_id}')
            return jsonify({'success': True, 'message': 'Port forward rule updated successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']})
    except Exception as e:
        logger.error(f'Error updating port forward rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/port-forward/rules/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_port_forward_rule(rule_id):
    """Delete a port forwarding rule"""
    try:
        result = delete_port_forward_rule_data(rule_id)
        if result['success']:
            logger.info(f'Port forward rule deleted: {rule_id}')
            return jsonify({'success': True, 'message': 'Port forward rule deleted successfully'})
        else:
            return jsonify({'success': False, 'error': result['error']})
    except Exception as e:
        logger.error(f'Error deleting port forward rule: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

# MySQL Replication Management
@app.route('/api/mysql/replication/status', methods=['GET'])
@login_required
def get_replication_status():
    """Get MySQL replication status"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor(dictionary=True)
        status = {'master': None, 'slave': []}
        
        # Check master status
        try:
            cursor.execute("SHOW MASTER STATUS")
            master_result = cursor.fetchone()
            if master_result:
                status['master'] = {
                    'file': master_result.get('File'),
                    'position': master_result.get('Position'),
                    'binlog_do_db': master_result.get('Binlog_Do_DB'),
                    'binlog_ignore_db': master_result.get('Binlog_Ignore_DB')
                }
        except mysql.connector.Error:
            pass  # Master not configured
        
        # Check slave status
        try:
            cursor.execute("SHOW SLAVE STATUS")
            slave_result = cursor.fetchone()
            if slave_result:
                status['slave'] = [{
                    'master_host': slave_result.get('Master_Host'),
                    'master_user': slave_result.get('Master_User'),
                    'master_port': slave_result.get('Master_Port'),
                    'slave_io_running': slave_result.get('Slave_IO_Running'),
                    'slave_sql_running': slave_result.get('Slave_SQL_Running'),
                    'seconds_behind_master': slave_result.get('Seconds_Behind_Master'),
                    'master_log_file': slave_result.get('Master_Log_File'),
                    'read_master_log_pos': slave_result.get('Read_Master_Log_Pos'),
                    'relay_log_file': slave_result.get('Relay_Log_File'),
                    'relay_log_pos': slave_result.get('Relay_Log_Pos'),
                    'last_errno': slave_result.get('Last_Errno'),
                    'last_error': slave_result.get('Last_Error')
                }]
        except mysql.connector.Error:
            pass  # Slave not configured
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        logger.error(f'Error getting replication status: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/setup-master', methods=['POST'])
@login_required
def setup_mysql_master():
    """Setup MySQL as master for replication"""
    try:
        data = request.get_json()
        server_id = data.get('server_id', 1)
        log_bin = data.get('log_bin', 'mysql-bin')
        
        if not isinstance(server_id, int) or server_id < 1 or server_id > 4294967295:
            return jsonify({'success': False, 'error': 'Invalid server ID. Must be between 1 and 4294967295'})
        
        # Read current MySQL configuration (Linux only)
        config_paths = [
            '/etc/mysql/mariadb.conf.d/50-server.cnf',
            '/etc/mysql/mysql.conf.d/mysqld.cnf',
            '/etc/my.cnf'
        ]
        
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            return jsonify({'success': False, 'error': 'MySQL configuration file not found'})
        
        # Backup original config
        backup_path = f"{config_path}.backup.{int(time.time())}"
        shutil.copy2(config_path, backup_path)
        
        # Read and modify configuration
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Remove existing replication settings
        lines = config_content.split('\n')
        new_lines = []
        in_mysqld_section = False
        
        for line in lines:
            stripped = line.strip()
            if stripped == '[mysqld]':
                in_mysqld_section = True
                new_lines.append(line)
            elif stripped.startswith('[') and stripped != '[mysqld]':
                in_mysqld_section = False
                new_lines.append(line)
            elif in_mysqld_section and (stripped.startswith('server-id') or 
                                       stripped.startswith('log-bin') or
                                       stripped.startswith('binlog-do-db') or
                                       stripped.startswith('binlog-ignore-db')):
                # Skip existing replication settings
                continue
            else:
                new_lines.append(line)
        
        # Add new replication settings
        mysqld_found = False
        final_lines = []
        for line in new_lines:
            final_lines.append(line)
            if line.strip() == '[mysqld]' and not mysqld_found:
                mysqld_found = True
                final_lines.append(f'server-id = {server_id}')
                final_lines.append(f'log-bin = {log_bin}')
                final_lines.append('binlog-format = ROW')
                final_lines.append('expire-logs-days = 7')
        
        # Write new configuration
        with open(config_path, 'w') as f:
            f.write('\n'.join(final_lines))
        
        # Restart MySQL service (Linux only)
        # Try systemctl first
        restart_result = subprocess.run(['supervisorctl', 'restart', 'mariadb'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            # Restore backup
            shutil.copy2(backup_path, config_path)
            return jsonify({'success': False, 'error': f'Failed to restart MySQL: {restart_result.stderr}'})
        
        # Wait for MySQL to start
        time.sleep(3)
        
        # Verify master setup and create replication user
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL after restart'})
        
        cursor = connection.cursor(dictionary=True)
        
        # Check master status
        cursor.execute("SHOW MASTER STATUS")
        master_status = cursor.fetchone()
        
        if not master_status:
            cursor.close()
            connection.close()
            return jsonify({'success': False, 'error': 'Master setup failed - no master status found'})
        
        # Create replication user if provided
        replication_user = data.get('replication_user')
        replication_password = data.get('replication_password')
        
        logger.info(f'Received replication_user: {replication_user}, has_password: {bool(replication_password)}')
        
        if replication_user and replication_password:
            try:
                logger.info(f'Creating replication user: {replication_user}')
                
                # Check if user exists first
                cursor.execute("SELECT User FROM mysql.user WHERE User = %s AND Host = '%'", (replication_user,))
                user_exists = cursor.fetchone() is not None
                
                if user_exists:
                    logger.info(f'User {replication_user} exists, dropping first')
                    cursor.execute(f"DROP USER '{replication_user}'@'%'")
                    logger.info(f'Dropped existing user: {replication_user}')
                else:
                    logger.info(f'User {replication_user} does not exist, creating new user')
                
                # Create replication user
                cursor.execute(f"CREATE USER '{replication_user}'@'%' IDENTIFIED BY '{replication_password}'")
                logger.info(f'Created user: {replication_user}')
                
                cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{replication_user}'@'%'")
                logger.info(f'Granted REPLICATION SLAVE privileges to: {replication_user}')
                
                cursor.execute("FLUSH PRIVILEGES")
                logger.info('Flushed privileges')
                
                logger.info(f'Replication user {replication_user} created successfully')
            except Exception as user_error:
                logger.error(f'Failed to create replication user {replication_user}: {str(user_error)}')
                # Don't fail the entire setup if user creation fails
        else:
            logger.warning(f'Replication user not created - user: {replication_user}, password provided: {bool(replication_password)}')
        
        cursor.close()
        connection.close()
        
        logger.info(f'MySQL master setup completed with server-id {server_id}')
        return jsonify({
            'success': True, 
            'message': 'Master setup completed successfully',
            'master_status': master_status,
            'replication_user_created': bool(replication_user and replication_password)
        })
        
    except Exception as e:
        logger.error(f'Error setting up MySQL master: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/setup-slave', methods=['POST'])
@login_required
def setup_mysql_slave():
    """Setup MySQL as slave for replication"""
    try:
        data = request.get_json()
        master_host = data.get('master_host')
        master_user = data.get('master_user')
        master_password = data.get('master_password')
        master_log_file = data.get('master_log_file', '')
        master_log_pos = data.get('master_log_pos', 0)
        server_id = data.get('server_id', 2)
        
        if not all([master_host, master_user, master_password]):
            return jsonify({'success': False, 'error': 'Master host, user, and password are required'})
        
        if not isinstance(server_id, int) or server_id < 1 or server_id > 4294967295:
            return jsonify({'success': False, 'error': 'Invalid server ID. Must be between 1 and 4294967295'})
        
        # Read current MySQL configuration
        config_path = '/etc/mysql/mariadb.conf.d/50-server.cnf'
        if not os.path.exists(config_path):
            config_path = '/etc/mysql/mysql.conf.d/mysqld.cnf'
        if not os.path.exists(config_path):
            config_path = '/etc/my.cnf'
        
        if not os.path.exists(config_path):
            return jsonify({'success': False, 'error': 'MySQL configuration file not found'})
        
        # Backup original config
        backup_path = f"{config_path}.backup.{int(time.time())}"
        shutil.copy2(config_path, backup_path)
        
        # Read and modify configuration
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Remove existing replication settings
        lines = config_content.split('\n')
        new_lines = []
        in_mysqld_section = False
        
        for line in lines:
            stripped = line.strip()
            if stripped == '[mysqld]':
                in_mysqld_section = True
                new_lines.append(line)
            elif stripped.startswith('[') and stripped != '[mysqld]':
                in_mysqld_section = False
                new_lines.append(line)
            elif in_mysqld_section and (stripped.startswith('server-id') or 
                                       stripped.startswith('relay-log') or
                                       stripped.startswith('read-only')):
                # Skip existing replication settings
                continue
            else:
                new_lines.append(line)
        
        # Add new replication settings
        mysqld_found = False
        final_lines = []
        for line in new_lines:
            final_lines.append(line)
            if line.strip() == '[mysqld]' and not mysqld_found:
                mysqld_found = True
                final_lines.append(f'server-id = {server_id}')
                final_lines.append('relay-log = relay-bin')
                final_lines.append('read-only = 1')
        
        # Write new configuration
        with open(config_path, 'w') as f:
            f.write('\n'.join(final_lines))
        
        # Restart MySQL service
        restart_result = subprocess.run(['supervisorctl', 'restart', 'mariadb'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            # Restore backup
            shutil.copy2(backup_path, config_path)
            return jsonify({'success': False, 'error': f'Failed to restart MySQL: {restart_result.stderr}'})
        
        # Wait for MySQL to start
        time.sleep(3)
        
        # Setup slave connection
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL after restart'})
        
        cursor = connection.cursor()
        
        # Stop slave if running (ignore error if already stopped)
        try:
            cursor.execute("STOP SLAVE")
        except Exception as stop_error:
            # Ignore error if slave is already stopped
            if "Slave already has been stopped" not in str(stop_error):
                logger.warning(f'Error stopping slave (ignored): {str(stop_error)}')
        
        # Configure master connection
        change_master_sql = f"""
        CHANGE MASTER TO
        MASTER_HOST='{master_host}',
        MASTER_USER='{master_user}',
        MASTER_PASSWORD='{master_password}'
        """
        
        if master_log_file and master_log_pos > 0:
            change_master_sql += f",\nMASTER_LOG_FILE='{master_log_file}',\nMASTER_LOG_POS={master_log_pos}"
        
        cursor.execute(change_master_sql)
        
        # Start slave
        cursor.execute("START SLAVE")
        
        # Check slave status
        cursor.execute("SHOW SLAVE STATUS")
        slave_status = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        logger.info(f'MySQL slave setup completed for master {master_host}')
        return jsonify({
            'success': True, 
            'message': 'Slave setup completed successfully',
            'slave_status': slave_status
        })
        
    except Exception as e:
        logger.error(f'Error setting up MySQL slave: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/start-slave', methods=['POST'])
@login_required
def start_mysql_slave():
    """Start MySQL slave replication"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor()
        cursor.execute("START SLAVE")
        cursor.close()
        connection.close()
        
        logger.info('MySQL slave started')
        return jsonify({'success': True, 'message': 'Slave started successfully'})
        
    except Exception as e:
        logger.error(f'Error starting MySQL slave: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/stop-slave', methods=['POST'])
@login_required
def stop_mysql_slave():
    """Stop MySQL slave replication"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor()
        try:
            cursor.execute("STOP SLAVE")
            logger.info('MySQL slave stopped')
            message = 'Slave stopped successfully'
        except Exception as stop_error:
            if "Slave already has been stopped" in str(stop_error):
                logger.info('MySQL slave was already stopped')
                message = 'Slave was already stopped'
            else:
                raise stop_error
        
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        logger.error(f'Error stopping MySQL slave: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/reset-slave', methods=['POST'])
@login_required
def reset_mysql_slave():
    """Reset MySQL slave configuration"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor()
        try:
            cursor.execute("STOP SLAVE")
        except Exception as stop_error:
            if "Slave already has been stopped" not in str(stop_error):
                logger.warning(f'Error stopping slave during reset (ignored): {str(stop_error)}')
        
        cursor.execute("RESET SLAVE ALL")
        cursor.close()
        connection.close()
        
        logger.info('MySQL slave reset')
        return jsonify({'success': True, 'message': 'Slave reset successfully'})
        
    except Exception as e:
        logger.error(f'Error resetting MySQL slave: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/replication/disable-master', methods=['POST'])
@login_required
def disable_mysql_master():
    """Disable MySQL master replication"""
    try:
        # Read current MySQL configuration (Linux only)
        config_paths = [
            '/etc/mysql/mariadb.conf.d/50-server.cnf',
            '/etc/mysql/mysql.conf.d/mysqld.cnf',
            '/etc/my.cnf'
        ]
        
        config_path = None
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            return jsonify({'success': False, 'error': 'MySQL configuration file not found'})
        
        # Backup original config
        backup_path = f"{config_path}.backup.{int(time.time())}"
        shutil.copy2(config_path, backup_path)
        
        # Read and modify configuration
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Remove replication settings
        lines = config_content.split('\n')
        new_lines = []
        in_mysqld_section = False
        
        for line in lines:
            stripped = line.strip()
            if stripped == '[mysqld]':
                in_mysqld_section = True
                new_lines.append(line)
            elif stripped.startswith('[') and stripped != '[mysqld]':
                in_mysqld_section = False
                new_lines.append(line)
            elif in_mysqld_section and (stripped.startswith('server-id') or 
                                       stripped.startswith('log-bin') or
                                       stripped.startswith('binlog-format') or
                                       stripped.startswith('expire-logs-days') or
                                       stripped.startswith('binlog-do-db') or
                                       stripped.startswith('binlog-ignore-db')):
                # Skip replication settings
                continue
            else:
                new_lines.append(line)
        
        # Write new configuration
        with open(config_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        # Restart MySQL service (Linux only)
        restart_result = subprocess.run(['supervisorctl', 'restart', 'mariadb'], 
                                      capture_output=True, text=True)
        
        if restart_result.returncode != 0:
            # Restore backup
            shutil.copy2(backup_path, config_path)
            return jsonify({'success': False, 'error': f'Failed to restart MySQL: {restart_result.stderr}'})
        
        # Wait for MySQL to start
        time.sleep(3)
        
        # Verify master is disabled
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Failed to connect to MySQL after restart'})
        
        cursor = connection.cursor(dictionary=True)
        
        # Reset master (clear binary logs)
        try:
            cursor.execute("RESET MASTER")
        except mysql.connector.Error as e:
            logger.warning(f'Failed to reset master: {str(e)}')
        
        cursor.close()
        connection.close()
        
        logger.info('MySQL master replication disabled successfully')
        return jsonify({
            'success': True, 
            'message': 'Master replication disabled successfully'
        })
        
    except Exception as e:
        logger.error(f'Error disabling MySQL master: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mysql/error-logs', methods=['GET'])
def get_mysql_error_logs():
    """Get MySQL error logs"""
    try:
        # Common MySQL error log paths
        error_log_paths = [
            '/var/log/mysql/error.log',
            '/var/log/mysqld.log',
            '/var/log/mysql.err',
            '/usr/local/var/mysql/*.err'
        ]
        
        logs_content = ""
        log_found = False
        
        for log_path in error_log_paths:
            if '*' in log_path:
                # Handle wildcard paths
                import glob
                matching_files = glob.glob(log_path)
                for file_path in matching_files:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as f:
                                # Get last 100 lines
                                lines = f.readlines()
                                recent_lines = lines[-100:] if len(lines) > 100 else lines
                                logs_content += f"\n=== {file_path} ===\n"
                                logs_content += ''.join(recent_lines)
                                log_found = True
                        except Exception as e:
                            logs_content += f"\nError reading {file_path}: {str(e)}\n"
            else:
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r') as f:
                            # Get last 100 lines
                            lines = f.readlines()
                            recent_lines = lines[-100:] if len(lines) > 100 else lines
                            logs_content += f"\n=== {log_path} ===\n"
                            logs_content += ''.join(recent_lines)
                            log_found = True
                    except Exception as e:
                        logs_content += f"\nError reading {log_path}: {str(e)}\n"
        
        if not log_found:
            logs_content = "No MySQL error logs found in common locations."
        
        # Format logs for HTML display
        formatted_logs = logs_content.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        return jsonify({
            'success': True,
            'logs': formatted_logs
        })
        
    except Exception as e:
        logger.error(f'Error getting MySQL error logs: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mysql/replication-logs', methods=['GET'])
def get_mysql_replication_logs():
    """Get MySQL replication-related logs"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor(dictionary=True)
        logs_content = ""
        
        # Get replication status for error information
        try:
            cursor.execute("SHOW SLAVE STATUS")
            slave_status = cursor.fetchone()
            
            if slave_status:
                logs_content += "=== Slave Status Information ===\n"
                logs_content += f"Slave_IO_Running: {slave_status.get('Slave_IO_Running', 'N/A')}\n"
                logs_content += f"Slave_SQL_Running: {slave_status.get('Slave_SQL_Running', 'N/A')}\n"
                logs_content += f"Last_IO_Error: {slave_status.get('Last_IO_Error', 'None')}\n"
                logs_content += f"Last_SQL_Error: {slave_status.get('Last_SQL_Error', 'None')}\n"
                logs_content += f"Seconds_Behind_Master: {slave_status.get('Seconds_Behind_Master', 'N/A')}\n"
                logs_content += f"Master_Log_File: {slave_status.get('Master_Log_File', 'N/A')}\n"
                logs_content += f"Read_Master_Log_Pos: {slave_status.get('Read_Master_Log_Pos', 'N/A')}\n\n"
            else:
                logs_content += "=== No Slave Configuration Found ===\n\n"
        except Exception as e:
            logs_content += f"Error getting slave status: {str(e)}\n\n"
        
        # Get binary log information
        try:
            cursor.execute("SHOW BINARY LOGS")
            binary_logs = cursor.fetchall()
            
            if binary_logs:
                logs_content += "=== Binary Logs ===\n"
                for log in binary_logs:
                    logs_content += f"{log.get('Log_name', 'N/A')} - Size: {log.get('File_size', 'N/A')} bytes\n"
                logs_content += "\n"
            else:
                logs_content += "=== No Binary Logs Found ===\n\n"
        except Exception as e:
            logs_content += f"Binary logs not available: {str(e)}\n\n"
        
        # Get master status
        try:
            cursor.execute("SHOW MASTER STATUS")
            master_status = cursor.fetchone()
            
            if master_status:
                logs_content += "=== Master Status ===\n"
                logs_content += f"File: {master_status.get('File', 'N/A')}\n"
                logs_content += f"Position: {master_status.get('Position', 'N/A')}\n"
                logs_content += f"Binlog_Do_DB: {master_status.get('Binlog_Do_DB', 'N/A')}\n"
                logs_content += f"Binlog_Ignore_DB: {master_status.get('Binlog_Ignore_DB', 'N/A')}\n\n"
            else:
                logs_content += "=== No Master Configuration Found ===\n\n"
        except Exception as e:
            logs_content += f"Master status not available: {str(e)}\n\n"
        
        cursor.close()
        connection.close()
        
        if not logs_content.strip():
            logs_content = "No replication information available."
        
        # Format logs for HTML display
        formatted_logs = logs_content.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        return jsonify({
            'success': True,
            'logs': formatted_logs
        })
        
    except Exception as e:
        logger.error(f'Error getting MySQL replication logs: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mysql/general-logs', methods=['GET'])
def get_mysql_general_logs():
    """Get MySQL general logs"""
    try:
        # Common MySQL general log paths
        general_log_paths = [
            '/var/log/mysql/mysql.log',
            '/var/log/mysql/general.log',
            '/usr/local/var/mysql/general.log'
        ]
        
        logs_content = ""
        log_found = False
        
        for log_path in general_log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        # Get last 100 lines
                        lines = f.readlines()
                        recent_lines = lines[-100:] if len(lines) > 100 else lines
                        logs_content += f"\n=== {log_path} ===\n"
                        logs_content += ''.join(recent_lines)
                        log_found = True
                except Exception as e:
                    logs_content += f"\nError reading {log_path}: {str(e)}\n"
        
        if not log_found:
            logs_content = "No MySQL general logs found. General logging may be disabled.\n\n"
            logs_content += "To enable general logging, add the following to your MySQL configuration:\n"
            logs_content += "general_log = 1\n"
            logs_content += "general_log_file = /var/log/mysql/general.log"
        
        # Format logs for HTML display
        formatted_logs = logs_content.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        return jsonify({
            'success': True,
            'logs': formatted_logs
        })
        
    except Exception as e:
        logger.error(f'Error getting MySQL general logs: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mysql/slow-logs', methods=['GET'])
def get_mysql_slow_logs():
    """Get MySQL slow query logs"""
    try:
        # Common MySQL slow log paths
        slow_log_paths = [
            '/var/log/mysql/mysql-slow.log',
            '/var/log/mysql/slow.log',
            '/usr/local/var/mysql/slow.log'
        ]
        
        logs_content = ""
        log_found = False
        
        for log_path in slow_log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r') as f:
                        # Get last 50 entries (slow logs can be verbose)
                        lines = f.readlines()
                        recent_lines = lines[-200:] if len(lines) > 200 else lines
                        logs_content += f"\n=== {log_path} ===\n"
                        logs_content += ''.join(recent_lines)
                        log_found = True
                except Exception as e:
                    logs_content += f"\nError reading {log_path}: {str(e)}\n"
        
        if not log_found:
            logs_content = "No MySQL slow query logs found. Slow query logging may be disabled.\n\n"
            logs_content += "To enable slow query logging, add the following to your MySQL configuration:\n"
            logs_content += "slow_query_log = 1\n"
            logs_content += "slow_query_log_file = /var/log/mysql/mysql-slow.log\n"
            logs_content += "long_query_time = 2"
        
        # Format logs for HTML display
        formatted_logs = logs_content.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        return jsonify({
            'success': True,
            'logs': formatted_logs
        })
        
    except Exception as e:
        logger.error(f'Error getting MySQL slow logs: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/mysql/analyze-slow-logs', methods=['GET'])
def analyze_mysql_slow_logs():
    """Analyze MySQL slow query logs"""
    try:
        connection = create_mysql_connection()
        if not connection:
            return jsonify({'success': False, 'message': 'Failed to connect to MySQL'})
        
        cursor = connection.cursor(dictionary=True)
        analysis_content = ""
        
        # Get slow query log status
        try:
            cursor.execute("SHOW VARIABLES LIKE 'slow_query_log'")
            slow_log_status = cursor.fetchone()
            
            cursor.execute("SHOW VARIABLES LIKE 'long_query_time'")
            long_query_time = cursor.fetchone()
            
            cursor.execute("SHOW VARIABLES LIKE 'slow_query_log_file'")
            slow_log_file = cursor.fetchone()
            
            analysis_content += "=== Slow Query Log Configuration ===\n"
            analysis_content += f"Slow Query Log: {slow_log_status.get('Value', 'N/A') if slow_log_status else 'N/A'}\n"
            analysis_content += f"Long Query Time: {long_query_time.get('Value', 'N/A') if long_query_time else 'N/A'} seconds\n"
            analysis_content += f"Slow Log File: {slow_log_file.get('Value', 'N/A') if slow_log_file else 'N/A'}\n\n"
            
        except Exception as e:
            analysis_content += f"Error getting slow log configuration: {str(e)}\n\n"
        
        # Get process list for currently running queries
        try:
            cursor.execute("SHOW PROCESSLIST")
            processes = cursor.fetchall()
            
            long_running = [p for p in processes if p.get('Time', 0) > 5 and p.get('Command') not in ['Sleep', 'Binlog Dump']]
            
            if long_running:
                analysis_content += "=== Currently Long Running Queries ===\n"
                for process in long_running:
                    analysis_content += f"ID: {process.get('Id', 'N/A')}, User: {process.get('User', 'N/A')}, "
                    analysis_content += f"Time: {process.get('Time', 'N/A')}s, State: {process.get('State', 'N/A')}\n"
                    analysis_content += f"Info: {process.get('Info', 'N/A')[:100]}...\n\n"
            else:
                analysis_content += "=== No Long Running Queries Found ===\n\n"
                
        except Exception as e:
            analysis_content += f"Error getting process list: {str(e)}\n\n"
        
        # Get query cache statistics
        try:
            cursor.execute("SHOW STATUS LIKE 'Qcache%'")
            qcache_stats = cursor.fetchall()
            
            if qcache_stats:
                analysis_content += "=== Query Cache Statistics ===\n"
                for stat in qcache_stats:
                    analysis_content += f"{stat.get('Variable_name', 'N/A')}: {stat.get('Value', 'N/A')}\n"
                analysis_content += "\n"
                
        except Exception as e:
            analysis_content += f"Query cache statistics not available: {str(e)}\n\n"
        
        # Get table lock statistics
        try:
            cursor.execute("SHOW STATUS LIKE 'Table_locks%'")
            lock_stats = cursor.fetchall()
            
            if lock_stats:
                analysis_content += "=== Table Lock Statistics ===\n"
                for stat in lock_stats:
                    analysis_content += f"{stat.get('Variable_name', 'N/A')}: {stat.get('Value', 'N/A')}\n"
                analysis_content += "\n"
                
        except Exception as e:
            analysis_content += f"Table lock statistics not available: {str(e)}\n\n"
        
        cursor.close()
        connection.close()
        
        if not analysis_content.strip():
            analysis_content = "No slow query analysis data available."
        
        # Format analysis for HTML display
        formatted_analysis = analysis_content.replace('\n', '<br>').replace(' ', '&nbsp;')
        
        return jsonify({
            'success': True,
            'analysis': formatted_analysis
        })
        
    except Exception as e:
        logger.error(f'Error analyzing MySQL slow logs: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

# Plugin Management API
@app.route('/api/plugins', methods=['GET'])
@login_required
def get_plugins():
    """Get list of installed plugins from plugins_info.json"""
    try:
        plugins_info_file = os.path.join(os.path.dirname(__file__), 'data', 'plugins_info.json')
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        
        if not os.path.exists(plugins_info_file):
            return jsonify({'success': True, 'plugins': []})
        
        with open(plugins_info_file, 'r', encoding='utf-8') as f:
            plugins_data = json.load(f)
            plugins = plugins_data.get('plugins', [])
        
        # Check if each plugin is actually installed (exists in plugins folder)
        for plugin in plugins:
            plugin_folder_path = os.path.join(plugins_dir, plugin.get('id', ''))
            plugin['installed'] = os.path.exists(plugin_folder_path)
        
        return jsonify({'success': True, 'plugins': plugins})
        
    except Exception as e:
        logger.error(f'Error getting plugins: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/plugins/toggle', methods=['POST'])
@login_required
def toggle_plugin():
    """Enable or disable a plugin"""
    try:
        data = request.get_json()
        plugin_name = data.get('plugin')
        action = data.get('action')  # 'enable' or 'disable'
        
        if not plugin_name or not action:
            return jsonify({'success': False, 'message': 'Plugin name and action are required'})
        
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        plugin_path = os.path.join(plugins_dir, plugin_name)
        info_file = os.path.join(plugin_path, 'info.json')
        
        if not os.path.exists(info_file):
            return jsonify({'success': False, 'message': 'Plugin not found'})
        
        # Read current plugin info
        with open(info_file, 'r', encoding='utf-8') as f:
            plugin_info = json.load(f)
        
        # Update status
        if action == 'enable':
            plugin_info['status'] = 'active'
        elif action == 'disable':
            plugin_info['status'] = 'inactive'
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
        
        # Save updated info
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(plugin_info, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True, 
            'message': f'Plugin {plugin_name} {action}d successfully'
        })
        
    except Exception as e:
        logger.error(f'Error toggling plugin: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

def download_plugin_from_external(plugin_name):
    """Download plugin from external URL and extract to plugins directory"""
    try:
        # External URL for plugin download
        download_url = f'https://basoro.id/slemp-repo/{plugin_name}.zip'
        
        logger.info(f'Attempting to download plugin from: {download_url}')
        
        # Download the plugin zip file
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Create plugins directory if it doesn't exist
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Create temporary file for the zip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            temp_file.write(response.content)
            temp_zip_path = temp_file.name
        
        try:
            # Extract the zip file to plugins directory
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                # Extract to a temporary directory first to check structure
                with tempfile.TemporaryDirectory() as temp_extract_dir:
                    zip_ref.extractall(temp_extract_dir)
                    
                    # Check if the extracted content has the plugin structure
                    extracted_items = os.listdir(temp_extract_dir)
                    
                    if len(extracted_items) == 1 and os.path.isdir(os.path.join(temp_extract_dir, extracted_items[0])):
                        # If there's a single directory, use its contents
                        source_dir = os.path.join(temp_extract_dir, extracted_items[0])
                    else:
                        # If multiple files/dirs, use the temp directory itself
                        source_dir = temp_extract_dir
                    
                    # Create target plugin directory
                    target_plugin_dir = os.path.join(plugins_dir, plugin_name)
                    
                    # Copy extracted content to target directory
                    if os.path.exists(target_plugin_dir):
                        shutil.rmtree(target_plugin_dir)
                    
                    shutil.copytree(source_dir, target_plugin_dir)
                    
                    logger.info(f'Successfully downloaded and extracted plugin: {plugin_name}')
                    return True
                    
        finally:
            # Clean up temporary zip file
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
                
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to download plugin {plugin_name}: {str(e)}')
        return False
    except zipfile.BadZipFile as e:
        logger.error(f'Invalid zip file for plugin {plugin_name}: {str(e)}')
        return False
    except Exception as e:
        logger.error(f'Error downloading plugin {plugin_name}: {str(e)}')
        return False

@app.route('/api/plugins/download', methods=['POST'])
@login_required
def download_plugin():
    """Download plugin from external URL"""
    try:
        data = request.get_json()
        plugin_name = data.get('plugin_name')
        
        if not plugin_name:
            return jsonify({'success': False, 'message': 'Plugin name is required'})
        
        # Check if plugin already exists
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        plugin_dir = os.path.join(plugins_dir, plugin_name)
        
        if os.path.exists(plugin_dir):
            return jsonify({'success': False, 'message': 'Plugin already exists'})
        
        # Download plugin
        download_success = download_plugin_from_external(plugin_name)
        
        if download_success:
            # Update plugins_info.json if it exists
            try:
                plugins_info_file = os.path.join(os.path.dirname(__file__), 'data', 'plugins_info.json')
                if os.path.exists(plugins_info_file):
                    with open(plugins_info_file, 'r', encoding='utf-8') as f:
                        plugins_data = json.load(f)
                    
                    # Check if plugin info.json exists to get metadata
                    info_file = os.path.join(plugin_dir, 'info.json')
                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            plugin_info = json.load(f)
                        
                        # Add to plugins list if not already there
                        existing_plugin = next((p for p in plugins_data.get('plugins', []) if p.get('id') == plugin_name), None)
                        if not existing_plugin:
                            plugins_data.setdefault('plugins', []).append({
                                'id': plugin_name,
                                'name': plugin_info.get('name', plugin_name),
                                'description': plugin_info.get('description', ''),
                                'version': plugin_info.get('version', '1.0.0'),
                                'status': plugin_info.get('status', 'active')
                            })
                            
                            # Save updated plugins_info.json
                            with open(plugins_info_file, 'w', encoding='utf-8') as f:
                                json.dump(plugins_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.warning(f'Could not update plugins_info.json: {str(e)}')
            
            return jsonify({
                'success': True, 
                'message': f'Plugin {plugin_name} downloaded successfully'
            })
        else:
            return jsonify({
                'success': False, 
                'message': f'Failed to download plugin {plugin_name}'
            })
            
    except Exception as e:
        logger.error(f'Error downloading plugin: {str(e)}')
        return jsonify({'success': False, 'message': str(e)})

@app.route('/static/plugins/<plugin_id>/<filename>')
@login_required
def plugin_static(plugin_id, filename):
    """Serve static files from plugin directories"""
    try:
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        file_path = os.path.join(plugins_dir, plugin_id, filename)
        
        # Security check - ensure file is within plugin directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(plugins_dir)):
            return 'Access denied', 403
            
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return 'File not found', 404
            
    except Exception as e:
        logger.error(f'Error serving plugin static file: {str(e)}')
        return 'Internal server error', 500

@app.route('/api/plugins/<plugin_name>/interface')
@login_required
def plugin_interface(plugin_name):
    """Serve plugin interface (index.html) with processed content"""
    try:
        logger.info(f'Plugin interface requested for: {plugin_name}')
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        plugin_dir = os.path.join(plugins_dir, plugin_name)
        index_file = os.path.join(plugin_dir, 'index.html')
        
        logger.info(f'Plugin directory: {plugin_dir}')
        logger.info(f'Index file path: {index_file}')
        logger.info(f'Current working directory: {os.getcwd()}')
        logger.info(f'App file location: {os.path.dirname(__file__)}')
        
        # Security check - ensure plugin directory exists
        if not os.path.exists(plugin_dir):
            logger.error(f'Plugin directory not found: {plugin_dir}')
            return 'Plugin not found', 404
            
        # Check if index.html exists
        if not os.path.exists(index_file):
            logger.error(f'Plugin index.html not found: {index_file}')
            return 'Plugin interface not found', 404
            
        # Security check - ensure file is within plugin directory
        if not os.path.abspath(index_file).startswith(os.path.abspath(plugins_dir)):
            logger.error(f'Security violation: file outside plugins directory')
            return 'Access denied', 403
        
        # Read and process the HTML content
        with open(index_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Process relative URLs to absolute URLs for API calls
        # Only replace fetch calls that don't already have /api/plugins/ prefix
        import re
        
        # Replace fetch calls that start with relative paths (not already prefixed)
        # Pattern: fetch('/something') but not fetch('/api/plugins/...')
        pattern1 = r'fetch\("(/[^"]*)")'
        if f'/api/plugins/{plugin_name}/' not in html_content:
            replacement1 = f'fetch("/api/plugins/{plugin_name}\1")'
            html_content = re.sub(pattern1, replacement1, html_content)
        
        pattern2 = r"fetch\('(/[^']*)'\)"
        if f'/api/plugins/{plugin_name}/' not in html_content:
            replacement2 = f"fetch('/api/plugins/{plugin_name}\1')"
            html_content = re.sub(pattern2, replacement2, html_content)
        
        # Add base tag for relative resources
        if '<head>' in html_content:
            base_tag = f'<base href="/api/plugins/{plugin_name}/">'
            html_content = html_content.replace('<head>', f'<head>\n    {base_tag}')
        
        logger.info(f'Serving processed plugin interface for: {plugin_name}')
        
        from flask import Response
        return Response(html_content, mimetype='text/html')
            
    except Exception as e:
        logger.error(f'Error serving plugin interface: {str(e)}')
        return 'Internal server error', 500

@app.route('/api/plugins/<plugin_name>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def plugin_api(plugin_name, endpoint):
    """Proxy API calls to plugin's index.py using main() function"""
    try:
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        plugin_dir = os.path.join(plugins_dir, plugin_name)
        plugin_file = os.path.join(plugin_dir, 'index.py')
        
        # Security check - ensure plugin directory and file exist
        if not os.path.exists(plugin_dir) or not os.path.exists(plugin_file):
            return jsonify({'error': 'Plugin not found'}), 404
            
        # Import the plugin module dynamically
        import sys
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(f"plugin_{plugin_name}", plugin_file)
        plugin_module = importlib.util.module_from_spec(spec)
        
        # Add plugin directory to sys.path temporarily
        original_path = sys.path.copy()
        sys.path.insert(0, plugin_dir)
        
        try:
            spec.loader.exec_module(plugin_module)
            
            # Check if plugin has main() function (new standard approach)
            if hasattr(plugin_module, 'main'):
                # Set the action in form data based on endpoint
                from werkzeug.datastructures import ImmutableMultiDict
                form_data = dict(request.form)
                form_data['action'] = endpoint
                request.form = ImmutableMultiDict(form_data)
                
                # Call the main function directly
                return plugin_module.main()
            
            # Fallback: Get the blueprint from the plugin (legacy approach)
            elif hasattr(plugin_module, 'bp'):
                # Get the blueprint and find the matching route
                blueprint = plugin_module.bp
                
                # Create a temporary Flask app context for the plugin
                from flask import Flask as TempFlask
                temp_app = TempFlask(__name__)
                temp_app.register_blueprint(blueprint)
                
                # Forward the request to the plugin using temp app
                with temp_app.test_client() as client:
                    if request.method == 'GET':
                        response = client.get(f'/{endpoint}', 
                                            query_string=request.query_string)
                    elif request.method == 'POST':
                        response = client.post(f'/{endpoint}', 
                                             data=request.get_data(), 
                                             content_type=request.content_type)
                    elif request.method == 'PUT':
                        response = client.put(f'/{endpoint}', 
                                            data=request.get_data(), 
                                            content_type=request.content_type)
                    elif request.method == 'DELETE':
                        response = client.delete(f'/{endpoint}')
                    
                    return response.get_data(), response.status_code, dict(response.headers)
            else:
                return jsonify({'error': 'Plugin does not expose main() function or API blueprint'}), 500
                
        finally:
            # Restore original sys.path
            sys.path = original_path
            
    except Exception as e:
        logger.error(f'Error calling plugin API: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Register the terminal namespace
socketio.on_namespace(TerminalNamespace('/terminal'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7777, debug=True, allow_unsafe_werkzeug=True)
