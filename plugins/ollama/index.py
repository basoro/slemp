#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Manager Plugin
Manage Ollama models and configurations
"""

import os
import json
import subprocess
import requests
import platform
import time
import signal
from flask import request, jsonify, Response

def main():
    """Main function to handle API requests"""
    try:
        # Get request method and endpoint
        method = request.method
        endpoint = request.endpoint
        
        # Parse the endpoint to get the action
        if 'plugin_api' in endpoint:
            path_parts = request.path.split('/')
            if len(path_parts) >= 5:
                action = path_parts[4]  # /api/plugins/ollama/{action}
            else:
                action = 'status'
        else:
            action = 'status'
        
        # Route to appropriate function based on action
        if action == 'status':
            return get_ollama_status()
        elif action == 'install':
            return install_ollama()
        elif action == 'install-stream':
            return install_ollama_stream()
        elif action == 'start':
            return start_ollama_service()
        elif action == 'stop':
            return stop_ollama_service()
        elif action == 'models':
            if method == 'GET':
                return get_models()
            elif method == 'POST':
                return pull_model()
            elif method == 'DELETE':
                return delete_model()
        elif action == 'start-http-api':
            return start_http_api()
        elif action == 'stop-http-api':
            return stop_http_api()
        elif action == 'generate':
            return generate_response()
        elif action == 'config':
            if method == 'GET':
                return get_config()
            elif method == 'POST':
                return update_config()
        else:
            return jsonify({'success': False, 'message': 'Unknown action'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_ollama_status():
    """Check if Ollama is installed and running"""
    global http_api_process
    try:
        # Check if Ollama is installed
        is_installed = check_ollama_installed()
        
        # Check if Ollama service is running via supervisorctl
        is_running = False
        if is_installed:
            try:
                result = subprocess.run(['supervisorctl', 'status', 'ollama'], capture_output=True, text=True)
                is_running = result.returncode == 0 and 'RUNNING' in result.stdout
            except subprocess.CalledProcessError:
                # Fallback to pgrep if supervisorctl fails
                result = subprocess.run(['pgrep', '-f', 'ollama'], capture_output=True, text=True)
                is_running = result.returncode == 0
        
        # Try to connect to Ollama service (port 11434)
        ollama_api_available = False
        if is_running:
            try:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                ollama_api_available = response.status_code == 200
            except:
                pass
        
        # Check if HTTP API process is running (port 5001)
        http_api_process_id = None
        http_api_available = False
        
        # First check if we have a tracked process
        if http_api_process and http_api_process.poll() is None:
            http_api_process_id = http_api_process.pid
        else:
            # Check if any process is running on port 5001
            try:
                result = subprocess.run(['lsof', '-ti:5001'], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    http_api_process_id = int(result.stdout.strip().split('\n')[0])
            except:
                pass
        
        # Check if HTTP API is actually responding
        if http_api_process_id:
            try:
                response = requests.get('http://localhost:5001/status', timeout=3)
                http_api_available = response.status_code == 200
            except:
                pass
        
        return jsonify({
            'success': True,
            'status': {
                'installed': is_installed,
                'running': is_running,
                'ollama_api_available': ollama_api_available,
                'ollama_port': 11434,
                'http_api_available': http_api_available,
                'http_api_port': 5001,
                'install_required': not is_installed,
                'http_api_process_id': http_api_process_id
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def check_ollama_installed():
    """Check if Ollama is installed and properly configured"""
    try:
        # Check if ollama command exists and is executable
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        # Verify ollama binary is actually functional by checking version
        try:
            version_result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0 and 'ollama version' in version_result.stdout.lower():
                return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        # Fallback: check for supervisor config file (Linux systems)
        if os.path.exists('/etc/supervisor/conf.d/supervisord.conf'):
            return True
        
        # Fallback: if binary exists and is executable, consider it installed
        ollama_path = result.stdout.strip()
        if ollama_path and os.path.isfile(ollama_path) and os.access(ollama_path, os.X_OK):
            return True
                
        return False
        
    except Exception:
        return False

def install_ollama():
    """Install Ollama on the system"""
    import time
    
    try:
        # Check if already installed
        if check_ollama_installed():
            return jsonify({
                'success': True,
                'message': 'Ollama is already installed',
                'already_installed': True
            })
        
        # Get OS type
        os_type = platform.system().lower()
        
        if os_type == 'linux':
            # Install on Linux using official script
            # Simulate progress by adding small delays
            time.sleep(1)  # Simulate download time
            
            result = subprocess.run(
                ['curl', '-fsSL', 'https://ollama.com/install.sh'],
                capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                # Simulate installation progress
                time.sleep(2)
                
                # Run the install script
                install_result = subprocess.run(
                    ['bash', '-c', result.stdout],
                    capture_output=True, text=True, timeout=600
                )
                
                if install_result.returncode == 0:                    
                    return jsonify({
                        'success': True,
                        'message': 'Ollama installed and started successfully',
                        'progress': 100
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'Installation failed: {install_result.stderr}',
                        'progress': 0
                    })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Failed to download installer: {result.stderr}',
                    'progress': 0
                })
                
        elif os_type == 'darwin':  # macOS
            return jsonify({
                'success': True,
                'message': 'Please download and install Ollama manually from https://ollama.com/download',
                'manual_install': True,
                'progress': 0
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Unsupported operating system: {os_type}. Please install manually from https://ollama.com/download',
                'unsupported_os': True,
                'progress': 0
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Installation timeout. Please try again or install manually.',
            'progress': 0
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'progress': 0
        })

def start_ollama_service():
    """Start Ollama service using supervisorctl"""
    try:
        # Check if Ollama is installed
        if not check_ollama_installed():
            return jsonify({
                'success': False,
                'message': 'Ollama is not installed. Please install it first.'
            })
        
        add_ollama_to_supervisord()      
        # Try to kill existing ollama processes (ignore if none exist)
        try:
            # Use pkill instead of killall for better macOS compatibility
            subprocess.run(['pkill', '-f', 'ollama'], check=False)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # No ollama processes running or pkill not found, which is fine
            pass
        # Reload supervisord configuration
        subprocess.run(['supervisorctl', 'reread'], check=True)
        subprocess.run(['supervisorctl', 'update'], check=True)

        # Start Ollama service via supervisorctl
        result = subprocess.run(['supervisorctl', 'start', 'ollama'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Ollama service started successfully'
            })
        else:
            # Fallback: try to start manually
            try:
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return jsonify({
                    'success': True,
                    'message': 'Ollama service started manually'
                })
            except Exception:
                return jsonify({
                    'success': False,
                    'message': f'Failed to start Ollama service: {result.stderr}'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting Ollama service: {str(e)}'
        })

def stop_ollama_service():
    """Stop Ollama service using supervisorctl"""
    try:
        # Stop Ollama service via supervisorctl
        result = subprocess.run(['supervisorctl', 'stop', 'ollama'], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'Ollama service stopped successfully'
            })
        else:
            # Fallback: try to kill process
            try:
                subprocess.run(['pkill', '-f', 'ollama'], check=True)
                return jsonify({
                    'success': True,
                    'message': 'Ollama service stopped manually'
                })
            except subprocess.CalledProcessError:
                return jsonify({
                    'success': False,
                    'message': f'Failed to stop Ollama service: {result.stderr}'
                })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping Ollama service: {str(e)}'
        })

def add_ollama_to_supervisord():
    supervisord_conf = '/etc/supervisor/conf.d/supervisord.conf'
    
    # Cek dulu isi file apakah sudah ada konfigurasi ollama
    if os.path.exists(supervisord_conf):
        with open(supervisord_conf, 'r') as f:
            content = f.read()
        if '[program:ollama]' in content:
            print('Ollama config already exists in supervisord.conf, skipping.')
            return
    else:
        content = ''
    
    try:
        # Cek user ollama
        try:
            subprocess.run(['id', 'ollama'], capture_output=True, check=True)
            user = 'ollama'
            home_dir = '/usr/share/ollama'
        except subprocess.CalledProcessError:
            user = 'root'
            home_dir = '/root'
        
        ollama_config = f"""[program:ollama]
command=/usr/local/bin/ollama serve
user={user}
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/ollama.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=OLLAMA_HOST="0.0.0.0:11434",HOME="{home_dir}",PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
"""
        with open(supervisord_conf, 'a') as f:
            f.write(ollama_config)
        
        print(f'Added Ollama config to {supervisord_conf}')
        
    except Exception as e:
        raise Exception(f'Failed to update supervisord.conf: {e}')

def install_ollama_stream():
    """Install Ollama with real-time progress streaming"""
    def generate_progress():
        try:
            # Check if already installed
            if check_ollama_installed():
                yield f"data: {{\"progress\": 100, \"message\": \"Ollama is already installed\", \"success\": true, \"already_installed\": true}}\n\n"
                return
            
            # Get OS type
            os_type = platform.system().lower()
            
            if os_type == 'linux':
                # Step 1: Download installer
                yield f"data: {{\"progress\": 10, \"message\": \"Downloading Ollama installer...\", \"success\": false}}\n\n"
                time.sleep(1)
                
                result = subprocess.run(
                    ['curl', '-fsSL', 'https://ollama.com/install.sh'],
                    capture_output=True, text=True, timeout=300
                )
                
                if result.returncode != 0:
                    yield f"data: {{\"progress\": 0, \"message\": \"Failed to download installer: {result.stderr}\", \"success\": false}}\n\n"
                    return
                
                # Step 2: Running installer
                yield f"data: {{\"progress\": 30, \"message\": \"Running Ollama installer...\", \"success\": false}}\n\n"
                time.sleep(1)
                
                # Run the install script with real-time output
                process = subprocess.Popen(
                    ['bash', '-c', result.stdout],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                progress = 30
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress = min(progress + 5, 80)
                        clean_output = output.strip().replace('"', '\\"')
                        yield f"data: {{\"progress\": {progress}, \"message\": \"Installing: {clean_output}\", \"success\": false}}\n\n"
                        time.sleep(0.5)
                
                if process.returncode == 0:
                    # Step 3: Configure supervisord
                    yield f"data: {{\"progress\": 75, \"message\": \"Configuring supervisord for Ollama...\", \"success\": false}}\n\n"
                    time.sleep(1)
                    
                    try:
                        # Add Ollama configuration to supervisord.conf
                        add_ollama_to_supervisord()
                        yield f"data: {{\"progress\": 85, \"message\": \"Reloading supervisord configuration...\", \"success\": false}}\n\n"
                        
                        # Reload supervisord configuration
                        subprocess.run(['supervisorctl', 'reread'], check=True)
                        subprocess.run(['supervisorctl', 'update'], check=True)
                        
                        # Start Ollama service
                        yield f"data: {{\"progress\": 90, \"message\": \"Starting Ollama service...\", \"success\": false}}\n\n"
                        subprocess.run(['supervisorctl', 'start', 'ollama'], check=True)
                        time.sleep(2)
                        
                    except subprocess.CalledProcessError as e:
                        yield f"data: {{\"progress\": 80, \"message\": \"Warning: Could not configure supervisord: {str(e)}\", \"success\": false}}\n\n"
                    
                    yield f"data: {{\"progress\": 100, \"message\": \"Ollama installed and configured successfully!\", \"success\": true}}\n\n"
                else:
                    stderr_output = process.stderr.read().replace('"', '\\"')
                    yield f"data: {{\"progress\": 0, \"message\": \"Installation failed: {stderr_output}\", \"success\": false}}\n\n"
                    
            elif os_type == 'darwin':  # macOS
                yield f"data: {{\"progress\": 0, \"message\": \"Please download and install Ollama manually from https://ollama.com/download\", \"success\": true, \"manual_install\": true}}\n\n"
            else:
                yield f"data: {{\"progress\": 0, \"message\": \"Unsupported operating system: {os_type}. Please install manually from https://ollama.com/download\", \"success\": true, \"unsupported_os\": true}}\n\n"
                
        except subprocess.TimeoutExpired:
            yield f"data: {{\"progress\": 0, \"message\": \"Installation timeout. Please try again or install manually.\", \"success\": false}}\n\n"
        except Exception as e:
            yield f"data: {{\"progress\": 0, \"message\": \"Error: {str(e)}\", \"success\": false}}\n\n"
    
    return Response(generate_progress(), mimetype='text/plain')

def get_models():
    """Get list of installed models"""
    try:
        # Get configuration
        config_response = get_config()
        config_data = config_response.get_json()
        config = config_data.get('config', {})
        
        host = config.get('host', 'localhost')
        port = config.get('port', 11434)
        api_key = config.get('api_key', '')
        
        url = f'http://{host}:{port}/api/tags'
        headers = {'Content-Type': 'application/json'}
        
        # Add API key to headers if provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            # Format model data
            formatted_models = []
            for model in models:
                formatted_models.append({
                    'name': model.get('name', ''),
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', ''),
                    'digest': model.get('digest', '')
                })
            
            return jsonify({
                'success': True,
                'models': formatted_models
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to Ollama API'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def pull_model():
    """Pull/download a new model"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'success': False, 'message': 'Model name is required'})
        
        # Get configuration
        config_response = get_config()
        config_data = config_response.get_json()
        config = config_data.get('config', {})
        
        host = config.get('host', 'localhost')
        port = config.get('port', 11434)
        api_key = config.get('api_key', '')
        
        url = f'http://{host}:{port}/api/pull'
        headers = {'Content-Type': 'application/json'}
        
        # Add API key to headers if provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Start model pull process
        response = requests.post(
            url,
            json={'name': model_name},
            headers=headers,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} pulled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to pull model: {response.text}'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def delete_model():
    """Delete a model"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        
        if not model_name:
            return jsonify({'success': False, 'message': 'Model name is required'})
        
        # Get configuration
        config_response = get_config()
        config_data = config_response.get_json()
        config = config_data.get('config', {})
        
        host = config.get('host', 'localhost')
        port = config.get('port', 11434)
        api_key = config.get('api_key', '')
        
        url = f'http://{host}:{port}/api/delete'
        headers = {'Content-Type': 'application/json'}
        
        # Add API key to headers if provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        response = requests.delete(
            url,
            json={'name': model_name},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Model {model_name} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to delete model: {response.text}'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def generate_response():
    """Generate response using a model"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        prompt = data.get('prompt')
        stream = data.get('stream', False)
        
        if not model_name or not prompt:
            return jsonify({'success': False, 'message': 'Model and prompt are required'})
        
        # Get configuration
        config_response = get_config()
        config_data = config_response.get_json()
        config = config_data.get('config', {})
        
        host = config.get('host', 'localhost')
        port = config.get('port', 11434)
        api_key = config.get('api_key', '')
        keep_alive = config.get('keep_alive', '5m')
        
        url = f'http://{host}:{port}/api/generate'
        headers = {'Content-Type': 'application/json'}
        
        # Add API key to headers if provided
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
        
        if stream:
            # Streaming response
            def generate():
                try:
                    response = requests.post(
                        url,
                        json={
                            'model': model_name,
                            'prompt': prompt,
                            'stream': True,
                            'keep_alive': keep_alive
                        },
                        headers=headers,
                        stream=True,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line.decode('utf-8'))
                                    yield f"data: {json.dumps(chunk)}\n\n"
                                    if chunk.get('done', False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        yield f"data: {json.dumps({'error': f'Failed to generate response: {response.text}'})}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            return Response(generate(), mimetype='text/plain')
        else:
            # Non-streaming response
            response = requests.post(
                url,
                json={
                    'model': model_name,
                    'prompt': prompt,
                    'stream': False,
                    'keep_alive': keep_alive
                },
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    'success': True,
                    'response': result.get('response', ''),
                    'model': model_name
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Failed to generate response: {response.text}'
                })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_config():
    """Get Ollama configuration"""
    try:
        # Try to read from config files (system first, then user)
        config_files = [
            '/etc/ollama/config.json',
            os.path.expanduser('~/.ollama/config.json')
        ]
        
        config = {}
        
        # Load from config file if exists
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    break  # Use first found config file
                except:
                    continue
        
        # Set defaults from environment or fallback values
        config.setdefault('host', os.environ.get('OLLAMA_HOST', 'localhost'))
        config.setdefault('port', int(os.environ.get('OLLAMA_PORT', '11434')))
        config.setdefault('api_key', os.environ.get('OLLAMA_API_KEY', ''))
        config.setdefault('models_path', os.environ.get('OLLAMA_MODELS', '~/.ollama/models'))
        config.setdefault('keep_alive', os.environ.get('OLLAMA_KEEP_ALIVE', '5m'))
        config.setdefault('num_parallel', int(os.environ.get('OLLAMA_NUM_PARALLEL', '1')))
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def update_config():
    """Update Ollama configuration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No configuration data provided'})
        
        # Validate configuration data
        config = {
            'host': data.get('host', 'localhost'),
            'port': int(data.get('port', 11434)),
            'api_key': data.get('api_key', ''),
            'models_path': data.get('models_path', '~/.ollama/models'),
            'keep_alive': data.get('keep_alive', '5m'),
            'num_parallel': int(data.get('num_parallel', 1))
        }
        
        # Ensure config directory exists
        config_dir = '/etc/ollama'
        os.makedirs(config_dir, exist_ok=True)
        
        # Save configuration to file
        config_file = os.path.join(config_dir, 'config.json')
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set proper permissions
            os.chmod(config_file, 0o644)
            
        except PermissionError:
            # Fallback: save to user directory if system directory is not writable
            user_config_dir = os.path.expanduser('~/.ollama')
            os.makedirs(user_config_dir, exist_ok=True)
            config_file = os.path.join(user_config_dir, 'config.json')
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        # Update environment variables for current session
        os.environ['OLLAMA_HOST'] = config['host']
        os.environ['OLLAMA_PORT'] = str(config['port'])
        if config['api_key']:
            os.environ['OLLAMA_API_KEY'] = config['api_key']
        os.environ['OLLAMA_MODELS'] = config['models_path']
        os.environ['OLLAMA_KEEP_ALIVE'] = config['keep_alive']
        os.environ['OLLAMA_NUM_PARALLEL'] = str(config['num_parallel'])
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully',
            'config_file': config_file
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid configuration value: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to update configuration: {str(e)}'})

# Global variable to store HTTP API process
http_api_process = None
VENV_PYTHON = "/opt/slemp-venv/bin/python3"
VENV_PIP = "/opt/slemp-venv/bin/pip"

def start_http_api():
    """Start the HTTP API server"""
    global http_api_process

    try:
        # Install Flask + Requests di venv kalau belum ada
        try:
            subprocess.run(
                [VENV_PIP, "install", "--upgrade", "flask", "requests"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({
                'success': False,
                'message': f'Failed to install Flask: {e.stderr.decode() if e.stderr else str(e)}'
            })

        # Check if API is already running
        if http_api_process and http_api_process.poll() is None:
            return jsonify({
                'success': False,
                'message': 'HTTP API is already running'
            })

        # Get api.py
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        api_file = os.path.join(plugin_dir, 'api.py')

        if not os.path.exists(api_file):
            return jsonify({
                'success': False,
                'message': f'API file not found: {api_file}'
            })

        # Start API pakai python dari venv
        http_api_process = subprocess.Popen(
            [VENV_PYTHON, api_file],
            cwd=plugin_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if platform.system() != 'Windows' else None
        )

        time.sleep(1)

        if http_api_process.poll() is None:
            return jsonify({
                'success': True,
                'message': 'HTTP API started successfully on port 5001',
                'process_id': http_api_process.pid
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to start HTTP API (process exited immediately)'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting HTTP API: {str(e)}'
        })

def stop_http_api():
    """Stop the HTTP API server"""
    global http_api_process
    
    try:
        data = request.get_json() or {}
        process_id = data.get('process_id')
        
        if not process_id:
            return jsonify({
                'success': False,
                'message': 'Process ID is required'
            })
        
        # Use PID directly
        try:
            pid = int(process_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid process ID format'
            })
        
        # Try to kill the process
        try:
            os.kill(pid, 9)  # SIGKILL
            http_api_process = None
            return jsonify({
                'success': True,
                'message': 'HTTP API stopped successfully'
            })
        except ProcessLookupError:
            return jsonify({
                'success': True,
                'message': 'Process already stopped'
            })
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Permission denied to stop the process'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping HTTP API: {str(e)}'
        })

if __name__ == '__main__':
    # For testing purposes
    print("Ollama Plugin loaded successfully")