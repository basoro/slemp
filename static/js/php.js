loadPhpModules();

// PHP Modal Functions
function showPhpFpmPoolModal() {
    document.getElementById('phpfpm-pool-modal').classList.remove('hidden');
    loadPhpFpmConfig();
}

function closePhpFpmPoolModal() {
    document.getElementById('phpfpm-pool-modal').classList.add('hidden');
}

function showPhpIniModal() {
    document.getElementById('phpini-modal').classList.remove('hidden');
    loadPhpIniConfig();
}

function closePhpIniModal() {
    document.getElementById('phpini-modal').classList.add('hidden');
}

function showPhpInfoModal() {
    document.getElementById('phpinfo-modal').classList.remove('hidden');
    loadPhpInfo();
}

function closePhpInfoModal() {
    document.getElementById('phpinfo-modal').classList.add('hidden');
}

// PHP Configuration Functions
async function loadPhpFpmConfig() {
    try {
        const response = await fetch('/api/php/phpfpm-config');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('phpfpm-config').value = data.config || '';
        } else {
            showNotification('Failed to load PHP-FPM configuration', 'error');
        }
    } catch (error) {
        console.error('Error loading PHP-FPM config:', error);
        showNotification('Error loading PHP-FPM configuration', 'error');
    }
}

async function testPhpFpmConfig() {
    const config = document.getElementById('phpfpm-config').value;
    try {
        const response = await fetch('/api/php/test-phpfpm-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('PHP-FPM configuration is valid', 'success');
        } else {
            showNotification('PHP-FPM configuration error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error testing PHP-FPM config:', error);
        showNotification('Error testing PHP-FPM configuration', 'error');
    }
}

async function savePhpFpmConfig() {
    const config = document.getElementById('phpfpm-config').value;
    try {
        const response = await fetch('/api/php/save-phpfpm-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('PHP-FPM configuration saved successfully', 'success');
        } else {
            showNotification('Failed to save PHP-FPM configuration: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error saving PHP-FPM config:', error);
        showNotification('Error saving PHP-FPM configuration', 'error');
    }
}

async function loadPhpIniConfig() {
    try {
        const response = await fetch('/api/php/phpini-config');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('phpini-config').value = data.config || '';
        } else {
            showNotification('Failed to load PHP.ini configuration', 'error');
        }
    } catch (error) {
        console.error('Error loading PHP.ini config:', error);
        showNotification('Error loading PHP.ini configuration', 'error');
    }
}

async function testPhpIniConfig() {
    const config = document.getElementById('phpini-config').value;
    try {
        const response = await fetch('/api/php/test-phpini-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('PHP.ini configuration is valid', 'success');
        } else {
            showNotification('PHP.ini configuration error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error testing PHP.ini config:', error);
        showNotification('Error testing PHP.ini configuration', 'error');
    }
}

async function savePhpIniConfig() {
    const config = document.getElementById('phpini-config').value;
    try {
        const response = await fetch('/api/php/save-phpini-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('PHP.ini configuration saved successfully', 'success');
        } else {
            showNotification('Failed to save PHP.ini configuration: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error saving PHP.ini config:', error);
        showNotification('Error saving PHP.ini configuration', 'error');
    }
}

async function loadPhpInfo() {
    try {
        const response = await fetch('/api/php/info');
        if (response.ok) {
            const data = await response.json();
            
            // Update PHP info display
            document.getElementById('php-version').textContent = data.version || '8.2.7';
            document.getElementById('php-system').textContent = data.system || 'Linux x86_64';
            document.getElementById('php-build-date').textContent = data.build_date || 'Jun 12 2023 09:45:01';
            document.getElementById('php-config-file').textContent = data.config_file || '/etc/php/8.2/fpm/php.ini';
            document.getElementById('php-server-api').textContent = data.server_api || 'FPM/FastCGI';
            document.getElementById('php-memory-limit').textContent = data.memory_limit || '128M';
            document.getElementById('php-max-execution-time').textContent = data.max_execution_time || '30 seconds';
            document.getElementById('php-upload-max-filesize').textContent = data.upload_max_filesize || '2M';
            document.getElementById('php-post-max-size').textContent = data.post_max_size || '8M';
            document.getElementById('php-opcache').textContent = data.opcache || 'Enabled';
            
            // Update extensions
            const extensionsContainer = document.getElementById('php-extensions');
            if (data.extensions && data.extensions.length > 0) {
                extensionsContainer.innerHTML = data.extensions.map(ext => 
                    `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">${ext}</span>`
                ).join('');
            }
        } else {
            showNotification('Failed to load PHP information', 'error');
        }
    } catch (error) {
        console.error('Error loading PHP info:', error);
        showNotification('Error loading PHP information', 'error');
    }
}

async function refreshPhpInfo() {
    showNotification('Refreshing PHP information...', 'info');
    await loadPhpInfo();
    showNotification('PHP information refreshed', 'success');
}

// Close modals when clicking outside
document.addEventListener('click', function(event) {
    const phpFpmModal = document.getElementById('phpfpm-pool-modal');
    const phpIniModal = document.getElementById('phpini-modal');
    const phpInfoModal = document.getElementById('phpinfo-modal');
    
    if (event.target === phpFpmModal) {
        closePhpFpmPoolModal();
    }
    if (event.target === phpIniModal) {
        closePhpIniModal();
    }
    if (event.target === phpInfoModal) {
        closePhpInfoModal();
    }
});

// Handle Escape key to close modals
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const phpFpmModal = document.getElementById('phpfpm-pool-modal');
        const phpIniModal = document.getElementById('phpini-modal');
        const phpInfoModal = document.getElementById('phpinfo-modal');
        
        if (!phpFpmModal.classList.contains('hidden')) {
            closePhpFpmPoolModal();
        }
        if (!phpIniModal.classList.contains('hidden')) {
            closePhpIniModal();
        }
        if (!phpInfoModal.classList.contains('hidden')) {
            closePhpInfoModal();
        }
    }
});

// Function to install PHP module with real-time progress modal
async function installPhpModule() {
    const moduleName = await showModuleInstallDialog();
    if (!moduleName) return;

    // Show confirmation dialog
    if (!(await showConfirm(`Apakah Anda yakin ingin menginstall modul PHP '${moduleName}'? Proses ini mungkin memakan waktu beberapa menit.`, 'Konfirmasi Install Modul PHP'))) {
        return;
    }

    try {
        // Show PHP module installation modal
        showPhpModuleInstallModal(moduleName);
        
        // Emit install_php_module event via WebSocket
        if (socket && socket.connected) {
            socket.emit('install_php_module', { module: moduleName });
        } else {
            showNotification('WebSocket connection not available', 'error');
            closePhpModuleInstallModal();
        }
    } catch (error) {
        console.error('Error starting PHP module installation:', error);
        showNotification('PHP module installation failed to start', 'error');
        closePhpModuleInstallModal();
    }
}

// Disable PHP module
async function disablePhpModule(moduleName) {
    try {
        const response = await fetch('/api/php/disable-module', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ module: moduleName })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification(`PHP module ${moduleName} disabled successfully`, 'success');
        } else {
            showNotification(`Failed to disable PHP module ${moduleName}: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Error disabling PHP module:', error);
        showNotification('Error disabling PHP module', 'error');
    }
}

// Show PHP module installation modal
function showPhpModuleInstallModal(moduleName) {
    const modal = document.getElementById('php-module-install-modal');
    const title = document.getElementById('php-module-install-title');
    const output = document.getElementById('php-module-install-output');
    const status = document.getElementById('php-module-install-status');
    const step = document.getElementById('php-module-install-step');
    const progressBar = document.getElementById('php-module-install-progress-bar');
    const closeBtn = document.getElementById('php-module-install-close-btn');
    const cancelBtn = document.getElementById('php-module-install-cancel-btn');
    
    // Set modal title
    title.textContent = `Installing PHP Module: ${moduleName}`;
    
    // Reset modal state
    output.innerHTML = '';
    status.textContent = 'Memulai instalasi modul PHP...';
    step.textContent = '0/3';
    progressBar.style.width = '0%';
    
    // Disable close buttons during installation
    closeBtn.style.display = 'none';
    cancelBtn.textContent = 'Installing...';
    cancelBtn.disabled = true;
    cancelBtn.classList.add('opacity-50', 'cursor-not-allowed');
    
    // Show modal
    modal.classList.remove('hidden');
}

// Close PHP module installation modal
function closePhpModuleInstallModal() {
    const modal = document.getElementById('php-module-install-modal');
    const closeBtn = document.getElementById('php-module-install-close-btn');
    const cancelBtn = document.getElementById('php-module-install-cancel-btn');
    
    // Re-enable close buttons
    closeBtn.style.display = 'block';
    cancelBtn.textContent = 'Close';
    cancelBtn.disabled = false;
    cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    
    // Hide modal
    modal.classList.add('hidden');
}

// Add PHP module installation output to terminal
function addPhpModuleInstallOutput(message, type = 'info') {
    const output = document.getElementById('php-module-install-output');
    const timestamp = new Date().toLocaleTimeString();
    
    let colorClass = 'text-green-400';
    let prefix = '';
    
    if (type === 'error') {
        colorClass = 'text-red-400';
        prefix = '❌ ';
    } else if (type === 'warning') {
        colorClass = 'text-yellow-400';
        prefix = '⚠️  ';
    } else if (type === 'success') {
        colorClass = 'text-blue-400';
        prefix = '✅ ';
    } else if (type === 'command') {
        colorClass = 'text-cyan-400';
        prefix = '$ ';
    }
    
    const line = document.createElement('div');
    line.className = `${colorClass} mb-1`;
    line.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${prefix}${message}`;
    
    output.appendChild(line);
    
    // Auto-scroll to bottom
    const terminal = document.getElementById('php-module-install-terminal');
    terminal.scrollTop = terminal.scrollHeight;
}

// Update PHP module installation progress
function updatePhpModuleInstallProgress(data) {
    const status = document.getElementById('php-module-install-status');
    const step = document.getElementById('php-module-install-step');
    const progressBar = document.getElementById('php-module-install-progress-bar');
    
    if (status) status.textContent = data.status || 'Processing...';
    if (step) step.textContent = `${data.step || 0}/${data.total || 3}`;
    if (progressBar) progressBar.style.width = `${data.percentage || 0}%`;
    
    // Add output message
    if (data.message) {
        addPhpModuleInstallOutput(data.message, data.type || 'info');
    }
}
    
// Show module installation dialog
function showModuleInstallDialog() {
    return new Promise((resolve) => {
        // Create modal HTML
        const modalHTML = `
            <div id="module-install-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
                <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                    <div class="mt-3">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium text-gray-900 dark:text-white">📦 Install Modul PHP</h3>
                            <button onclick="closeModuleInstallDialog()" class="text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-gray-100">
                                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Nama Modul PHP:
                            </label>
                            <input type="text" id="module-name-input"
                                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                    placeholder="Contoh: curl, gd, mbstring, zip"
                                    autocomplete="off">
                            <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                                Masukkan nama modul PHP yang ingin diinstall. Contoh: curl, gd, mbstring, zip, xml, etc.
                            </p>
                        </div>
                        
                        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 mb-4">
                            <div class="flex">
                                <div class="flex-shrink-0">
                                    <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                                    </svg>
                                </div>
                                <div class="ml-3">
                                    <p class="text-sm text-blue-700 dark:text-blue-300">
                                        <strong>Info:</strong> Proses instalasi akan memakan waktu beberapa menit. Server akan restart otomatis setelah instalasi selesai.
                                    </p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="flex space-x-3">
                            <button onclick="confirmModuleInstall()" class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                                </svg>
                                Install
                            </button>
                            <button onclick="closeModuleInstallDialog()" class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                                Batal
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Focus on input
        setTimeout(() => {
            document.getElementById('module-name-input').focus();
        }, 100);
        
        // Handle Enter key
        document.getElementById('module-name-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                confirmModuleInstall();
            }
        });
        
        // Store resolve function globally
        window.moduleInstallResolve = resolve;
    });
}
    
function confirmModuleInstall() {
    const moduleName = document.getElementById('module-name-input').value.trim();
    if (!moduleName) {
        showNotification('Nama modul tidak boleh kosong', 'error');
        return;
    }
    
    closeModuleInstallDialog();
    if (window.moduleInstallResolve) {
        window.moduleInstallResolve(moduleName);
    }
}
    
function closeModuleInstallDialog() {
    const modal = document.getElementById('module-install-modal');
    if (modal) {
        modal.remove();
    }
    if (window.moduleInstallResolve) {
        window.moduleInstallResolve(null);
        delete window.moduleInstallResolve;
    }
}

// Load PHP modules from API
async function loadPhpModules() {
    try {
        const response = await fetch('/api/php/modules');
        const data = await response.json();
        
        if (response.ok) {
            const modulesList = document.getElementById('php-modules-list');
            modulesList.innerHTML = '';
            
            data.modules.forEach(module => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${module.name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${module.description}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 text-right">
                        <div class="flex items-center justify-end">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                module.enabled ? 
                                'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' : 
                                'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                            } mr-2">${module.enabled ? 'Enabled' : 'Disabled'}</span>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" class="sr-only peer" ${module.enabled ? 'checked' : ''} onchange="togglePhpModule('${module.name}', this.checked)">
                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                    </td>
                `;
                modulesList.appendChild(row);
            });
            
            // Initialize search functionality after loading modules
            initializeModuleSearch();
        } else {
            showNotification(data.error || 'Failed to load PHP modules', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred while loading modules', 'error');
    }
}

// PHP Module Management
async function togglePhpModule(moduleName, isEnabled) {
    const moduleRow = document.querySelector(`input[onchange*="togglePhpModule('${moduleName}'"]`).closest('tr');
    const statusSpan = moduleRow.querySelector('span');
    const toggleSwitch = moduleRow.querySelector('input[type="checkbox"]');
    
    // Disable the toggle switch during processing
    toggleSwitch.disabled = true;
    
    // Show loading state
    statusSpan.textContent = isEnabled ? 'Enabling...' : 'Disabling...';
    statusSpan.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100 mr-2';
    
    try {
        const response = await fetch('/api/php/toggle-module', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                module: moduleName,
                action: isEnabled ? 'enable' : 'disable'
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Update status display on success
            if (isEnabled) {
                statusSpan.textContent = 'Enabled';
                statusSpan.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100 mr-2';
            } else {
                statusSpan.textContent = 'Disabled';
                statusSpan.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 mr-2';
            }
            
            // Show success notification
            let message = result.message;
            if (result.installed) {
                message += ' (Module was installed automatically)';
            }
            showNotification(message, 'success');
        } else {
            // Revert toggle switch on error
            toggleSwitch.checked = !isEnabled;
            statusSpan.textContent = !isEnabled ? 'Enabled' : 'Disabled';
            statusSpan.className = !isEnabled ? 
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100 mr-2' :
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 mr-2';
            
            showNotification(result.error || 'Failed to toggle module', 'error');
        }
    } catch (error) {
        // Revert toggle switch on error
        toggleSwitch.checked = !isEnabled;
        statusSpan.textContent = !isEnabled ? 'Enabled' : 'Disabled';
        statusSpan.className = !isEnabled ? 
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100 mr-2' :
            'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 mr-2';
        
        showNotification('Network error occurred', 'error');
    } finally {
        // Re-enable the toggle switch
        toggleSwitch.disabled = false;
    }
}

// Search functionality for PHP modules
function initializeModuleSearch() {
    const searchInput = document.getElementById('module-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const moduleRows = document.querySelectorAll('#php-section tbody tr');
            
            moduleRows.forEach(row => {
                const moduleName = row.querySelector('td:first-child')?.textContent.toLowerCase() || '';
                const moduleDescription = row.querySelector('td:nth-child(2)')?.textContent.toLowerCase() || '';
                
                if (moduleName.includes(searchTerm) || moduleDescription.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}
