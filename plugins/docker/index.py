#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker Manager Plugin for SLEMP
Manage Docker containers, images, networks, and volumes

Features:
- Automatic Docker installation with robust GPG key handling
- Real-time installation progress tracking via Socket.IO
- Automatic GPG error detection and fixing (NO_PUBKEY 7EA0A9C3F273FCD8)
- Dynamic Ubuntu codename detection for repository setup
- Retry mechanisms for network and repository issues
- Container, image, network, and volume management
- System cleanup and monitoring capabilities

GPG Error Handling:
This plugin includes advanced GPG error handling that automatically:
- Detects Docker repository GPG key issues
- Downloads and imports fresh GPG keys
- Reconfigures repository settings
- Retries failed operations after applying fixes
"""

import subprocess
import json
import os
import sys
import time
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

def run_command_with_gpg_fix(cmd, retries=3):
    """Execute command with automatic GPG error handling
    
    This function automatically detects and fixes Docker GPG key issues:
    - Detects NO_PUBKEY 7EA0A9C3F273FCD8 errors
    - Detects repository signature verification failures
    - Detects GPG key verification failures
    - Detects corrupted GPG key files
    - Automatically calls fix_docker_gpg() to resolve issues
    - Retries the command after applying fixes
    
    Args:
        cmd (str): Command to execute
        retries (int): Number of retry attempts after GPG fix
    
    Returns:
        str: Command output on success
        
    Raises:
        SystemExit: If command fails after all retries and fixes
    """
    for i in range(retries + 1):
        try:
            if logger:
                logger.info(f"[RUN] {cmd}")
            else:
                print(f"[RUN] {cmd}")
            
            result = subprocess.run(
                cmd, shell=True, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            
            if logger:
                logger.info(result.stdout)
            else:
                print(result.stdout)
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.lower() if e.stderr else ""
            stdout_msg = e.stdout.lower() if e.stdout else ""
            combined_output = error_msg + stdout_msg
            
            if logger:
                logger.error(e.stderr)
            else:
                print(e.stderr)
            
            # Enhanced GPG error detection
            gpg_errors = [
                "no_pubkey 7ea0a9c3f273fcd8",
                "no_pubkey",
                "not signed",
                "signature verification failed",
                "key verification failed",
                "repository is not signed",
                "gpg error",
                "gpg key verification failed",
                "corrupted gpg",
                "invalid gpg",
                "public key is not available"
            ]
            
            has_gpg_error = any(error in combined_output for error in gpg_errors)
                
            if has_gpg_error and i < retries:
                fix_msg = "⚠️ GPG error detected. Applying comprehensive Docker GPG fix..."
                if logger:
                    logger.warning(fix_msg)
                else:
                    print(fix_msg)
                fix_docker_gpg()
                time.sleep(3)  # Wait before retry
                continue  # retry after fix
                
            if i < retries:
                retry_msg = f"Retrying... (attempt {i+2}/{retries+1})"
                if logger:
                    logger.info(retry_msg)
                else:
                    print(retry_msg)
                time.sleep(2)
            else:
                final_error = f"Command failed after {retries+1} attempts: {cmd}"
                if logger:
                    logger.error(final_error)
                else:
                    print(final_error)
                sys.exit(1)


def fix_docker_gpg():
    """Fix Docker GPG key issues with dynamic codename detection
    
    This function provides a comprehensive fix for Docker GPG key problems:
    - Removes corrupted or outdated GPG keys and repository files
    - Downloads fresh GPG key from Docker's official repository with multiple methods
    - Properly imports the key using gpg --dearmor
    - Dynamically detects Ubuntu codename for correct repository setup
    - Cleans apt cache thoroughly to prevent conflicts
    - Sets proper file permissions
    - Verifies GPG key file integrity
    
    This addresses common errors like:
    - NO_PUBKEY 7EA0A9C3F273FCD8
    - Repository signature verification failures
    - Outdated or corrupted GPG keys
    - GPG key verification failures
    """
    try:
        # Use logger if available, otherwise fallback to print
        def log_info(msg):
            if logger:
                logger.info(msg)
            else:
                print(f"INFO: {msg}")
                
        def log_error(msg):
            if logger:
                logger.error(msg)
            else:
                print(f"ERROR: {msg}")
        
        log_info("Starting comprehensive Docker GPG key fix process...")
        
        # Remove all existing Docker-related keys and repositories
        log_info("Removing all existing Docker GPG keys and repository files...")
        subprocess.run(['rm', '-f', '/etc/apt/keyrings/docker.gpg'], capture_output=True, text=True)
        subprocess.run(['rm', '-f', '/usr/share/keyrings/docker-archive-keyring.gpg'], capture_output=True, text=True)
        subprocess.run(['rm', '-f', '/etc/apt/sources.list.d/docker.list'], capture_output=True, text=True)
        subprocess.run(['rm', '-f', '/etc/apt/sources.list.d/docker.list.save'], capture_output=True, text=True)
        
        # Clean apt cache thoroughly
        log_info("Cleaning apt cache thoroughly...")
        subprocess.run(['apt-get', 'clean'], capture_output=True, text=True)
        subprocess.run(['rm', '-rf', '/var/lib/apt/lists/*'], capture_output=True, text=True)
        
        # Get Ubuntu codename dynamically
        log_info("Detecting Ubuntu codename...")
        try:
            codename_result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
            if codename_result.returncode == 0:
                codename = codename_result.stdout.strip()
            else:
                # Fallback: try to detect codename from /etc/os-release
                try:
                    with open('/etc/os-release', 'r') as f:
                        os_release = f.read()
                        if 'VERSION_CODENAME=' in os_release:
                            for line in os_release.split('\n'):
                                if line.startswith('VERSION_CODENAME='):
                                    codename = line.split('=')[1].strip('"')
                                    break
                        else:
                            codename = 'focal'  # Default fallback
                except Exception:
                    codename = 'focal'  # Safe fallback
        except Exception:
            codename = 'focal'  # Safe fallback
        
        log_info(f"Using Ubuntu codename: {codename}")
        
        # Create keyrings directory
        log_info("Creating keyrings directory...")
        subprocess.run(['mkdir', '-p', '/etc/apt/keyrings'], capture_output=True, text=True)
        
        # Try multiple methods to download and import Docker's GPG key
        log_info("Downloading Docker GPG key with robust method...")
        
        # Method 1: Direct curl and gpg dearmor pipeline
        method1_result = subprocess.run([
            'bash', '-c', 
            'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg'
        ], capture_output=True, text=True)
        
        if method1_result.returncode == 0 and os.path.exists('/etc/apt/keyrings/docker.gpg') and os.path.getsize('/etc/apt/keyrings/docker.gpg') > 0:
            log_info("GPG key imported successfully using method 1")
        else:
            log_info("Method 1 failed, trying method 2...")
            
            # Method 2: Download first, then import
            key_download = subprocess.run([
                'curl', '-fsSL', 'https://download.docker.com/linux/ubuntu/gpg'
            ], capture_output=True, text=True)
            
            if key_download.returncode != 0:
                log_error(f"Failed to download GPG key: {key_download.stderr}")
                raise Exception(f"GPG key download failed: {key_download.stderr}")
            
            # Import GPG key
            log_info("Importing Docker GPG key...")
            import_result = subprocess.run([
                'gpg', '--dearmor', '-o', '/etc/apt/keyrings/docker.gpg'
            ], input=key_download.stdout, text=True, capture_output=True)
            
            if import_result.returncode != 0:
                log_error(f"Failed to import GPG key: {import_result.stderr}")
                raise Exception(f"GPG key import failed: {import_result.stderr}")
        
        # Verify the key file exists and has content
        if not os.path.exists('/etc/apt/keyrings/docker.gpg'):
            raise Exception("GPG key file was not created")
        
        if os.path.getsize('/etc/apt/keyrings/docker.gpg') == 0:
            raise Exception("GPG key file is empty")
        
        # Set proper permissions
        log_info("Setting GPG key permissions...")
        subprocess.run(['chmod', 'a+r', '/etc/apt/keyrings/docker.gpg'], capture_output=True, text=True)
        
        # Add Docker repository
        log_info("Adding Docker repository...")
        repo_line = f"deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {codename} stable"
        with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
            f.write(repo_line + '\n')
        
        # Update package lists
        log_info("Updating package lists...")
        update_result = subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
        
        if update_result.returncode != 0:
            log_error(f"Package list update failed: {update_result.stderr}")
            raise Exception(f"Package list update failed: {update_result.stderr}")
        
        log_info("Docker GPG key fix completed successfully")
        
    except Exception as e:
        error_msg = f"Docker GPG fix failed: {str(e)}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)
        sys.exit(1)


def run_command(cmd, timeout=30):
    """Execute shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip(),
            'code': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': f'Command timed out after {timeout} seconds',
            'code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'code': -1
        }

def run_command_with_progress(cmd, timeout=300):
    """Run a command with longer timeout for installation processes"""
    return run_command(cmd, timeout)

def check_docker_status():
    """Check if Docker is installed and running"""
    # Check if Docker is installed
    docker_check = run_command('which docker')
    if not docker_check['success']:
        return {
            'installed': False,
            'running': False,
            'version': None,
            'message': 'Docker is not installed'
        }
    
    # Check Docker version
    version_result = run_command('docker --version')
    version = version_result['output'] if version_result['success'] else 'Unknown'
    
    # Check if Docker daemon is running
    status_result = run_command('docker info')
    running = status_result['success']
    
    return {
        'installed': True,
        'running': running,
        'version': version,
        'message': 'Docker is running' if running else 'Docker daemon is not running'
    }

def get_containers():
    """Get list of all Docker containers"""
    cmd = 'docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}" --no-trunc'
    result = run_command(cmd)
    
    if not result['success']:
        return {'success': False, 'error': result['error'], 'containers': []}
    
    containers = []
    lines = result['output'].split('\n')
    
    # Debug: log raw output
    if logger:
        logger.info(f"Docker ps output: {repr(result['output'])}")
        logger.info(f"Number of lines: {len(lines)}")
        for i, line in enumerate(lines):
            logger.info(f"Line {i}: {repr(line)}")
    
    if len(lines) > 1:  # Skip header
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                # Split by tab, but handle cases where tabs might be spaces
                parts = line.split('\t')
                if len(parts) < 7:
                    # Try splitting by multiple spaces if tab split doesn't work
                    import re
                    parts = re.split(r'\s{2,}', line.strip())
                
                if logger:
                    logger.info(f"Line {i} parts ({len(parts)}): {parts}")
                
                if len(parts) >= 7:
                    containers.append({
                        'id': parts[0][:12],
                        'image': parts[1],
                        'command': parts[2][:50] + '...' if len(parts[2]) > 50 else parts[2],
                        'created': parts[3],
                        'status': parts[4],
                        'ports': parts[5],
                        'name': parts[6]
                    })
                elif len(parts) >= 6:
                    # Handle case where ports might be empty
                    containers.append({
                        'id': parts[0][:12],
                        'image': parts[1],
                        'command': parts[2][:50] + '...' if len(parts[2]) > 50 else parts[2],
                        'created': parts[3],
                        'status': parts[4],
                        'ports': '',
                        'name': parts[5]
                    })
    
    if logger:
        logger.info(f"Parsed {len(containers)} containers")
    
    return {'success': True, 'containers': containers}

def get_images():
    """Get list of Docker images"""
    cmd = 'docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}" --no-trunc'
    result = run_command(cmd)
    
    if not result['success']:
        return {'success': False, 'error': result['error'], 'images': []}
    
    images = []
    lines = result['output'].split('\n')
    
    # Debug: log raw output
    if logger:
        logger.info(f"Docker images output: {repr(result['output'])}")
        logger.info(f"Number of lines: {len(lines)}")
        for i, line in enumerate(lines):
            logger.info(f"Line {i}: {repr(line)}")
    
    if len(lines) > 1:  # Skip header
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                # Split by tab, but handle cases where tabs might be spaces
                parts = line.split('\t')
                if len(parts) < 5:
                    # Try splitting by multiple spaces if tab split doesn't work
                    import re
                    parts = re.split(r'\s{2,}', line.strip())
                
                if logger:
                    logger.info(f"Line {i} parts ({len(parts)}): {parts}")
                
                if len(parts) >= 5:
                    images.append({
                        'repository': parts[0],
                        'tag': parts[1],
                        'id': parts[2][:12],
                        'created': parts[3],
                        'size': parts[4]
                    })
    
    if logger:
        logger.info(f"Parsed {len(images)} images")
    
    return {'success': True, 'images': images}

def get_networks():
    """Get list of Docker networks"""
    cmd = 'docker network ls --format "table {{.ID}}\t{{.Name}}\t{{.Driver}}\t{{.Scope}}" --no-trunc'
    result = run_command(cmd)
    
    if not result['success']:
        return {'success': False, 'error': result['error'], 'networks': []}
    
    networks = []
    lines = result['output'].split('\n')
    
    # Debug: log raw output
    if logger:
        logger.info(f"Docker networks output: {repr(result['output'])}")
        logger.info(f"Number of lines: {len(lines)}")
    
    if len(lines) > 1:  # Skip header
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                # Split by tab, but handle cases where tabs might be spaces
                parts = line.split('\t')
                if len(parts) < 4:
                    # Try splitting by multiple spaces if tab split doesn't work
                    import re
                    parts = re.split(r'\s{2,}', line.strip())
                
                if logger:
                    logger.info(f"Line {i} parts ({len(parts)}): {parts}")
                
                if len(parts) >= 4:
                    networks.append({
                        'id': parts[0][:12],
                        'name': parts[1],
                        'driver': parts[2],
                        'scope': parts[3]
                    })
    
    if logger:
        logger.info(f"Parsed {len(networks)} networks")
    
    return {'success': True, 'networks': networks}

def get_volumes():
    """Get list of Docker volumes"""
    cmd = 'docker volume ls --format "table {{.Driver}}\t{{.Name}}"'
    result = run_command(cmd)
    
    if not result['success']:
        return {'success': False, 'error': result['error'], 'volumes': []}
    
    volumes = []
    lines = result['output'].split('\n')
    
    # Debug: log raw output
    if logger:
        logger.info(f"Docker volumes output: {repr(result['output'])}")
        logger.info(f"Number of lines: {len(lines)}")
    
    if len(lines) > 1:  # Skip header
        for i, line in enumerate(lines[1:], 1):
            if line.strip():
                # Split by tab, but handle cases where tabs might be spaces
                parts = line.split('\t')
                if len(parts) < 2:
                    # Try splitting by multiple spaces if tab split doesn't work
                    import re
                    parts = re.split(r'\s{2,}', line.strip())
                
                if logger:
                    logger.info(f"Line {i} parts ({len(parts)}): {parts}")
                
                if len(parts) >= 2:
                    volumes.append({
                        'driver': parts[0],
                        'name': parts[1]
                    })
    
    if logger:
        logger.info(f"Parsed {len(volumes)} volumes")
    
    return {'success': True, 'volumes': volumes}

def container_action(container_id, action):
    """Perform action on container (start, stop, restart, remove)"""
    valid_actions = ['start', 'stop', 'restart', 'remove', 'pause', 'unpause']
    
    if action not in valid_actions:
        return {'success': False, 'error': f'Invalid action: {action}'}
    
    if action == 'remove':
        cmd = f'docker rm -f {container_id}'
    else:
        cmd = f'docker {action} {container_id}'
    
    result = run_command(cmd)
    
    return {
        'success': result['success'],
        'message': f'Container {action} successful' if result['success'] else result['error']
    }

def image_action(image_id, action):
    """Perform action on image (remove)"""
    if action == 'remove':
        cmd = f'docker rmi -f {image_id}'
        result = run_command(cmd)
        
        return {
            'success': result['success'],
            'message': 'Image removed successfully' if result['success'] else result['error']
        }
    
    return {'success': False, 'error': f'Invalid action: {action}'}

def network_action(network_id, action):
    """Perform action on network (remove)"""
    if action == 'remove':
        cmd = f'docker network rm {network_id}'
        result = run_command(cmd)
        
        return {
            'success': result['success'],
            'message': 'Network removed successfully' if result['success'] else result['error']
        }
    
    return {'success': False, 'error': f'Invalid action: {action}'}

def volume_action(volume_name, action):
    """Perform action on volume (remove)"""
    if action == 'remove':
        cmd = f'docker volume rm {volume_name}'
        result = run_command(cmd)
        
        return {
            'success': result['success'],
            'message': 'Volume removed successfully' if result['success'] else result['error']
        }
    
    return {'success': False, 'error': f'Invalid action: {action}'}

def pull_image(image_name):
    """Pull Docker image"""
    cmd = f'docker pull {image_name}'
    result = run_command(cmd)
    
    return {
        'success': result['success'],
        'message': f'Image {image_name} pulled successfully' if result['success'] else result['error']
    }

def create_container(image, name=None, ports=None, volumes=None, env_vars=None):
    """Create new Docker container"""
    cmd = 'docker run -d'
    
    if name:
        cmd += f' --name {name}'
    
    if ports:
        for port_mapping in ports:
            cmd += f' -p {port_mapping}'
    
    if volumes:
        for volume_mapping in volumes:
            cmd += f' -v {volume_mapping}'
    
    if env_vars:
        for env_var in env_vars:
            cmd += f' -e {env_var}'
    
    cmd += f' {image}'
    
    result = run_command(cmd)
    
    return {
        'success': result['success'],
        'message': 'Container created successfully' if result['success'] else result['error'],
        'container_id': result['output'][:12] if result['success'] else None
    }

def get_container_logs(container_id, lines=100):
    """Get container logs"""
    cmd = f'docker logs --tail {lines} {container_id}'
    result = run_command(cmd)
    
    return {
        'success': result['success'],
        'logs': result['output'] if result['success'] else result['error']
    }

def get_system_info():
    """Get Docker system information"""
    info_result = run_command('docker system df')
    version_result = run_command('docker version --format json')
    
    system_info = {
        'disk_usage': info_result['output'] if info_result['success'] else 'Unable to get disk usage',
        'version_info': {}
    }
    
    if version_result['success']:
        try:
            version_data = json.loads(version_result['output'])
            system_info['version_info'] = version_data
        except json.JSONDecodeError:
            system_info['version_info'] = {'error': 'Unable to parse version info'}
    
    return system_info

def cleanup_system():
    """Clean up Docker system (remove unused containers, networks, images)"""
    # First check if Docker is available
    docker_status = check_docker_status()
    if not docker_status.get('installed', False):
        return {
            'success': False,
            'message': 'Docker is not installed',
            'details': 'Please install Docker first before attempting cleanup'
        }
    
    if not docker_status.get('running', False):
        return {
            'success': False,
            'message': 'Docker is not running',
            'details': 'Please start Docker service before attempting cleanup'
        }
    
    cmd = 'docker system prune -f'
    result = run_command(cmd)
    
    return {
        'success': result['success'],
        'message': 'System cleanup completed' if result['success'] else result['error'],
        'details': result['output'] if result['success'] else result['error']
    }

def install_docker_package():
    """Install Docker package using apt-get for Ubuntu Linux
    
    This function implements a robust Docker installation process that:
    - Handles GPG key import issues by using proper dearmoring
    - Includes retry mechanisms for package list updates
    - Provides fallback methods for Ubuntu codename detection
    - Cleans apt cache to prevent repository conflicts
    - Uses run_command_with_gpg_fix() for automatic GPG error detection and fixing
    - Automatically retries critical commands after applying GPG fixes
    
    The integration with run_command_with_gpg_fix() provides:
    - Automatic detection of NO_PUBKEY 7EA0A9C3F273FCD8 errors
    - Automatic repository signature verification error handling
    - Dynamic GPG key refresh and repository reconfiguration
    - Seamless retry mechanism after applying fixes
    """
    try:
        # Check if Docker is already installed
        check_result = subprocess.run(['which', 'docker'], capture_output=True, text=True)
        if check_result.returncode == 0:
            return {'success': True, 'message': 'Docker is already installed'}
        
        # Update package list with automatic GPG error handling
        # This will automatically detect and fix GPG key issues if they occur
        try:
            run_command_with_gpg_fix('env DEBIAN_FRONTEND=noninteractive apt-get update', retries=2)
        except SystemExit:
            return {'success': False, 'error': 'Failed to update package list after GPG fixes'}
        
        # Install required packages
        prereq_result = subprocess.run([
            'env', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '-y', 
            'apt-transport-https', 'ca-certificates', 'curl', 'gnupg', 'lsb-release'
        ], capture_output=True, text=True)
        if prereq_result.returncode != 0:
            return {'success': False, 'error': f'Failed to install prerequisites: {prereq_result.stderr}'}
        
        # Remove any existing Docker GPG key and repository to prevent conflicts
        # This fixes issues with corrupted or outdated GPG keys
        subprocess.run(['rm', '-f', '/etc/apt/keyrings/docker.gpg'], capture_output=True, text=True)
        subprocess.run(['rm', '-f', '/etc/apt/sources.list.d/docker.list'], capture_output=True, text=True)
        
        # Create keyrings directory if it doesn't exist
        subprocess.run(['mkdir', '-p', '/etc/apt/keyrings'], capture_output=True, text=True)
        
        # Add Docker's official GPG key using the robust method with automatic error handling
        # This fixes the "NO_PUBKEY 7EA0A9C3F273FCD8" error by properly importing the key
        try:
            # Use the integrated GPG fix function for robust key handling
            run_command_with_gpg_fix('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg', retries=2)
            
            # Set proper permissions for the GPG key
            subprocess.run(['chmod', 'a+r', '/etc/apt/keyrings/docker.gpg'], capture_output=True, text=True)
            
            # Verify GPG key was imported successfully with more robust check
            if not os.path.exists('/etc/apt/keyrings/docker.gpg'):
                return {'success': False, 'error': 'GPG key file was not created'}
            
            # Check if file has content (size > 0)
            key_stat = os.stat('/etc/apt/keyrings/docker.gpg')
            if key_stat.st_size == 0:
                return {'success': False, 'error': 'GPG key file is empty'}
                
        except SystemExit:
            return {'success': False, 'error': 'Failed to download and import Docker GPG key after multiple attempts'}
        
        # Get Ubuntu codename
        codename_result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
        if codename_result.returncode != 0:
            # Fallback: try to detect codename from /etc/os-release
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = f.read()
                    if 'VERSION_CODENAME=' in os_release:
                        for line in os_release.split('\n'):
                            if line.startswith('VERSION_CODENAME='):
                                codename = line.split('=')[1].strip('"')
                                break
                    else:
                        # Default to focal for older Ubuntu versions
                        codename = 'focal'
            except Exception:
                codename = 'focal'  # Safe fallback
        else:
            codename = codename_result.stdout.strip()
        
        # Validate codename
        if not codename or codename == '':
            codename = 'focal'  # Safe fallback
        
        # Add Docker repository (Ubuntu 22.04 compatible method)
        repo_line = f'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu {codename} stable'
        
        with open('/etc/apt/sources.list.d/docker.list', 'w') as f:
            f.write(repo_line + '\n')
        
        # Clean apt cache and update package list again
        subprocess.run(['apt-get', 'clean'], capture_output=True, text=True)
        subprocess.run(['rm', '-rf', '/var/lib/apt/lists/*'], capture_output=True, text=True)
        
        # Update package list after adding Docker repository with automatic GPG error handling
        # This will detect and fix any GPG signature issues with the new Docker repository
        try:
            run_command_with_gpg_fix('env DEBIAN_FRONTEND=noninteractive apt-get update', retries=3)
        except SystemExit:
            return {'success': False, 'error': 'Failed to update package list after adding repository with GPG fixes'}
        
        # Install Docker packages with automatic GPG error handling
        # This ensures any remaining GPG issues are resolved during package installation
        try:
            run_command_with_gpg_fix('env DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin', retries=2)
        except SystemExit:
            return {'success': False, 'error': 'Failed to install Docker packages after GPG fixes'}
        
        # Start and enable Docker service using systemctl
        start_result = subprocess.run(['systemctl', 'start', 'docker'], capture_output=True, text=True)
        if start_result.returncode != 0:
            return {'success': False, 'error': f'Failed to start Docker service: {start_result.stderr}'}
        
        enable_result = subprocess.run(['systemctl', 'enable', 'docker'], capture_output=True, text=True)
        if enable_result.returncode != 0:
            return {'success': False, 'error': f'Failed to enable Docker service: {enable_result.stderr}'}
        
        # Verify Docker installation
        verify_result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if verify_result.returncode != 0:
            return {'success': False, 'error': 'Docker installation verification failed'}
        
        return {'success': True, 'message': f'Docker installed and started successfully. Version: {verify_result.stdout.strip()}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Error installing Docker: {str(e)}'}


def uninstall_docker_package():
    """
    Comprehensive Docker uninstallation function.
    
    This function completely removes Docker and all related components:
    - Stops and disables Docker services
    - Removes all Docker packages and dependencies
    - Cleans up Docker data directories
    - Removes Docker GPG keys and repository configuration
    - Removes Docker user groups
    - Cleans up system files and caches
    
    Returns:
        dict: Success status and message or error details
    """
    try:
        # Get SocketIO instance for progress updates
        socketio = None
        if FLASK_AVAILABLE:
            try:
                from flask import current_app
                socketio = current_app.extensions.get('socketio')
            except:
                pass
        
        def emit_progress(message, progress):
            """Emit progress update if SocketIO is available"""
            if socketio:
                socketio.emit('docker_uninstall_output', {
                    'output': message,
                    'type': 'info'
                })
                time.sleep(1)
                # Step 1: Stop containers
                socketio.emit('docker_uninstall_progress', {
                    'status': 'stopping_containers',
                    'message': 'Stopping all running Docker containers...',
                    'progress': 10
                })
                time.sleep(1)
                
                # Step 2: Stop services
                socketio.emit('docker_uninstall_progress', {
                    'status': 'stopping_services',
                    'message': 'Stopping and disabling Docker services...',
                    'progress': 20
                })
                time.sleep(1)
                
                # Step 3: Remove packages
                socketio.emit('docker_uninstall_progress', {
                    'status': 'removing_packages',
                    'message': 'Removing Docker packages...',
                    'progress': 40
                })
                time.sleep(1)
                
                # Step 4: Clean data directories
                socketio.emit('docker_uninstall_progress', {
                    'status': 'cleaning_data',
                    'message': 'Removing Docker data directories...',
                    'progress': 60
                })
                time.sleep(1)
                                
                # Step 5: Remove GPG keys and repository
                socketio.emit('docker_uninstall_progress', {
                    'status': 'cleaning_gpg',
                    'message': 'Removing Docker GPG keys and repository configuration...',
                    'progress': 75
                })
                time.sleep(1)
                
                # Step 6: Final cleanup
                socketio.emit('docker_uninstall_progress', {
                    'status': 'final_cleanup',
                    'message': 'Performing final cleanup and verification...',
                    'progress': 90
                })
                time.sleep(1)
        
        # Use logger if available, otherwise fallback to print
        def log_info(msg):
            if 'logger' in globals() and logger:
                logger.info(msg)
            else:
                print(f"INFO: {msg}")
                
        def log_error(msg):
            if 'logger' in globals() and logger:
                logger.error(msg)
            else:
                print(f"ERROR: {msg}")
        
        # Check if Docker is actually installed before attempting uninstallation
        docker_installed = False
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                docker_installed = True
        except FileNotFoundError:
            docker_installed = False
        except Exception:
            docker_installed = False
        
        if not docker_installed:
            log_info("Docker is not installed, skipping uninstallation")
            emit_progress("Docker is not installed, skipping uninstallation", 100)
            return {'success': True, 'message': 'Docker was not installed'}
        
        log_info("Starting comprehensive Docker uninstallation...")
        emit_progress("Starting comprehensive Docker uninstallation...", 90)
        
        # Step 1: Stop all running Docker containers
        log_info("Stopping all running Docker containers...")
        emit_progress("Stopping all running Docker containers...", 91)
        try:
            containers_result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
            if containers_result.returncode == 0 and containers_result.stdout.strip():
                subprocess.run(['docker', 'stop'] + containers_result.stdout.strip().split('\n'), capture_output=True, text=True)
                log_info("All Docker containers stopped")
                emit_progress("All Docker containers stopped", 92)
        except Exception as e:
            log_info(f"No running containers to stop or Docker not accessible: {e}")
            emit_progress("No running containers to stop", 92)
        
        # Step 2: Stop and disable Docker services
        log_info("Stopping and disabling Docker services...")
        emit_progress("Stopping and disabling Docker services...", 93)
        services = ['docker.service', 'docker.socket', 'containerd.service']
        for service in services:
            try:
                subprocess.run(['systemctl', 'stop', service], capture_output=True, text=True)
                subprocess.run(['systemctl', 'disable', service], capture_output=True, text=True)
                log_info(f"Service {service} stopped and disabled")
            except Exception as e:
                log_info(f"Service {service} may not exist: {e}")
        emit_progress("Docker services stopped and disabled", 94)
        
        # Step 3: Remove Docker packages
        log_info("Removing Docker packages...")
        emit_progress("Removing Docker packages...", 95)
        docker_packages = [
            'docker-ce', 'docker-ce-cli', 'containerd.io',
            'docker-buildx-plugin', 'docker-compose-plugin',
            'docker.io', 'docker-doc', 'docker-compose',
            'podman-docker', 'containerd', 'runc'
        ]
        
        # Remove packages with purge to remove configuration files
        for package in docker_packages:
            try:
                result = subprocess.run(['apt-get', 'purge', '-y', package], capture_output=True, text=True)
                if result.returncode == 0:
                    log_info(f"Package {package} removed successfully")
            except Exception as e:
                log_info(f"Package {package} may not be installed: {e}")
        emit_progress("Docker packages removed", 96)
        
        # Step 4: Remove Docker data directories
        log_info("Removing Docker data directories...")
        emit_progress("Removing Docker data directories...", 97)
        docker_dirs = [
            '/var/lib/docker',
            '/var/lib/containerd',
            '/etc/docker',
            '/var/run/docker.sock',
            '/var/run/docker',
            '/usr/local/bin/docker-compose'
        ]
        
        for directory in docker_dirs:
            try:
                subprocess.run(['rm', '-rf', directory], capture_output=True, text=True)
                log_info(f"Directory {directory} removed")
            except Exception as e:
                log_info(f"Directory {directory} may not exist: {e}")
        emit_progress("Docker data directories removed", 98)
        
        # Step 5: Remove Docker GPG keys and repository
        log_info("Removing Docker GPG keys and repository configuration...")
        emit_progress("Removing Docker GPG keys and repository...", 99)
        gpg_files = [
            '/etc/apt/keyrings/docker.gpg',
            '/usr/share/keyrings/docker-archive-keyring.gpg',
            '/etc/apt/sources.list.d/docker.list',
            '/etc/apt/sources.list.d/docker.list.save'
        ]
        
        for gpg_file in gpg_files:
            try:
                subprocess.run(['rm', '-f', gpg_file], capture_output=True, text=True)
                log_info(f"GPG file {gpg_file} removed")
            except Exception as e:
                log_info(f"GPG file {gpg_file} may not exist: {e}")
        
        # Step 6: Remove Docker user group
        log_info("Removing Docker user group...")
        try:
            subprocess.run(['groupdel', 'docker'], capture_output=True, text=True)
            log_info("Docker group removed")
        except Exception as e:
            log_info(f"Docker group may not exist: {e}")
        
        # Step 7: Clean up package cache and autoremove
        log_info("Cleaning up package cache and removing orphaned packages...")
        emit_progress("Cleaning up package cache...", 99.5)
        try:
            subprocess.run(['apt-get', 'autoremove', '-y'], capture_output=True, text=True)
            subprocess.run(['apt-get', 'autoclean'], capture_output=True, text=True)
            subprocess.run(['apt-get', 'clean'], capture_output=True, text=True)
            log_info("Package cache cleaned")
        except Exception as e:
            log_error(f"Failed to clean package cache: {e}")
        
        # Step 8: Update package lists
        log_info("Updating package lists...")
        try:
            subprocess.run(['apt-get', 'update'], capture_output=True, text=True)
            log_info("Package lists updated")
            emit_progress("Final cleanup completed successfully", 100)
        except Exception as e:
            log_error(f"Failed to update package lists: {e}")
            emit_progress("Final cleanup completed with warnings", 100)
        
        # Step 9: Verify Docker removal
        log_info("Verifying Docker removal...")
        verify_result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if verify_result.returncode == 0:
            log_error("Docker command still available - uninstallation may be incomplete")
            return {'success': False, 'error': 'Docker uninstallation incomplete - Docker command still available'}
        
        # Check if Docker service files still exist
        service_check = subprocess.run(['systemctl', 'status', 'docker'], capture_output=True, text=True)
        if 'could not be found' not in service_check.stderr and 'not found' not in service_check.stderr:
            log_error("Docker service still exists - uninstallation may be incomplete")
            return {'success': False, 'error': 'Docker uninstallation incomplete - Docker service still exists'}
        
        log_info("Docker uninstallation completed successfully")
        return {
            'success': True, 
            'message': 'Docker has been completely uninstalled. All packages, data, and configuration files have been removed.'
        }
        
    except Exception as e:
        error_msg = f'Error during Docker uninstallation: {str(e)}'
        log_error(error_msg)
        return {'success': False, 'error': error_msg}


def uninstall_with_socketio():
    """Handle Docker uninstallation with SocketIO progress updates"""
    try:
        # Import SocketIO if available
        if FLASK_AVAILABLE:
            try:
                from flask import current_app
                socketio = current_app.extensions.get('socketio')
                
                if socketio:
                    import threading
                    import time
                    
                    def uninstall_in_background():
                        try:
                            # Emit progress updates during uninstallation
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'starting',
                                'message': 'Starting Docker uninstallation...',
                                'progress': 0
                            })
                            
                            time.sleep(1)
                            
                            # Step 1: Stop containers
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'stopping_containers',
                                'message': 'Stopping all running Docker containers...',
                                'progress': 10
                            })
                            time.sleep(1)
                            
                            # Step 2: Stop services
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'stopping_services',
                                'message': 'Stopping and disabling Docker services...',
                                'progress': 20
                            })
                            time.sleep(1)
                            
                            # Step 3: Remove packages
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'removing_packages',
                                'message': 'Removing Docker packages...',
                                'progress': 40
                            })
                            time.sleep(1)
                            
                            # Step 4: Clean data directories
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'cleaning_data',
                                'message': 'Removing Docker data directories...',
                                'progress': 60
                            })
                            time.sleep(1)
                            
                            # Step 5: Remove GPG keys and repository
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'cleaning_gpg',
                                'message': 'Removing Docker GPG keys and repository configuration...',
                                'progress': 75
                            })
                            time.sleep(1)
                            
                            # Step 6: Final cleanup
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'final_cleanup',
                                'message': 'Performing final cleanup and verification...',
                                'progress': 90
                            })
                            time.sleep(1)
                            
                            # Perform actual uninstallation
                            result = uninstall_docker_package()
                            
                            if result['success']:
                                socketio.emit('docker_uninstall_progress', {
                                    'status': 'completed',
                                    'message': 'Docker uninstallation completed successfully!',
                                    'progress': 100
                                })
                                socketio.emit('docker_uninstall_complete', {
                                    'success': True,
                                    'message': result['message']
                                })
                            else:
                                socketio.emit('docker_uninstall_progress', {
                                    'status': 'error',
                                    'message': f'Uninstallation failed: {result["error"]}',
                                    'progress': 100
                                })
                                socketio.emit('docker_uninstall_error', {
                                    'success': False,
                                    'message': result['error']
                                })
                                
                        except Exception as e:
                            socketio.emit('docker_uninstall_progress', {
                                'status': 'error',
                                'message': f'Uninstallation error: {str(e)}',
                                'progress': 100
                            })
                            socketio.emit('docker_uninstall_error', {
                                'success': False,
                                'message': str(e)
                            })
                    
                    # Start uninstallation in background thread
                    thread = threading.Thread(target=uninstall_in_background)
                    thread.daemon = True
                    thread.start()
                    
                    return {
                        'success': True,
                        'message': 'Docker uninstallation started with real-time progress updates'
                    }
                    
            except ImportError:
                pass
        
        # Fallback to regular uninstallation if SocketIO not available
        return uninstall_docker_package()
        
    except Exception as e:
        return {'success': False, 'error': f'Error starting Docker uninstallation: {str(e)}'}


# Docker installation function moved to install_docker_package()

# Docker plugin follows modular pattern - handlers managed through main() function

def install_with_socketio():
    """Handle Docker installation with SocketIO progress updates"""
    try:
        # Import SocketIO if available
        if FLASK_AVAILABLE:
            try:
                from flask import current_app
                socketio = current_app.extensions.get('socketio')
                
                if socketio:
                    import threading
                    import time
                    
                    def install_in_background():
                        try:
                            # Emit initial progress
                            socketio.emit('docker_install_progress', {
                                'step': 1,
                                'total': 8,
                                'status': 'Starting Docker installation...',
                                'percentage': 12
                            })
                            
                            socketio.emit('docker_install_output', {
                                'output': 'Starting Docker installation...',
                                'type': 'info'
                            })
                            
                            socketio.emit('docker_install_output', {
                                'output': 'Updating package lists...',
                                'type': 'info'
                            })
                            
                            socketio.emit('docker_install_progress', {
                                'step': 2,
                                'total': 8,
                                'status': 'Updating package lists...',
                                'percentage': 25
                            })
                            
                            time.sleep(1)
                            
                            # Call the actual installation function
                            # install_docker_package() now includes automatic GPG error handling
                            # via run_command_with_gpg_fix() which will provide additional
                            # real-time feedback if GPG issues are detected and fixed
                            result = install_docker_package()
                            
                            if result.get('success'):
                                socketio.emit('docker_install_progress', {
                                    'step': 8,
                                    'total': 8,
                                    'status': 'Docker installation completed successfully',
                                    'percentage': 100
                                })
                                
                                socketio.emit('docker_install_output', {
                                    'output': 'Docker installation completed successfully',
                                    'type': 'success'
                                })
                                
                                socketio.emit('docker_install_output', {
                                    'output': 'Docker service started and enabled',
                                    'type': 'success'
                                })
                                
                                socketio.emit('docker_install_complete', {
                                    'message': 'Docker has been installed successfully',
                                    'version': result.get('version', 'Unknown')
                                })
                            else:
                                socketio.emit('docker_install_error', {
                                    'message': result.get('error', 'Docker installation failed')
                                })
                                
                        except Exception as e:
                            socketio.emit('docker_install_error', {
                                'message': f'Docker installation failed: {str(e)}'
                            })
                    
                    # Start background thread
                    thread = threading.Thread(target=install_in_background)
                    thread.daemon = True
                    thread.start()
                    
                    return {'success': True, 'message': 'Installation started'}
                    
            except ImportError:
                pass
        
        # Fallback to regular installation
        return install_docker_package()
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def build_from_dockerfile(dockerfile_content, image_name, container_name=None):
    """Build Docker image from Dockerfile content and optionally run container"""
    try:
        if not dockerfile_content or not image_name:
            return {'success': False, 'error': 'Dockerfile content and image name are required'}
        
        # Create temporary directory for Dockerfile
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            
            # Write Dockerfile content to temporary file
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Build the image
            build_cmd = f'docker build -t "{image_name}" "{temp_dir}"'
            result = run_command(build_cmd, timeout=300)  # 5 minutes timeout for build
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'Failed to build image: {result["error"]}'
                }
            
            # If container name is provided, create and run the container
            if container_name:
                run_cmd = f'docker run -d --name "{container_name}" "{image_name}"'
                run_result = run_command(run_cmd)
                
                if not run_result['success']:
                    return {
                        'success': True,
                        'message': f'Image "{image_name}" built successfully, but failed to create container: {run_result["error"]}'
                    }
                
                return {
                    'success': True,
                    'message': f'Image "{image_name}" built and container "{container_name}" created successfully'
                }
            else:
                return {
                    'success': True,
                    'message': f'Image "{image_name}" built successfully'
                }
                
    except Exception as e:
        return {'success': False, 'error': f'Error building from Dockerfile: {str(e)}'}

def deploy_from_compose(compose_content, project_name=None):
    """Deploy services from Docker Compose YAML content"""
    try:
        if not compose_content:
            return {'success': False, 'error': 'Docker Compose content is required'}
        
        # Create temporary directory for docker-compose.yml
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_path = os.path.join(temp_dir, 'docker-compose.yml')
            
            # Write compose content to temporary file
            with open(compose_path, 'w') as f:
                f.write(compose_content)
            
            # Build the docker-compose command
            if project_name:
                compose_cmd = f'docker-compose -f "{compose_path}" -p "{project_name}" up -d'
            else:
                compose_cmd = f'docker-compose -f "{compose_path}" up -d'
            
            # Deploy the services
            result = run_command(compose_cmd, timeout=300)  # 5 minutes timeout for deployment
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'Failed to deploy from Docker Compose: {result["error"]}'
                }
            
            project_msg = f' with project name "{project_name}"' if project_name else ''
            return {
                'success': True,
                'message': f'Services deployed successfully from Docker Compose{project_msg}'
            }
                
    except Exception as e:
        return {'success': False, 'error': f'Error deploying from Docker Compose: {str(e)}'}

def main(data=None, **kwargs):
    """Main function to handle plugin actions"""
    try:
        # Handle different input formats
        if isinstance(data, dict):
            action = data.get('action')
            kwargs.update(data)
        else:
            action = data
        
        # Import Flask request if available (when called from Flask app)
        if FLASK_AVAILABLE:
            try:
                from flask import request, has_app_context
                # Only access request if we're in an app context
                if has_app_context():
                    # Get action from Flask request if not provided as parameter
                    if action is None:
                        # First try to get from form data (set by API route handler)
                        action = request.form.get('action')
                        # Then try JSON if form data is empty
                        if action is None and request.json:
                            action = request.json.get('action')
                    
                    # Get additional parameters from request
                    if not kwargs and request.method == 'POST':
                        if request.json:
                            kwargs.update(request.json)
                        else:
                            kwargs.update({
                                'container_id': request.form.get('container_id'),
                                'action_type': request.form.get('action_type'),
                                'image_id': request.form.get('image_id'),
                                'network_id': request.form.get('network_id'),
                                'volume_name': request.form.get('volume_name'),
                                'image_name': request.form.get('image_name'),
                                'image': request.form.get('image'),
                                'name': request.form.get('name'),
                                'ports': request.form.get('ports'),
                                'volumes': request.form.get('volumes'),
                                'env_vars': request.form.get('env_vars'),
                                'lines': int(request.form.get('lines', 100)) if request.form.get('lines') else 100
                            })
            except ImportError:
                # Running outside Flask context
                pass
        
        if action == 'status':
            result = check_docker_status()
        elif action == 'containers':
            result = get_containers()
        elif action == 'images':
            result = get_images()
        elif action == 'networks':
            result = get_networks()
        elif action == 'volumes':
            result = get_volumes()
        elif action == 'container_action':
            result = container_action(kwargs.get('container_id'), kwargs.get('action_type'))
        elif action == 'image_action':
            result = image_action(kwargs.get('image_id'), kwargs.get('action_type'))
        elif action == 'network_action':
            result = network_action(kwargs.get('network_id'), kwargs.get('action_type'))
        elif action == 'volume_action':
            result = volume_action(kwargs.get('volume_name'), kwargs.get('action_type'))
        elif action == 'pull_image':
            result = pull_image(kwargs.get('image_name'))
        elif action == 'create_container':
            result = create_container(
                kwargs.get('image'),
                kwargs.get('name'),
                kwargs.get('ports'),
                kwargs.get('volumes'),
                kwargs.get('env_vars')
            )
        elif action == 'container_logs':
            result = get_container_logs(kwargs.get('container_id'), kwargs.get('lines', 100))
        elif action == 'build_from_dockerfile':
            result = build_from_dockerfile(
                kwargs.get('dockerfile_content'),
                kwargs.get('image_name'),
                kwargs.get('container_name')
            )
        elif action == 'deploy_from_compose':
            result = deploy_from_compose(
                kwargs.get('compose_content'),
                kwargs.get('project_name')
            )
        elif action == 'system_info':
            result = get_system_info()
        elif action == 'cleanup':
            result = cleanup_system()
        elif action == 'install':
            # Check if this is a SocketIO request
            if FLASK_AVAILABLE:
                try:
                    from flask import has_app_context, current_app
                    if has_app_context() and current_app.extensions.get('socketio'):
                        result = install_with_socketio()
                    else:
                        result = install_docker_package()
                except ImportError:
                    result = install_docker_package()
            else:
                result = install_docker_package()
        elif action == 'uninstall':
            # Check if this is a SocketIO request for real-time feedback
            if FLASK_AVAILABLE:
                try:
                    from flask import has_app_context, current_app
                    if has_app_context() and current_app.extensions.get('socketio'):
                        result = uninstall_with_socketio()
                    else:
                        result = uninstall_docker_package()
                except ImportError:
                    result = uninstall_docker_package()
            else:
                result = uninstall_docker_package()
        else:
            result = {'success': False, 'error': f'Unknown action: {action}'}
        
        # Return JSON response if Flask is available and we're in Flask context
        if FLASK_AVAILABLE:
            try:
                from flask import jsonify, has_app_context
                if has_app_context():
                    return jsonify(result)
            except ImportError:
                pass
        
        return result
            
    except Exception as e:
        error_result = {'success': False, 'error': f'Plugin error: {str(e)}'}
        if FLASK_AVAILABLE:
            try:
                from flask import jsonify, has_app_context
                if has_app_context():
                    return jsonify(error_result)
            except ImportError:
                pass
        
        return error_result

# Plugin follows modular pattern - no auto-registration

"""
Comprehensive GPG Error Handling Documentation:

1. Using run_command_with_gpg_fix for automatic GPG error handling:
   try:
       run_command_with_gpg_fix('apt-get update', retries=3)
       run_command_with_gpg_fix('apt-get install docker-ce docker-ce-cli containerd.io', retries=2)
   except SystemExit:
       print("Failed after comprehensive GPG fixes")

2. Manual GPG fix (called automatically by run_command_with_gpg_fix):
   fix_docker_gpg()  # Comprehensive GPG keys and repository configuration fix

3. Docker installation with integrated robust GPG handling:
   result = install_docker_package()  # Automatically handles all GPG errors

Comprehensive GPG Errors Fixed:
- NO_PUBKEY 7EA0A9C3F273FCD8: Docker's GPG key not found or corrupted
- Repository signature verification failures
- Corrupted or outdated GPG key files
- Invalid GPG data and malformed key content
- Public key not available errors
- GPG key verification failures
- Empty or zero-size GPG key files
- Incorrect repository configuration

Robust GPG Fix Process:
1. Detects comprehensive GPG-related errors in command output
2. Removes ALL existing Docker GPG keys and repository files (including backups)
3. Cleans apt cache thoroughly to prevent conflicts
4. Downloads fresh GPG key using multiple robust methods with fallbacks
5. Properly imports the key using gpg --dearmor with verification
6. Dynamically detects Ubuntu codename with multiple fallback methods
7. Reconfigures repository with correct architecture and codename
8. Verifies GPG key file integrity (existence and non-zero size)
9. Sets proper file permissions for security
10. Cleans apt cache and retries the original command

Advanced Error Detection Keywords:
- 'no_pubkey', 'gpg error', 'not signed', 'signature verification failed'
- 'key verification failed', 'repository is not signed', 'gpg key verification failed'
- 'corrupted gpg', 'invalid gpg', 'public key is not available'

This ensures extremely robust Docker installation even on systems with
complex GPG key issues, repository configuration problems, or network issues.

Comprehensive Docker Uninstallation Documentation:

1. Basic Docker uninstallation:
   result = uninstall_docker_package()  # Complete Docker removal
   
2. Docker uninstallation with real-time progress (SocketIO):
   result = uninstall_with_socketio()  # Real-time progress updates
   
3. Command-line usage:
   python index.py uninstall  # Direct uninstallation

Uninstallation Process:
1. Stops all running Docker containers gracefully
2. Stops and disables Docker system services (docker.service, docker.socket, containerd.service)
3. Removes all Docker packages and dependencies with purge (docker-ce, docker-ce-cli, containerd.io, etc.)
4. Cleans up Docker data directories (/var/lib/docker, /var/lib/containerd, /etc/docker)
5. Removes Docker GPG keys and repository configuration
6. Removes Docker user group and permissions
7. Performs comprehensive package cache cleanup and autoremove
8. Updates package lists and verifies complete removal

Safety Features:
- Graceful container shutdown before service termination
- Comprehensive verification to ensure complete removal
- Detailed logging of each uninstallation step
- Error handling for missing components or partial installations
- Real-time progress updates via SocketIO when available

SocketIO Events for Real-time Uninstallation:
- 'docker_uninstall_progress': Progress updates with status and percentage
- 'docker_uninstall_complete': Final result with success/error status

Uninstallation Status Messages:
- 'starting': Beginning uninstallation process
- 'stopping_containers': Stopping running containers
- 'stopping_services': Disabling Docker services
- 'removing_packages': Removing Docker packages
- 'cleaning_data': Removing data directories
- 'cleaning_gpg': Removing GPG keys and repository
- 'final_cleanup': Final cleanup and verification
- 'completed': Successful uninstallation
- 'error': Uninstallation failed

This ensures complete Docker removal including all data, configurations,
and system modifications, returning the system to pre-Docker state.
"""

if __name__ == '__main__':
    if len(sys.argv) > 1:
        action = sys.argv[1]
        result = main(action)
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({'success': False, 'error': 'No action specified'}, indent=2))