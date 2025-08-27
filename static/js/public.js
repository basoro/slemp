function formatFileSize(bytes) {

    if (bytes === null) return '-';
    if (bytes === 0) return '0 Bytes';
    
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'];
    let i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    if (i < 0) i = 0; // antisipasi ukuran < 1 Byte
    if (i >= sizes.length) i = sizes.length - 1;
    
    const size = bytes / Math.pow(1024, i);
    return size.toFixed(2) + ' ' + sizes[i];
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleString();
}

// Helper function to show custom alert modal
function showAlert(message, title = 'Pemberitahuan') {
    return new Promise((resolve) => {
        // Remove any existing alert modals to prevent conflicts
        const existingModals = document.querySelectorAll('.alert-modal');
        existingModals.forEach(modal => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        });
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[200] alert-modal';
        modal.setAttribute('data-modal-type', 'alert');
        
        // Determine modal width based on content
        const isWideContent = message.includes('<table') || message.includes('DNS Records');
        const modalWidth = isWideContent ? 'w-11/12 md:w-5/6 lg:w-4/5 xl:w-3/4 max-w-7xl' : 'w-96';
        const textAlign = isWideContent ? 'text-left' : 'text-center';
        
        modal.innerHTML = `
            <div class="relative top-10 mx-auto p-5 border ${modalWidth} shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3 ${textAlign}">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">${title}</h3>
                    <div class="mt-4">
                        <div class="text-sm text-gray-600 dark:text-gray-300">${message}</div>
                    </div>
                    <div class="flex justify-center mt-6">
                        <button id="alertOkBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">OK</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const handleOk = () => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
            resolve();
        };
        
        document.getElementById('alertOkBtn').addEventListener('click', handleOk);
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === 'Escape') {
                handleOk();
            }
        });
    });
}

// Helper function to show custom confirm modal
function showConfirm(message, title = 'Konfirmasi') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[200]';
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3 text-center">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">${title}</h3>
                    <div class="mt-4">
                        <p class="text-sm text-gray-600 dark:text-gray-300">${message}</p>
                    </div>
                    <div class="flex justify-center space-x-3 mt-6">
                        <button id="confirmCancelBtn" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Batal</button>
                        <button id="confirmOkBtn" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">Ya</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const handleOk = () => {
            document.body.removeChild(modal);
            resolve(true);
        };
        
        const handleCancel = () => {
            document.body.removeChild(modal);
            resolve(false);
        };
        
        document.getElementById('confirmOkBtn').addEventListener('click', handleOk);
        document.getElementById('confirmCancelBtn').addEventListener('click', handleCancel);
        
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                handleOk();
            } else if (e.key === 'Escape') {
                handleCancel();
            }
        });
    });
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());

    const notification = document.createElement('div');
    notification.className = `notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;
    
    const colors = {
        'success': 'bg-green-500 text-white',
        'error': 'bg-red-500 text-white',
        'warning': 'bg-yellow-500 text-black',
        'info': 'bg-blue-500 text-white'
    };
    
    notification.className += ` ${colors[type] || colors.info}`;
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-lg font-bold">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Helper function to show custom prompt modal
function showPrompt(message, defaultValue = '', title = 'Input') {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[100]';
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3 text-center">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">${title}</h3>
                    <div class="mt-4">
                        <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">${message}</p>
                        <input type="text" id="promptInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                value="${defaultValue}">
                    </div>
                    <div class="flex justify-center space-x-3 mt-6">
                        <button id="promptCancelBtn" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Batal</button>
                        <button id="promptOkBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">OK</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        const input = document.getElementById('promptInput');
        input.focus();
        input.select();
        
        const handleOk = () => {
            const value = input.value;
            document.body.removeChild(modal);
            resolve(value);
        };
        
        const handleCancel = () => {
            document.body.removeChild(modal);
            resolve(null);
        };
        
        document.getElementById('promptOkBtn').addEventListener('click', handleOk);
        document.getElementById('promptCancelBtn').addEventListener('click', handleCancel);
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleOk();
            }
        });
        
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                handleCancel();
            }
        });
    });
}

function showChangePasswordModal() {
    document.getElementById('changePasswordModal').classList.remove('hidden');
}

function hideChangePasswordModal() {
    document.getElementById('changePasswordModal').classList.add('hidden');
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
}

function changePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;

    if (!currentPassword || !newPassword) {
        showAlert('Please fill in all fields', 'Peringatan');
        return;
    }

    fetch('/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert(data.error, 'Error');
        } else {
            showAlert('Password changed successfully', 'Sukses');
            hideChangePasswordModal();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while changing the password', 'Error');
    });
}

let realtimeChart;
let systemRealtimeChart;
let socket;

setTimeout(() => {
    initializeSocket();
}, 100);

// Initialize SocketIO connection
const initializeSocket = () => {
    socket = io(window.location.origin, {
        withCredentials: true,
        transports: ['polling', 'websocket']
    });
    
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('connect_error', (error) => {
        console.error('SocketIO connection error:', error);
        showNotification('Koneksi WebSocket gagal. Progress bar mungkin tidak berfungsi.', 'error');
    });
    
    socket.on('network_data', (data) => {
        // Only update network charts if we're on the network page
        if (window.location.pathname === '/network' || window.location.pathname.endsWith('/network')) {
            updateNetworkCharts(data);
        }
    });
    
    socket.on('error', (error) => {
        console.error('SocketIO error:', error);
        showNotification('Terjadi kesalahan WebSocket.', 'error');
    });
    
    socket.on('install_error', (data) => {
        console.log('Received install_error:', data);
        addInstallOutput(`❌ Error: ${data.message}`, 'error');
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('install-close-btn');
        const cancelBtn = document.getElementById('install-cancel-btn');
        if (closeBtn) closeBtn.style.display = 'block';
        if (cancelBtn) {
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    });
    
    // Installation progress events
    socket.on('install_progress', (data) => {
        console.log('Received install_progress:', data);
        updateInstallProgress(data.step, data.total, data.status, data.percentage);
    });
    
    socket.on('install_output', (data) => {
        console.log('Received install_output:', data);
        addInstallOutput(data.output, data.type || 'info');
    });
    
    socket.on('install_complete', (data) => {
        console.log('Received install_complete:', data);
        addInstallOutput(`✅ ${data.service} berhasil diinstall!`, 'success');
        updateInstallProgress(4, 4, 'Instalasi selesai', 100);
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('install-close-btn');
        const cancelBtn = document.getElementById('install-cancel-btn');
        closeBtn.style.display = 'block';
        cancelBtn.textContent = 'Close';
        cancelBtn.disabled = false;
        cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        // Update service status
        setTimeout(() => {
            updateServiceStatus();
        }, 1000);
        
        showNotification(`${data.service} berhasil diinstall!`, 'success');
    });
    
    socket.on('install_error', (data) => {
        addInstallOutput(`❌ Error: ${data.message}`, 'error');
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('install-close-btn');
        const cancelBtn = document.getElementById('install-cancel-btn');
        closeBtn.style.display = 'block';
        cancelBtn.textContent = 'Close';
        cancelBtn.disabled = false;
        cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        showNotification(`Instalasi gagal: ${data.message}`, 'error');
    });
    
    // Uninstallation events
    socket.on('uninstall_progress', (data) => {
        console.log('Received uninstall_progress:', data);
        updateUninstallProgress(data.step, data.total, data.status, data.percentage);
    });
    
    socket.on('uninstall_output', (data) => {
        console.log('Received uninstall_output:', data);
        addUninstallOutput(data.output, data.type || 'info');
    });
    
    socket.on('uninstall_complete', (data) => {
        console.log('Received uninstall_complete:', data);
        addUninstallOutput(`✅ ${data.service} berhasil diuninstall!`, 'success');
        updateUninstallProgress(5, 5, 'Uninstall selesai', 100);
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('uninstall-close-btn');
        const cancelBtn = document.getElementById('uninstall-cancel-btn');
        closeBtn.style.display = 'block';
        cancelBtn.textContent = 'Close';
        cancelBtn.disabled = false;
        cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        // Update service status
        setTimeout(() => {
            updateServiceStatus();
        }, 1000);
        
        showNotification(`${data.service} berhasil diuninstall!`, 'success');
    });
    
    socket.on('uninstall_error', (data) => {
        console.log('Received uninstall_error:', data);
        addUninstallOutput(`❌ Error: ${data.message}`, 'error');
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('uninstall-close-btn');
        const cancelBtn = document.getElementById('uninstall-cancel-btn');
        if (closeBtn) closeBtn.style.display = 'block';
        if (cancelBtn) {
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        showNotification(`Uninstall gagal: ${data.message}`, 'error');
    });
    
    // PHP Module Installation Events
    socket.on('php_module_install_progress', (data) => {
        console.log('Received php_module_install_progress:', data);
        updatePhpModuleInstallProgress(data.step, data.total, data.status, data.percentage);
    });
    
    socket.on('php_module_install_output', (data) => {
        console.log('Received php_module_install_output:', data);
        addPhpModuleInstallOutput(data.output, data.type || 'info');
    });
    
    socket.on('php_module_install_complete', (data) => {
        console.log('Received php_module_install_complete:', data);
        addPhpModuleInstallOutput(`✅ Modul ${data.module} berhasil diinstall!`, 'success');
        updatePhpModuleInstallProgress(3, 3, 'Instalasi selesai', 100);
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('php-module-install-cancel-btn');
        if (closeBtn) {
            closeBtn.textContent = 'Close';
            closeBtn.disabled = false;
            closeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        showNotification(`Modul PHP ${data.module} berhasil diinstall!`, 'success');
    });
    
    socket.on('php_module_install_error', (data) => {
        console.log('Received php_module_install_error:', data);
        addPhpModuleInstallOutput(`❌ Error: ${data.message}`, 'error');
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('php-module-install-cancel-btn');
        if (closeBtn) {
            closeBtn.textContent = 'Close';
            closeBtn.disabled = false;
            closeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        showNotification(`Instalasi modul PHP gagal: ${data.message}`, 'error');
    });
    
    socket.on('php_module_install_output', (data) => {
        console.log('Received php_module_install_output:', data);
        addPhpModuleInstallOutput(data.output, data.type || 'info');
    });
    
    socket.on('php_module_install_complete', (data) => {
        console.log('Received php_module_install_complete:', data);
        addPhpModuleInstallOutput(`✅ Modul PHP ${data.module} berhasil diinstall!`, 'success');
        updatePhpModuleInstallProgress({
            step: 3,
            total: 3,
            status: 'Instalasi selesai',
            percentage: 100
        });
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('php-module-install-close-btn');
        const cancelBtn = document.getElementById('php-module-install-cancel-btn');
        if (closeBtn) closeBtn.style.display = 'block';
        if (cancelBtn) {
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        showNotification(`Modul PHP ${data.module} berhasil diinstall!`, 'success');
    });
    
    socket.on('php_module_install_error', (data) => {
        console.log('Received php_module_install_error:', data);
        addPhpModuleInstallOutput(`❌ Error: ${data.message}`, 'error');
        
        // Re-enable close buttons
        const closeBtn = document.getElementById('php-module-install-close-btn');
        const cancelBtn = document.getElementById('php-module-install-cancel-btn');
        if (closeBtn) closeBtn.style.display = 'block';
        if (cancelBtn) {
            cancelBtn.textContent = 'Close';
            cancelBtn.disabled = false;
            cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        showNotification('Instalasi modul PHP gagal', 'error');
    });
    
    // Request network data every 2 seconds
    setInterval(() => {
        if (socket.connected) {
            socket.emit('request_network_data');
        }
    }, 2000);
};

// Theme Management
let currentTheme = 'system';
let systemPrefersDark = false;
let sidebarCollapsed = false;

function toggleSidebarCollapse() {
    const sidebar = document.getElementById('sidebar');
    const sidebarTexts = document.querySelectorAll('.sidebar-text');
    const logoText = document.querySelector('.sidebar-logo-text');
    const logoContainer = document.querySelector('#sidebar > div:first-child');
    const menuButtons = document.querySelectorAll('nav button');
    const footerButtons = document.querySelectorAll('#sidebar > div:last-child button');
    
    sidebarCollapsed = !sidebarCollapsed;
    
    // Save state to localStorage
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.toString());
    
    if (sidebarCollapsed) {
        // Add collapsed class for CSS styling
        sidebar.classList.add('sidebar-collapsed');
        // Hide menu text elements
        sidebarTexts.forEach(text => {
            text.style.display = 'none';
        });
        // Hide logo text
        if (logoText) {
            logoText.style.display = 'none';
        }
        // Adjust logo container padding for collapsed state
        if (logoContainer) {
            logoContainer.style.padding = '1.1rem';
            logoContainer.style.justifyContent = 'center';
        }
        // Make sidebar narrower
        sidebar.style.width = '4rem';
        
        // Resize charts after sidebar collapse
        setTimeout(() => {
            if (realtimeChart) realtimeChart.resize();
            if (systemRealtimeChart) systemRealtimeChart.resize();
        }, 300);
    } else {
        // Remove collapsed class
        sidebar.classList.remove('sidebar-collapsed');
        // Show menu text elements
        sidebarTexts.forEach(text => {
            text.style.display = 'block';
        });
        // Show logo text
        if (logoText) {
            logoText.style.display = 'block';
        }
        // Restore logo container padding
        if (logoContainer) {
            logoContainer.style.padding = '1rem 1.5rem';
            logoContainer.style.justifyContent = 'flex-start';
        }
        // Restore sidebar width
        sidebar.style.width = '16rem';
        
        // Resize charts after sidebar expand
        setTimeout(() => {
            if (realtimeChart) realtimeChart.resize();
            if (systemRealtimeChart) systemRealtimeChart.resize();
        }, 300);
    }
}

function applySidebarState() {
    const sidebar = document.getElementById('sidebar');
    const sidebarTexts = document.querySelectorAll('.sidebar-text');
    const logoText = document.querySelector('.sidebar-logo-text');
    const logoContainer = document.querySelector('#sidebar > div:first-child');
    
    if (sidebarCollapsed) {
        // Add collapsed class for CSS styling
        sidebar.classList.add('sidebar-collapsed');
        // Hide menu text elements
        sidebarTexts.forEach(text => {
            text.style.display = 'none';
        });
        // Hide logo text
        if (logoText) {
            logoText.style.display = 'none';
        }
        // Adjust logo container padding for collapsed state
        if (logoContainer) {
            logoContainer.style.padding = '1.1rem';
            logoContainer.style.justifyContent = 'center';
        }
        // Make sidebar narrower
            sidebar.style.width = '4rem';
            
            // Resize charts after applying collapsed state
            setTimeout(() => {
                if (realtimeChart) realtimeChart.resize();
                if (systemRealtimeChart) systemRealtimeChart.resize();
            }, 300);
        } else {
        // Remove collapsed class
        sidebar.classList.remove('sidebar-collapsed');
        // Show menu text elements
        sidebarTexts.forEach(text => {
            text.style.display = 'block';
        });
        // Show logo text
        if (logoText) {
            logoText.style.display = 'block';
        }
        // Restore logo container padding
        if (logoContainer) {
            logoContainer.style.padding = '1rem 1.5rem';
            logoContainer.style.justifyContent = 'flex-start';
        }
        // Restore sidebar width
            sidebar.style.width = '16rem';
            
            // Resize charts after applying expanded state
            setTimeout(() => {
                if (realtimeChart) realtimeChart.resize();
                if (systemRealtimeChart) systemRealtimeChart.resize();
            }, 300);
        }
}

function setTheme(theme) {
    currentTheme = theme;
    localStorage.setItem('theme', theme);
    applyTheme();
    updateThemeUI();
    toggleThemeDropdown();
}

function applyTheme() {
    const html = document.documentElement;
    
    if (currentTheme === 'system') {
        if (systemPrefersDark) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
    } else if (currentTheme === 'dark') {
        html.classList.add('dark');
    } else {
        html.classList.remove('dark');
    }
    
    // Update chart colors when theme changes
    setTimeout(() => {
        if (realtimeChart) {
            const isDark = html.classList.contains('dark');
            const textColor = isDark ? '#fff' : '#000';
            
            realtimeChart.setOption({
                title: {
                    textStyle: { color: textColor }
                },
                legend: {
                    textStyle: { color: textColor }
                },
                xAxis: {
                    axisLabel: { color: textColor }
                },
                yAxis: {
                    axisLabel: { color: textColor }
                }
            });
        }
        if (systemRealtimeChart) {
            const isDark = html.classList.contains('dark');
            const textColor = isDark ? '#fff' : '#000';
            
            systemRealtimeChart.setOption({
                title: {
                    textStyle: { color: textColor }
                },
                legend: {
                    textStyle: { color: textColor }
                },
                xAxis: {
                    axisLabel: { color: textColor }
                },
                yAxis: {
                    axisLabel: { color: textColor }
                }
            });
        }
    }, 100);
}

function updateThemeUI() {
    const themeIcon = document.getElementById('theme-icon-path');
    
    if (themeIcon) {
        if (currentTheme === 'light') {
            themeIcon.setAttribute('d', 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z');
        } else if (currentTheme === 'dark') {
            themeIcon.setAttribute('d', 'M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z');
        } else {
            themeIcon.setAttribute('d', 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z');
        }
    }
}

function toggleThemeDropdown() {
    const dropdown = document.getElementById('theme-dropdown-menu');
    dropdown.classList.toggle('hidden');
}

function initializeTheme() {
    // Check system preference
    systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Get saved theme or default to system
    const savedTheme = localStorage.getItem('theme');
    currentTheme = savedTheme || 'system';
    
    // Check if device is mobile
    const isMobile = window.innerWidth <= 768;
    
    // Initialize sidebar state from localStorage or auto-collapse on mobile
    const savedSidebarState = localStorage.getItem('sidebarCollapsed');
    if (savedSidebarState !== null && !isMobile) {
        sidebarCollapsed = savedSidebarState === 'true';
    } else if (isMobile) {
        // Auto-collapse sidebar on mobile devices
        sidebarCollapsed = true;
    }
    
    // Apply sidebar state
    if (sidebarCollapsed) {
        applySidebarState();
    }
    
    // Apply theme and update UI
    applyTheme();
    updateThemeUI();
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        systemPrefersDark = e.matches;
        if (currentTheme === 'system') {
            applyTheme();
        }
    });
    
    // Listen for window resize to handle mobile/desktop transitions
    window.addEventListener('resize', () => {
        const isMobile = window.innerWidth <= 768;
        const wasMobile = sidebarCollapsed && !localStorage.getItem('sidebarCollapsed');
        
        if (isMobile && !sidebarCollapsed) {
            // Auto-collapse when switching to mobile
            sidebarCollapsed = true;
            applySidebarState();
        } else if (!isMobile && wasMobile) {
            // Auto-expand when switching to desktop (if it was auto-collapsed)
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === null) {
                sidebarCollapsed = false;
                applySidebarState();
            }
        }
    });
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    const themeDropdown = document.getElementById('theme-dropdown');
    const actionsDropdown = document.getElementById('actions-dropdown');
    
    if (themeDropdown && !themeDropdown.contains(event.target)) {
        document.getElementById('theme-dropdown-menu').classList.add('hidden');
    }
    
    if (actionsDropdown && !actionsDropdown.contains(event.target)) {
        document.getElementById('actions-dropdown-menu').classList.add('hidden');
    }
});

// Call initialize function when page loads
document.addEventListener('DOMContentLoaded', initializeTheme);

// Actions Dropdown Management
function toggleActionsDropdown() {
    const dropdown = document.getElementById('actions-dropdown-menu');
    dropdown.classList.toggle('hidden');
}

// Fungsi untuk update aplikasi Flask
async function updateApp() {
    if (!(await showConfirm('Apakah Anda yakin ingin update aplikasi? Koneksi akan terputus sementara.', 'Konfirmasi Update'))) {
        return;
    }

    try {
        showNotification('Memulai update aplikasi...', 'info');
        
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'update-loading';
        loadingDiv.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        loadingDiv.innerHTML = `
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-gray-700 dark:text-gray-300">Sedang mengupdate aplikasi...</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">Mohon tunggu, proses ini dapat memakan waktu beberapa menit</p>
            </div>
        `;
        document.body.appendChild(loadingDiv);
        
        const response = await fetch('/api/app/update', {
            method: 'POST'
        });
        
        // Remove loading indicator
        const loading = document.getElementById('update-loading');
        if (loading) loading.remove();
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Aplikasi berhasil diupdate! Halaman akan dimuat ulang dalam 3 detik...', 'success');
            
            // Reload halaman setelah 3 detik
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            showNotification(`Gagal update aplikasi: ${data.message}`, 'error');
        }
    } catch (error) {
        // Remove loading indicator if still present
        const loading = document.getElementById('update-loading');
        if (loading) loading.remove();
        
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat update aplikasi', 'error');
    }
}

// Fungsi untuk restart aplikasi Flask
async function restartApp() {
    if (!(await showConfirm('Apakah Anda yakin ingin restart aplikasi? Koneksi akan terputus sementara.', 'Konfirmasi Restart'))) {
        return;
    }

    try {
        showNotification('Memulai restart aplikasi...', 'info');
        
        const response = await fetch('/api/app/restart', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Aplikasi berhasil direstart! Halaman akan dimuat ulang dalam 3 detik...', 'success');
            
            // Reload halaman setelah 3 detik
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        } else {
            showNotification(`Gagal restart aplikasi: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat restart aplikasi', 'error');
    }
}

// Fungsi untuk memulai layanan
async function startService(service) {
    try {
        const response = await fetch(`/api/service/${service}/start`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            updateServiceStatus();
        } else {
            showAlert(`Gagal memulai ${service}: ${data.message}`, 'Error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(`Terjadi kesalahan saat memulai ${service}`, 'Error');
    }
}

// Fungsi untuk menghentikan layanan
async function stopService(service) {
    try {
        const response = await fetch(`/api/service/${service}/stop`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            updateServiceStatus();
        } else {
            showAlert(`Gagal menghentikan ${service}: ${data.message}`, 'Error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(`Terjadi kesalahan saat menghentikan ${service}`, 'Error');
    }
}

// Fungsi untuk restart layanan
async function restartService(service) {
    try {
        const response = await fetch(`/api/service/${service}/restart`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            showNotification(`${service} berhasil direstart`, 'success');
            updateServiceStatus();
        } else {
            showAlert(`Gagal merestart ${service}: ${data.message}`, 'Error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(`Terjadi kesalahan saat merestart ${service}`, 'Error');
    }
}

// Fungsi untuk menginstall layanan dengan modal real-time
async function installService(service) {
    if (!(await showConfirm(`Apakah Anda yakin ingin menginstall ${service}? Proses ini mungkin memakan waktu beberapa menit.`, 'Konfirmasi Install'))) {
        return;
    }

    try {
        // Show installation modal
        showInstallModal(service);
        
        // Emit install_service event via WebSocket
        if (socket && socket.connected) {
            socket.emit('install_service', { service: service });
        } else {
            showNotification('WebSocket connection not available', 'error');
            closeInstallModal();
        }
    } catch (error) {
        console.error('Error starting installation:', error);
        showNotification('Installation failed to start', 'error');
        closeInstallModal();
    }
}

// Show installation modal
function showInstallModal(service) {
    const modal = document.getElementById('install-modal');
    const title = document.getElementById('install-modal-title');
    const output = document.getElementById('install-output');
    const status = document.getElementById('install-status');
    const step = document.getElementById('install-step');
    const progressBar = document.getElementById('install-progress-bar');
    const closeBtn = document.getElementById('install-close-btn');
    const cancelBtn = document.getElementById('install-cancel-btn');
    
    // Set modal title
    title.textContent = `Installing ${service.charAt(0).toUpperCase() + service.slice(1)}`;
    
    // Reset modal state
    output.innerHTML = '';
    status.textContent = 'Memulai instalasi...';
    step.textContent = '0/4';
    progressBar.style.width = '0%';
    
    // Disable close buttons during installation
    closeBtn.style.display = 'none';
    cancelBtn.textContent = 'Installing...';
    cancelBtn.disabled = true;
    cancelBtn.classList.add('opacity-50', 'cursor-not-allowed');
    
    // Show modal
    modal.classList.remove('hidden');
}

// Close installation modal
function closeInstallModal() {
    const modal = document.getElementById('install-modal');
    const closeBtn = document.getElementById('install-close-btn');
    const cancelBtn = document.getElementById('install-cancel-btn');
    
    // Re-enable close buttons
    closeBtn.style.display = 'block';
    cancelBtn.textContent = 'Close';
    cancelBtn.disabled = false;
    cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    
    // Hide modal
    modal.classList.add('hidden');
}

function showUninstallModal(service) {
    const modal = document.getElementById('uninstall-modal');
    const title = document.getElementById('uninstall-modal-title');
    const output = document.getElementById('uninstall-output');
    const status = document.getElementById('uninstall-status');
    const step = document.getElementById('uninstall-step');
    const progressBar = document.getElementById('uninstall-progress-bar');
    const closeBtn = document.getElementById('uninstall-close-btn');
    const cancelBtn = document.getElementById('uninstall-cancel-btn');
    
    // Set modal title
    title.textContent = `Uninstalling ${service.charAt(0).toUpperCase() + service.slice(1)}`;
    
    // Reset status
    output.innerHTML = '';
    status.textContent = 'Memulai uninstall...';
    step.textContent = '0/5';
    progressBar.style.width = '0%';
    
    // Disable close buttons during uninstallation
    closeBtn.style.display = 'none';
    cancelBtn.textContent = 'Uninstalling...';
    cancelBtn.disabled = true;
    cancelBtn.classList.add('opacity-50', 'cursor-not-allowed');
    
    // Show modal
    modal.classList.remove('hidden');
}

function closeUninstallModal() {
    const modal = document.getElementById('uninstall-modal');
    const closeBtn = document.getElementById('uninstall-close-btn');
    const cancelBtn = document.getElementById('uninstall-cancel-btn');
    
    // Re-enable close buttons
    closeBtn.style.display = 'block';
    cancelBtn.textContent = 'Close';
    cancelBtn.disabled = false;
    cancelBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    
    // Hide modal
    modal.classList.add('hidden');
}

// Add installation output to terminal
function addInstallOutput(message, type = 'info') {
    const output = document.getElementById('install-output');
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
        colorClass = 'text-cyan-400 font-bold';
        prefix = '➤ ';
    } else {
        colorClass = 'text-green-400';
        prefix = '  ';
    }
    
    const line = document.createElement('div');
    line.className = `${colorClass} mb-1 leading-relaxed`;
    
    if (type === 'command') {
        line.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${prefix}<span class="text-cyan-300">${message}</span>`;
    } else {
        line.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${prefix}<span>${message}</span>`;
    }
    
    output.appendChild(line);
    
    // Auto-scroll to bottom with smooth behavior
    const terminal = document.getElementById('install-terminal');
    terminal.scrollTop = terminal.scrollHeight;
}

// Update installation progress
function updateInstallProgress(step, total, status, percentage) {
    console.log('updateInstallProgress called with:', { step, total, status, percentage });
    const statusElement = document.getElementById('install-status');
    const stepElement = document.getElementById('install-step');
    const progressBar = document.getElementById('install-progress-bar');
    
    if (statusElement) {
        statusElement.textContent = status;
        console.log('Updated status to:', status);
    } else {
        console.error('install-status element not found');
    }
    
    if (stepElement) {
        stepElement.textContent = `${step}/${total}`;
        console.log('Updated step to:', `${step}/${total}`);
    } else {
        console.error('install-step element not found');
    }
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        console.log('Updated progress bar to:', `${percentage}%`);
    } else {
        console.error('install-progress-bar element not found');
    }
}

// Add uninstallation output to terminal
function addUninstallOutput(message, type = 'info') {
    const output = document.getElementById('uninstall-output');
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
        colorClass = 'text-cyan-400 font-bold';
        prefix = '➤ ';
    } else {
        colorClass = 'text-green-400';
        prefix = '  ';
    }
    
    const line = document.createElement('div');
    line.className = `${colorClass} mb-1 leading-relaxed`;
    
    if (type === 'command') {
        line.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${prefix}<span class="text-cyan-300">${message}</span>`;
    } else {
        line.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> ${prefix}<span>${message}</span>`;
    }
    
    output.appendChild(line);
    
    // Auto-scroll to bottom with smooth behavior
    const terminal = document.getElementById('uninstall-terminal');
    terminal.scrollTop = terminal.scrollHeight;
}

// Update uninstallation progress
function updateUninstallProgress(step, total, status, percentage) {
    console.log('updateUninstallProgress called with:', { step, total, status, percentage });
    const statusElement = document.getElementById('uninstall-status');
    const stepElement = document.getElementById('uninstall-step');
    const progressBar = document.getElementById('uninstall-progress-bar');
    
    if (statusElement) {
        statusElement.textContent = status;
        console.log('Updated uninstall status to:', status);
    } else {
        console.error('uninstall-status element not found');
    }
    
    if (stepElement) {
        stepElement.textContent = `${step}/${total}`;
        console.log('Updated uninstall step to:', `${step}/${total}`);
    } else {
        console.error('uninstall-step element not found');
    }
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        console.log('Updated uninstall progress bar to:', `${percentage}%`);
    } else {
        console.error('uninstall-progress-bar element not found');
    }
}

// Fungsi untuk menguninstall layanan
async function uninstallService(service) {
    if (!(await showConfirm(`Apakah Anda yakin ingin menguninstall ${service}? Semua data dan konfigurasi akan dihapus!`, 'Konfirmasi Uninstall'))) {
        return;
    }

    try {
        showNotification(`Memulai uninstall ${service}...`, 'info');
        showUninstallModal(service);
        
        // Emit uninstall_service event via WebSocket
        if (socket && socket.connected) {
            socket.emit('uninstall_service', { service: service });
        } else {
            showNotification('WebSocket connection not available', 'error');
            closeUninstallModal();
        }
    } catch (error) {
        console.error('Error starting uninstallation:', error);
        showNotification('Uninstallation failed to start', 'error');
        closeUninstallModal();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Get current path
    const currentPath = window.location.pathname;
    
    // Remove active class from all menu items
    const menuItems = document.querySelectorAll('nav a');
    menuItems.forEach(item => {
        item.classList.remove('bg-blue-600', 'text-white');
        item.classList.add('text-gray-300');
    });
    
    // Find and activate current menu item
    let activeItem = null;
    
    // Check for exact matches first
    menuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPath) {
            activeItem = item;
        }
    });
    
    // If no exact match, check for partial matches (for sub-pages)
    if (!activeItem && currentPath !== '/') {
        menuItems.forEach(item => {
            const href = item.getAttribute('href');
            if (href !== '/' && currentPath.startsWith(href)) {
                activeItem = item;
            }
        });
    }
    
    // If still no match and we're on root, activate dashboard
    if (!activeItem && currentPath === '/') {
        activeItem = document.querySelector('nav a[href="/"]');
    }
    
    // Apply active styles
    if (activeItem) {
        activeItem.classList.remove('text-gray-300');
        activeItem.classList.add('bg-blue-600', 'text-white');
    }
});