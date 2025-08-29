// Initialize ECharts for network monitoring
let systemData = {
    timestamps: [],
    cpu: [],
    memory: [],
    disk: []
};

setTimeout(() => {
    initializeSystemCharts();
}, 100);

const initializeSystemCharts = () => {
    // System resources real-time chart
    systemRealtimeChart = echarts.init(document.getElementById('system-realtime-chart'));
    const systemOption = {
        title: {
            textStyle: { color: document.documentElement.classList.contains('dark') ? '#fff' : '#000' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: [],
            axisLabel: { color: document.documentElement.classList.contains('dark') ? '#fff' : '#000' }
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 100,
            axisLabel: {
                color: document.documentElement.classList.contains('dark') ? '#fff' : '#000',
                formatter: '{value}%'
            }
        },
        series: [
            {
                name: 'CPU',
                type: 'line',
                data: [],
                smooth: true,
                lineStyle: { color: '#ef4444' },
                areaStyle: { color: 'rgba(239, 68, 68, 0.1)' }
            }
        ]
    };
    systemRealtimeChart.setOption(systemOption);
};


// Update system information
const updateSystemInfo = async () => {
    try {
        const response = await fetch('/api/system-info');
        const data = await response.json();
        
        // console.log('Raw system data from API:', data);

        // Update server uptime
        if (data.uptime) {
            document.getElementById('server-uptime').textContent = data.uptime;
        }
        
        // Update progress bars
        updateProgressBars({
            cpu: parseFloat(data.cpu) || 0,
            memory: parseFloat(data.memory.percent) || 0,
            disk: parseFloat(data.disk.percent) || 0
        });

        // Update real-time system chart
        updateSystemCharts({
            cpu_usage: data.cpu,
            memory_usage: data.memory.percent,
            disk_usage: data.disk.percent
        });
    } catch (error) {
        console.error('Error fetching system info:', error);
    }
};

// Update progress bars for system resources
const updateProgressBars = (data) => {
    // Update CPU progress bar
    const cpuProgress = document.getElementById('cpu-bar');
    const cpuPercent = document.getElementById('cpu-percentage');
    if (cpuProgress && cpuPercent) {
        cpuProgress.style.width = `${data.cpu}%`;
        cpuPercent.textContent = `${data.cpu.toFixed(1)}%`;
        
        // Update color based on usage
        cpuProgress.className = `h-2 rounded-full transition-all duration-300 ${
            data.cpu > 80 ? 'bg-red-500' : 
            data.cpu > 60 ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
    }
    
    // Update Memory progress bar
    const memoryProgress = document.getElementById('memory-bar');
    const memoryPercent = document.getElementById('memory-percentage');
    if (memoryProgress && memoryPercent) {
        memoryProgress.style.width = `${data.memory}%`;
        memoryPercent.textContent = `${data.memory.toFixed(1)}%`;
        
        // Update color based on usage
        memoryProgress.className = `h-2 rounded-full transition-all duration-300 ${
            data.memory > 80 ? 'bg-red-500' : 
            data.memory > 60 ? 'bg-yellow-500' : 'bg-purple-500'
        }`;
    }
    
    // Update Disk progress bar
    const diskProgress = document.getElementById('disk-bar');
    const diskPercent = document.getElementById('disk-percentage');
    if (diskProgress && diskPercent) {
        diskProgress.style.width = `${data.disk}%`;
        diskPercent.textContent = `${data.disk.toFixed(1)}%`;
        
        // Update color based on usage
        diskProgress.className = `h-2 rounded-full transition-all duration-300 ${
            data.disk > 80 ? 'bg-red-500' : 
            data.disk > 60 ? 'bg-yellow-500' : 'bg-green-500'
        }`;
    }
};

// Update recent activity
const updateRecentActivity = async () => {
    try {
        const response = await fetch('/api/recent-activity');
        const data = await response.json();
        
        const activityList = document.getElementById('activity-list');
        if (activityList && data.activities) {
            activityList.innerHTML = data.activities.map(activity => `
                <div class="flex items-start space-x-3">
                    <div class="w-2 h-2 rounded-full mt-2 ${
                        activity.type === 'success' ? 'bg-green-500' :
                        activity.type === 'warning' ? 'bg-yellow-500' :
                        activity.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    }"></div>
                    <div class="flex-1">
                        <p class="text-sm font-medium text-gray-900 dark:text-white">
                            ${activity.message}
                        </p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            ${activity.timestamp}
                        </p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error fetching recent activity:', error);
        const activityList = document.getElementById('activity-list');
        if (activityList) {
            activityList.innerHTML = `
                <div class="text-center text-gray-500 dark:text-gray-400 py-4">
                    <p>Tidak dapat memuat aktivitas terbaru</p>
                </div>
            `;
        }
    }
};

const updateSystemCharts = (data) => {
    if (!data || !systemRealtimeChart) {
        return;
    }
    
    // console.log('System chart data received:', data);
    
    const currentTime = new Date().toLocaleTimeString();
    const cpuUsage = parseFloat(data.cpu_usage) || 0;
    const memoryUsage = parseFloat(data.memory_usage) || 0;
    const diskUsage = parseFloat(data.disk_usage) || 0;
    
    // console.log('Parsed values - CPU:', cpuUsage, 'Memory:', memoryUsage, 'Disk:', diskUsage);
    
    // Update system data arrays
    systemData.timestamps.push(currentTime);
    systemData.cpu.push(cpuUsage);
    systemData.memory.push(memoryUsage);
    systemData.disk.push(diskUsage);
    
    // Keep only last 30 data points
    if (systemData.timestamps.length > 30) {
        systemData.timestamps.shift();
        systemData.cpu.shift();
        systemData.memory.shift();
        systemData.disk.shift();
    }
    
    // Update real-time chart
    systemRealtimeChart.setOption({
        xAxis: { data: systemData.timestamps },
        series: [
            { data: systemData.cpu },
            { data: systemData.memory },
            { data: systemData.disk }
        ]
    });
};

updateServiceStatus();

// Update information periodically
setInterval(updateSystemInfo, 2000);
setInterval(updateServiceStatus, 3000);

setInterval(updateRecentActivity, 5000);

// Initial load of recent activity
updateRecentActivity();

// Fungsi untuk memperbarui status layanan
async function updateServiceStatus() {
    try {
        const response = await fetch('/api/services/status');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        
        // Update status Nginx
        const nginxStatus = document.getElementById('nginx-status');
        const nginxStatusBadge = document.getElementById('nginx-status-badge');
        const nginxButtons = document.querySelector('#nginx-buttons');
        if (nginxStatus && nginxButtons) {
            if (data.nginx.installed) {
                nginxStatus.innerHTML = `
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                        <div>Version: ${data.nginx.version ? data.nginx.version.replace(/nginx version: nginx\//,'') : 'Unknown'}</div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            Uptime: ${data.nginx.uptime || 'Not available'}
                        </div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                            </svg>
                            PID: ${data.nginx.pid ? (Array.isArray(data.nginx.pid) ? data.nginx.pid.join(', ') : data.nginx.pid) : '-'}
                        </div>
                    </div>
                `;
                nginxStatus.className = `text-sm ${data.nginx.running ? 'text-green-600' : 'text-red-600'}`;
                if (nginxStatusBadge) {
                    nginxStatusBadge.textContent = data.nginx.running ? 'Running' : 'Stopped';
                    nginxStatusBadge.className = `px-2 py-1 text-xs font-medium rounded-full ${
                        data.nginx.running 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`;
                }
                nginxButtons.innerHTML = `
                    <button onclick="startService('nginx')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h8a2 2 0 012 2v8a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2z"></path>
                        </svg>
                        <span class="service-btn-text">Start</span>
                    </button>
                    <button onclick="stopService('nginx')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10h6m-6 4h6"></path>
                        </svg>
                        <span class="service-btn-text">Stop</span>
                    </button>
                    <button onclick="restartService('nginx')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <span class="service-btn-text">Restart</span>
                    </button>
                    <button onclick="uninstallService('nginx')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                        <span class="service-btn-text">Uninstall</span>
                    </button>
                `;
            } else {
                nginxStatus.textContent = 'Status: Tidak Terinstall';
                nginxStatus.className = 'text-sm text-gray-500';
                if (nginxStatusBadge) {
                    nginxStatusBadge.textContent = 'Not Installed';
                    nginxStatusBadge.className = 'px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full';
                }
                nginxButtons.innerHTML = `
                    <button onclick="installService('nginx')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        <span class="service-btn-text">Install Nginx</span>
                    </button>
                `;
            }
        }

        // Update status PHP-FPM
        const phpStatus = document.getElementById('php-status');
        const phpStatusBadge = document.getElementById('php-status-badge');
        const phpButtons = document.querySelector('#php-buttons');
        if (phpStatus && phpButtons) {
            if (data.php_fpm.installed) {
                phpStatus.innerHTML = `
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                        <div>Version: ${data.php_fpm.version ? data.php_fpm.version.replace(/^PHP\s+/,'').replace(/\s+\(built:.*$/,'') : 'Unknown'}</div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            Uptime: ${data.php_fpm.uptime || 'Not available'}
                        </div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                            </svg>
                            PID: ${data.php_fpm.pid ? (Array.isArray(data.php_fpm.pid) ? data.php_fpm.pid.join(', ') : data.php_fpm.pid) : '-'}
                        </div>
                    </div>
                `;
                phpStatus.className = `text-sm ${data.php_fpm.running ? 'text-green-600' : 'text-red-600'}`;
                if (phpStatusBadge) {
                    phpStatusBadge.textContent = data.php_fpm.running ? 'Running' : 'Stopped';
                    phpStatusBadge.className = `px-2 py-1 text-xs font-medium rounded-full ${
                        data.php_fpm.running 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`;
                }
                phpButtons.innerHTML = `
                    <button onclick="startService('php-fpm')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h8a2 2 0 012 2v8a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2z"></path>
                        </svg>
                        <span class="service-btn-text">Start</span>
                    </button>
                    <button onclick="stopService('php-fpm')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10h6m-6 4h6"></path>
                        </svg>
                        <span class="service-btn-text">Stop</span>
                    </button>
                    <button onclick="restartService('php-fpm')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <span class="service-btn-text">Restart</span>
                    </button>
                    <button onclick="uninstallService('php-fpm')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                        <span class="service-btn-text">Uninstall</span>
                    </button>
                `;
            } else {
                phpStatus.textContent = 'Status: Tidak Terinstall';
                phpStatus.className = 'text-sm text-gray-500';
                if (phpStatusBadge) {
                    phpStatusBadge.textContent = 'Not Installed';
                    phpStatusBadge.className = 'px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full';
                }
                phpButtons.innerHTML = `
                    <button onclick="installService('php-fpm')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        <span class="service-btn-text">Install PHP-FPM</span>
                    </button>
                `;
            }
        }

        // Update status MySQL
        const mysqlStatus = document.getElementById('mysql-status');
        const mysqlStatusBadge = document.getElementById('mysql-status-badge');
        const mysqlButtons = document.querySelector('#mysql-buttons');
        if (mysqlStatus && mysqlButtons) {
            if (data.mysql.installed) {
                mysqlStatus.innerHTML = `
                    <div class="text-sm text-gray-600 dark:text-gray-400">
                        <div>Version: ${data.mysql.version ? data.mysql.version.replace(/^mysql\s+Ver\s+/,'').replace(/\s+for\s+.*$/,'') : 'Unknown'}</div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            Uptime: ${data.mysql.uptime || 'Not available'}
                        </div>
                        <div class="flex items-center mt-1">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                            </svg>
                            PID: ${data.mysql.pid ? (Array.isArray(data.mysql.pid) ? data.mysql.pid.join(', ') : data.mysql.pid) : '-'}
                        </div>
                    </div>
                `;
                mysqlStatus.className = `text-sm ${data.mysql.running ? 'text-green-600' : 'text-red-600'}`;
                if (mysqlStatusBadge) {
                    mysqlStatusBadge.textContent = data.mysql.running ? 'Running' : 'Stopped';
                    mysqlStatusBadge.className = `px-2 py-1 text-xs font-medium rounded-full ${
                        data.mysql.running 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`;
                }
                mysqlButtons.innerHTML = `
                    <button onclick="startService('mysql')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h8a2 2 0 012 2v8a2 2 0 01-2 2H8a2 2 0 01-2-2V8a2 2 0 012-2z"></path>
                        </svg>
                        <span class="service-btn-text">Start</span>
                    </button>
                    <button onclick="stopService('mysql')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10h6m-6 4h6"></path>
                        </svg>
                        <span class="service-btn-text">Stop</span>
                    </button>
                    <button onclick="restartService('mysql')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <span class="service-btn-text">Restart</span>
                    </button>
                    <button onclick="uninstallService('mysql')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                        <span class="service-btn-text">Uninstall</span>
                    </button>
                `;
            } else {
                mysqlStatus.textContent = 'Status: Tidak Terinstall';
                mysqlStatus.className = 'text-sm text-gray-500';
                if (mysqlStatusBadge) {
                    mysqlStatusBadge.textContent = 'Not Installed';
                    mysqlStatusBadge.className = 'px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200 rounded-full';
                }
                mysqlButtons.innerHTML = `
                    <button onclick="installService('mysql')" class="service-btn px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                        <span class="service-btn-text">Install MySQL</span>
                    </button>
                `;
            }
        }

        // Update status PowerDNS
        const dnsStatus = document.getElementById('dns-status');
        const dnsButtons = document.querySelector('#dns-buttons');
        if (dnsStatus && dnsButtons && data.powerdns) {
            if (data.powerdns.installed) {
                dnsStatus.textContent = `Status: ${data.powerdns.running ? 'Berjalan' : 'Berhenti'} | Version: ${data.powerdns.version} | PID: ${data.powerdns.pid || 'N/A'}`;
                dnsStatus.className = `text-sm ${data.powerdns.running ? 'text-green-600' : 'text-red-600'}`;
                dnsButtons.innerHTML = `
                    <button onclick="startService('powerdns')" class="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">Start</button>
                    <button onclick="stopService('powerdns')" class="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">Stop</button>
                    <button onclick="restartService('powerdns')" class="px-3 py-1 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">Restart</button>
                    <button onclick="uninstallService('powerdns')" class="px-3 py-1 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">Uninstall</button>
                `;
            } else {
                dnsStatus.textContent = 'Status: Tidak Terinstall';
                dnsStatus.className = 'text-sm text-gray-500';
                dnsButtons.innerHTML = `
                    <button onclick="installService('powerdns')" class="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Install PowerDNS</button>
                `;
            }
        }
        
        // Update status UFW Firewall
        const firewallStatus = document.getElementById('firewall-status');
        const firewallButtons = document.querySelector('#firewall-buttons');
        if (firewallStatus && firewallButtons && data.ufw) {
            if (data.ufw.installed) {
                firewallStatus.textContent = `Status: ${data.ufw.running ? 'Aktif' : 'Tidak Aktif'} | Version: ${data.ufw.version} | PID: ${data.ufw.pid || 'N/A'}`;
                firewallStatus.className = `text-sm ${data.ufw.running ? 'text-green-600' : 'text-red-600'}`;
                firewallButtons.innerHTML = `
                    <button onclick="startService('ufw')" class="px-3 py-1 text-sm font-medium text-white bg-green-600 rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500">Enable</button>
                    <button onclick="stopService('ufw')" class="px-3 py-1 text-sm font-medium text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">Disable</button>
                    <button onclick="restartService('ufw')" class="px-3 py-1 text-sm font-medium text-white bg-yellow-600 rounded hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500">Restart</button>
                    <button onclick="uninstallService('ufw')" class="px-3 py-1 text-sm font-medium text-white bg-orange-600 rounded hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500">Uninstall</button>
                `;
            } else {
                firewallStatus.textContent = 'Status: Tidak Terinstall';
                firewallStatus.className = 'text-sm text-gray-500';
                firewallButtons.innerHTML = `
                    <button onclick="installService('ufw')" class="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Install UFW</button>
                `;
            }
        }
    } catch (error) {
        console.error('Error updating service status:', error);
        // Set status to error state
        ['nginx-status', 'php-status', 'mysql-status'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Error: Tidak dapat memuat status';
                element.className = 'text-sm text-red-600';
            }
        });
        // Set status badges to error state
        ['nginx-status-badge', 'php-status-badge', 'mysql-status-badge'].forEach(id => {
            const badge = document.getElementById(id);
            if (badge) {
                badge.textContent = 'Error';
                badge.className = 'px-2 py-1 text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-full';
            }
        });
    }
}
