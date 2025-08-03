from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
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
import re
import logging
from logging.handlers import RotatingFileHandler
import datetime

# Konfigurasi logging 
if not os.path.exists('logs'):
    os.makedirs('logs')

log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_file = 'logs/server_manager.log'
log_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('server_manager')
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# MySQL Connection Pool Configuration
def load_config():
    """Load configuration from JSON file - force load from config.json only"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_file, 'r') as f:
        return json.load(f)

def save_config(config_data):
    """Save configuration to JSON file"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
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

def format_uptime(seconds):
    """Format uptime seconds into human readable format"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"
    elif hours > 0:
        return f"{int(hours)}h {int(minutes)}m"
    else:
        return f"{int(minutes)}m"

@app.route('/api/system-info')
@login_required
def system_info():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get system uptime
    boot_time = psutil.boot_time()
    uptime_seconds = datetime.datetime.now().timestamp() - boot_time
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
                    'speed': stats.speed if stats.speed > 0 else 'Unknown',
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
        'mysql': 'mariadb-server'
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
            
            socketio.emit('install_progress', {'message': f'Memulai instalasi {service_name}...', 'step': 1, 'total': 4, 'status': f'Memulai instalasi {service_name}...', 'percentage': 25})
            
            # Update package list first
            socketio.emit('install_progress', {'message': 'Memperbarui daftar paket...', 'step': 2, 'total': 4, 'status': 'Memperbarui daftar paket...', 'percentage': 50})
            socketio.emit('install_output', {'output': '$ apt-get update', 'type': 'command'})
            
            update_code, update_output = run_command_with_realtime_output(['apt-get', 'update'], 300)
            
            if update_code != 0:
                logger.warning(f'Package update failed with code {update_code}')
                socketio.emit('install_progress', {'message': 'Peringatan: Gagal memperbarui daftar paket', 'step': 2, 'total': 4, 'status': 'Peringatan: Gagal memperbarui daftar paket', 'percentage': 50})
            else:
                socketio.emit('install_progress', {'message': 'Daftar paket berhasil diperbarui', 'step': 2, 'total': 4, 'status': 'Daftar paket berhasil diperbarui', 'percentage': 50})
            
            # Install the service
            socketio.emit('install_progress', {'message': f'Menginstall {service_name}...', 'step': 3, 'total': 4, 'status': f'Menginstall {service_name}...', 'percentage': 75})
            socketio.emit('install_output', {'output': f'$ apt-get install -y {service_name}', 'type': 'command'})
            
            install_code, install_output = run_command_with_realtime_output(['apt-get', 'install', '-y', service_name], 600)
            
            if install_code == 0:
                logger.info(f'Service {service_name} installed successfully via WebSocket')
                socketio.emit('install_progress', {'message': f'{service_name} berhasil diinstall', 'step': 3, 'total': 4, 'status': f'{service_name} berhasil diinstall', 'percentage': 75})
                
                # Start the service using supervisorctl
                socketio.emit('install_progress', {'message': f'Memulai layanan {service_name}...', 'step': 4, 'total': 4, 'status': f'Memulai layanan {service_name}...', 'percentage': 100})
                if service_name != 'mariadb-server':
                    socketio.emit('install_output', {'output': f'$ supervisorctl start {service}', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'start', service], 30)
                else:
                    # For MariaDB, create socket directory first
                    socketio.emit('install_output', {'output': 'Menyiapkan direktori socket MariaDB...', 'type': 'info'})
                    socketio.emit('install_output', {'output': '$ mkdir -p /run/mysqld', 'type': 'command'})
                    subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    socketio.emit('install_output', {'output': '$ chown mysql:mysql /run/mysqld', 'type': 'command'})
                    subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    socketio.emit('install_output', {'output': '$ chmod 755 /run/mysqld', 'type': 'command'})
                    subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True, timeout=10)
                    # For MariaDB, use 'mariadb' as service name in supervisor
                    socketio.emit('install_output', {'output': '$ supervisorctl start mariadb', 'type': 'command'})
                    start_code, start_output = run_command_with_realtime_output(['supervisorctl', 'start', 'mariadb'], 30)
                    
                    # Reset MySQL root password after MariaDB starts
                    if start_code == 0:
                        socketio.emit('install_output', {'output': 'Mengatur password root MySQL...', 'type': 'info'})
                        
                        # Start mysqld_safe with skip-grant-tables
                        socketio.emit('install_output', {'output': '$ mysqld_safe --skip-grant-tables --skip-networking &', 'type': 'command'})
                        subprocess.run(['mysqld_safe', '--skip-grant-tables', '--skip-networking'], capture_output=True, text=True, timeout=10)
                        
                        # Wait for mysqld_safe to start
                        socketio.emit('install_output', {'output': '$ sleep 5', 'type': 'command'})
                        subprocess.run(['sleep', '5'], capture_output=True, text=True, timeout=10)
                        
                        # Reset root password
                        mysql_commands = "FLUSH PRIVILEGES;\nALTER USER 'root'@'localhost' IDENTIFIED BY '';\nFLUSH PRIVILEGES;"
                        socketio.emit('install_output', {'output': '$ mysql -u root <<EOF', 'type': 'command'})
                        socketio.emit('install_output', {'output': mysql_commands, 'type': 'info'})
                        socketio.emit('install_output', {'output': 'EOF', 'type': 'command'})
                        
                        mysql_process = subprocess.Popen(['mysql', '-u', 'root'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        mysql_output, mysql_error = mysql_process.communicate(input=mysql_commands, timeout=30)
                        
                        # Stop mysqld_safe before starting with supervisor
                        socketio.emit('install_output', {'output': '$ pkill mysqld', 'type': 'command'})
                        subprocess.run(['pkill', 'mysqld'], capture_output=True, text=True, timeout=10)
                        
                        # Restart gunicorn to reload database configuration
                        socketio.emit('install_output', {'output': 'Merestart aplikasi untuk memuat konfigurasi database baru...', 'type': 'info'})
                        socketio.emit('install_output', {'output': '$ supervisorctl restart gunicorn', 'type': 'command'})
                        subprocess.run(['supervisorctl', 'restart', 'gunicorn'], capture_output=True, text=True, timeout=30)
                        
                        # Restart MariaDB with supervisor
                        socketio.emit('install_output', {'output': '$ supervisorctl restart mariadb', 'type': 'command'})
                        restart_code, restart_output = run_command_with_realtime_output(['supervisorctl', 'restart', 'mariadb'], 30)
                        start_code = restart_code  # Use restart result for final status
                
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
    emit('install_progress', {'message': 'Instalasi dimulai...', 'step': 1, 'total': 4, 'status': 'Instalasi dimulai...', 'percentage': 25})

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
            
            # Cek status proses hanya jika terinstall
            running = False
            pid = None
            version = 'Not Installed' if not installed else 'N/A'
            
            if installed:
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
        'mysql': get_service_info('mysql', 'mariadbd')
    }
    return jsonify(services)

@app.route('/api/service/<service>/start', methods=['POST'])
@login_required
def start_service(service):
    service_map = {
        'nginx': 'nginx',
        'php-fpm': 'php-fpm',
        'mysql': 'mariadb'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        # Use different commands based on service type
        if service_name == 'mariadb':
            # For MariaDB, create socket directory first
            subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True)
            subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True)
            result = subprocess.run(['supervisorctl', 'start', service_name], capture_output=True, text=True)
        else:
            # For nginx and php-fpm, try supervisorctl first, then systemctl as fallback
            result = subprocess.run(['supervisorctl', 'start', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f'Service {service_name} started successfully')
            return jsonify({'success': True, 'message': f'{service_name} berhasil dimulai'})
        else:
            if service_name != 'mariadb':
                # Fallback to systemctl for non-mariadb services
                result = subprocess.run(['systemctl', 'start', service_name], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f'Service {service_name} started successfully via systemctl')
                    return jsonify({'success': True, 'message': f'{service_name} berhasil dimulai'})
            
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
        'mysql': 'mariadb'
    }

    if service not in service_map:
        return jsonify({'success': False, 'message': 'Layanan tidak valid'}), 400

    try:
        service_name = service_map[service]
        # Use different commands based on service type
        if service_name == 'mariadb':
            result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        else:
            # For nginx and php-fpm, try supervisorctl first, then systemctl as fallback
            result = subprocess.run(['supervisorctl', 'stop', service_name], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f'Service {service_name} stopped successfully')
            return jsonify({'success': True, 'message': f'{service_name} berhasil dihentikan'})
        else:
            if service_name != 'mariadb':
                # Fallback to systemctl for non-mariadb services
                result = subprocess.run(['systemctl', 'stop', service_name], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f'Service {service_name} stopped successfully via systemctl')
                    return jsonify({'success': True, 'message': f'{service_name} berhasil dihentikan'})
            
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
        'mysql': 'mariadb-server'
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
            
            # Start the service using supervisorctl
            if service_name != 'mariadb-server':
                start_result = subprocess.run(['supervisorctl', 'start', service], capture_output=True, text=True)
            else:
                # For MariaDB, create socket directory first
                subprocess.run(['mkdir', '-p', '/run/mysqld'], capture_output=True, text=True)
                subprocess.run(['chown', 'mysql:mysql', '/run/mysqld'], capture_output=True, text=True)
                subprocess.run(['chmod', '755', '/run/mysqld'], capture_output=True, text=True)
                # For MariaDB, use 'mariadb' as service name in supervisor
                start_result = subprocess.run(['supervisorctl', 'start', 'mariadb'], capture_output=True, text=True)
            
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
        'mysql': 'mariadb-server'
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
                # Remove nginx configuration directories if they exist
                config_dirs = ['/etc/nginx/sites-available', '/etc/nginx/sites-enabled']
                for config_dir in config_dirs:
                    if os.path.exists(config_dir):
                        try:
                            shutil.rmtree(config_dir)
                            logger.info(f'Removed directory: {config_dir}')
                        except Exception as e:
                            logger.warning(f'Could not remove {config_dir}: {str(e)}')
            
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

        # Reload nginx
        logger.info('Restarting nginx via supervisorctl')
        result = subprocess.run(['supervisorctl', 'restart', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to restart nginx: {result.stderr}')
            return jsonify({'error': f'Failed to restart nginx: {result.stderr}'}), 500

        logger.info(f'Virtual host {domain} created successfully')
        return jsonify({'message': 'Virtual host created successfully'})
    except Exception as e:
        logger.error(f'Error creating virtual host: {str(e)}')
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

        # Restart nginx
        logger.info('Restarting nginx via supervisorctl')
        result = subprocess.run(['supervisorctl', 'restart', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to restart nginx: {result.stderr}')
            return jsonify({'error': f'Failed to restart nginx: {result.stderr}'}), 500

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

        # Restart nginx
        logger.info('Restarting nginx via supervisorctl')
        result = subprocess.run(['supervisorctl', 'restart', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f'Failed to restart nginx: {result.stderr}')
            return jsonify({'error': f'Failed to restart nginx: {result.stderr}'}), 500

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
        subprocess.run(['sudo', 'systemctl', 'restart', 'php-fpm'])

        return jsonify({'message': 'PHP configuration updated successfully'})
    except Exception as e:
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
        
        # Restart gunicorn to reload database configuration
        try:
            logger.info('Restarting gunicorn to reload database configuration')
            restart_result = subprocess.run(['supervisorctl', 'restart', 'gunicorn'], capture_output=True, text=True, timeout=30)
            if restart_result.returncode == 0:
                logger.info('Gunicorn restarted successfully')
            else:
                logger.warning(f'Failed to restart gunicorn: {restart_result.stderr}')
        except Exception as e:
            logger.warning(f'Error restarting gunicorn: {str(e)}')
        
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

@app.route('/api/app/restart', methods=['POST'])
@login_required
def restart_app():
    """Restart aplikasi Flask (gunicorn)"""
    
    try:
        app.logger.info(f"App restart initiated")
        
        # Restart gunicorn menggunakan supervisorctl
        result = subprocess.run(
            ['supervisorctl', 'restart', 'gunicorn'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            app.logger.info("Gunicorn restarted successfully")
            return jsonify({
                'success': True,
                'message': 'Aplikasi berhasil direstart'
            })
        else:
            app.logger.error(f"Failed to restart gunicorn: {result.stderr}")
            return jsonify({
                'success': False,
                'message': f'Gagal restart aplikasi: {result.stderr}'
            }), 500
            
    except subprocess.TimeoutExpired:
        app.logger.error("Timeout restarting gunicorn")
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
        logger.error(f'Error managing Nginx config: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)