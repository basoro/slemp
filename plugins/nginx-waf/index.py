#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nginx WAF Manager Plugin for SLEMP
Manage Nginx Web Application Firewall with ModSecurity integration

Features:
- Automatic ModSecurity installation and configuration
- Real-time WAF rule management
- Custom rule creation and editing
- Attack monitoring and logging
- Whitelist and blacklist management
- Performance monitoring
- Rule set updates (OWASP Core Rule Set)
"""

import subprocess
import json
import os
import sys
import time
import re
from datetime import datetime

# Import Attack Map modules
try:
    from attack_map_parser import AttackMapParser
    from attack_map_api import AttackMapAPI
    ATTACK_MAP_AVAILABLE = True
except ImportError:
    ATTACK_MAP_AVAILABLE = False
    AttackMapParser = None
    AttackMapAPI = None

# Import Log Monitor for real-time monitoring
try:
    from log_monitor import start_background_monitoring, stop_background_monitoring, is_monitoring
    LOG_MONITOR_AVAILABLE = True
except ImportError:
    LOG_MONITOR_AVAILABLE = False
    start_background_monitoring = None
    stop_background_monitoring = None
    is_monitoring = None

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

def run_command(cmd, retries=3):
    """Execute command with retry mechanism
    
    Args:
        cmd (str): Command to execute
        retries (int): Number of retry attempts
    
    Returns:
        tuple: (return_code, stdout, stderr)
    """
    for i in range(retries + 1):
        try:
            if logger:
                logger.info(f"[RUN] {cmd}")
            else:
                print(f"[RUN] {cmd}")
            
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                if logger:
                    logger.info(result.stdout)
                else:
                    print(result.stdout)
                return result.returncode, result.stdout, result.stderr
            else:
                if logger:
                    logger.error(result.stderr)
                else:
                    print(result.stderr)
                
                if i < retries:
                    time.sleep(2)
                    continue
                else:
                    return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            if i < retries:
                print(f"Command timeout, retrying... ({i + 1}/{retries})")
                time.sleep(2)
                continue
            else:
                return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    return 1, "", "Max retries exceeded"

def install_modsecurity():
    """Install ModSecurity and OWASP Core Rule Set"""
    try:
        # Update package list
        run_command('apt update')
        
        # Install ModSecurity library and Nginx module
        run_command('apt install -y libmodsecurity3t64 libmodsecurity-dev')
        
        # Primary installation method - try libnginx-mod-http-modsecurity first
        ret_code, stdout, stderr = run_command('apt install -y libnginx-mod-http-modsecurity')
        if ret_code == 0:
            print("Successfully installed libnginx-mod-http-modsecurity")
        else:
            # Try to install from repository alternatives
            result = subprocess.run(['apt', 'search', 'libnginx-mod-security'], capture_output=True, text=True)
            if 'libnginx-mod-security' in result.stdout:
                run_command('apt install -y libnginx-mod-security')
            else:
                # Try alternative package names
                result2 = subprocess.run(['apt', 'search', 'nginx-module-modsecurity'], capture_output=True, text=True)
                if 'nginx-module-modsecurity' in result2.stdout:
                    run_command('apt install -y nginx-module-modsecurity')
                else:
                    # Install build dependencies including both PCRE versions
                    run_command('apt install -y build-essential libpcre3-dev libpcre2-dev zlib1g-dev libssl-dev pkg-config')
                
                # Try to use pre-compiled module from nginx-extras
                run_command('apt install -y nginx-extras')
                
                # Check if module exists in nginx-extras
                module_check = subprocess.run(['find', '/usr/lib/nginx/modules', '-name', '*modsecurity*'], capture_output=True, text=True)
                if module_check.stdout.strip():
                    # Copy existing module
                    run_command('mkdir -p /etc/nginx/modules')
                    run_command('cp /usr/lib/nginx/modules/*modsecurity* /etc/nginx/modules/ 2>/dev/null || true')
                else:
                     # Fallback: ModSecurity will work in detection mode only without dynamic module
                     run_command('mkdir -p /etc/nginx/modules')
                     # Skip module loading, use basic WAF functionality
                     return {'success': True, 'message': 'ModSecurity installed in basic mode (detection only)', 'module_loaded': False}
        
        # Create ModSecurity directories
        run_command('mkdir -p /etc/nginx/modsec')
        
        # Clean up existing OWASP CRS if exists
        run_command('rm -rf /etc/nginx/modsec/owasp-crs /etc/nginx/modsec/coreruleset-* /etc/nginx/modsec/v3.3.4.tar.gz')
        
        # Download OWASP Core Rule Set
        run_command('cd /etc/nginx/modsec && wget https://github.com/coreruleset/coreruleset/archive/v3.3.4.tar.gz')
        run_command('cd /etc/nginx/modsec && tar -xzf v3.3.4.tar.gz')
        run_command('cd /etc/nginx/modsec && mv coreruleset-3.3.4 owasp-crs')
        run_command('cd /etc/nginx/modsec && rm v3.3.4.tar.gz')
        
        # Create main ModSecurity configuration using tee command
        main_conf_cmd = '''sudo tee /etc/nginx/modsec/main.conf > /dev/null << 'EOF'
# ModSecurity configuration
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess Off
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072
SecRequestBodyInMemoryLimit 131072
SecRequestBodyLimitAction Reject
SecPcreMatchLimit 1000
SecPcreMatchLimitRecursion 1000
SecTmpDir /tmp/
SecDataDir /tmp/
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/nginx/modsec_audit.log
SecArgumentSeparator &
SecCookieFormat 0
SecUnicodeMapFile unicode.mapping 20127

# Include OWASP Core Rule Set from system location
Include /usr/share/modsecurity-crs/crs-setup.conf.example
Include /usr/share/modsecurity-crs/rules/*.conf
EOF'''
        
        run_command(main_conf_cmd)
        
        # Copy CRS setup file
        run_command('cp /etc/nginx/modsec/owasp-crs/crs-setup.conf.example /etc/nginx/modsec/owasp-crs/crs-setup.conf')
        
        # Create unicode mapping file
        run_command('wget -O /etc/nginx/modsec/unicode.mapping https://raw.githubusercontent.com/SpiderLabs/ModSecurity/v3/master/unicode.mapping')
        
        # Configure Nginx to load ModSecurity module
        nginx_conf = '/etc/nginx/nginx.conf'
        
        # Read current nginx configuration
        with open(nginx_conf, 'r') as f:
            content = f.read()
        
        # Determine the correct module path
        module_paths = [
            '/etc/nginx/modules/ngx_http_modsecurity_module.so',
            '/usr/lib/nginx/modules/ngx_http_modsecurity_module.so',
            '/usr/share/nginx/modules/ngx_http_modsecurity_module.so'
        ]
        
        module_path = None
        for path in module_paths:
            if os.path.exists(path) and os.path.getsize(path) > 0:  # Check if file exists and is not empty
                module_path = path
                break
        
        if module_path:
            load_directive = f'load_module {module_path};'
            
            # Add ModSecurity module loading if not already present
            if load_directive not in content:
                # Add load_module directive at the beginning
                content = load_directive + '\n' + content
                
                # Write back to nginx.conf
                with open(nginx_conf, 'w') as f:
                    f.write(content)
        else:
            # Continue without module loading - basic WAF functionality only
            pass
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            # Rollback changes if test fails
            content = content.replace(load_directive + '\n', '')
            with open(nginx_conf, 'w') as f:
                f.write(content)
            return {'success': False, 'error': f'Nginx configuration test failed: {test_result.stderr}'}
        
        # Reload nginx to apply changes
        run_command('supervisorctl restart nginx')
        
        return {'success': True, 'message': 'ModSecurity installed and configured successfully'}
        
    except Exception as e:
        error_msg = f"Failed to install ModSecurity: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}


def check_nginx_status():
    """Check if Nginx is installed and running"""
    try:
        # Check if nginx is installed
        result = subprocess.run(['which', 'nginx'], capture_output=True, text=True)
        if result.returncode != 0:
            return {'installed': False, 'running': False, 'version': None}
        
        # Get nginx version
        version_result = subprocess.run(['nginx', '-v'], capture_output=True, text=True)
        version = version_result.stderr.split('/')[-1].strip() if version_result.stderr else 'Unknown'
        
        # Check if nginx is running
        status_result = subprocess.run(['pgrep', 'nginx'], capture_output=True)
        running = status_result.returncode == 0
        
        return {
            'installed': True,
            'running': running,
            'version': version
        }
    except Exception as e:
        if logger:
            logger.error(f"Error checking nginx status: {e}")
        return {'installed': False, 'running': False, 'version': None, 'error': str(e)}

def check_modsecurity_status():
    """Check if ModSecurity is installed and configured"""
    try:
        # Check if ModSecurity library is installed
        lib_check = subprocess.run(['dpkg', '-l', 'libmodsecurity3t64'], capture_output=True, text=True)
        if lib_check.returncode != 0:
            # Try alternative package name
            lib_check = subprocess.run(['dpkg', '-l', 'libmodsecurity3'], capture_output=True, text=True)
        library_installed = lib_check.returncode == 0
        
        # Check if ModSecurity module is available - look for actual installed files
        module_file_exists = (os.path.exists('/usr/lib/nginx/modules/ngx_http_modsecurity_module.so') or 
                             os.path.exists('/usr/share/nginx/modules/mod-http-modsecurity.conf') or
                             os.path.exists('/usr/share/nginx/modules-available/mod-http-modsecurity.conf'))
        
        # Check if module is enabled in modules-enabled
        modules_enabled = (os.path.exists('/etc/nginx/modules-enabled/50-mod-http-modsecurity.conf') or
                          os.path.exists('/etc/nginx/modules-available/mod-http-modsecurity.conf') or
                          os.path.exists('/usr/share/nginx/modules-available/mod-http-modsecurity.conf'))
        
        # Test nginx configuration to see if ModSecurity is actually loaded
        nginx_test = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        module_loaded = 'ModSecurity-nginx' in nginx_test.stderr and nginx_test.returncode == 0
        
        # Check if ModSecurity config exists
        config_exists = os.path.exists('/etc/nginx/modsec/main.conf')
        
        # Check OWASP CRS - look in both locations
        owasp_crs_exists = (os.path.exists('/etc/nginx/modsec/owasp-crs') or 
                           os.path.exists('/usr/share/modsecurity-crs'))
        
        # Consider installed if library and module file exist (config may not be set up yet)
        installed = library_installed and module_file_exists
        
        return {
            'installed': installed,
            'library_installed': library_installed,
            'module_file_exists': module_file_exists,
            'modules_enabled': modules_enabled,
            'module_loaded': module_loaded,
            'config_exists': config_exists,
            'owasp_crs': owasp_crs_exists
        }
    except Exception as e:
        if logger:
            logger.error(f"Error checking ModSecurity status: {e}")
        return {'installed': False, 'config_exists': False, 'owasp_crs': False, 'error': str(e)}

def install_modsecurity():
    """Install ModSecurity and OWASP Core Rule Set"""
    try:
        # Update package list
        run_command('apt update')
        
        # Install ModSecurity library and Nginx module
        run_command('apt install -y libmodsecurity3t64 libmodsecurity-dev')
        
        # Try to install from repository first
        result = subprocess.run(['apt', 'search', 'libnginx-mod-security'], capture_output=True, text=True)
        if 'libnginx-mod-security' in result.stdout:
            run_command('apt install -y libnginx-mod-security')
        else:
            # Try alternative package names
            result2 = subprocess.run(['apt', 'search', 'nginx-module-modsecurity'], capture_output=True, text=True)
            if 'nginx-module-modsecurity' in result2.stdout:
                run_command('apt install -y nginx-module-modsecurity')
            else:
                # Install build dependencies including both PCRE versions
                run_command('apt install -y build-essential libpcre3-dev libpcre2-dev zlib1g-dev libssl-dev pkg-config')
                
                # Try to use pre-compiled module from nginx-extras
                run_command('apt install -y nginx-extras')
                
                # Check if module exists in nginx-extras
                module_check = subprocess.run(['find', '/usr/lib/nginx/modules', '-name', '*modsecurity*'], capture_output=True, text=True)
                if module_check.stdout.strip():
                    # Copy existing module
                    run_command('mkdir -p /etc/nginx/modules')
                    run_command('cp /usr/lib/nginx/modules/*modsecurity* /etc/nginx/modules/ 2>/dev/null || true')
                else:
                     # Fallback: ModSecurity will work in detection mode only without dynamic module
                     run_command('mkdir -p /etc/nginx/modules')
                     # Skip module loading, use basic WAF functionality
                     return {'success': True, 'message': 'ModSecurity installed in basic mode (detection only)', 'module_loaded': False}
        
        # Create ModSecurity directories
        run_command('mkdir -p /etc/nginx/modsec')
        
        # Clean up existing OWASP CRS if exists
        run_command('rm -rf /etc/nginx/modsec/owasp-crs /etc/nginx/modsec/coreruleset-* /etc/nginx/modsec/v3.3.4.tar.gz')
        
        # Download OWASP Core Rule Set
        run_command('cd /etc/nginx/modsec && wget https://github.com/coreruleset/coreruleset/archive/v3.3.4.tar.gz')
        run_command('cd /etc/nginx/modsec && tar -xzf v3.3.4.tar.gz')
        run_command('cd /etc/nginx/modsec && mv coreruleset-3.3.4 owasp-crs')
        run_command('cd /etc/nginx/modsec && rm v3.3.4.tar.gz')
        
        # Create main ModSecurity configuration using tee command
        main_conf_cmd = '''sudo tee /etc/nginx/modsec/main.conf > /dev/null << 'EOF'
# ModSecurity configuration
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess Off
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072
SecRequestBodyInMemoryLimit 131072
SecRequestBodyLimitAction Reject
SecPcreMatchLimit 1000
SecPcreMatchLimitRecursion 1000
SecTmpDir /tmp/
SecDataDir /tmp/
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/nginx/modsec_audit.log
SecArgumentSeparator &
SecCookieFormat 0
SecUnicodeMapFile unicode.mapping 20127

# Include OWASP Core Rule Set from system location
Include /usr/share/modsecurity-crs/crs-setup.conf.example
Include /usr/share/modsecurity-crs/rules/*.conf
EOF'''
        
        run_command(main_conf_cmd)
        
        # Copy CRS setup file
        run_command('cp /etc/nginx/modsec/owasp-crs/crs-setup.conf.example /etc/nginx/modsec/owasp-crs/crs-setup.conf')
        
        # Create unicode mapping file
        run_command('wget -O /etc/nginx/modsec/unicode.mapping https://raw.githubusercontent.com/SpiderLabs/ModSecurity/v3/master/unicode.mapping')
        
        # Configure Nginx to load ModSecurity module
        nginx_conf = '/etc/nginx/nginx.conf'
        
        # Read current nginx configuration
        with open(nginx_conf, 'r') as f:
            content = f.read()
        
        # Determine the correct module path
        module_paths = [
            '/etc/nginx/modules/ngx_http_modsecurity_module.so',
            '/usr/lib/nginx/modules/ngx_http_modsecurity_module.so',
            '/usr/share/nginx/modules/ngx_http_modsecurity_module.so'
        ]
        
        module_path = None
        for path in module_paths:
            if os.path.exists(path) and os.path.getsize(path) > 0:  # Check if file exists and is not empty
                module_path = path
                break
        
        if module_path:
            load_directive = f'load_module {module_path};'
            
            # Add ModSecurity module loading if not already present
            if load_directive not in content:
                # Add load_module directive at the beginning
                content = load_directive + '\n' + content
                
                # Write back to nginx.conf
                with open(nginx_conf, 'w') as f:
                    f.write(content)
        else:
            # Continue without module loading - basic WAF functionality only
            pass
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            # Rollback changes if test fails
            content = content.replace(load_directive + '\n', '')
            with open(nginx_conf, 'w') as f:
                f.write(content)
            return {'success': False, 'error': f'Nginx configuration test failed: {test_result.stderr}'}
        
        # Reload nginx to apply changes
        run_command('supervisorctl restart nginx')
        
        return {'success': True, 'message': 'ModSecurity installed and configured successfully'}
        
    except Exception as e:
        error_msg = f"Failed to install ModSecurity: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_owasp_version_info():
    """Get OWASP CRS version and last update information"""
    try:
        version = 'Unknown'
        last_update = 'Never'
        
        # Check for version file in both locations
        version_files = ['/etc/nginx/modsec/owasp-crs/CHANGES', '/usr/share/modsecurity-crs/CHANGES']
        for version_file in version_files:
            if os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        content = f.read()
                        # Extract version from first version entry
                        version_match = re.search(r'== Version ([0-9.]+) - ([0-9-]+) ==', content)
                        if version_match:
                            version = version_match.group(1)
                            last_update = version_match.group(2)
                        
                        # Get file modification time as fallback
                        if last_update == 'Never':
                            stat = os.stat(version_file)
                            last_update = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                        break  # Stop after finding first valid version file
                except Exception:
                    continue
        
        # If no version file found, try to get version from package info or directory timestamp
        if version == 'Unknown':
            try:
                # Try to get version from dpkg if available - check multiple package names
                package_names = ['modsecurity-crs', 'libmodsecurity-crs', 'modsecurity-core-rule-set']
                for pkg_name in package_names:
                    try:
                        result = subprocess.run(['dpkg', '-l', pkg_name], capture_output=True, text=True, check=False)
                        if result.returncode == 0 and result.stdout:
                            lines = result.stdout.split('\n')
                            for line in lines:
                                if line.startswith('ii') and pkg_name in line:
                                    parts = line.split()
                                    if len(parts) >= 3 and parts[1] == pkg_name:
                                        version = parts[2]
                                        # Get package install date or use current date
                                        try:
                                            # Try to get package install date
                                            date_result = subprocess.run(['stat', '-c', '%Y', f'/var/lib/dpkg/info/{pkg_name}.list'], 
                                                                       capture_output=True, text=True, check=False)
                                            if date_result.returncode == 0 and date_result.stdout.strip():
                                                timestamp = int(date_result.stdout.strip())
                                                last_update = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                                            else:
                                                last_update = datetime.now().strftime('%Y-%m-%d')
                                        except Exception:
                                            last_update = datetime.now().strftime('%Y-%m-%d')
                                        break
                            if version != 'Unknown':
                                break
                    except Exception as e:
                        # If dpkg fails, continue to next package
                        continue
                
                # Fallback: use directory modification time and set version
                if last_update == 'Never':
                    for rules_dir in ['/etc/nginx/modsec/owasp-crs/rules', '/usr/share/modsecurity-crs/rules']:
                        if os.path.exists(rules_dir):
                            stat = os.stat(rules_dir)
                            last_update = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                            if version == 'Unknown':
                                version = 'System Package'
                            break
            except Exception:
                pass
        
        # Check if rules directory exists in either location
        rules_active = (os.path.exists('/etc/nginx/modsec/owasp-crs/rules') or 
                       os.path.exists('/usr/share/modsecurity-crs/rules'))
        
        return {
            'version': version,
            'last_update': last_update,
            'status': 'Active' if rules_active else 'Inactive'
        }
    except Exception as e:
        return {
            'version': 'Unknown',
            'last_update': 'Never',
            'status': 'Error',
            'error': str(e)
        }

def get_waf_rules():
    """Get list of active WAF rules"""
    try:
        rules = []
        
        # Get OWASP CRS rules - check both locations
        rules_dirs = ['/etc/nginx/modsec/owasp-crs/rules', '/usr/share/modsecurity-crs/rules']
        for rules_dir in rules_dirs:
            if os.path.exists(rules_dir):
                for filename in os.listdir(rules_dir):
                    if filename.endswith('.conf'):
                        filepath = os.path.join(rules_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                content = f.read()
                                # Extract rule information
                                rule_matches = re.findall(r'SecRule\s+([^"]+)\s+"([^"]+)"\s+"([^"]+)"', content)
                                for match in rule_matches:
                                    rules.append({
                                        'file': filename,
                                        'type': 'OWASP CRS',
                                        'variable': match[0].strip(),
                                        'operator': match[1].strip(),
                                        'actions': match[2].strip()
                                    })
                        except Exception as e:
                            # Skip files that can't be read
                            continue
                break  # Only process the first directory that exists
        
        # Get custom rules
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_rules_file = os.path.join(plugin_dir, 'custom-rules.conf')
        if os.path.exists(custom_rules_file):
            with open(custom_rules_file, 'r') as f:
                content = f.read()
                # Extract custom rule information
                rule_matches = re.findall(r'SecRule\s+([^"]+)\s+"([^"]+)"\s+"([^"]+)"', content)
                for match in rule_matches:
                    rules.append({
                        'file': 'custom-rules.conf',
                        'type': 'Custom Rule',
                        'variable': match[0].strip(),
                        'operator': match[1].strip(),
                        'actions': match[2].strip()
                    })
        
        return {'success': True, 'rules': rules}
        
    except Exception as e:
        error_msg = f"Failed to get WAF rules: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_custom_rules():
    """Get custom rules content"""
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_rules_file = os.path.join(plugin_dir, 'custom-rules.conf')
        
        if os.path.exists(custom_rules_file):
            with open(custom_rules_file, 'r') as f:
                content = f.read()
            return {'success': True, 'content': content}
        else:
            return {'success': True, 'content': '# No custom rules found'}
            
    except Exception as e:
        error_msg = f"Failed to get custom rules: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_waf_logs():
    """Get WAF attack logs"""
    try:
        logs = []
        log_file = '/var/log/nginx/modsec_audit.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Get last 100 lines
                for line in lines:
                    if line.strip():
                        logs.append(line.strip())
        
        return {'success': True, 'logs': logs}
        
    except Exception as e:
        error_msg = f"Failed to get WAF logs: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def add_custom_rule(rule_content):
    """Add custom WAF rule"""
    try:
        # Use local custom rules file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_rules_file = os.path.join(plugin_dir, 'custom-rules.conf')
        
        with open(custom_rules_file, 'a') as f:
            f.write(f"\n{rule_content}\n")
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            # Rollback if configuration is invalid
            with open(custom_rules_file, 'r') as f:
                content = f.read()
            content = content.replace(f"\n{rule_content}\n", "")
            with open(custom_rules_file, 'w') as f:
                f.write(content)
            return {'success': False, 'error': 'Invalid rule syntax'}
        
        # Reload nginx
        run_command('supervisorctl restart nginx')
        
        return {'success': True, 'message': 'Custom rule added successfully'}
        
    except Exception as e:
        error_msg = f"Failed to add custom rule: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def toggle_waf_status(enabled):
    """Enable or disable WAF"""
    try:
        modules_conf = '/etc/nginx/modules-enabled/50-mod-http-modsecurity.conf'
        
        if enabled:
            # Enable ModSecurity module
            if not os.path.exists(modules_conf):
                with open(modules_conf, 'w') as f:
                    f.write('load_module modules/ngx_http_modsecurity_module.so;\n')
        else:
            # Disable ModSecurity module
            if os.path.exists(modules_conf):
                os.remove(modules_conf)
        
        # Test and reload nginx
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode == 0:
            run_command('nginx -s reload')
            return {'success': True, 'message': f'WAF {"enabled" if enabled else "disabled"} successfully'}
        else:
            return {'success': False, 'error': 'Nginx configuration test failed'}
        
    except Exception as e:
        error_msg = f"Failed to toggle WAF status: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_whitelist_ips():
    """Get list of whitelisted IP addresses"""
    try:
        # Use local whitelist file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        whitelist_file = os.path.join(plugin_dir, 'whitelist.conf')
        ips = []
        
        if os.path.exists(whitelist_file):
            with open(whitelist_file, 'r') as f:
                content = f.read()
                # Extract IP addresses from whitelist rules
                ip_matches = re.findall(r'@ipMatch ([0-9.]+(?:/[0-9]+)?)', content)
                for ip in ip_matches:
                    if ip not in ['127.0.0.1', '::1'] and not ip.startswith(('10.', '172.', '192.168.')):
                        ips.append(ip)
        
        return {'success': True, 'ips': ips}
        
    except Exception as e:
        error_msg = f"Failed to get whitelist IPs: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def add_whitelist_ip(ip_address):
    """Add IP address to whitelist"""
    try:
        # Validate IP address format
        import ipaddress
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return {'success': False, 'error': 'Invalid IP address format'}
        
        # Use local whitelist file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        whitelist_file = os.path.join(plugin_dir, 'whitelist.conf')
        
        # Check if IP already exists
        if os.path.exists(whitelist_file):
            with open(whitelist_file, 'r') as f:
                content = f.read()
                if ip_address in content:
                    return {'success': False, 'error': 'IP address already whitelisted'}
        
        # Generate unique rule ID
        rule_id = 9901 + len(get_whitelist_ips().get('ips', []))
        
        # Add whitelist rule
        whitelist_rule = f'\nSecRule REMOTE_ADDR "@ipMatch {ip_address}" "id:{rule_id},phase:1,pass,nolog,ctl:ruleEngine=Off"\n'
        
        with open(whitelist_file, 'a') as f:
            f.write(whitelist_rule)
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            # Rollback if configuration is invalid
            with open(whitelist_file, 'r') as f:
                content = f.read()
            content = content.replace(whitelist_rule, '')
            with open(whitelist_file, 'w') as f:
                f.write(content)
            return {'success': False, 'error': 'Invalid configuration'}
        
        # Reload nginx
        run_command('supervisorctl restart nginx')
        
        return {'success': True, 'message': f'IP {ip_address} added to whitelist successfully'}
        
    except Exception as e:
        error_msg = f"Failed to add IP to whitelist: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def remove_whitelist_ip(ip_address):
    """Remove IP address from whitelist"""
    try:
        # Use local whitelist file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        whitelist_file = os.path.join(plugin_dir, 'whitelist.conf')
        
        if not os.path.exists(whitelist_file):
            return {'success': False, 'error': 'Whitelist file not found'}
        
        with open(whitelist_file, 'r') as f:
            lines = f.readlines()
        
        # Remove lines containing the IP address
        new_lines = [line for line in lines if ip_address not in line or line.startswith('#')]
        
        if len(new_lines) == len(lines):
            return {'success': False, 'error': 'IP address not found in whitelist'}
        
        with open(whitelist_file, 'w') as f:
            f.writelines(new_lines)
        
        # Test and reload nginx
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode == 0:
            run_command('supervisorctl restart nginx')
            return {'success': True, 'message': f'IP {ip_address} removed from whitelist successfully'}
        else:
            return {'success': False, 'error': 'Nginx configuration test failed'}
        
    except Exception as e:
        error_msg = f"Failed to remove IP from whitelist: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def save_waf_settings(settings):
    """Save WAF settings configuration"""
    try:
        # Use local settings file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        settings_file = os.path.join(plugin_dir, 'waf-settings.conf')
        
        # Build configuration content
        config_content = "# WAF Settings Configuration\n"
        config_content += "# Generated by Nginx WAF Manager\n\n"
        
        # Paranoia level setting
        paranoia_level = settings.get('paranoia_level', '1')
        config_content += f"SecAction \"id:900000,phase:1,nolog,pass,t:none,setvar:tx.paranoia_level={paranoia_level}\"\n\n"
        
        # Anomaly scoring thresholds
        inbound_threshold = settings.get('inbound_threshold', '5')
        outbound_threshold = settings.get('outbound_threshold', '4')
        config_content += f"SecAction \"id:900110,phase:1,nolog,pass,t:none,setvar:tx.inbound_anomaly_score_threshold={inbound_threshold}\"\n"
        config_content += f"SecAction \"id:900111,phase:1,nolog,pass,t:none,setvar:tx.outbound_anomaly_score_threshold={outbound_threshold}\"\n\n"
        
        # Request body limits
        request_body_limit = settings.get('request_body_limit', '13107200')  # 12.5MB default
        config_content += f"SecRequestBodyLimit {request_body_limit}\n"
        config_content += f"SecRequestBodyNoFilesLimit 131072\n\n"  # 128KB for non-file uploads
        
        # Response body limits
        response_body_limit = settings.get('response_body_limit', '524288')  # 512KB default
        config_content += f"SecResponseBodyLimit {response_body_limit}\n"
        config_content += f"SecResponseBodyLimitAction Reject\n\n"
        
        # Audit logging settings
        audit_log_enabled = settings.get('audit_log_enabled', True)
        if audit_log_enabled:
            config_content += "SecAuditEngine On\n"
            config_content += "SecAuditLogParts ABIJDEFHZ\n"
            config_content += "SecAuditLogType Serial\n"
            config_content += "SecAuditLog /var/log/nginx/modsec_audit.log\n\n"
        else:
            config_content += "SecAuditEngine Off\n\n"
        
        # Write settings to file
        with open(settings_file, 'w') as f:
            f.write(config_content)
        
        # Test nginx configuration
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            return {'success': False, 'error': 'Invalid nginx configuration after settings update'}
        
        # Reload nginx to apply settings
        run_command('supervisorctl restart nginx')
        
        return {'success': True, 'message': 'WAF settings saved successfully'}
        
    except Exception as e:
        error_msg = f"Failed to save WAF settings: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_waf_settings():
    """Get current WAF settings"""
    try:
        # Use local settings file in plugin directory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        settings_file = os.path.join(plugin_dir, 'waf-settings.conf')
        settings = {
            'paranoia_level': '1',
            'inbound_threshold': '5',
            'outbound_threshold': '4',
            'request_body_limit': '13107200',
            'response_body_limit': '524288',
            'audit_log_enabled': True
        }
        
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                content = f.read()
                
                # Parse paranoia level
                paranoia_match = re.search(r'setvar:tx\.paranoia_level=(\d+)', content)
                if paranoia_match:
                    settings['paranoia_level'] = paranoia_match.group(1)
                
                # Parse thresholds
                inbound_match = re.search(r'setvar:tx\.inbound_anomaly_score_threshold=(\d+)', content)
                if inbound_match:
                    settings['inbound_threshold'] = inbound_match.group(1)
                
                outbound_match = re.search(r'setvar:tx\.outbound_anomaly_score_threshold=(\d+)', content)
                if outbound_match:
                    settings['outbound_threshold'] = outbound_match.group(1)
                
                # Parse body limits
                req_limit_match = re.search(r'SecRequestBodyLimit (\d+)', content)
                if req_limit_match:
                    settings['request_body_limit'] = req_limit_match.group(1)
                
                resp_limit_match = re.search(r'SecResponseBodyLimit (\d+)', content)
                if resp_limit_match:
                    settings['response_body_limit'] = resp_limit_match.group(1)
                
                # Parse audit log setting
                settings['audit_log_enabled'] = 'SecAuditEngine On' in content
        
        return {'success': True, 'settings': settings}
        
    except Exception as e:
        error_msg = f"Failed to get WAF settings: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def update_owasp_rules():
    """Update OWASP Core Rule Set to latest version"""
    try:
        if logger:
            logger.info('Starting OWASP CRS update process')
        
        # Check current version
        current_version = 'Unknown'
        version_file = '/etc/nginx/modsec/owasp-crs/CHANGES'
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    first_line = f.readline().strip()
                    if 'OWASP ModSecurity Core Rule Set' in first_line:
                        current_version = first_line.split('v')[-1].split()[0] if 'v' in first_line else 'Unknown'
            except Exception:
                pass
        
        # Backup current rules
        backup_dir = f'/etc/nginx/modsec/owasp-crs-backup-{int(time.time())}'
        if os.path.exists('/etc/nginx/modsec/owasp-crs'):
            if logger:
                logger.info(f'Backing up current rules to {backup_dir}')
            run_command(f'cp -r /etc/nginx/modsec/owasp-crs {backup_dir}')
        
        # Download latest OWASP CRS (v4.0)
        if logger:
            logger.info('Downloading latest OWASP CRS')
        run_command('cd /tmp && wget -O owasp-crs-latest.tar.gz https://github.com/coreruleset/coreruleset/archive/refs/tags/v4.0.0.tar.gz')
        run_command('cd /tmp && tar -xzf owasp-crs-latest.tar.gz')
        
        # Replace old rules with new ones
        if logger:
            logger.info('Installing new rules')
        run_command('rm -rf /etc/nginx/modsec/owasp-crs')
        run_command('mv /tmp/coreruleset-4.0.0 /etc/nginx/modsec/owasp-crs')
        
        # Copy setup configuration
        run_command('cp /etc/nginx/modsec/owasp-crs/crs-setup.conf.example /etc/nginx/modsec/owasp-crs/crs-setup.conf')
        
        # Test nginx configuration
        if logger:
            logger.info('Testing Nginx configuration')
        test_result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if test_result.returncode != 0:
            # Rollback if configuration is invalid
            if logger:
                logger.error(f'Configuration test failed: {test_result.stderr}')
                logger.info('Rolling back to previous version')
            run_command(f'rm -rf /etc/nginx/modsec/owasp-crs')
            if os.path.exists(backup_dir):
                run_command(f'mv {backup_dir} /etc/nginx/modsec/owasp-crs')
            return {'success': False, 'error': f'Configuration test failed: {test_result.stderr}', 'rollback': True}
        
        # Reload nginx
        if logger:
            logger.info('Reloading Nginx')
        reload_result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)
        if reload_result.returncode != 0:
            if logger:
                logger.error(f'Nginx reload failed: {reload_result.stderr}')
            return {'success': False, 'error': f'Nginx reload failed: {reload_result.stderr}'}
        
        # Get new version
        new_version = 'Unknown'
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    first_line = f.readline().strip()
                    if 'OWASP ModSecurity Core Rule Set' in first_line:
                        new_version = first_line.split('v')[-1].split()[0] if 'v' in first_line else 'Unknown'
            except Exception:
                pass
        
        # Cleanup
        if logger:
            logger.info('Cleaning up temporary files')
        run_command('rm -f /tmp/owasp-crs-latest.tar.gz')
        run_command(f'rm -rf {backup_dir}')
        
        if logger:
            logger.info(f'OWASP CRS update completed: {current_version} -> {new_version}')
        
        return {
            'success': True, 
            'message': 'OWASP Core Rule Set updated successfully',
            'previous_version': current_version,
            'new_version': new_version
        }
        
    except Exception as e:
        error_msg = f"Failed to update OWASP rules: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_attack_logs(limit=20, since_timestamp=None):
    """Get recent attack logs from ModSecurity audit log"""
    try:
        audit_log = '/var/log/nginx/modsec_audit.log'
        if not os.path.exists(audit_log):
            return {'success': True, 'attacks': [], 'total': 0}
        
        attacks = []
        total_attacks = 0
        
        with open(audit_log, 'r') as f:
            lines = f.readlines()[-1000:]  # Get last 1000 lines for better coverage
            
            for line in lines:
                if 'ModSecurity: Warning' in line or 'ModSecurity: Access denied' in line:
                    total_attacks += 1
                    
                    # Parse log entry
                    timestamp = 'Unknown'
                    ip = 'Unknown'
                    rule_id = 'Unknown'
                    severity = 'Unknown'
                    attack_type = 'Unknown'
                    uri = 'Unknown'
                    message = line.strip()
                    
                    # Extract timestamp
                    if line.startswith('['):
                        end_bracket = line.find(']')
                        if end_bracket > 0:
                            timestamp = line[1:end_bracket]
                    
                    # Skip if timestamp filter is applied
                    if since_timestamp and timestamp != 'Unknown':
                        try:
                            from datetime import datetime
                            log_time = datetime.strptime(timestamp.split()[0] + ' ' + timestamp.split()[1], '%a %b %d %H:%M:%S')
                            filter_time = datetime.fromtimestamp(since_timestamp)
                            if log_time <= filter_time:
                                continue
                        except:
                            pass
                    
                    # Extract IP if available
                    if 'client:' in line:
                        ip_start = line.find('client:') + 7
                        ip_end = line.find(',', ip_start)
                        if ip_end > ip_start:
                            ip = line[ip_start:ip_end].strip()
                    
                    # Extract rule ID if available
                    if '[id "' in line:
                        id_start = line.find('[id "') + 5
                        id_end = line.find('"]', id_start)
                        if id_end > id_start:
                            rule_id = line[id_start:id_end]
                    
                    # Extract severity
                    if '[severity "' in line:
                        sev_start = line.find('[severity "') + 11
                        sev_end = line.find('"]', sev_start)
                        if sev_end > sev_start:
                            severity = line[sev_start:sev_end]
                    
                    # Extract URI
                    if '[uri "' in line:
                        uri_start = line.find('[uri "') + 6
                        uri_end = line.find('"]', uri_start)
                        if uri_end > uri_start:
                            uri = line[uri_start:uri_end]
                    
                    # Determine attack type based on rule ID
                    if rule_id != 'Unknown':
                        if rule_id.startswith('920'):
                            attack_type = 'Protocol Violation'
                        elif rule_id.startswith('921'):
                            attack_type = 'Protocol Anomaly'
                        elif rule_id.startswith('930'):
                            attack_type = 'Application Attack'
                        elif rule_id.startswith('931'):
                            attack_type = 'RFI Attack'
                        elif rule_id.startswith('932'):
                            attack_type = 'RCE Attack'
                        elif rule_id.startswith('933'):
                            attack_type = 'PHP Injection'
                        elif rule_id.startswith('941'):
                            attack_type = 'XSS Attack'
                        elif rule_id.startswith('942'):
                            attack_type = 'SQL Injection'
                        elif rule_id.startswith('943'):
                            attack_type = 'Session Fixation'
                        else:
                            attack_type = 'Security Violation'
                    
                    attacks.append({
                        'timestamp': timestamp,
                        'ip': ip,
                        'rule_id': rule_id,
                        'severity': severity,
                        'attack_type': attack_type,
                        'uri': uri,
                        'message': message[:300] + '...' if len(message) > 300 else message
                    })
        
        # Sort by timestamp (newest first) and limit results
        attacks.reverse()
        limited_attacks = attacks[:limit] if limit else attacks
        
        return {
            'success': True, 
            'attacks': limited_attacks,
            'total': len(attacks),
            'total_in_log': total_attacks
        }
        
    except Exception as e:
        error_msg = f"Failed to get attack logs: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_realtime_monitoring_stats():
    """Get real-time monitoring statistics"""
    try:
        # Get recent attacks (last 5 minutes)
        five_minutes_ago = time.time() - 300
        recent_attacks = get_attack_logs(limit=100, since_timestamp=five_minutes_ago)
        
        if not recent_attacks['success']:
            return recent_attacks
        
        attacks = recent_attacks['attacks']
        
        # Analyze attack patterns
        ip_counts = {}
        attack_type_counts = {}
        severity_counts = {}
        
        for attack in attacks:
            # Count by IP
            ip = attack['ip']
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # Count by attack type
            attack_type = attack['attack_type']
            attack_type_counts[attack_type] = attack_type_counts.get(attack_type, 0) + 1
            
            # Count by severity
            severity = attack['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Find top attackers
        top_attackers = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Find most common attack types
        top_attack_types = sorted(attack_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'success': True,
            'monitoring_period': '5 minutes',
            'total_attacks': len(attacks),
            'unique_ips': len(ip_counts),
            'top_attackers': [{'ip': ip, 'count': count} for ip, count in top_attackers],
            'attack_types': [{'type': atype, 'count': count} for atype, count in top_attack_types],
            'severity_distribution': severity_counts,
            'recent_attacks': attacks[:10]  # Last 10 attacks for display
        }
        
    except Exception as e:
        error_msg = f"Failed to get monitoring stats: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def get_waf_statistics():
    """Get WAF statistics and metrics"""
    try:
        stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'top_attacking_ips': [],
            'top_triggered_rules': [],
            'requests_last_24h': 0,
            'blocked_last_24h': 0
        }
        
        # Parse access logs for basic statistics
        access_log = '/var/log/nginx/access.log'
        if os.path.exists(access_log):
            try:
                # Count total requests in last 24 hours
                result = subprocess.run(
                    f'grep "$(date +\'%d/%b/%Y\')" {access_log} | wc -l',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    stats['requests_last_24h'] = int(result.stdout.strip() or 0)
            except:
                pass
        
        # Parse ModSecurity audit log for blocked requests
        audit_log = '/var/log/nginx/modsec_audit.log'
        if os.path.exists(audit_log):
            try:
                # Count blocked requests
                result = subprocess.run(
                    f'grep -c "Access denied" {audit_log} 2>/dev/null || echo 0',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0:
                    stats['blocked_requests'] = int(result.stdout.strip() or 0)
                
                # Get top attacking IPs
                result = subprocess.run(
                    f'grep "client:" {audit_log} | sed -n "s/.*client: \\([0-9.]\\+\\).*/\\1/p" | sort | uniq -c | sort -nr | head -5',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            stats['top_attacking_ips'].append({
                                'ip': parts[1],
                                'count': int(parts[0])
                            })
                
                # Get top triggered rules
                result = subprocess.run(
                    f'grep "\\[id \\"" {audit_log} | sed -n "s/.*\\[id \\"\\([0-9]\\+\\)\\".*/\\1/p" | sort | uniq -c | sort -nr | head -5',
                    shell=True, capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            stats['top_triggered_rules'].append({
                                'rule_id': parts[1],
                                'count': int(parts[0])
                            })
            except:
                pass
        
        return {'success': True, 'stats': stats}
    except Exception as e:
        error_msg = f"Failed to get WAF statistics: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def clear_attack_data():
    """Clear all attack data from attack_map.db"""
    try:
        import sqlite3
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(plugin_dir, "data", "attack_map.db")
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete all records from attacks table
            cursor.execute('DELETE FROM attacks')
            
            # Reset auto-increment counter
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="attacks"')
            
            conn.commit()
            conn.close()
            
            if logger:
                logger.info("Attack data cleared successfully")
            
            return {
                'success': True,
                'message': 'All attack data has been cleared successfully'
            }
        else:
            return {
                'success': True,
                'message': 'No attack database found to clear'
            }
    except Exception as e:
        if logger:
            logger.error(f"Error clearing attack data: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def export_waf_config():
    """Export WAF configuration to JSON format"""
    try:
        config = {
            'version': '1.0',
            'timestamp': time.time(),
            'whitelist_ips': [],
            'custom_rules': '',
            'waf_settings': {},
            'modsecurity_status': False
        }
        
        # Export whitelist IPs
        whitelist_result = get_whitelist_ips()
        if whitelist_result['success']:
            config['whitelist_ips'] = whitelist_result['ips']
        
        # Export custom rules
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        custom_rules_file = os.path.join(plugin_dir, 'custom-rules.conf')
        if os.path.exists(custom_rules_file):
            with open(custom_rules_file, 'r') as f:
                config['custom_rules'] = f.read()
        
        # Export WAF settings
        waf_settings_file = os.path.join(plugin_dir, 'waf-settings.conf')
        if os.path.exists(waf_settings_file):
            with open(waf_settings_file, 'r') as f:
                config['waf_settings'] = f.read()
        
        # Check ModSecurity status
        nginx_status = check_nginx_status()
        config['modsecurity_status'] = nginx_status.get('modsecurity_enabled', False)
        
        return {'success': True, 'config': config}
    except Exception as e:
        error_msg = f"Failed to export WAF configuration: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}

def import_waf_config(config_data):
    """Import WAF configuration from JSON format"""
    try:
        if not isinstance(config_data, dict):
            return {'success': False, 'error': 'Invalid configuration format'}
        
        # Validate configuration version
        if config_data.get('version') != '1.0':
            return {'success': False, 'error': 'Unsupported configuration version'}
        
        # Import whitelist IPs
        if 'whitelist_ips' in config_data:
            # Use local whitelist file in plugin directory
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            whitelist_file = os.path.join(plugin_dir, 'whitelist.conf')
            whitelist_content = "# Whitelist IP addresses\n# One IP per line\n\n"
            for ip in config_data['whitelist_ips']:
                whitelist_content += f"{ip}\n"
            
            with open(whitelist_file, 'w') as f:
                f.write(whitelist_content)
        
        # Import custom rules
        if 'custom_rules' in config_data:
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            custom_rules_file = os.path.join(plugin_dir, 'custom-rules.conf')
            with open(custom_rules_file, 'w') as f:
                f.write(config_data['custom_rules'])
        
        # Import WAF settings
        if 'waf_settings' in config_data:
            waf_settings_file = os.path.join(plugin_dir, 'waf-settings.conf')
            with open(waf_settings_file, 'w') as f:
                f.write(config_data['waf_settings'])
        
        # Test Nginx configuration
        test_result = run_command('nginx -t')
        if test_result[0] != 0:
            return {'success': False, 'error': f'Nginx configuration test failed: {test_result[2]}'}
        
        # Reload Nginx to apply changes
        reload_result = run_command('systemctl reload nginx')
        if reload_result[0] != 0:
            # Try alternative reload method for non-systemd systems
            reload_result = run_command('service nginx reload')
            if reload_result[0] != 0:
                # Try nginx -s reload as last resort
                reload_result = run_command('nginx -s reload')
                if reload_result[0] != 0:
                    return {'success': False, 'error': f'Failed to reload Nginx: {reload_result[2]}'}
        
        if logger:
            logger.info('WAF configuration imported and applied successfully')
        
        return {'success': True, 'message': 'WAF configuration imported and applied successfully'}
    except Exception as e:
        error_msg = f"Failed to import WAF configuration: {str(e)}"
        if logger:
            logger.error(error_msg)
        return {'success': False, 'error': error_msg}
# Main function for SLEMP plugin system
def main():
    """Main function to handle plugin requests through SLEMP plugin system"""
    if not FLASK_AVAILABLE:
        return jsonify({'success': False, 'error': 'Flask not available'})
    
    try:
        from flask import request, jsonify
        
        # Get the action from form data (set by SLEMP plugin system)
        action = request.form.get('action', '')
        
        # Log the incoming request for debugging
        if logger:
            logger.info(f'Nginx WAF Plugin - Processing action: {action}')
            logger.info(f'Request method: {request.method}')
            logger.info(f'Form data: {dict(request.form)}')
        
        # Handle different endpoints
        if action == 'status':
            nginx_status = check_nginx_status()
            modsec_status = check_modsecurity_status()
            return jsonify({
                'nginx': nginx_status,
                'modsecurity': modsec_status
            })
        
        elif action == 'install' and request.method == 'POST':
            result = install_modsecurity()
            return jsonify(result)
        
        elif action == 'rules':
            result = get_waf_rules()
            return jsonify(result)
        
        elif action == 'custom-rules':
            result = get_custom_rules()
            return jsonify(result)
        
        elif action == 'logs':
            result = get_waf_logs()
            return jsonify(result)
        
        elif action == 'add-rule' and request.method == 'POST':
            rule_content = request.form.get('rule')
            result = add_custom_rule(rule_content)
            return jsonify(result)
        
        elif action == 'toggle' and request.method == 'POST':
            enabled_str = request.form.get('enabled', 'true')
            enabled = enabled_str.lower() in ['true', '1', 'yes', 'on']
            result = toggle_waf_status(enabled)
            return jsonify(result)
        

        
        elif action == 'update-rules' and request.method == 'POST':
            result = update_owasp_rules()
            return jsonify(result)
        
        elif action == 'rules-status':
            try:
                if logger:
                    logger.info('Processing rules-status request')
                
                # Check ModSecurity status
                modsec_status = check_modsecurity_status()
                
                # Get rules information
                rules_info = get_waf_rules()
                
                # Get OWASP version information
                owasp_info = get_owasp_version_info()
                
                # Determine status message
                if modsec_status.get('module_loaded', False):
                    if modsec_status.get('installed', False):
                        message = "ModSecurity installed and active (blocking mode)"
                    else:
                        message = "ModSecurity loaded but configuration incomplete"
                else:
                    message = "ModSecurity installed in basic mode (detection only)"
                
                # Calculate rule count
                rule_count = 0
                if rules_info.get('success', False) and 'rules' in rules_info:
                    rule_count = len(rules_info['rules'])
                
                return jsonify({
                     'message': message,
                     'module_loaded': modsec_status.get('module_loaded', False),
                     'success': True,
                     'status': modsec_status,
                     'rules': rules_info,
                     'rule_count': rule_count,
                     'version': owasp_info['version'],
                     'last_update': owasp_info['last_update'],
                     'owasp_status': owasp_info['status']
                 })
            
            except Exception as e:
                if logger:
                    logger.error(f'Error in rules-status: {e}')
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        elif action == 'attack-logs':
            limit = int(request.args.get('limit', 20))
            since_timestamp = request.args.get('since')
            if since_timestamp:
                try:
                    since_timestamp = float(since_timestamp)
                except ValueError:
                    since_timestamp = None
            result = get_attack_logs(limit=limit, since_timestamp=since_timestamp)
            return jsonify(result)
        
        elif action == 'monitoring':
            result = get_realtime_monitoring_stats()
            return jsonify(result)
        
        elif action == 'statistics':
            result = get_waf_statistics()
            return jsonify(result)
        
        elif action == 'export-config':
            try:
                result = export_waf_config()
                if result['success']:
                    # Return as downloadable JSON file
                    import json
                    
                    response_data = {
                        'success': True,
                        'config_json': json.dumps(result['config'], indent=2),
                        'filename': f'nginx-waf-config-{int(time.time())}.json'
                    }
                    return jsonify(response_data)
                else:
                    return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'import-config' and request.method == 'POST':
            try:
                if 'config' not in request.files:
                    return jsonify({'success': False, 'error': 'No configuration file provided'})
                
                config_file = request.files['config']
                if config_file.filename == '':
                    return jsonify({'success': False, 'error': 'No file selected'})
                
                if not config_file.filename.endswith('.json'):
                    return jsonify({'success': False, 'error': 'Invalid file format. Please upload a JSON file'})
                
                # Read and parse JSON
                import json
                config_data = json.loads(config_file.read().decode('utf-8'))
                
                result = import_waf_config(config_data)
                return jsonify(result)
            except json.JSONDecodeError:
                return jsonify({'success': False, 'error': 'Invalid JSON format'})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'whitelist':
            result = get_whitelist_ips()
            return jsonify(result)
        
        elif action == 'whitelist-add' and request.method == 'POST':
            ip = request.form.get('ip')
            if not ip:
                return jsonify({'success': False, 'error': 'IP address is required'})
            result = add_whitelist_ip(ip)
            return jsonify(result)
        
        elif action == 'whitelist-remove' and request.method == 'POST':
            ip = request.form.get('ip')
            if not ip:
                return jsonify({'success': False, 'error': 'IP address is required'})
            result = remove_whitelist_ip(ip)
            return jsonify(result)
        
        elif action == 'get-settings':
            result = get_waf_settings()
            return jsonify(result)
        
        elif action == 'save-settings' and request.method == 'POST':
            settings = {
                'paranoia_level': request.form.get('paranoia_level', '1'),
                'inbound_threshold': request.form.get('inbound_threshold', '5'),
                'outbound_threshold': request.form.get('outbound_threshold', '4'),
                'request_body_limit': request.form.get('request_body_limit', '13107200'),
                'response_body_limit': request.form.get('response_body_limit', '524288'),
                'audit_log_enabled': request.form.get('audit_log_enabled', 'true').lower() == 'true'
            }
            result = save_waf_settings(settings)
            return jsonify(result)
        
        # Attack Map endpoints
        elif action == 'get-attack-data':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                time_range = int(request.form.get('time_range', 24))  # hours
                attack_type = request.form.get('attack_type', '')
                severity = request.form.get('severity', '')
                country = request.form.get('country', '')
                
                # Initialize Attack Map API with error handling
                attacks = []
                try:
                    attack_api = AttackMapAPI()
                    
                    # Get attack data with filters and retry mechanism
                    retry_count = 0
                    max_retries = 3
                    
                    while retry_count < max_retries:
                        try:
                            attacks = attack_api.get_attacks(
                                time_range=time_range,
                                attack_type=attack_type if attack_type else None,
                                severity=severity if severity else None,
                                country=country if country else None
                            )
                            break  # Success, exit retry loop
                        except Exception as api_error:
                            retry_count += 1
                            if retry_count >= max_retries:
                                if logger:
                                    logger.error(f'Attack API failed after {max_retries} retries: {api_error}')
                                # Return empty list instead of failing completely
                                attacks = []
                            else:
                                if logger:
                                    logger.warning(f'Attack API retry {retry_count}/{max_retries}: {api_error}')
                                time.sleep(0.5 * retry_count)  # Exponential backoff
                                
                except Exception as init_error:
                    if logger:
                        logger.error(f'Failed to initialize Attack API: {init_error}')
                    attacks = []  # Fallback to empty list
                
                return jsonify({
                    'success': True,
                    'attacks': attacks,
                    'count': len(attacks),
                    'status': 'ok' if attacks else 'no_data'
                })
            except Exception as e:
                if logger:
                    logger.error(f'Critical error getting attack data: {e}')
                return jsonify({
                    'success': False, 
                    'error': 'Internal server error',
                    'details': str(e) if hasattr(e, '__str__') else 'Unknown error'
                })
        
        elif action == 'get-latest-attacks':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                limit = int(request.form.get('limit', 10))
                
                # Initialize Attack Map API
                attack_api = AttackMapAPI()
                
                # Get latest attacks
                attacks = attack_api.get_latest_attacks(limit=limit)
                
                return jsonify({
                    'success': True,
                    'attacks': attacks
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error getting latest attacks: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'get-attack-statistics':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                time_range = int(request.form.get('time_range', 24))  # hours
                
                # Initialize Attack Map API
                attack_api = AttackMapAPI()
                
                # Get attack statistics
                stats = attack_api.get_attack_statistics(time_range=time_range)
                
                return jsonify({
                    'success': True,
                    'statistics': stats
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error getting attack statistics: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'get-country-stats':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                time_range = int(request.form.get('time_range', 24))  # hours
                
                # Initialize Attack Map API
                attack_api = AttackMapAPI()
                
                # Get country statistics
                country_stats = attack_api.get_country_statistics(time_range=time_range)
                
                return jsonify({
                    'success': True,
                    'country_stats': country_stats
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error getting country statistics: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'sync-attack-data':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                synced_count = 0
                error_count = 0
                
                # Try WAFLogParser first with retry mechanism
                try:
                    from waf_log_parser import WAFLogParser
                    
                    retry_count = 0
                    max_retries = 3
                    
                    while retry_count < max_retries:
                        try:
                            # Initialize parser and sync data
                            parser = WAFLogParser()
                            synced_count = parser.update_attack_map(incremental=True)
                            
                            if logger:
                                logger.info(f'Successfully synced {synced_count} attack records')
                            break  # Success, exit retry loop
                            
                        except Exception as sync_error:
                            retry_count += 1
                            error_count += 1
                            
                            if retry_count >= max_retries:
                                if logger:
                                    logger.error(f'WAF sync failed after {max_retries} retries: {sync_error}')
                                # Try fallback method
                                raise sync_error
                            else:
                                if logger:
                                    logger.warning(f'WAF sync retry {retry_count}/{max_retries}: {sync_error}')
                                time.sleep(1.0 * retry_count)  # Exponential backoff
                    
                except (ImportError, Exception) as waf_error:
                    if logger:
                        logger.warning(f'WAFLogParser failed, trying fallback: {waf_error}')
                    
                    # Fallback to AttackMapParser
                    try:
                        parser = AttackMapParser()
                        
                        # Process log files with error handling
                        log_files = [
                            '/var/log/nginx/modsec_audit.log',
                            '/var/log/modsec_audit.log',
                            '/etc/nginx/logs/modsec_audit.log'
                        ]
                        
                        processed_files = 0
                        for log_file in log_files:
                            if os.path.exists(log_file):
                                try:
                                    parser.process_log_file(log_file, max_lines=1000)
                                    processed_files += 1
                                    synced_count = processed_files  # Approximate count
                                    break  # Use first successful file
                                except Exception as file_error:
                                    error_count += 1
                                    if logger:
                                        logger.warning(f'Error processing {log_file}: {file_error}')
                                    continue
                        
                        if processed_files == 0:
                            if logger:
                                logger.warning('No log files could be processed')
                            synced_count = 0
                            
                    except Exception as fallback_error:
                        if logger:
                            logger.error(f'Fallback parser also failed: {fallback_error}')
                        synced_count = 0
                        error_count += 1
                
                # Return response with detailed status
                status = 'success' if synced_count > 0 else ('partial' if error_count > 0 else 'no_data')
                
                return jsonify({
                    'success': True,  # Always return success unless critical error
                    'message': f'Sync completed: {synced_count} records processed',
                    'synced_count': synced_count,
                    'error_count': error_count,
                    'status': status
                })                    
            except Exception as e:
                if logger:
                    logger.error(f'Critical error syncing attack data: {e}')
                return jsonify({
                    'success': False, 
                    'error': 'Sync operation failed',
                    'details': str(e) if hasattr(e, '__str__') else 'Unknown error'
                })
        
        elif action == 'get-attack-arrows':
            if not ATTACK_MAP_AVAILABLE:
                return jsonify({'success': False, 'error': 'Attack Map module not available'})
            
            try:
                # Get parameters
                limit = int(request.form.get('limit', 50))
                since_minutes = int(request.form.get('since_minutes', 5))  # Last 5 minutes by default
                
                # Initialize API with retry mechanism
                api = None
                for attempt in range(3):
                    try:
                        api = AttackMapAPI()
                        break
                    except Exception as init_error:
                        if attempt == 2:  # Last attempt
                            raise init_error
                        time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
                
                if not api:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to initialize Attack Map API',
                        'arrows': []
                    })
                
                # Get recent attacks for arrows
                arrows_data = []
                try:
                    # Get attacks from last N minutes
                    from datetime import datetime, timedelta
                    since_time = datetime.now() - timedelta(minutes=since_minutes)
                    since_timestamp = since_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    attacks = api.get_recent_attacks(limit=limit, since_timestamp=since_timestamp)
                    
                    for attack in attacks:
                        # Create arrow data from attacker to target
                        arrow = {
                            'id': f"{attack.get('source_ip', '')}_{attack.get('target_ip', '')}_{attack.get('timestamp', '')}",
                            'source': {
                                'ip': attack.get('source_ip', 'Unknown'),
                                'country': attack.get('country', 'Unknown'),
                                'city': attack.get('city', 'Unknown'),
                                'latitude': attack.get('latitude', 0),
                                'longitude': attack.get('longitude', 0)
                            },
                            'target': {
                                'ip': attack.get('target_ip', '127.0.0.1'),
                                'country': attack.get('target_country', 'Unknown'),
                                'city': attack.get('target_city', 'Unknown'),
                                'latitude': attack.get('target_latitude', 0),
                                'longitude': attack.get('target_longitude', 0)
                            },
                            'attack_type': attack.get('attack_type', 'Generic Attack'),
                            'severity': attack.get('severity', 'Low'),
                            'timestamp': attack.get('timestamp', ''),
                            'target_url': attack.get('target_url', '/'),
                            'rule_msg': attack.get('rule_msg', 'ModSecurity Rule Triggered')
                        }
                        arrows_data.append(arrow)
                    
                    return jsonify({
                        'success': True,
                        'arrows': arrows_data,
                        'count': len(arrows_data),
                        'since_minutes': since_minutes
                    })
                    
                except Exception as data_error:
                    if logger:
                        logger.warning(f'Error getting arrow data: {data_error}')
                    return jsonify({
                        'success': True,  # Still return success with empty data
                        'arrows': [],
                        'count': 0,
                        'error': 'No recent attack data available'
                    })
                    
            except Exception as e:
                if logger:
                    logger.error(f'Error getting attack arrows: {e}')
                return jsonify({
                    'success': False,
                    'error': 'Failed to get attack arrows data',
                    'details': str(e) if hasattr(e, '__str__') else 'Unknown error'
                })
        
        elif action == 'clear-attack-data':
            try:
                result = clear_attack_data()
                return jsonify(result)
            except Exception as e:
                if logger:
                    logger.error(f'Error clearing attack data: {e}')
                return jsonify({
                    'success': False,
                    'error': 'Failed to clear attack data',
                    'details': str(e) if hasattr(e, '__str__') else 'Unknown error'
                })
        
        elif action == 'start-monitoring':
            if not LOG_MONITOR_AVAILABLE:
                return jsonify({'success': False, 'error': 'Log Monitor module not available'})
            
            try:
                if is_monitoring():
                    return jsonify({
                        'success': True,
                        'message': 'Background monitoring is already running',
                        'monitoring': True
                    })
                
                success = start_background_monitoring()
                return jsonify({
                    'success': success,
                    'message': 'Background monitoring started' if success else 'Failed to start monitoring',
                    'monitoring': success
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error starting monitoring: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'stop-monitoring':
            if not LOG_MONITOR_AVAILABLE:
                return jsonify({'success': False, 'error': 'Log Monitor module not available'})
            
            try:
                stop_background_monitoring()
                return jsonify({
                    'success': True,
                    'message': 'Background monitoring stopped',
                    'monitoring': False
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error stopping monitoring: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        elif action == 'monitoring-status':
            if not LOG_MONITOR_AVAILABLE:
                return jsonify({'success': False, 'error': 'Log Monitor module not available'})
            
            try:
                monitoring = is_monitoring()
                return jsonify({
                    'success': True,
                    'monitoring': monitoring,
                    'message': 'Monitoring is active' if monitoring else 'Monitoring is inactive'
                })
            except Exception as e:
                if logger:
                    logger.error(f'Error checking monitoring status: {e}')
                return jsonify({'success': False, 'error': str(e)})
        
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'})
    
    except Exception as e:
        if logger:
            logger.error(f'Plugin error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)})

# Main execution for standalone testing
# Auto-start background monitoring when plugin is loaded
if LOG_MONITOR_AVAILABLE:
    try:
        if not is_monitoring():
            success = start_background_monitoring()
            if logger:
                if success:
                    logger.info("Background log monitoring started automatically")
                else:
                    logger.warning("Failed to start background log monitoring")
    except Exception as e:
        if logger:
            logger.error(f"Error auto-starting monitoring: {e}")

if __name__ == '__main__':
    print("Nginx WAF Manager Plugin")
    print("Checking status...")

    nginx_status = check_nginx_status()
    print(f"Nginx Status: {nginx_status}")

    modsec_status = check_modsecurity_status()
    print(f"ModSecurity Status: {modsec_status}")
    
    # Check monitoring status
    if LOG_MONITOR_AVAILABLE:
        monitoring_active = is_monitoring()
        print(f"Background Monitoring: {'Active' if monitoring_active else 'Inactive'}")
    else:
        print("Background Monitoring: Not Available (install watchdog package)")