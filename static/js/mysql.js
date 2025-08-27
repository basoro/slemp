// MariaDB Config Editor Functions
async function editMariaDBConfig() {
    try {
        const response = await fetch('/api/mariadb/config');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('mariadb-config-content').value = data.content;
            document.getElementById('mariadb-config-modal').classList.remove('hidden');
        } else {
            showNotification(`Gagal membaca konfigurasi: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat membaca konfigurasi MariaDB', 'error');
    }
}

function closeMariaDBConfigModal() {
    document.getElementById('mariadb-config-modal').classList.add('hidden');
}

async function saveMariaDBConfig() {
    try {
        const content = document.getElementById('mariadb-config-content').value;
        
        const response = await fetch('/api/mariadb/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Konfigurasi MariaDB berhasil disimpan!', 'success');
            closeMariaDBConfigModal();
        } else {
            showNotification(`Gagal menyimpan konfigurasi: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat menyimpan konfigurasi MariaDB', 'error');
    }
}

// MySQL Logs Functions
function openMySQLLogs() {
    document.getElementById('mysql-logs-modal').classList.remove('hidden');
    // Load MySQL logs by default
    switchLogTab('mysql');
}

function closeMySQLLogsModal() {
    document.getElementById('mysql-logs-modal').classList.add('hidden');
}

function switchLogTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.log-tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.log-tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        btn.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    
    // Show selected tab content
    document.getElementById(`log-content-${tabName}`).classList.remove('hidden');
    
    // Add active class to selected tab button
    const activeBtn = document.getElementById(`log-tab-${tabName}`);
    activeBtn.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    activeBtn.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
}

async function loadMySQLErrorLogsMain() {
    const logDisplay = document.getElementById('mysql-main-logs-display');
    logDisplay.innerHTML = '<div class="text-yellow-400">Loading MySQL error logs...</div>';
    
    try {
        const response = await fetch('/api/mysql/error-logs');
        const data = await response.json();
        
        if (data.success) {
            logDisplay.innerHTML = data.logs || '<div class="text-gray-500">No error logs found.</div>';
        } else {
            logDisplay.innerHTML = `<div class="text-red-400">Error loading logs: ${data.message}</div>`;
        }
    } catch (error) {
        logDisplay.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
    }
}

async function loadMySQLGeneralLogs() {
    const logDisplay = document.getElementById('mysql-main-logs-display');
    logDisplay.innerHTML = '<div class="text-yellow-400">Loading MySQL general logs...</div>';
    
    try {
        const response = await fetch('/api/mysql/general-logs');
        const data = await response.json();
        
        if (data.success) {
            logDisplay.innerHTML = data.logs || '<div class="text-gray-500">No general logs found.</div>';
        } else {
            logDisplay.innerHTML = `<div class="text-red-400">Error loading logs: ${data.message}</div>`;
        }
    } catch (error) {
        logDisplay.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
    }
}

function clearMySQLLogDisplay() {
    const logDisplay = document.getElementById('mysql-main-logs-display');
    logDisplay.innerHTML = '<div class="text-gray-500">Click "Load Error Logs" or "Load General Logs" to view log entries...</div>';
}

async function loadMySQLSlowLogs() {
    const logDisplay = document.getElementById('mysql-slow-logs-display');
    logDisplay.innerHTML = '<div class="text-yellow-400">Loading MySQL slow query logs...</div>';
    
    try {
        const response = await fetch('/api/mysql/slow-logs');
        const data = await response.json();
        
        if (data.success) {
            logDisplay.innerHTML = data.logs || '<div class="text-gray-500">No slow query logs found.</div>';
        } else {
            logDisplay.innerHTML = `<div class="text-red-400">Error loading logs: ${data.message}</div>`;
        }
    } catch (error) {
        logDisplay.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
    }
}

async function analyzeMySQLSlowLogs() {
    const logDisplay = document.getElementById('mysql-slow-logs-display');
    logDisplay.innerHTML = '<div class="text-yellow-400">Analyzing MySQL slow queries...</div>';
    
    try {
        const response = await fetch('/api/mysql/analyze-slow-logs');
        const data = await response.json();
        
        if (data.success) {
            logDisplay.innerHTML = data.analysis || '<div class="text-gray-500">No slow query analysis available.</div>';
        } else {
            logDisplay.innerHTML = `<div class="text-red-400">Error analyzing logs: ${data.message}</div>`;
        }
    } catch (error) {
        logDisplay.innerHTML = `<div class="text-red-400">Error: ${error.message}</div>`;
    }
}

function clearSlowLogDisplay() {
    const logDisplay = document.getElementById('mysql-slow-logs-display');
    logDisplay.innerHTML = '<div class="text-gray-500">Click "Load Slow Query Logs" to view slow query entries...</div>';
}

// Replica Management Functions
function manageReplica() {
    document.getElementById('replica-modal').classList.remove('hidden');
    // Set default tab to master
    switchReplicaTab('master');
    loadReplicationStatus();
}

function closeReplicaModal() {
    document.getElementById('replica-modal').classList.add('hidden');
}

async function loadReplicationStatus() {
    try {
        const response = await fetch('/api/mysql/replication/status');
        const data = await response.json();
        
        if (data.success) {
            updateReplicationStatusDisplay(data.status);
        } else {
            showNotification('Gagal memuat status replikasi: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error loading replication status:', error);
        showNotification('Error loading replication status', 'error');
    }
}

function updateReplicationStatusDisplay(status) {
    const masterStatus = document.getElementById('master-status');
    const slaveStatus = document.getElementById('slave-status');
    
    // Update Master Status
    if (status.master) {
        masterStatus.innerHTML = `
            <div class="bg-green-50 dark:bg-green-900 p-4 rounded-lg">
                <h4 class="font-medium text-green-800 dark:text-green-200 mb-2">Master Status: Active</h4>
                <div class="text-sm text-green-700 dark:text-green-300">
                    <p><strong>File:</strong> ${status.master.file}</p>
                    <p><strong>Position:</strong> ${status.master.position}</p>
                    <p><strong>Binlog Do DB:</strong> ${status.master.binlog_do_db || 'All'}</p>
                </div>
            </div>
        `;
    } else {
        masterStatus.innerHTML = `
            <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 class="font-medium text-gray-600 dark:text-gray-300">Master Status: Not Configured</h4>
            </div>
        `;
    }
    
    // Update Slave Status
    if (status.slave && status.slave.length > 0) {
        slaveStatus.innerHTML = status.slave.map(slave => `
            <div class="bg-blue-50 dark:bg-blue-900 p-4 rounded-lg mb-2">
                <h4 class="font-medium text-blue-800 dark:text-blue-200 mb-2">Slave Status</h4>
                <div class="text-sm text-blue-700 dark:text-blue-300">
                    <p><strong>Master Host:</strong> ${slave.master_host}</p>
                    <p><strong>Master User:</strong> ${slave.master_user}</p>
                    <p><strong>Slave IO Running:</strong> <span class="${slave.slave_io_running === 'Yes' ? 'text-green-600' : 'text-red-600'}">${slave.slave_io_running}</span></p>
                    <p><strong>Slave SQL Running:</strong> <span class="${slave.slave_sql_running === 'Yes' ? 'text-green-600' : 'text-red-600'}">${slave.slave_sql_running}</span></p>
                    <p><strong>Seconds Behind Master:</strong> ${slave.seconds_behind_master || 'N/A'}</p>
                </div>
            </div>
        `).join('');
    } else {
        slaveStatus.innerHTML = `
            <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 class="font-medium text-gray-600 dark:text-gray-300">Slave Status: Not Configured</h4>
            </div>
        `;
    }
}

async function setupMaster() {
    const serverIdInput = document.getElementById('master-server-id');
    const logBinInput = document.getElementById('master-log-bin');
    const replicationUserInput = document.getElementById('master-replication-user');
    const replicationPasswordInput = document.getElementById('master-replication-password');
    

    if (!serverIdInput.value) {
        showNotification('Server ID harus diisi', 'error');
        return;
    }
    
    if (!replicationUserInput.value) {
        showNotification('Username replika harus diisi', 'error');
        return;
    }
    
    if (!replicationPasswordInput.value) {
        showNotification('Password replika harus diisi', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/mysql/replication/setup-master', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                server_id: parseInt(serverIdInput.value),
                log_bin: logBinInput.value || 'mysql-bin',
                replication_user: replicationUserInput.value,
                replication_password: replicationPasswordInput.value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Master berhasil dikonfigurasi dan user replika dibuat', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal mengkonfigurasi master: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error setting up master:', error);
        showNotification('Error setting up master', 'error');
    }
}

async function disableMaster() {
    if (!(await showConfirm('Apakah Anda yakin ingin mematikan master replication? Ini akan menghapus konfigurasi replication dari MySQL.', 'Konfirmasi Disable Master'))) {
        return;
    }
    
    try {
        const response = await fetch('/api/mysql/replication/disable-master', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Master replication berhasil dimatikan', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal mematikan master replication: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error disabling master:', error);
        showNotification('Error disabling master', 'error');
    }
}

async function setupSlave() {
    const masterHostInput = document.getElementById('slave-master-host');
    const masterUserInput = document.getElementById('slave-master-user');
    const masterPasswordInput = document.getElementById('slave-master-password');
    const masterLogFileInput = document.getElementById('slave-master-log-file');
    const masterLogPosInput = document.getElementById('slave-master-log-pos');
    const serverIdInput = document.getElementById('slave-server-id');
    
    if (!masterHostInput.value || !masterUserInput.value || !masterPasswordInput.value || !serverIdInput.value) {
        showNotification('Semua field harus diisi', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/mysql/replication/setup-slave', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                master_host: masterHostInput.value,
                master_user: masterUserInput.value,
                master_password: masterPasswordInput.value,
                master_log_file: masterLogFileInput.value,
                master_log_pos: parseInt(masterLogPosInput.value) || 0,
                server_id: parseInt(serverIdInput.value)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Slave berhasil dikonfigurasi', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal mengkonfigurasi slave: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error setting up slave:', error);
        showNotification('Error setting up slave', 'error');
    }
}

async function startSlave() {
    try {
        const response = await fetch('/api/mysql/replication/start-slave', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Slave berhasil dijalankan', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal menjalankan slave: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error starting slave:', error);
        showNotification('Error starting slave', 'error');
    }
}

async function stopSlave() {
    try {
        const response = await fetch('/api/mysql/replication/stop-slave', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Slave berhasil dihentikan', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal menghentikan slave: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error stopping slave:', error);
        showNotification('Error stopping slave', 'error');
    }
}

async function resetSlave() {
    if (!(await showConfirm('Apakah Anda yakin ingin mereset konfigurasi slave?', 'Konfirmasi Reset Slave'))) {
        return;
    }
    
    try {
        const response = await fetch('/api/mysql/replication/reset-slave', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Slave berhasil direset', 'success');
            loadReplicationStatus();
        } else {
            showNotification('Gagal mereset slave: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Error resetting slave:', error);
        showNotification('Error resetting slave', 'error');
    }
}

// Update MySQL information
const updateMySQLInfo = async () => {
    try {
        const response = await fetch('/api/mysql-info');
        const data = await response.json();

        if (data.error) {
            document.getElementById('mysql-version').textContent = 'Error connecting to MySQL';
            document.getElementById('mysql-connections').textContent = 'N/A';
            return;
        }

        document.getElementById('mysql-version').textContent = data.version['version'] || 'N/A';
        document.getElementById('mysql-connections').textContent = data.status['Connections'] || 'N/A';
    } catch (error) {
        console.error('Error fetching MySQL info:', error);
    }
};

updateMySQLInfo();
setInterval(updateMySQLInfo, 5000); // Update every 5 seconds
loadDatabases();

function showTables(dbName) {
    document.getElementById('current-database').textContent = dbName;
    document.getElementById('tables-section').classList.remove('hidden');
    
    fetch(`/api/mysql/tables?database=${encodeURIComponent(dbName)}`)
        .then(response => response.json())
        .then(tables => {
            const tableList = document.getElementById('table-list');
            tableList.innerHTML = '';
            
            tables.forEach(table => {
                tableList.innerHTML += `
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${table.name}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${table.rows}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${table.size}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button onclick="deleteTable('${table.name}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                        </td>
                    </tr>
                `;
            });
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Failed to load tables', 'Error');
        });
}

async function executeQuery() {
    const database = document.getElementById('query-database').value;
    const query = document.getElementById('query-input').value;

    if (!database) {
        showAlert('Please select a database', 'Peringatan');
        return;
    }

    if (!query) {
        showAlert('Please enter a query', 'Peringatan');
        return;
    }

    try {
        const response = await fetch('/api/mysql/execute-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                database: database,
                query: query
            })
        });

        const result = await response.json();

        if (response.ok) {
            displayQueryResult(result);
            
            // Auto reload tables if query affects table structure
            const upperQuery = query.trim().toUpperCase();
            if (upperQuery.startsWith('CREATE TABLE') || 
                upperQuery.startsWith('DROP TABLE') || 
                upperQuery.startsWith('ALTER TABLE') ||
                upperQuery.startsWith('TRUNCATE TABLE')) {
                
                // Check if tables section is visible and reload if needed
                const tablesSection = document.getElementById('tables-section');
                if (!tablesSection.classList.contains('hidden')) {
                    const currentDatabase = document.getElementById('current-database').textContent;
                    if (currentDatabase && currentDatabase === database) {
                        showTables(currentDatabase);
                    }
                }
            }
        } else {
            showAlert(result.error || 'Error executing query', 'Error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Error executing query', 'Error');
    }
}

function displayQueryResult(result) {
    const resultDiv = document.getElementById('query-result');
    const headerDiv = document.getElementById('query-result-header');
    const bodyDiv = document.getElementById('query-result-body');

    resultDiv.classList.remove('hidden');
    headerDiv.innerHTML = '';
    bodyDiv.innerHTML = '';

    if (result.length === 0) {
        bodyDiv.innerHTML = '<tr><td colspan="100%" class="px-6 py-4 text-sm text-gray-500 dark:text-gray-300 text-center">No results found</td></tr>';
        return;
    }

    // Create header
    const headerRow = document.createElement('tr');
    Object.keys(result[0]).forEach(key => {
        headerRow.innerHTML += `
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">${key}</th>
        `;
    });
    headerDiv.appendChild(headerRow);

    // Create body
    result.forEach(row => {
        const bodyRow = document.createElement('tr');
        bodyRow.className = 'hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200';
        Object.values(row).forEach(value => {
            bodyRow.innerHTML += `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${value}</td>
            `;
        });
        bodyDiv.appendChild(bodyRow);
    });
}

// MySQL Database Management
async function createDatabase() {
    showCreateDatabaseModal();
}

function showCreateDatabaseModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white text-center mb-4">Buat Database Baru</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nama Database *</label>
                        <input type="text" id="dbNameInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="nama_database">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username Database (Opsional)</label>
                        <input type="text" id="dbUserInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password Database (Opsional)</label>
                        <input type="password" id="dbPasswordInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="password">
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">
                        <p>• Nama database hanya boleh menggunakan huruf, angka, dan underscore</p>
                        <p>• Jika username dan password diisi, akan dibuat user khusus untuk database ini</p>
                    </div>
                </div>
                <div class="flex justify-end space-x-2 mt-6">
                    <button id="createDbCancelBtn" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Batal</button>
                    <button id="createDbOkBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Buat Database</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const dbNameInput = document.getElementById('dbNameInput');
    const dbUserInput = document.getElementById('dbUserInput');
    const dbPasswordInput = document.getElementById('dbPasswordInput');
    
    dbNameInput.focus();
    
    const handleCreate = async () => {
        const dbName = dbNameInput.value.trim();
        const dbUser = dbUserInput.value.trim();
        const dbPassword = dbPasswordInput.value;
        
        if (!dbName) {
            showNotification('Nama database harus diisi', 'warning');
            return;
        }
        
        if (dbUser && !dbPassword) {
            showNotification('Password harus diisi jika username diisi', 'warning');
            return;
        }
        
        if (!dbUser && dbPassword) {
            showNotification('Username harus diisi jika password diisi', 'warning');
            return;
        }
        
        document.body.removeChild(modal);
        
        // Show loading notification
        showNotification('Membuat database...', 'info');
        
        try {
            const requestBody = { name: dbName };
            if (dbUser && dbPassword) {
                requestBody.user = dbUser;
                requestBody.password = dbPassword;
            }
            
            const response = await fetch('/api/mysql/create-db', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showNotification(result.message || 'Database berhasil dibuat', 'success');
                loadDatabases();
            } else {
                showNotification(result.error || 'Error membuat database', 'error');
            }
        } catch (error) {
            console.error('Error creating database:', error);
            showNotification('Terjadi kesalahan saat membuat database', 'error');
        }
    };
    
    const handleCancel = () => {
        document.body.removeChild(modal);
    };
    
    document.getElementById('createDbOkBtn').addEventListener('click', handleCreate);
    document.getElementById('createDbCancelBtn').addEventListener('click', handleCancel);
    
    // Handle Enter key
    [dbNameInput, dbUserInput, dbPasswordInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleCreate();
            }
        });
    });
    
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            handleCancel();
        }
    });
}

async function manageUsers() {
    showManageUsersModal();
}

function showManageUsersModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-10 mx-auto p-5 border w-4/5 max-w-4xl shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">Kelola User MySQL</h3>
                    <button id="closeUserModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <div class="mb-4">
                    <button id="createUserBtn" class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Buat User Baru
                    </button>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-700">
                            <tr>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Username</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Host</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Privileges</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700" id="user-list">
                            <!-- Users will be populated here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Load users
    loadMySQLUsers();
    
    // Event listeners
    document.getElementById('closeUserModal').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    document.getElementById('createUserBtn').addEventListener('click', () => {
        showCreateUserModal();
    });
    
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
        }
    });
}

async function loadMySQLUsers() {
    try {
        const response = await fetch('/api/mysql/users');
        const data = await response.json();
        
        const userList = document.getElementById('user-list');
        if (!userList) return;
        
        userList.innerHTML = '';
        
        if (data.error) {
            userList.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Error: ${data.error}
                    </td>
                </tr>
            `;
            return;
        }
        
        if (data.users && data.users.length > 0) {
            // Filter out system users
            const filteredUsers = data.users.filter(user => 
                !['root', 'mysql', 'mariadb.sys'].includes(user.User)
            );
            
            if (filteredUsers.length > 0) {
                filteredUsers.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${user.User}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${user.Host}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${user.privileges || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button onclick="editUser('${user.User}', '${user.Host}')" class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-3">Edit</button>
                            <button onclick="deleteUser('${user.User}', '${user.Host}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                        </td>
                    `;
                    userList.appendChild(row);
                });
            } else {
                userList.innerHTML = `
                    <tr>
                        <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                            No users found
                        </td>
                    </tr>
                `;
            }
        } else {
            userList.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        No users found
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading MySQL users:', error);
        const userList = document.getElementById('user-list');
        if (userList) {
            userList.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Error loading users
                    </td>
                </tr>
            `;
        }
    }
}

function showCreateUserModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white text-center mb-4">Buat User MySQL Baru</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username *</label>
                        <input type="text" id="userNameInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password *</label>
                        <input type="password" id="userPasswordInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="password">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Host</label>
                        <select id="userHostInput" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                            <option value="%">% (Any host)</option>
                            <option value="localhost">localhost</option>
                            <option value="127.0.0.1">127.0.0.1</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Database Privileges</label>
                        <select id="userPrivilegesInput" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                            <option value="ALL">ALL PRIVILEGES</option>
                            <option value="SELECT">SELECT only</option>
                            <option value="SELECT,INSERT,UPDATE,DELETE">Basic CRUD</option>
                        </select>
                    </div>
                </div>
                <div class="flex justify-end space-x-2 mt-6">
                    <button id="createUserCancelBtn" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Batal</button>
                    <button id="createUserOkBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Buat User</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const userNameInput = document.getElementById('userNameInput');
    const userPasswordInput = document.getElementById('userPasswordInput');
    const userHostInput = document.getElementById('userHostInput');
    const userPrivilegesInput = document.getElementById('userPrivilegesInput');
    
    userNameInput.focus();
    
    const handleCreateUser = async () => {
        const username = userNameInput.value.trim();
        const password = userPasswordInput.value;
        const host = userHostInput.value;
        const privileges = userPrivilegesInput.value;
        
        if (!username || !password) {
            showNotification('Username dan password harus diisi', 'warning');
            return;
        }
        
        document.body.removeChild(modal);
        showNotification('Membuat user...', 'info');
        
        try {
            const response = await fetch('/api/mysql/create-user', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    host: host,
                    privileges: privileges
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showNotification(result.message || 'User berhasil dibuat', 'success');
                loadMySQLUsers();
            } else {
                showNotification(result.error || 'Error membuat user', 'error');
            }
        } catch (error) {
            console.error('Error creating user:', error);
            showNotification('Terjadi kesalahan saat membuat user', 'error');
        }
    };
    
    const handleCancel = () => {
        document.body.removeChild(modal);
    };
    
    document.getElementById('createUserOkBtn').addEventListener('click', handleCreateUser);
    document.getElementById('createUserCancelBtn').addEventListener('click', handleCancel);
    
    [userNameInput, userPasswordInput].forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleCreateUser();
            }
        });
    });
    
    modal.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            handleCancel();
        }
    });
}

async function deleteUser(username, host) {
    if (!(await showConfirm(`Apakah Anda yakin ingin menghapus user '${username}'@'${host}'?`, 'Konfirmasi Hapus User'))) {
        return;
    }
    
    showNotification('Menghapus user...', 'info');
    
    try {
        const response = await fetch('/api/mysql/delete-user', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                host: host
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message || 'User berhasil dihapus', 'success');
            loadMySQLUsers();
        } else {
            showNotification(result.error || 'Error menghapus user', 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showNotification('Terjadi kesalahan saat menghapus user', 'error');
    }
}

function editUser(username, host) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white text-center mb-4">Edit User MySQL</h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
                        <input type="text" id="editUserNameInput" value="${username}" readonly
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-600 dark:text-white" 
                                placeholder="username">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Host</label>
                        <input type="text" id="editUserHostInput" value="${host}"
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="host">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password Baru</label>
                        <input type="password" id="editUserPasswordInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" 
                                placeholder="Masukkan password baru">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Hak Akses</label>
                        <select id="editUserPrivilegesInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                            <option value="ALL PRIVILEGES">ALL PRIVILEGES</option>
                            <option value="SELECT">SELECT</option>
                            <option value="INSERT">INSERT</option>
                            <option value="UPDATE">UPDATE</option>
                            <option value="DELETE">DELETE</option>
                            <option value="CREATE">CREATE</option>
                            <option value="DROP">DROP</option>
                        </select>
                    </div>
                </div>
                <div class="flex justify-end space-x-3 mt-6">
                    <button onclick="document.body.removeChild(this.closest('.fixed'))" 
                            class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">
                        Batal
                    </button>
                    <button onclick="handleEditUser('${username}', '${host}')" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                        Update User
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus on password input
    setTimeout(() => {
        document.getElementById('editUserPasswordInput').focus();
    }, 100);
    
    // Handle Enter key
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            handleEditUser(username, host);
        } else if (e.key === 'Escape') {
            document.body.removeChild(modal);
        }
    });
}

async function handleEditUser(originalUsername, originalHost) {
    const password = document.getElementById('editUserPasswordInput').value.trim();
    const privileges = document.getElementById('editUserPrivilegesInput').value;
    const newHost = document.getElementById('editUserHostInput').value.trim();
    
    if (!password) {
        showNotification('Password baru harus diisi', 'error');
        return;
    }
    
    if (!newHost) {
        showNotification('Host harus diisi', 'error');
        return;
    }
    
    showNotification('Mengupdate user...', 'info');
    
    try {
        const response = await fetch('/api/mysql/update-user', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: originalUsername,
                host: originalHost,
                new_host: newHost,
                password: password,
                privileges: privileges
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(result.message || 'User berhasil diupdate', 'success');
            document.body.removeChild(document.querySelector('.fixed'));
            loadMySQLUsers();
        } else {
            showNotification(result.error || 'Error mengupdate user', 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showNotification('Terjadi kesalahan saat mengupdate user', 'error');
    }
}

async function deleteDatabase(dbName) {
    if (!(await showConfirm(`Apakah Anda yakin ingin menghapus database '${dbName}'?`, 'Konfirmasi Hapus Database'))) return;

    // Show loading notification
    showNotification('Menghapus database...', 'info');

    try {
        const response = await fetch('/api/mysql/delete-db', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: dbName
            })
        });

        const result = await response.json();

        if (response.ok) {
            showNotification(result.message || 'Database berhasil dihapus', 'success');
            loadDatabases();
        } else {
            showNotification(result.error || 'Error menghapus database', 'error');
        }
    } catch (error) {
        console.error('Error deleting database:', error);
        showNotification('Terjadi kesalahan saat menghapus database', 'error');
    }
}

async function setRootPassword() {
    try {
        // Get current password first
        const currentResponse = await fetch('/api/mysql/get-root-password');
        const currentData = await currentResponse.json();
        
        let currentPassword = '';
        if (currentResponse.ok) {
            currentPassword = currentData.password || '';
        }
        
        // Create modal dialog with form input
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-[200]';
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3 text-center">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white">Set Root Password MySQL</h3>
                    <div class="mt-4">
                        <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">Password saat ini: <span class="font-mono">${currentPassword || '(kosong)'}</span></p>
                        <input type="text" id="newPasswordInput" 
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                                placeholder="Masukkan password baru (kosongkan untuk password kosong)" 
                                value="${currentPassword}">
                    </div>
                    <div class="flex justify-center space-x-3 mt-6">
                        <button id="cancelBtn" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Batal</button>
                        <button id="confirmBtn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Simpan</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus on input
        const input = document.getElementById('newPasswordInput');
        input.focus();
        input.select();
        
        // Handle modal events
            const handleSubmit = async () => {
                const newPassword = input.value;
                document.body.removeChild(modal);
                
                try {
                    // Show loading notification
                    showNotification('Mengatur password root...', 'info');

                    const response = await fetch('/api/mysql/set-root-password', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            password: newPassword
                        })
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showNotification(result.message || 'Password root berhasil diatur', 'success');
                    } else {
                        showNotification(result.error || 'Error mengatur password root', 'error');
                    }
                } catch (error) {
                    console.error('Error setting root password:', error);
                    showNotification('Terjadi kesalahan saat mengatur password root', 'error');
                }
            };
            
            const handleCancel = () => {
                document.body.removeChild(modal);
            };
            
            // Add event listeners
            document.getElementById('confirmBtn').addEventListener('click', handleSubmit);
            document.getElementById('cancelBtn').addEventListener('click', handleCancel);
            
            // Handle Enter key
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    handleSubmit();
                }
            });
            
            // Handle Escape key
            modal.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    handleCancel();
                }
            });
            
        } catch (error) {
            console.error('Error getting current password:', error);
            showNotification('Terjadi kesalahan saat mengambil password saat ini', 'error');
        }
}

async function deleteTable(tableName) {
    const currentDatabase = document.getElementById('current-database').textContent;
    if (!(await showConfirm(`Apakah Anda yakin ingin menghapus tabel '${tableName}' dari database '${currentDatabase}'?`, 'Konfirmasi Hapus Tabel'))) return;

    // Show loading notification
    showNotification('Menghapus tabel...', 'info');

    try {
        const response = await fetch('/api/mysql/delete-table', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                database: currentDatabase,
                table: tableName
            })
        });

        const result = await response.json();

        if (response.ok) {
            showNotification(result.message || 'Tabel berhasil dihapus', 'success');
            showTables(currentDatabase); // Refresh table list
        } else {
            showNotification(result.error || 'Error menghapus tabel', 'error');
        }
    } catch (error) {
        console.error('Error deleting table:', error);
        showNotification('Terjadi kesalahan saat menghapus tabel', 'error');
    }
}

async function loadDatabases() {
    try {
        const response = await fetch('/api/mysql/databases');
        
        // Check if response is successful
        if (!response.ok) {
            console.error('Error loading databases: HTTP', response.status);
            return;
        }
        
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Error parsing databases response as JSON:', jsonError);
            return;
        }
        const dbList = document.getElementById('database-list');
        const queryDatabase = document.getElementById('query-database');
        dbList.innerHTML = '';
        queryDatabase.innerHTML = '<option value="">Choose a database...</option>';

        // Check if response contains error
        if (data.error) {
            console.error('Error loading databases:', data.error);
            // Show error message in the table
            dbList.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        MySQL connection not available: ${data.error}
                    </td>
                </tr>
            `;
            return;
        }

        // Check if MySQL service is unavailable
        if (data.service_status === 'unavailable') {
            showNotification(data.message, 'warning');
            // Show empty state message in the table
            dbList.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        ${data.message}
                    </td>
                </tr>
            `;
            return;
        }

        // Handle normal database list (when service is available)
        const databases = data.databases || data; // Support both new and old response format
        
        // Check if databases is an array
        if (!Array.isArray(databases)) {
            console.error('Error loading databases: databases is not an array', databases);
            // Show error message in the table
            dbList.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Unable to load databases: Invalid data format
                    </td>
                </tr>
            `;
            return;
        }
        
        try {
            databases.forEach(db => {
                dbList.innerHTML += `
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${db.name}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${formatFileSize(db.size)}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                            <button onclick="showTables('${db.name}')" class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-4">Show Tables</button>
                            <button onclick="deleteDatabase('${db.name}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                    </td>
                </tr>`;
                queryDatabase.innerHTML += `<option value="${db.name}">${db.name}</option>`;
            });
        } catch (forEachError) {
            console.error('Error iterating databases:', forEachError);
            dbList.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        Error displaying databases
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading databases:', error);
    }
}