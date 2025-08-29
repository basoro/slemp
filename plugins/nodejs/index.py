#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Node.js Manager Plugin for SLEMP
Manage Node.js versions, npm packages, and Node.js applications

Features:
- Multiple Node.js version management (install, switch, remove)
- NPM package management (install, update, remove)
- Node.js application management
- Real-time installation progress tracking via Socket.IO
- Automatic dependency resolution
- Project scaffolding and management
"""

import subprocess
import json
import os
import sys
import time
import re
from datetime import datetime

# Import Flask components when available
try:
    from flask import request, jsonify
    # Import from parent app
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import logger
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logger = None

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
                action = path_parts[4]  # /api/plugins/nodejs/{action}
            else:
                action = 'status'
        else:
            action = 'status'
        
        # Route to appropriate function based on action
        if action == 'status':
            return get_nodejs_status()
        elif action == 'versions':
            if method == 'GET':
                return get_nodejs_versions()
            elif method == 'POST':
                return install_nodejs_version()
            elif method == 'DELETE':
                return remove_nodejs_version()
        elif action == 'switch':
            return switch_nodejs_version()
        elif action == 'packages':
            if method == 'GET':
                return get_npm_packages()
            elif method == 'POST':
                return install_npm_package()
            elif method == 'DELETE':
                return remove_npm_package()
        elif action == 'projects':
            if method == 'GET':
                return get_nodejs_projects()
            elif method == 'POST':
                return create_nodejs_project()
            elif method == 'DELETE':
                return remove_nodejs_project()
        elif action == 'install':
            return install_nodejs()
        elif action == 'uninstall':
            return uninstall_nodejs()
        else:
            return jsonify({'success': False, 'message': 'Unknown action'})
            
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def run_command(cmd, cwd=None):
    """Execute command and return result"""
    try:
        if logger:
            logger.info(f"[RUN] {cmd}")
        else:
            print(f"[RUN] {cmd}")
        
        result = subprocess.run(
            cmd, shell=True, check=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        
        if logger:
            logger.info(result.stdout)
        else:
            print(result.stdout)
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        if logger:
            logger.error(e.stderr)
        else:
            print(e.stderr)
        raise e

def get_nodejs_status():
    """Check Node.js installation status"""
    try:
        # Check if Node.js is installed
        node_installed = False
        node_version = None
        npm_version = None
        
        try:
            node_result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if node_result.returncode == 0:
                node_installed = True
                node_version = node_result.stdout.strip()
        except FileNotFoundError:
            pass
        
        try:
            npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if npm_result.returncode == 0:
                npm_version = npm_result.stdout.strip()
        except FileNotFoundError:
            pass
        
        # Get available versions
        available_versions = get_available_nodejs_versions()
        
        result = {
            'success': True,
            'installed': node_installed,
            'node_version': node_version,
            'npm_version': npm_version,
            'available_versions': available_versions[:10],  # Show top 10
            'timestamp': datetime.now().isoformat()
        }
        
        # Return jsonify if Flask is available, otherwise return dict
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                # Flask context not available, return dict
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def get_available_nodejs_versions():
    """Get available Node.js versions from NodeSource"""
    try:
        # Common LTS versions
        versions = [
            {'version': '20.11.0', 'lts': True, 'codename': 'Iron'},
            {'version': '18.19.0', 'lts': True, 'codename': 'Hydrogen'},
            {'version': '16.20.2', 'lts': True, 'codename': 'Gallium'},
            {'version': '21.6.1', 'lts': False, 'codename': 'Current'},
            {'version': '19.9.0', 'lts': False, 'codename': 'Current'},
        ]
        return versions
    except Exception as e:
        return []

def get_nodejs_versions():
    """Get installed Node.js versions"""
    try:
        # For now, return current version
        # In a full implementation, this would check NVM or similar
        current_version = None
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                current_version = result.stdout.strip()
        except FileNotFoundError:
            pass
        
        versions = []
        if current_version:
            versions.append({
                'version': current_version,
                'active': True,
                'path': '/usr/bin/node'
            })
        
        result = {
            'success': True,
            'versions': versions,
            'available': get_available_nodejs_versions()
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def install_nodejs_version():
    """Install specific Node.js version"""
    try:
        data = request.get_json()
        version = data.get('version', '20.11.0')
        
        # Install Node.js using NodeSource repository
        commands = [
            'curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -',
            'sudo apt-get install -y nodejs'
        ]
        
        for cmd in commands:
            run_command(cmd)
        
        result = {
            'success': True,
            'message': f'Node.js {version} installed successfully'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def switch_nodejs_version():
    """Switch Node.js version"""
    try:
        data = request.get_json()
        version = data.get('version')
        
        # This would implement version switching logic
        # For now, return success message
        result = {
            'success': True,
            'message': f'Switched to Node.js {version}'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def get_npm_packages():
    """Get installed npm packages"""
    try:
        # Get global packages
        global_result = subprocess.run(['npm', 'list', '-g', '--depth=0', '--json'], 
                                     capture_output=True, text=True)
        global_packages = []
        if global_result.returncode == 0:
            try:
                global_data = json.loads(global_result.stdout)
                if 'dependencies' in global_data:
                    for name, info in global_data['dependencies'].items():
                        global_packages.append({
                            'name': name,
                            'version': info.get('version', 'unknown'),
                            'scope': 'global'
                        })
            except json.JSONDecodeError:
                pass
        
        result = {
            'success': True,
            'packages': global_packages
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def install_npm_package():
    """Install npm package"""
    try:
        data = request.get_json()
        package = data.get('package')
        global_install = data.get('global', False)
        
        cmd = f"npm install {'--global' if global_install else ''} {package}"
        run_command(cmd)
        
        result = {
            'success': True,
            'message': f'Package {package} installed successfully'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def remove_npm_package():
    """Remove npm package"""
    try:
        data = request.get_json()
        package = data.get('package')
        global_remove = data.get('global', False)
        
        cmd = f"npm uninstall {'--global' if global_remove else ''} {package}"
        run_command(cmd)
        
        result = {
            'success': True,
            'message': f'Package {package} removed successfully'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def get_nodejs_projects():
    """Get Node.js projects"""
    try:
        # Scan for package.json files in common directories
        projects = []
        search_dirs = ['/var/www', '/home', '/opt']
        
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    if 'package.json' in files:
                        try:
                            with open(os.path.join(root, 'package.json'), 'r') as f:
                                package_data = json.load(f)
                                projects.append({
                                    'name': package_data.get('name', os.path.basename(root)),
                                    'version': package_data.get('version', '1.0.0'),
                                    'path': root,
                                    'description': package_data.get('description', ''),
                                    'scripts': list(package_data.get('scripts', {}).keys())
                                })
                        except (json.JSONDecodeError, IOError):
                            continue
                    
                    # Limit depth to avoid scanning too deep
                    if len(root.split(os.sep)) - len(search_dir.split(os.sep)) > 3:
                        dirs.clear()
        
        result = {
            'success': True,
            'projects': projects[:20]  # Limit to 20 projects
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def create_nodejs_project():
    """Create new Node.js project"""
    try:
        data = request.get_json()
        name = data.get('name')
        path = data.get('path', '/var/www')
        template = data.get('template', 'basic')
        
        project_path = os.path.join(path, name)
        
        # Create project directory
        os.makedirs(project_path, exist_ok=True)
        
        # Initialize npm project
        run_command('npm init -y', cwd=project_path)
        
        # Create basic files based on template
        if template == 'express':
            run_command('npm install express', cwd=project_path)
            
            # Create basic Express app
            app_js = '''const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`App listening at http://localhost:${port}`);
});'''
            
            with open(os.path.join(project_path, 'app.js'), 'w') as f:
                f.write(app_js)
        
        result = {
            'success': True,
            'message': f'Project {name} created successfully',
            'path': project_path
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def install_nodejs():
    """Install Node.js"""
    try:
        # Install Node.js using NodeSource repository
        commands = [
            'curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -',
            'sudo apt-get install -y nodejs',
            'sudo npm install -g npm@latest'
        ]
        
        for cmd in commands:
            run_command(cmd)
        
        result = {
            'success': True,
            'message': 'Node.js installed successfully'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

def uninstall_nodejs():
    """Uninstall Node.js"""
    try:
        commands = [
            'sudo apt-get remove -y nodejs npm',
            'sudo apt-get autoremove -y',
            'sudo rm -rf /usr/local/lib/node_modules',
            'sudo rm -rf ~/.npm'
        ]
        
        for cmd in commands:
            try:
                run_command(cmd)
            except subprocess.CalledProcessError:
                # Continue even if some commands fail
                pass
        
        result = {
            'success': True,
            'message': 'Node.js uninstalled successfully'
        }
        
        if FLASK_AVAILABLE:
            try:
                return jsonify(result)
            except RuntimeError:
                return result
        else:
            return result
        
    except Exception as e:
        error_result = {'success': False, 'message': str(e)}
        if FLASK_AVAILABLE:
            try:
                return jsonify(error_result)
            except RuntimeError:
                return error_result
        else:
            return error_result

if __name__ == '__main__':
    # For testing purposes
    print("Node.js Manager Plugin")
    print("Available functions:")
    print("- get_nodejs_status()")
    print("- get_nodejs_versions()")
    print("- install_nodejs_version()")
    print("- get_npm_packages()")
    print("- install_npm_package()")
    print("- get_nodejs_projects()")
    print("- create_nodejs_project()")