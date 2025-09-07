loadNginxStatus();
checkCertbotStatus();
loadVirtualHosts();

// Function to refresh Nginx status
function refreshNginxStatus() {
    // Show loading state
    document.getElementById('nginx-active-connections').textContent = 'Loading...';
    document.getElementById('nginx-requests-per-sec').textContent = 'Loading...';
    document.getElementById('nginx-total-requests').textContent = 'Loading...';
    document.getElementById('nginx-server-load').textContent = 'Loading...';
    document.getElementById('nginx-uptime').textContent = 'Loading...';
    document.getElementById('nginx-version').textContent = 'Loading...';
    document.getElementById('nginx-workers').textContent = 'Loading...';
    document.getElementById('nginx-reading').textContent = 'Loading...';
    document.getElementById('nginx-writing').textContent = 'Loading...';
    document.getElementById('nginx-waiting').textContent = 'Loading...';
    
    loadNginxStatus();
}

// Function to load Nginx status data
function loadNginxStatus() {
    fetch('/api/nginx/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('nginx-active-connections').textContent = data.active_connections || '0';
                document.getElementById('nginx-requests-per-sec').textContent = data.requests_per_sec || '0';
                document.getElementById('nginx-total-requests').textContent = data.total_requests || '0';
                document.getElementById('nginx-server-load').textContent = data.server_load || '0%';
                document.getElementById('nginx-uptime').textContent = data.uptime || 'Unknown';
                document.getElementById('nginx-version').textContent = data.version || 'Unknown';
                document.getElementById('nginx-workers').textContent = data.worker_processes || '0';
                document.getElementById('nginx-reading').textContent = data.reading || '0';
                document.getElementById('nginx-writing').textContent = data.writing || '0';
                document.getElementById('nginx-waiting').textContent = data.waiting || '0';
            } else {
                // Show error state
                document.getElementById('nginx-active-connections').textContent = 'Error';
                document.getElementById('nginx-requests-per-sec').textContent = 'Error';
                document.getElementById('nginx-total-requests').textContent = 'Error';
                document.getElementById('nginx-server-load').textContent = 'Error';
                document.getElementById('nginx-uptime').textContent = 'Error';
                document.getElementById('nginx-version').textContent = 'Error';
                document.getElementById('nginx-workers').textContent = 'Error';
                document.getElementById('nginx-reading').textContent = 'Error';
                document.getElementById('nginx-writing').textContent = 'Error';
                document.getElementById('nginx-waiting').textContent = 'Error';
            }
        })
        .catch(error => {
            console.error('Error loading Nginx status:', error);
            // Show error state
            document.getElementById('nginx-active-connections').textContent = 'N/A';
            document.getElementById('nginx-requests-per-sec').textContent = 'N/A';
            document.getElementById('nginx-total-requests').textContent = 'N/A';
            document.getElementById('nginx-server-load').textContent = 'N/A';
            document.getElementById('nginx-uptime').textContent = 'N/A';
            document.getElementById('nginx-version').textContent = 'N/A';
            document.getElementById('nginx-workers').textContent = 'N/A';
            document.getElementById('nginx-reading').textContent = 'N/A';
            document.getElementById('nginx-writing').textContent = 'N/A';
            document.getElementById('nginx-waiting').textContent = 'N/A';
        });
}

// Function to check Certbot installation status
async function checkCertbotStatus() {
    try {
        const response = await fetch('/api/certbot/status');
        const data = await response.json();
        
        const certbotBtn = document.getElementById('certbot-install-btn');
        if (certbotBtn && data.success) {
            if (data.installed) {
                // Certbot is installed - disable button and change text
                certbotBtn.disabled = true;
                certbotBtn.onclick = null;
                certbotBtn.className = 'inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-gray-400 cursor-not-allowed';
                certbotBtn.innerHTML = `
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    Certbot Installed
                `;
                certbotBtn.title = `Certbot is already installed: ${data.version}`;
            } else {
                // Certbot is not installed - keep button enabled
                certbotBtn.disabled = false;
                certbotBtn.className = 'inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500';
            }
        }
    } catch (error) {
        console.error('Error checking Certbot status:', error);
    }
}

// Nginx Config Functions
async function editNginxConfig() {
    try {
        const response = await fetch('/api/nginx/config');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('nginx-config-content').value = data.content;
            document.getElementById('nginx-config-modal').classList.remove('hidden');
        } else {
            showNotification(`Gagal memuat konfigurasi: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat memuat konfigurasi Nginx', 'error');
    }
}

function closeNginxConfigModal() {
    document.getElementById('nginx-config-modal').classList.add('hidden');
}

async function saveNginxConfig() {
    try {
        const content = document.getElementById('nginx-config-content').value;
        const response = await fetch('/api/nginx/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Konfigurasi Nginx berhasil disimpan', 'success');
            closeNginxConfigModal();
        } else {
            showNotification(`Gagal menyimpan konfigurasi: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat menyimpan konfigurasi Nginx', 'error');
    }
}

// Install Certbot Function
async function installCertbot() {
    if (!(await showConfirm('Are you sure you want to install Certbot? This will run: apt install certbot python3-certbot-nginx -y', 'Install Certbot'))) return;

    // Show installation modal
    showInstallModal('Certbot');
    
    // Update progress
    updateInstallProgress('Memulai instalasi Certbot...', '1/3', 10);
    addInstallOutput('Starting Certbot installation...', 'info');
    addInstallOutput('apt update && apt install certbot python3-certbot-nginx -y', 'command');

    try {
        // Connect to WebSocket for real-time output
        const socket = io();
        
        socket.on('certbot_install_output', function(data) {
            addInstallOutput(data.message, data.type || 'info');
        });
        
        socket.on('certbot_install_progress', function(data) {
            updateCertbotProgress(data.status, data.step, data.progress);
        });
        
        socket.on('certbot_install_complete', function(data) {
            if (data.success) {
                addInstallOutput('Certbot installation completed successfully!', 'success');
                updateCertbotProgress('Installation completed', '3/3', 100);
                showNotification('Certbot installed successfully!', 'success');
                
                // Update the Certbot button status
                checkCertbotStatus();
            } else {
                addInstallOutput(`Installation failed: ${data.error}`, 'error');
                updateCertbotProgress('Installation failed', '3/3', 100);
                showNotification(data.error || 'Failed to install Certbot', 'error');
            }
            
            // Re-enable close button
            const closeBtn = document.getElementById('install-close-btn');
            const cancelBtn = document.getElementById('install-cancel-btn');
            closeBtn.style.display = 'block';
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            
            socket.disconnect();
        });
        
        const response = await fetch('/api/certbot/install', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const data = await response.json();
            addInstallOutput(`Installation failed: ${data.error}`, 'error');
            updateInstallProgress('Installation failed', '3/3', 100);
            showNotification(data.error || 'Failed to install Certbot', 'error');
            
            // Re-enable close button
            const closeBtn = document.getElementById('install-close-btn');
            const cancelBtn = document.getElementById('install-cancel-btn');
            closeBtn.style.display = 'block';
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
    } catch (error) {
        console.error('Error installing Certbot:', error);
        addInstallOutput(`Installation error: ${error.message}`, 'error');
        updateCertbotProgress('Installation failed', '3/3', 100);
        showNotification('Failed to install Certbot. Please try again.', 'error');
        
        // Re-enable close button
        const closeBtn = document.getElementById('install-close-btn');
        const cancelBtn = document.getElementById('install-cancel-btn');
        closeBtn.style.display = 'block';
        cancelBtn.textContent = 'Close';
        cancelBtn.disabled = false;
        cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Update installation progress for certbot (different parameter order)
function updateCertbotProgress(status, step, progress) {
    const statusElement = document.getElementById('install-status');
    const stepElement = document.getElementById('install-step');
    const progressBar = document.getElementById('install-progress-bar');
    
    if (statusElement) statusElement.textContent = status;
    if (stepElement) stepElement.textContent = step;
    if (progressBar) progressBar.style.width = `${progress}%`;
}

// Virtual Host Management
async function createVirtualHost() {
    const domain = await showPrompt('Enter domain name:', '', 'Add Virtual Host');
    if (!domain) return;

    const rootDir = await showPrompt('Enter root directory:', '/opt/slemp/data/www/' + domain, 'Root Directory');
    if (!rootDir) return;

    try {
        const response = await fetch('/api/nginx/create-vhost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                root_dir: rootDir
            })
        });

        if (response.ok) {
            loadVirtualHosts();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error creating virtual host', 'Error');
        }
    } catch (error) {
        console.error('Error creating virtual host:', error);
        showAlert('Error creating virtual host', 'Error');
    }
}

async function createDefaultSite() {
    try {
        // Get list of available virtual hosts
        const response = await fetch('/api/nginx/vhosts');
        if (!response.ok) {
            showAlert('Error loading virtual hosts', 'Error');
            return;
        }
        
        const vhosts = await response.json();
        if (!vhosts || vhosts.length === 0) {
            showAlert('No virtual hosts found. Please create a virtual host first.', 'Warning');
            return;
        }
        
        // Create options for the dropdown
        const options = vhosts.map(vhost => `<option value="${vhost.domain}">${vhost.domain}</option>`).join('');
        
        // Show custom modal with dropdown
        const modalHtml = `
            <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" id="defaultSiteModal">
                <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                    <div class="mt-3 text-center">
                        <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">Set Default Site</h3>
                        <div class="mt-2 px-7 py-3">
                            <p class="text-sm text-gray-500 dark:text-gray-300 mb-4">
                                Select a virtual host to set as the default site. This will add 'default_server' to the listen directives.
                            </p>
                            <select id="defaultSiteSelect" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                                <option value="">Select a site...</option>
                                ${options}
                            </select>
                        </div>
                        <div class="items-center px-4 py-3">
                            <button id="confirmDefaultSite" class="px-4 py-2 bg-purple-500 text-white text-base font-medium rounded-md w-24 mr-2 hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-300">
                                Set
                            </button>
                            <button id="cancelDefaultSite" class="px-4 py-2 bg-gray-500 text-white text-base font-medium rounded-md w-24 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-300">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Handle confirm button
        document.getElementById('confirmDefaultSite').onclick = async () => {
            const selectedDomain = document.getElementById('defaultSiteSelect').value;
            if (!selectedDomain) {
                showAlert('Please select a site', 'Warning');
                return;
            }
            
            try {
                const setResponse = await fetch('/api/nginx/create-default-site', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        domain: selectedDomain
                    })
                });
                
                if (setResponse.ok) {
                    showAlert(`Successfully set ${selectedDomain} as default site`, 'Success');
                    loadVirtualHosts();
                } else {
                    const error = await setResponse.json();
                    showAlert(error.error || 'Error setting default site', 'Error');
                }
            } catch (error) {
                console.error('Error setting default site:', error);
                showAlert('Error setting default site', 'Error');
            }
            
            // Remove modal
            document.getElementById('defaultSiteModal').remove();
        };
        
        // Handle cancel button
        document.getElementById('cancelDefaultSite').onclick = () => {
            document.getElementById('defaultSiteModal').remove();
        };
        
        // Handle click outside modal
        document.getElementById('defaultSiteModal').onclick = (e) => {
            if (e.target.id === 'defaultSiteModal') {
                document.getElementById('defaultSiteModal').remove();
            }
        };
        
    } catch (error) {
        console.error('Error in createDefaultSite:', error);
        showAlert('Error loading virtual hosts', 'Error');
    }
}

async function loadVirtualHosts() {
    try {
        const response = await fetch('/api/nginx/vhosts');
        
        // Check if response is successful
        if (!response.ok) {
            console.error('Error loading virtual hosts: HTTP', response.status);
            return;
        }
        
        let vhosts;
        try {
            vhosts = await response.json();
        } catch (jsonError) {
            console.error('Error parsing virtual hosts response as JSON:', jsonError);
            return;
        }
        
        const vhostList = document.getElementById('vhost-list');
        vhostList.innerHTML = '';

        // Check if response contains error or is not an array
        if (vhosts.error || !Array.isArray(vhosts)) {
            console.error('Error loading virtual hosts:', vhosts.error || 'Invalid response format');
            vhostList.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Unable to load virtual hosts: ${vhosts.error || 'Authentication required'}
                    </td>
                </tr>
            `;
            return;
        }

        try {
            vhosts.forEach(vhost => {
                vhostList.innerHTML += `
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                            <a href="http://${vhost.domain}" target="_blank" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline">${vhost.domain}</a>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                            <a href="/files?path=${encodeURIComponent(vhost.root_dir)}" class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline cursor-pointer">${vhost.root_dir}</a>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${vhost.enabled ? 'Enabled' : 'Disabled'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                            <button onclick="openVHostSettings('${vhost.domain}', '${vhost.root_dir}', ${vhost.enabled})" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-2">Settings</button>
                            <button onclick="toggleVHost('${vhost.domain}', ${!vhost.enabled})" class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-2">${vhost.enabled ? 'Disable' : 'Enable'}</button>
                            <button onclick="deleteVHost('${vhost.domain}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                        </td>
                    </tr>`;
            });
        } catch (forEachError) {
            console.error('Error iterating virtual hosts:', forEachError);
            vhostList.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Error displaying virtual hosts
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading virtual hosts:', error);
    }
}

async function deleteVHost(domain) {
    if (!(await showConfirm(`Are you sure you want to delete virtual host '${domain}'?`, 'Konfirmasi Hapus'))) return;

    try {
        const response = await fetch('/api/nginx/delete-vhost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain
            })
        });

        if (response.ok) {
            loadVirtualHosts();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error deleting virtual host', 'Error');
        }
    } catch (error) {
        console.error('Error deleting virtual host:', error);
        showAlert('Error deleting virtual host', 'Error');
    }
}

async function toggleVHost(domain, enable) {
    try {
        const response = await fetch('/api/nginx/toggle-vhost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                enable: enable
            })
        });

        if (response.ok) {
            loadVirtualHosts();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error toggling virtual host', 'Error');
        }
    } catch (error) {
        console.error('Error toggling virtual host:', error);
        showAlert('Error toggling virtual host', 'Error');
    }
}

// Virtual Host Settings Management
function openVHostSettings(domain, rootDir, enabled) {
    document.getElementById('vhost-domain').value = domain;
    document.getElementById('vhost-root-dir').value = rootDir;
    document.getElementById('vhost-status').value = enabled.toString();
    
    // Set config filename
    document.getElementById('config-filename').textContent = domain;
    
    // Reset to first tab
    switchVHostTab('domain');
    
    document.getElementById('vhost-settings-modal').classList.remove('hidden');
}

function closeVHostSettingsModal() {
    document.getElementById('vhost-settings-modal').classList.add('hidden');
    resetVHostForm();
}

function resetVHostForm() {
    // Reset all form fields
    document.getElementById('vhost-domain').value = '';
    document.getElementById('vhost-root-dir').value = '';
    document.getElementById('vhost-status').value = 'true';
    document.getElementById('vhost-ssl').checked = false;
    document.getElementById('vhost-ssl-cert').value = '';
    document.getElementById('vhost-ssl-key').value = '';
    document.getElementById('vhost-force-https').checked = false;
    document.getElementById('vhost-php-version').value = '8.1';
    document.getElementById('vhost-rewrite-rules').value = '';
    document.getElementById('vhost-index-files').value = '';
    document.getElementById('vhost-error-404').value = '';
    document.getElementById('vhost-error-500').value = '';
    document.getElementById('vhost-proxy-enabled').checked = false;
    document.getElementById('vhost-proxy-pass').value = '';
    document.getElementById('vhost-proxy-headers').value = '';
    document.getElementById('vhost-modsecurity-enabled').checked = true;
    document.getElementById('vhost-modsecurity-rules').value = '/etc/nginx/modsec/main.conf';
    document.getElementById('vhost-custom-config').value = '';
    
    // Reset config textarea flags
    const configTextarea = document.getElementById('vhost-custom-config');
    if (configTextarea) {
        configTextarea.dataset.manualEdit = 'false';
        configTextarea.dataset.loadedFromFile = 'false';
        configTextarea.dataset.allowFormUpdate = 'true';
    }
    
    // Reset to General tab
    switchVHostTab('general');
}

function switchVHostTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.vhost-tab-content');
    tabContents.forEach(content => {
        content.classList.add('hidden');
    });

    // Reset all tab buttons
    const tabButtons = document.querySelectorAll('.vhost-tab-btn');
    tabButtons.forEach(button => {
        button.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        button.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });

    // Show selected tab content
    const selectedContent = document.getElementById(`content-${tabName}`);
    if (selectedContent) {
        selectedContent.classList.remove('hidden');
    }

    // Activate selected tab button
    const selectedButton = document.getElementById(`tab-${tabName}`);
    if (selectedButton) {
        selectedButton.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        selectedButton.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
    }

    // Don't auto-load config anymore, user will use Load Config button
    
    // Auto-check SSL certificates when SSL tab is clicked
    if (tabName === 'ssl') {
        checkExistingSSLCertificates();
        // Also check SSL certificate info automatically
        setTimeout(() => {
            checkSSLCertificate();
        }, 500);
    }
}

async function loadVHostConfig() {
    const domain = document.getElementById('vhost-domain').value;
    if (!domain) {
        showAlert('Please select a virtual host first.');
        return;
    }

    try {
        const response = await fetch(`/api/nginx/config/${domain}`);
        if (response.ok) {
            const data = await response.json();
            const configTextarea = document.getElementById('vhost-custom-config');
            configTextarea.value = data.config || '';
            // Mark as loaded from file and reset manual edit flag
            configTextarea.dataset.loadedFromFile = 'true';
            configTextarea.dataset.manualEdit = 'false';
            configTextarea.dataset.allowFormUpdate = 'false';
            showAlert('Configuration loaded successfully!', 'Success');
        } else {
            const error = await response.json();
            showAlert(`Failed to load configuration: ${error.message}`, 'Error');
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showAlert('Failed to load configuration. Please try again.', 'Error');
    }
}

async function checkExistingSSLCertificates() {
    const domain = document.getElementById('vhost-domain').value;
    if (!domain) {
        return;
    }

    try {
        const response = await fetch(`/api/ssl/check/${domain}`);
        if (response.ok) {
            const data = await response.json();
            if (data.cert_exists && data.key_exists) {
                // Auto-fill SSL certificate paths
                document.getElementById('vhost-ssl-cert').value = data.cert_path;
                document.getElementById('vhost-ssl-key').value = data.key_path;
                
                // Show notification
                showNotification(`SSL certificate found for ${domain}`, 'success');
            }
        }
    } catch (error) {
        console.error('Error checking SSL certificates:', error);
    }
}

async function saveVHostSettings(showSuccessAlert = true, closeModal = true) {
    const domain = document.getElementById('vhost-domain').value;
    const rootDir = document.getElementById('vhost-root-dir').value;
    const enabled = document.getElementById('vhost-status').value === 'true';
    const ssl = document.getElementById('vhost-ssl').checked;
    const sslCert = document.getElementById('vhost-ssl-cert').value;
    const sslKey = document.getElementById('vhost-ssl-key').value;
    const forceHttps = document.getElementById('vhost-force-https').checked;
    const phpVersion = document.getElementById('vhost-php-version').value;
    const customConfig = document.getElementById('vhost-custom-config').value;
    
    // Collect proxy settings
    const proxyEnabled = document.getElementById('vhost-proxy-enabled').checked;
    const proxyPass = document.getElementById('vhost-proxy-pass').value;
    const proxyHeaders = document.getElementById('vhost-proxy-headers').value;
    
    // Collect WAF settings
    const modsecurityEnabled = document.getElementById('vhost-modsecurity-enabled').checked;
    const modsecurityRules = document.getElementById('vhost-modsecurity-rules').value;
    
    // Collect rewrite settings
    const rewriteRules = document.getElementById('vhost-rewrite-rules').value;
    
    // Collect default settings
    const indexFiles = document.getElementById('vhost-index-files').value;
    const error404 = document.getElementById('vhost-error-404').value;
    const error500 = document.getElementById('vhost-error-500').value;

    try {
        const response = await fetch('/api/nginx/update-vhost', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                root_dir: rootDir,
                enabled: enabled,
                ssl: ssl,
                ssl_cert: sslCert,
                ssl_key: sslKey,
                force_https: forceHttps,
                php_version: phpVersion,
                custom_config: customConfig,
                proxy_enabled: proxyEnabled,
                proxy_pass: proxyPass,
                proxy_headers: proxyHeaders,
                modsecurity_enabled: modsecurityEnabled,
                modsecurity_rules: modsecurityRules,
                rewrite_rules: rewriteRules,
                index_files: indexFiles,
                error_404: error404,
                error_500: error500
            })
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                if (showSuccessAlert) {
                    showAlert('Virtual host settings updated successfully!', 'Success');
                }
                if (closeModal) {
                    closeVHostSettingsModal();
                }
                loadVirtualHosts(); // Refresh the list
            } else {
                showAlert(result.error || 'Error updating virtual host settings', 'Error');
            }
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error updating virtual host settings', 'Error');
        }
    } catch (error) {
        console.error('Error updating virtual host settings:', error);
        showAlert('Error updating virtual host settings', 'Error');
    }
}

async function generateLetsEncryptSSL() {
    const domain = document.getElementById('vhost-domain').value;
    const email = document.getElementById('vhost-letsencrypt-email').value;

    if (!domain) {
        showAlert('Domain is required', 'Error');
        return;
    }

    if (!email) {
        showAlert('Email address is required for Let\'s Encrypt', 'Error');
        return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address', 'Error');
        return;
    }

    // Show installation modal
    showInstallModal('Let\'s Encrypt SSL');
    
    // Update progress
    updateInstallProgress('1', '4', 'Memulai proses generate SSL certificate...', 10);
    addInstallOutput('Starting Let\'s Encrypt SSL certificate generation...', 'info');
    addInstallOutput(`Domain: ${domain}`, 'info');
    addInstallOutput(`Email: ${email}`, 'info');

    try {
        // Connect to WebSocket for real-time output
        const socket = io();
        
        socket.on('ssl_generate_output', function(data) {
            addInstallOutput(data.message, data.type || 'info');
        });
        
        socket.on('ssl_generate_progress', function(data) {
            updateInstallProgress(data.step || '1', '4', data.status, data.progress);
        });
        
        socket.on('ssl_generate_complete', function(data) {
            if (data.success) {
                addInstallOutput('SSL certificate generated successfully!', 'success');
                updateInstallProgress('4', '4', 'SSL certificate generated', 100);
                
                // Update SSL certificate paths if provided
                if (data.cert_path) {
                    document.getElementById('vhost-ssl-cert').value = data.cert_path;
                }
                if (data.key_path) {
                    document.getElementById('vhost-ssl-key').value = data.key_path;
                }
                
                // Enable SSL checkbox
                document.getElementById('vhost-ssl').checked = true;
                
                // Auto-save virtual host settings with new SSL configuration
                setTimeout(async () => {
                    try {
                        await saveVHostSettings(false, false); // Don't show alert, don't close modal
                        showNotification('SSL certificate generated and virtual host updated successfully!', 'success');
                    } catch (error) {
                        console.error('Error auto-saving virtual host settings:', error);
                        showNotification('SSL certificate generated successfully! Please save settings manually.', 'warning');
                    }
                }, 1000);
            } else {
                addInstallOutput(`SSL generation failed: ${data.error}`, 'error');
                updateInstallProgress('4', '4', 'SSL generation failed', 100);
                showNotification(data.error || 'Failed to generate SSL certificate', 'error');
            }
            
            // Re-enable close button
            const closeBtn = document.getElementById('install-close-btn');
            const cancelBtn = document.getElementById('install-cancel-btn');
            closeBtn.style.display = 'block';
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            
            socket.disconnect();
        });
        
        const response = await fetch('/api/ssl/letsencrypt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                email: email
            })
        });

        if (!response.ok) {
            const data = await response.json();
            addInstallOutput(`SSL generation failed: ${data.error}`, 'error');
            updateInstallProgress('4', '4', 'SSL generation failed', 100);
            showNotification(data.error || 'Failed to generate SSL certificate', 'error');
            
            // Re-enable close button
            const closeBtn = document.getElementById('install-close-btn');
            const cancelBtn = document.getElementById('install-cancel-btn');
            closeBtn.style.display = 'block';
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
    } catch (error) {
        console.error('Error generating SSL certificate:', error);
        addInstallOutput(`SSL generation error: ${error.message}`, 'error');
        updateInstallProgress('4', '4', 'SSL generation failed', 100);
        showNotification('Failed to generate SSL certificate. Please try again.', 'error');
        
        // Re-enable close button
        const closeBtn = document.getElementById('install-close-btn');
        const cancelBtn = document.getElementById('install-cancel-btn');
        closeBtn.style.display = 'block';
        cancelBtn.textContent = 'Close';
        cancelBtn.disabled = false;
        cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Check SSL Certificate Information
async function checkSSLCertificate() {
    const domain = document.getElementById('vhost-domain').value;
    const sslCert = document.getElementById('vhost-ssl-cert').value;
    
    if (!domain) {
        showAlert('Domain is required', 'Error');
        return;
    }
    
    // Reset SSL info display
    document.getElementById('vhost-ssl-status').textContent = 'Checking...';
    document.getElementById('vhost-ssl-expiry').textContent = 'Checking...';
    document.getElementById('vhost-ssl-days-left').textContent = 'Checking...';
    
    try {
        const response = await fetch('/api/ssl/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                cert_path: sslCert
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update SSL status
            const statusElement = document.getElementById('vhost-ssl-status');
            const expiryElement = document.getElementById('vhost-ssl-expiry');
            const daysLeftElement = document.getElementById('vhost-ssl-days-left');
            
            statusElement.textContent = data.status || 'Valid';
            statusElement.className = statusElement.className.replace(/text-\w+-\d+/g, '');
            
            if (data.valid) {
                statusElement.classList.add('text-green-600', 'dark:text-green-400');
            } else {
                statusElement.classList.add('text-red-600', 'dark:text-red-400');
            }
            
            // Update expiry date
            if (data.expiry_date) {
                expiryElement.textContent = new Date(data.expiry_date).toLocaleDateString('id-ID', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } else {
                expiryElement.textContent = 'Not available';
            }
            
            // Update days left
            if (data.days_left !== undefined) {
                daysLeftElement.textContent = `${data.days_left} days`;
                daysLeftElement.className = daysLeftElement.className.replace(/text-\w+-\d+/g, '');
                
                if (data.days_left > 30) {
                    daysLeftElement.classList.add('text-green-600', 'dark:text-green-400');
                } else if (data.days_left > 7) {
                    daysLeftElement.classList.add('text-yellow-600', 'dark:text-yellow-400');
                } else {
                    daysLeftElement.classList.add('text-red-600', 'dark:text-red-400');
                }
            } else {
                daysLeftElement.textContent = 'Not available';
            }
            
            showNotification('SSL certificate checked successfully', 'success');
        } else {
            document.getElementById('vhost-ssl-status').textContent = data.error || 'Check failed';
            document.getElementById('vhost-ssl-expiry').textContent = 'Not available';
            document.getElementById('vhost-ssl-days-left').textContent = 'Not available';
            
            showAlert(data.error || 'Failed to check SSL certificate', 'Error');
        }
    } catch (error) {
        console.error('Error checking SSL certificate:', error);
        document.getElementById('vhost-ssl-status').textContent = 'Check failed';
        document.getElementById('vhost-ssl-expiry').textContent = 'Not available';
        document.getElementById('vhost-ssl-days-left').textContent = 'Not available';
        
        showAlert('Error checking SSL certificate', 'Error');
    }
}

// Virtual Host Config Generator
function generateVHostConfig() {
    const domain = document.getElementById('vhost-domain').value;
    const rootDir = document.getElementById('vhost-root-dir').value;
    const ssl = document.getElementById('vhost-ssl').checked;
    const sslCert = document.getElementById('vhost-ssl-cert').value;
    const sslKey = document.getElementById('vhost-ssl-key').value;
    const forceHttps = document.getElementById('vhost-force-https').checked;
    const phpVersion = document.getElementById('vhost-php-version').value;
    const rewriteRules = document.getElementById('vhost-rewrite-rules').value;
    const indexFiles = document.getElementById('vhost-index-files').value || 'index.html index.htm index.php';
    const error404 = document.getElementById('vhost-error-404').value;
    const error500 = document.getElementById('vhost-error-500').value;
    const proxyEnabled = document.getElementById('vhost-proxy-enabled').checked;
    const proxyPass = document.getElementById('vhost-proxy-pass').value;
    const proxyHeaders = document.getElementById('vhost-proxy-headers').value;
    const modsecurity = document.getElementById('vhost-modsecurity-enabled').checked;
    const modsecurityRules = document.getElementById('vhost-modsecurity-rules').value;

    let config = `server {\n    listen 80;`;

    // Add SSL configuration if enabled (following app.py structure)
    if (ssl && sslCert && sslKey) {
        config += `\n    listen 443 ssl;\n    ssl_certificate ${sslCert};\n    ssl_certificate_key ${sslKey};\n    ssl_protocols TLSv1.2 TLSv1.3;\n    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;\n    ssl_prefer_server_ciphers on;\n    ssl_session_cache shared:SSL:10m;\n    ssl_session_timeout 10m;`;
    }

    config += `\n    server_name ${domain};\n    root ${rootDir};\n\n    index ${indexFiles};\n`;

    // Add ModSecurity configuration if enabled
    if (modsecurity) {
        config += `\n    # ModSecurity WAF\n    modsecurity on;\n    modsecurity_rules_file ${modsecurityRules || '/etc/nginx/modsec/main.conf'};\n`;
    }

    // Add HTTPS redirect if force_https is enabled
    if (ssl && forceHttps) {
        config += `\n    # Redirect HTTP to HTTPS\n    if ($scheme != "https") {\n        return 301 https://$server_name$request_uri;\n    }\n`;
    }

    // Add custom error pages if specified
    if (error404) {
        config += `\n    error_page 404 ${error404};\n`;
    }
    if (error500) {
        config += `\n    error_page 500 502 503 504 ${error500};\n`;
    }

    // Add rewrite rules if specified
    if (rewriteRules) {
        config += `\n    # Custom rewrite rules\n${rewriteRules}\n`;
    }

    // Add proxy configuration if enabled
    if (proxyEnabled && proxyPass) {
        config += `\n    location / {\n        proxy_pass ${proxyPass};\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;`;
        
        // Add custom proxy headers if specified
        if (proxyHeaders) {
            const headers = proxyHeaders.trim().split('\n');
            headers.forEach(header => {
                if (header.trim()) {
                    let headerClean = header.trim();
                    if (!headerClean.endsWith(';')) {
                        headerClean += ';';
                    }
                    config += `\n        ${headerClean}`;
                }
            });
        }
        
        config += `\n    }\n`;
    } else {
        // Standard location block for non-proxy setup
        config += `\n    location / {\n        try_files $uri $uri/ /index.php?$query_string;\n    }\n\n    location ~ \\.php$ {\n        include snippets/fastcgi-php.conf;\n        fastcgi_pass unix:/run/php/php${phpVersion || '8.1'}-fpm.sock;\n    }\n\n    location ~ /\\.ht {\n        deny all;\n    }\n`;
    }

    config += `}`;

    return config;
}

function updateConfigFromForm() {
    const configTextarea = document.getElementById('vhost-custom-config');
    // Only update if:
    // 1. Not manually edited by user
    // 2. AND (not loaded from file OR explicitly allowed to update)
    if (configTextarea && 
        configTextarea.dataset.manualEdit !== 'true' && 
        (configTextarea.dataset.loadedFromFile !== 'true' || configTextarea.dataset.allowFormUpdate === 'true')) {
        configTextarea.value = generateVHostConfig();
    }
}

// Load config from file when modal opens (one time only)
async function loadVHostConfigOnOpen(domain) {
    if (!domain) return;
    
    try {
        const response = await fetch(`/api/nginx/config/${domain}`);
        if (response.ok) {
            const data = await response.json();
            const configTextarea = document.getElementById('vhost-custom-config');
            if (data.config && data.config.trim()) {
                // If config exists, load it and mark as loaded from file
                configTextarea.value = data.config;
                configTextarea.dataset.loadedFromFile = 'true';
            } else {
                // If no config exists, generate from form and allow updates
                configTextarea.value = generateVHostConfig();
                configTextarea.dataset.loadedFromFile = 'false';
            }
        } else {
            // If failed to load, generate from form
            const configTextarea = document.getElementById('vhost-custom-config');
            configTextarea.value = generateVHostConfig();
            configTextarea.dataset.loadedFromFile = 'false';
        }
    } catch (error) {
        console.error('Error loading config:', error);
        // If error, generate from form
        const configTextarea = document.getElementById('vhost-custom-config');
        configTextarea.value = generateVHostConfig();
        configTextarea.dataset.loadedFromFile = 'false';
    }
}

// Add event listeners for form inputs
function initVHostFormListeners() {
    const inputs = [
            'vhost-domain', 'vhost-root-dir', 'vhost-ssl-cert', 'vhost-ssl-key',
            'vhost-force-https', 'vhost-php-version', 'vhost-rewrite-rules',
            'vhost-index-files', 'vhost-error-404', 'vhost-error-500',
            'vhost-proxy-enabled', 'vhost-proxy-pass', 'vhost-proxy-headers',
            'vhost-modsecurity-enabled', 'vhost-modsecurity-rules'
        ];

    inputs.forEach(inputId => {
        const element = document.getElementById(inputId);
        if (element) {
            if (element.type === 'checkbox') {
                element.addEventListener('change', updateConfigFromForm);
            } else {
                element.addEventListener('input', updateConfigFromForm);
            }
        }
    });

    // Special handlers for key checkboxes to trigger config update
    const triggerCheckboxes = ['vhost-ssl', 'vhost-proxy-enabled', 'vhost-force-https', 'vhost-modsecurity-enabled'];
    triggerCheckboxes.forEach(checkboxId => {
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                const configTextarea = document.getElementById('vhost-custom-config');
                if (configTextarea) {
                    // Allow form update when key settings are toggled
                    configTextarea.dataset.allowFormUpdate = 'true';
                    updateConfigFromForm();
                }
            });
        }
    });

    // Special handlers for key input fields to trigger config update
    const triggerInputs = ['vhost-rewrite-rules', 'vhost-proxy-pass', 'vhost-proxy-headers', 'vhost-ssl-cert', 'vhost-ssl-key', 'vhost-modsecurity-rules'];
    triggerInputs.forEach(inputId => {
        const inputElement = document.getElementById(inputId);
        if (inputElement) {
            inputElement.addEventListener('input', function() {
                const configTextarea = document.getElementById('vhost-custom-config');
                if (configTextarea) {
                    // Allow form update when key fields are modified
                    configTextarea.dataset.allowFormUpdate = 'true';
                    updateConfigFromForm();
                }
            });
        }
    });

    // Mark config as manually edited when user types in textarea
    const configTextarea = document.getElementById('vhost-custom-config');
    if (configTextarea) {
        configTextarea.addEventListener('input', function() {
            this.dataset.manualEdit = 'true';
            // If user starts typing, allow form updates to override
            this.dataset.allowFormUpdate = 'true';
        });
    }
}

// Load vhost settings including WAF configuration
async function loadVHostSettings(domain) {
    try {
        const response = await fetch(`/api/nginx/vhost-settings/${domain}`);
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.settings) {
                // Set ModSecurity settings
                document.getElementById('vhost-modsecurity-enabled').checked = result.settings.modsecurity_enabled;
                document.getElementById('vhost-modsecurity-rules').value = result.settings.modsecurity_rules || '/etc/nginx/modsec/main.conf';
            }
        }
    } catch (error) {
        console.error('Error loading vhost settings:', error);
        // Set defaults on error
        document.getElementById('vhost-modsecurity-enabled').checked = true;
        document.getElementById('vhost-modsecurity-rules').value = '/etc/nginx/modsec/main.conf';
    }
}

// Initialize form listeners when modal opens
function openVHostSettings(domain, rootDir, enabled) {
    document.getElementById('vhost-domain').value = domain;
    document.getElementById('vhost-root-dir').value = rootDir;
    document.getElementById('vhost-status').value = enabled.toString();
    
    // Set config filename
    document.getElementById('config-filename').textContent = domain;
    
    // Reset manual edit flag
    const configTextarea = document.getElementById('vhost-custom-config');
    if (configTextarea) {
        configTextarea.dataset.manualEdit = 'false';
        configTextarea.value = '';
    }
    
    // Reset to first tab
    switchVHostTab('domain');
    
    // Initialize form listeners
    setTimeout(initVHostFormListeners, 100);
    
    // Load vhost settings including WAF configuration
    loadVHostSettings(domain);
    
    // Load existing config from file once when modal opens
    setTimeout(() => {
        loadVHostConfigOnOpen(domain);
    }, 300);
    
    document.getElementById('vhost-settings-modal').classList.remove('hidden');
}
