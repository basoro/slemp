// Initialize ECharts for network monitoring
let networkData = {
    timestamps: [],
    inbound: [],
    outbound: []
};

const initializeNetworkCharts = () => {
    
    // Large real-time chart
    realtimeChart = echarts.init(document.getElementById('network-realtime-chart'));
    const realtimeOption = {
        title: {
            textStyle: { color: document.documentElement.classList.contains('dark') ? '#fff' : '#000' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' }
        },
        legend: {
            data: ['Inbound', 'Outbound'],
            textStyle: { color: document.documentElement.classList.contains('dark') ? '#fff' : '#000' }
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
            axisLabel: {
                color: document.documentElement.classList.contains('dark') ? '#fff' : '#000',
                formatter: function(value) {
                    if (value >= 1024 * 1024 * 1024) {
                        return (value / (1024 * 1024 * 1024)).toFixed(1) + 'GB';
                    } else if (value >= 1024 * 1024) {
                        return (value / (1024 * 1024)).toFixed(1) + 'MB';
                    } else if (value >= 1024) {
                        return (value / 1024).toFixed(1) + 'KB';
                    }
                    return value + 'B';
                }
            }
        },
        series: [
            {
                name: 'Inbound',
                type: 'line',
                data: [],
                smooth: true,
                lineStyle: { color: '#3b82f6' },
                areaStyle: { color: 'rgba(59, 130, 246, 0.1)' }
            },
            {
                name: 'Outbound',
                type: 'line',
                data: [],
                smooth: true,
                lineStyle: { color: '#10b981' },
                areaStyle: { color: 'rgba(16, 185, 129, 0.1)' }
            }
        ]
    };
    realtimeChart.setOption(realtimeOption);
};

let previousNetworkData = null;

const updateNetworkCharts = (data) => {
    // console.log('Received network data:', data);
    if (!data || !data.total_traffic) {
        console.log('No network data or total_traffic missing');
        return;
    }
    
    const currentTime = new Date().toLocaleTimeString();
    const currentInbound = data.total_traffic.bytes_recv;
    const currentOutbound = data.total_traffic.bytes_sent;
    
    // Calculate rates if we have previous data
    let inboundRate = 0;
    let outboundRate = 0;
    
    if (previousNetworkData) {
        const timeDiff = 2; // 2 seconds interval
        inboundRate = Math.max(0, (currentInbound - previousNetworkData.bytes_recv) / timeDiff);
        outboundRate = Math.max(0, (currentOutbound - previousNetworkData.bytes_sent) / timeDiff);
    }
    
    previousNetworkData = {
        bytes_recv: currentInbound,
        bytes_sent: currentOutbound
    };
    
    // Update network data arrays
    networkData.timestamps.push(currentTime);
    networkData.inbound.push(inboundRate);
    networkData.outbound.push(outboundRate);
    
    // Keep only last 30 data points
    if (networkData.timestamps.length > 30) {
        networkData.timestamps.shift();
        networkData.inbound.shift();
        networkData.outbound.shift();
    }
    
    // Update real-time chart only if it's initialized
    if (realtimeChart && typeof realtimeChart.setOption === 'function') {
        realtimeChart.setOption({
            xAxis: { data: networkData.timestamps },
            series: [
                { data: networkData.inbound },
                { data: networkData.outbound }
            ]
        });
    }
};

setTimeout(() => {
    initializeNetworkCharts();
    checkPowerDNSStatus();
}, 100);

// Handle window resize for charts
window.addEventListener('resize', () => {
    if (realtimeChart) realtimeChart.resize();
});

// DNS Manager Modal Functions
function showDnsManagerModal() {
    document.getElementById('dns-manager-modal').classList.remove('hidden');
    loadDomainList();
    loadDefaultNameServers();
}

function hideDnsManagerModal() {
    document.getElementById('dns-manager-modal').classList.add('hidden');
}

// Firewall Modal Functions
function showFirewallModal() {
    document.getElementById('firewall-modal').classList.remove('hidden');
    switchFirewallTab('rules');
    loadFirewallRules();
    loadFirewallStatus();
}

function hideFirewallModal() {
    document.getElementById('firewall-modal').classList.add('hidden');
}

function switchFirewallTab(tabName) {
    // Hide all sections
    document.querySelectorAll('.firewall-section').forEach(el => el.classList.add('hidden'));
    
    // Remove active class from all tabs
    document.querySelectorAll('.firewall-tab-btn').forEach(tab => {
        tab.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        tab.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    
    // Show selected section
    document.getElementById(tabName + '-section').classList.remove('hidden');
    
    // Add active class to selected tab
    const activeTab = document.getElementById('tab-' + tabName);
    if (activeTab) {
        activeTab.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        activeTab.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
    }
    
    // Load content based on tab
    if (tabName === 'rules') {
        loadFirewallRules();
    } else if (tabName === 'status') {
        loadFirewallStatus();
        loadFirewallLogs();
    } else if (tabName === 'ports') {
        initializePortManagement();
    } else if (tabName === 'settings') {
        loadFirewallSettings();
    }
}

function loadFirewallRules() {
    fetch('/api/ufw/rules')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayFirewallRules(data.rules);
            } else {
                showAlert('Error', data.error || 'Failed to load firewall rules');
            }
        })
        .catch(error => {
            console.error('Error loading firewall rules:', error);
            showAlert('Error', 'Failed to load firewall rules');
        });
}

function displayFirewallRules(rules) {
    const tbody = document.querySelector('#firewall-rules-tbody');
    tbody.innerHTML = '';
    
    if (rules.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    No firewall rules found
                </td>
            </tr>
        `;
        return;
    }
    
    rules.forEach(rule => {
        const row = document.createElement('tr');
        const actionColor = rule.action === 'ALLOW' ? 'text-green-600 dark:text-green-400' : 
                            rule.action === 'DENY' ? 'text-red-600 dark:text-red-400' : 
                            'text-yellow-600 dark:text-yellow-400';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${rule.port_protocol || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm ${actionColor}">${rule.action}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${rule.source}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${rule.destination}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button onclick="deleteFirewallRule('${rule.number}')" class="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function addFirewallRule() {
    showFirewallRuleModal();
}

function showFirewallRuleModal(rule = null) {
    const isEdit = rule !== null;
    const modalHtml = `
        <div id="firewall-rule-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">${isEdit ? 'Edit' : 'Add'} Firewall Rule</h3>
                    <form id="firewall-rule-form">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Action</label>
                            <select id="rule-action" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                                <option value="allow">Allow</option>
                                <option value="deny">Deny</option>
                                <option value="reject">Reject</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Port</label>
                            <input type="text" id="rule-port" placeholder="e.g., 80, 443, 8080-8090" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Protocol</label>
                            <select id="rule-protocol" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                                <option value="">Any</option>
                                <option value="tcp">TCP</option>
                                <option value="udp">UDP</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Source IP/Network</label>
                            <input type="text" id="rule-source" placeholder="e.g., 192.168.1.0/24, any" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                        </div>
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Destination IP/Network</label>
                            <input type="text" id="rule-destination" placeholder="e.g., 192.168.1.100, any" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button type="button" onclick="hideFirewallRuleModal()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">${isEdit ? 'Update' : 'Add'} Rule</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Handle form submission
    document.getElementById('firewall-rule-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitFirewallRule();
    });
}

function hideFirewallRuleModal() {
    const modal = document.getElementById('firewall-rule-modal');
    if (modal) {
        modal.remove();
    }
}

// Port Forward Modal Functions
function showPortForwardModal(isEdit = false, ruleId = null) {
    const modalHtml = `
        <div id="port-forward-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">${isEdit ? 'Edit' : 'Add'} Port Forward Rule</h3>
                    <form id="port-forward-form">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">External Port</label>
                            <input type="number" id="forward-external-port" placeholder="e.g., 8080" min="1" max="65535" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Internal IP</label>
                            <input type="text" id="forward-internal-ip" placeholder="e.g., 192.168.1.100" pattern="^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Internal Port</label>
                            <input type="number" id="forward-internal-port" placeholder="e.g., 80" min="1" max="65535" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Protocol</label>
                            <select id="forward-protocol" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                                <option value="tcp">TCP</option>
                                <option value="udp">UDP</option>
                                <option value="both">Both (TCP & UDP)</option>
                            </select>
                        </div>
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description (Optional)</label>
                            <input type="text" id="forward-description" placeholder="e.g., Web server forward" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button type="button" onclick="hidePortForwardModal()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">${isEdit ? 'Update' : 'Add'} Rule</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Store rule ID for editing
    if (isEdit && ruleId) {
        document.getElementById('port-forward-modal').dataset.ruleId = ruleId;
        loadPortForwardRuleData(ruleId);
    }
    
    // Handle form submission
    document.getElementById('port-forward-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitPortForwardRule();
    });
}

function hidePortForwardModal() {
    const modal = document.getElementById('port-forward-modal');
    if (modal) {
        modal.remove();
    }
}

function submitFirewallRule() {
    const formData = {
        action: document.getElementById('rule-action').value,
        port: document.getElementById('rule-port').value,
        protocol: document.getElementById('rule-protocol').value,
        source: document.getElementById('rule-source').value,
        destination: document.getElementById('rule-destination').value
    };
    
    fetch('/api/ufw/rule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            hideFirewallRuleModal();
            loadFirewallRules();
        } else {
            showAlert('Error', data.error || 'Failed to add firewall rule');
        }
    })
    .catch(error => {
        console.error('Error adding firewall rule:', error);
        showAlert('Error', 'Failed to add firewall rule');
    });
}

async function deleteFirewallRule(ruleNumber) {
    const confirmed = await showConfirm('Konfirmasi Hapus Rule', `Apakah Anda yakin ingin menghapus rule firewall nomor ${ruleNumber}?`);
    if (!confirmed) return;
    
    fetch('/api/ufw/rule/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rule_number: ruleNumber })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            loadFirewallRules();
        } else {
            showAlert('Error', data.error || 'Failed to delete port forward rule');
        }
    })
    .catch(error => {
        console.error('Error deleting port forward rule:', error);
        showAlert('Error', 'Failed to delete port forward rule');
    });
}

function loadPortForwardRuleData(ruleId) {
    fetch(`/api/port-forward/rules/${ruleId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success && data.rule) {
            const rule = data.rule;
            document.getElementById('forward-external-port').value = rule.external_port;
            document.getElementById('forward-internal-ip').value = rule.internal_ip;
            document.getElementById('forward-internal-port').value = rule.internal_port;
            document.getElementById('forward-protocol').value = rule.protocol;
            document.getElementById('forward-description').value = rule.description || '';
        } else {
            showAlert('Error', 'Failed to load rule data');
        }
    })
    .catch(error => {
        console.error('Error loading rule data:', error);
        showAlert('Error', 'Failed to load rule data');
    });
}

function initializePortManagement() {
    showPortTab('rules');
}

// Port Forwarding Functions
function showPortTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.port-tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.port-tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        btn.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    
    // Show selected tab content
    if (tabName === 'rules') {
        document.getElementById('port-rules-content').classList.remove('hidden');
        document.getElementById('port-rules-tab').classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        document.getElementById('port-rules-tab').classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        loadFirewallRules();
    } else if (tabName === 'forwarding') {
        document.getElementById('port-forwarding-content').classList.remove('hidden');
        document.getElementById('port-forwarding-tab').classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        document.getElementById('port-forwarding-tab').classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        loadPortForwardRules();
    }
}

function loadPortForwardRules() {
    fetch('/api/port-forward/rules')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayPortForwardRules(data.rules);
        } else {
            console.error('Failed to load port forward rules:', data.error);
            showAlert('Error', 'Failed to load port forward rules');
        }
    })
    .catch(error => {
        console.error('Error loading port forward rules:', error);
        showAlert('Error', 'Failed to load port forward rules');
    });
}

function displayPortForwardRules(rules) {
    const tbody = document.getElementById('port-forward-rules-list');
    const emptyDiv = document.getElementById('port-forward-rules-empty');
    
    if (!rules || rules.length === 0) {
        tbody.innerHTML = '';
        emptyDiv.classList.remove('hidden');
        return;
    }
    
    emptyDiv.classList.add('hidden');
    
    tbody.innerHTML = rules.map(rule => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.external_port}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.internal_ip}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.internal_port}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.protocol.toUpperCase()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.description || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    rule.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' : 
                    'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                }">
                    ${rule.status === 'active' ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="editPortForwardRule(${rule.id})" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-3">
                    Edit
                </button>
                <button onclick="deletePortForwardRule(${rule.id})" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">
                    Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function addPortForwardRule() {
    showPortForwardModal();
}

function editPortForwardRule(ruleId) {
    showPortForwardModal(ruleId);
}

function showPortForwardModal(ruleId = null) {
    const isEdit = ruleId !== null;
    
    const modalHtml = `
        <div id="port-forward-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">${isEdit ? 'Edit' : 'Add'} Port Forward Rule</h3>
                    <form id="port-forward-form">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">External Port</label>
                            <input type="number" id="forward-external-port" placeholder="e.g., 8080" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Internal IP</label>
                            <input type="text" id="forward-internal-ip" placeholder="e.g., 192.168.1.100" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Internal Port</label>
                            <input type="number" id="forward-internal-port" placeholder="e.g., 80" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Protocol</label>
                            <select id="forward-protocol" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" required>
                                <option value="tcp">TCP</option>
                                <option value="udp">UDP</option>
                                <option value="both">Both</option>
                            </select>
                        </div>
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</label>
                            <input type="text" id="forward-description" placeholder="Optional description" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                        </div>
                        <input type="hidden" id="forward-rule-id" value="${ruleId || ''}">
                        <div class="flex justify-end space-x-3">
                            <button type="button" onclick="hidePortForwardModal()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">${isEdit ? 'Update' : 'Add'} Rule</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Load existing data if editing
    if (isEdit) {
        loadPortForwardRuleData(ruleId);
    }
    
    // Handle form submission
    document.getElementById('port-forward-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitPortForwardRule();
    });
}

function hidePortForwardModal() {
    const modal = document.getElementById('port-forward-modal');
    if (modal) {
        modal.remove();
    }
}

function submitPortForwardRule() {
    const ruleId = document.getElementById('forward-rule-id').value;
    const isEdit = ruleId !== '';
    
    const formData = {
        external_port: parseInt(document.getElementById('forward-external-port').value),
        internal_ip: document.getElementById('forward-internal-ip').value,
        internal_port: parseInt(document.getElementById('forward-internal-port').value),
        protocol: document.getElementById('forward-protocol').value,
        description: document.getElementById('forward-description').value
    };
    
    const url = isEdit ? `/api/port-forward/rules/${ruleId}` : '/api/port-forward/rules';
    const method = isEdit ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            hidePortForwardModal();
            loadPortForwardRules();
        } else {
            showAlert('Error', data.error || 'Failed to save port forward rule');
        }
    })
    .catch(error => {
        console.error('Error saving port forward rule:', error);
        showAlert('Error', 'Failed to save port forward rule');
    });
}

async function deletePortForwardRule(ruleId) {
    const confirmed = await showConfirm('Konfirmasi Hapus Rule', 'Apakah Anda yakin ingin menghapus rule port forwarding ini?');
    if (!confirmed) return;
    
    fetch(`/api/port-forward/rules/${ruleId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            loadPortForwardRules();
        } else {
            showAlert('Error', data.error || 'Failed to delete firewall rule');
        }
    })
    .catch(error => {
        console.error('Error deleting firewall rule:', error);
        showAlert('Error', 'Failed to delete firewall rule');
    });
}

function loadFirewallStatus() {
    fetch('/api/ufw/status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayFirewallStatus(data);
            } else {
                showAlert('Error', data.error || 'Failed to load firewall status');
            }
        })
        .catch(error => {
            console.error('Error loading firewall status:', error);
            showAlert('Error', 'Failed to load firewall status');
        });
}

function displayFirewallStatus(statusData) {
    const statusSection = document.getElementById('status-section');
    const statusHtml = `
        <h4 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Firewall Status & Logs</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div class="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-6">
                <h5 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Status</h5>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-sm text-gray-600 dark:text-gray-400">Installed:</span>
                        <span class="text-sm font-medium ${statusData.installed ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                            ${statusData.installed ? 'Yes' : 'No'}
                        </span>
                    </div>
                    ${statusData.installed ? `
                        <div class="flex justify-between">
                            <span class="text-sm text-gray-600 dark:text-gray-400">Status:</span>
                            <span class="text-sm font-medium ${statusData.active ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}">
                                ${statusData.active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-sm text-gray-600 dark:text-gray-400">Default Incoming:</span>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">${statusData.default_incoming}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-sm text-gray-600 dark:text-gray-400">Default Outgoing:</span>
                            <span class="text-sm font-medium text-gray-900 dark:text-white">${statusData.default_outgoing}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="mt-4 space-y-2">
                    ${!statusData.installed ? `
                        <button onclick="installUFW()" class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Install UFW</button>
                    ` : `
                        ${!statusData.active ? `
                            <button onclick="enableUFW()" class="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">Enable Firewall</button>
                        ` : `
                            <button onclick="disableUFW()" class="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">Disable Firewall</button>
                        `}
                        <button onclick="resetUFW()" class="w-full px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700">Reset to Defaults</button>
                    `}
                </div>
            </div>
            <div class="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-6">
                <h5 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Actions</h5>
                <div class="space-y-2">
                    <button onclick="loadFirewallLogs()" class="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">Refresh Logs</button>
                    <button onclick="loadFirewallStatus()" class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Refresh Status</button>
                </div>
            </div>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg p-6">
            <h5 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Recent Logs</h5>
            <div id="firewall-logs" class="bg-gray-50 dark:bg-gray-900 rounded-md p-4 max-h-64 overflow-y-auto">
                <p class="text-sm text-gray-600 dark:text-gray-400">Loading logs...</p>
            </div>
        </div>
    `;
    statusSection.innerHTML = statusHtml;
    
    // Load logs after displaying status
    loadFirewallLogs();
}

function loadFirewallLogs() {
    fetch('/api/ufw/logs')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayFirewallLogs(data.logs);
            } else {
                document.getElementById('firewall-logs').innerHTML = '<p class="text-sm text-red-600 dark:text-red-400">Failed to load logs</p>';
            }
        })
        .catch(error => {
            console.error('Error loading firewall logs:', error);
            document.getElementById('firewall-logs').innerHTML = '<p class="text-sm text-red-600 dark:text-red-400">Failed to load logs</p>';
        });
}

function displayFirewallLogs(logs) {
    const logsContainer = document.getElementById('firewall-logs');
    if (logs.length === 0) {
        logsContainer.innerHTML = '<p class="text-sm text-gray-600 dark:text-gray-400">No recent firewall logs found</p>';
        return;
    }
    
    const logsHtml = logs.map(log => `
        <div class="text-xs text-gray-700 dark:text-gray-300 mb-1 font-mono">
            <span class="text-gray-500 dark:text-gray-400">[${log.file}]</span> ${log.line}
        </div>
    `).join('');
    
    logsContainer.innerHTML = logsHtml;
}

function enableUFW() {
    fetch('/api/ufw/enable', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Success', data.message);
                loadFirewallStatus();
            } else {
                showAlert('Error', data.error || 'Failed to enable firewall');
            }
        })
        .catch(error => {
            console.error('Error enabling firewall:', error);
            showAlert('Error', 'Failed to enable firewall');
        });
}

function disableUFW() {
    fetch('/api/ufw/disable', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Success', data.message);
                loadFirewallStatus();
            } else {
                showAlert('Error', data.error || 'Failed to disable firewall');
            }
        })
        .catch(error => {
            console.error('Error disabling firewall:', error);
            showAlert('Error', 'Failed to disable firewall');
        });
}

function installUFW() {
    fetch('/api/ufw/install', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Success', data.message);
                loadFirewallStatus();
            } else {
                showAlert('Error', data.error || 'Failed to install UFW');
            }
        })
        .catch(error => {
            console.error('Error installing UFW:', error);
            showAlert('Error', 'Failed to install UFW');
        });
}

async function resetUFW() {
    const confirmed = await showConfirm('Konfirmasi Reset UFW', 'Apakah Anda yakin ingin mereset UFW ke pengaturan default? Semua rule akan dihapus.');
    if (!confirmed) return;
    
    fetch('/api/ufw/reset', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Success', data.message);
                loadFirewallStatus();
                loadFirewallRules();
            } else {
                showAlert('Error', data.error || 'Failed to reset UFW');
            }
        })
        .catch(error => {
            console.error('Error resetting UFW:', error);
            showAlert('Error', 'Failed to reset UFW');
        });
}

// Port Management Functions
function addPortRule() {
    showPortRuleModal();
}

function showPortRuleModal(rule = null) {
    const isEdit = rule !== null;
    const modalHtml = `
        <div id="port-rule-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">${isEdit ? 'Edit' : 'Add'} Port Rule</h3>
                    <form id="port-rule-form">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Port/Range</label>
                            <input type="text" id="port-number" placeholder="e.g., 80, 443, 8080-8090" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" value="${isEdit ? rule.port : ''}">
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Protocol</label>
                            <select id="port-protocol" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                                <option value="tcp" ${isEdit && rule.protocol === 'tcp' ? 'selected' : ''}>TCP</option>
                                <option value="udp" ${isEdit && rule.protocol === 'udp' ? 'selected' : ''}>UDP</option>
                                <option value="both" ${isEdit && rule.protocol === 'both' ? 'selected' : ''}>Both</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Action</label>
                            <select id="port-action" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white">
                                <option value="allow" ${isEdit && rule.action === 'allow' ? 'selected' : ''}>Allow</option>
                                <option value="deny" ${isEdit && rule.action === 'deny' ? 'selected' : ''}>Deny</option>
                                <option value="reject" ${isEdit && rule.action === 'reject' ? 'selected' : ''}>Reject</option>
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Source</label>
                            <input type="text" id="port-source" placeholder="e.g., 192.168.1.0/24, any" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" value="${isEdit ? rule.source : 'any'}">
                        </div>
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</label>
                            <input type="text" id="port-description" placeholder="Optional description" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" value="${isEdit ? rule.description : ''}">
                        </div>
                        <div class="flex justify-end space-x-3">
                            <button type="button" onclick="hidePortRuleModal()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">${isEdit ? 'Update' : 'Add'} Rule</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Handle form submission
    document.getElementById('port-rule-form').addEventListener('submit', function(e) {
        e.preventDefault();
        submitPortRule(isEdit ? rule.id : null);
    });
}

function hidePortRuleModal() {
    const modal = document.getElementById('port-rule-modal');
    if (modal) {
        modal.remove();
    }
}

function submitPortRule(ruleId = null) {
    const formData = {
        port: document.getElementById('port-number').value,
        protocol: document.getElementById('port-protocol').value,
        action: document.getElementById('port-action').value,
        source: document.getElementById('port-source').value,
        description: document.getElementById('port-description').value
    };

    const url = ruleId ? `/api/ports/rule/${ruleId}` : '/api/ports/rule';
    const method = ruleId ? 'PUT' : 'POST';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            hidePortRuleModal();
            loadPortRules();
        } else {
            showAlert('Error', data.error || 'Failed to save port rule');
        }
    })
    .catch(error => {
        console.error('Error saving port rule:', error);
        showAlert('Error', 'Failed to save port rule');
    });
}

function loadPortRules() {
    fetch('/api/ports/rules')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPortRules(data.rules);
            } else {
                showAlert('Error', data.error || 'Failed to load port rules');
            }
        })
        .catch(error => {
            console.error('Error loading port rules:', error);
            showAlert('Error', 'Failed to load port rules');
        });
}

function displayPortRules(rules) {
    const tbody = document.querySelector('#port-rules-list');
    tbody.innerHTML = '';
    
    if (rules.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    No port rules found
                </td>
            </tr>
        `;
        return;
    }

    rules.forEach(rule => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700';
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.port}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.protocol.toUpperCase()}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    rule.action === 'allow' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                    rule.action === 'deny' ? 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100' :
                    'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
                }">
                    ${rule.action.charAt(0).toUpperCase() + rule.action.slice(1)}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.source}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${rule.description || '-'}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    rule.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                }">
                    ${rule.status.charAt(0).toUpperCase() + rule.status.slice(1)}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="editPortRule('${rule.id}')" class="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300 mr-3">Edit</button>
                <button onclick="deletePortRule('${rule.id}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function editPortRule(ruleId) {
    fetch(`/api/ports/rule/${ruleId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showPortRuleModal(data.rule);
            } else {
                showAlert('Error', data.error || 'Failed to load port rule');
            }
        })
        .catch(error => {
            console.error('Error loading port rule:', error);
            showAlert('Error', 'Failed to load port rule');
        });
}

async function deletePortRule(ruleId) {
    const confirmed = await showConfirm('Konfirmasi Hapus Rule', 'Apakah Anda yakin ingin menghapus rule port ini?');
    if (!confirmed) return;
    
    fetch(`/api/ports/rule/${ruleId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', data.message);
            loadPortRules();
        } else {
            showAlert('Error', data.error || 'Failed to delete port rule');
        }
    })
    .catch(error => {
        console.error('Error deleting port rule:', error);
        showAlert('Error', 'Failed to delete port rule');
    });
}

function allowCommonPort(port, protocol, description) {
    const formData = {
        port: port,
        protocol: protocol,
        action: 'allow',
        source: 'any',
        description: description
    };

    fetch('/api/ports/rule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', `${description} port ${port} allowed successfully`);
            loadPortRules();
        } else {
            showAlert('Error', data.error || `Failed to allow ${description} port`);
        }
    })
    .catch(error => {
        console.error('Error allowing port:', error);
        showAlert('Error', `Failed to allow ${description} port`);
    });
}

function refreshPortList() {
    loadPortRules();
    loadPortStatistics();
}

function quickAllowPort(port, description) {
    const formData = {
        port: port,
        protocol: 'tcp',
        action: 'allow',
        source: 'any',
        description: description
    };

    fetch('/api/ports/rule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', `${description} port ${port} allowed successfully`);
            refreshPortList();
        } else {
            showAlert('Error', data.error || `Failed to allow ${description} port`);
        }
    })
    .catch(error => {
        console.error('Error allowing port:', error);
        showAlert('Error', `Failed to allow ${description} port`);
    });
}

function scanPorts() {
    // Get target from input field
    const targetInput = document.getElementById('scan-target');
    const target = targetInput ? targetInput.value.trim() : '127.0.0.1';
    if (!target) {
        showAlert('Error', 'Please enter a target IP or hostname');
        return;
    }

    const scanButton = document.querySelector('button[onclick="scanPorts()"]');
    const originalText = scanButton.textContent;
    scanButton.textContent = 'Scanning...';
    scanButton.disabled = true;

    fetch('/api/ports/scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ target: target })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayPortScanResults(data.results);
            showAlert('Success', 'Port scan completed');
        } else {
            showAlert('Error', data.error || 'Failed to scan ports');
        }
    })
    .catch(error => {
        console.error('Error scanning ports:', error);
        showAlert('Error', 'Failed to scan ports');
    })
    .finally(() => {
        scanButton.textContent = originalText;
        scanButton.disabled = false;
    });
}

function displayPortScanResults(results) {
    const resultsContainer = document.getElementById('port-scan-results');
    if (results.length === 0) {
        resultsContainer.innerHTML = '<p class="text-sm text-gray-600 dark:text-gray-400">No open ports found</p>';
        return;
    }

    const resultsHtml = results.map(port => `
        <div class="flex justify-between items-center py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded mb-2">
            <div>
                <span class="font-medium text-gray-900 dark:text-white">Port ${port.port}</span>
                <span class="text-sm text-gray-600 dark:text-gray-400 ml-2">${port.protocol.toUpperCase()}</span>
                ${port.service ? `<span class="text-sm text-blue-600 dark:text-blue-400 ml-2">(${port.service})</span>` : ''}
            </div>
            <span class="px-2 py-1 text-xs font-semibold rounded-full ${
                port.status === 'open' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' :
                'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
            }">
                ${port.status.toUpperCase()}
            </span>
        </div>
    `).join('');

    resultsContainer.innerHTML = resultsHtml;
}

function loadPortStatistics() {
    fetch('/api/ports/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPortStatistics(data.stats);
            } else {
                showAlert('Error', data.error || 'Failed to load port statistics');
            }
        })
        .catch(error => {
            console.error('Error loading port statistics:', error);
            showAlert('Error', 'Failed to load port statistics');
        });
}

function displayPortStatistics(stats) {
    // Update individual statistics elements
    const openPortsElement = document.getElementById('open-ports-count');
    const blockedPortsElement = document.getElementById('blocked-ports-count');
    const totalRulesElement = document.getElementById('total-rules-count');
    
    if (openPortsElement) openPortsElement.textContent = stats.open_ports || 0;
    if (blockedPortsElement) blockedPortsElement.textContent = stats.blocked_ports || 0;
    if (totalRulesElement) totalRulesElement.textContent = stats.total_rules || 0;
}

function filterPortRules() {
    const searchTerm = document.getElementById('port-search').value.toLowerCase();
    const statusFilter = document.getElementById('port-status-filter').value;
    const actionFilter = document.getElementById('port-action-filter').value;
    
    const rows = document.querySelectorAll('#port-rules-list tr');
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length === 1) return; // Skip "no data" row
        
        const port = cells[0].textContent.toLowerCase();
        const protocol = cells[1].textContent.toLowerCase();
        const action = cells[2].textContent.toLowerCase();
        const source = cells[3].textContent.toLowerCase();
        const description = cells[4].textContent.toLowerCase();
        const status = cells[5].textContent.toLowerCase();
        
        const matchesSearch = !searchTerm || 
            port.includes(searchTerm) || 
            protocol.includes(searchTerm) || 
            source.includes(searchTerm) || 
            description.includes(searchTerm);
        
        const matchesStatus = !statusFilter || status.includes(statusFilter.toLowerCase());
        const matchesAction = !actionFilter || action.includes(actionFilter.toLowerCase());
        
        if (matchesSearch && matchesStatus && matchesAction) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Initialize Port Management when modal is shown
function initializePortManagement() {
    loadPortRules();
    loadPortStatistics();
}

// Firewall Settings Functions
function loadFirewallSettings() {
    // Load current SSH settings
    fetch('/api/ssh/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('ssh-port').value = data.port || 22;
                document.getElementById('ssh-allow-root').checked = data.allow_root || false;
                document.getElementById('ssh-password-auth').checked = data.password_auth !== false;
            }
        })
        .catch(error => console.error('Error loading SSH config:', error));

    // Load current firewall policies
    fetch('/api/ufw/policies')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('default-incoming').value = data.incoming || 'deny';
                document.getElementById('default-outgoing').value = data.outgoing || 'allow';
                document.getElementById('default-forward').value = data.forward || 'deny';
            }
        })
        .catch(error => console.error('Error loading firewall policies:', error));

    // Load logging settings
    fetch('/api/ufw/logging')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('logging-level').value = data.level || 'off';
                document.getElementById('log-denied').checked = data.log_denied || false;
                document.getElementById('log-allowed').checked = data.log_allowed || false;
            }
        })
        .catch(error => console.error('Error loading logging settings:', error));
}

function updateSSHSettings() {
    const port = document.getElementById('ssh-port').value;
    const allowRoot = document.getElementById('ssh-allow-root').checked;
    const passwordAuth = document.getElementById('ssh-password-auth').checked;

    if (!port || port < 1 || port > 65535) {
        showAlert('Error', 'Please enter a valid port number (1-65535)');
        return;
    }

    const settings = {
        port: parseInt(port),
        allow_root: allowRoot,
        password_auth: passwordAuth
    };

    fetch('/api/ssh/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', 'SSH settings updated successfully. Please restart SSH service to apply changes.');
        } else {
            showAlert('Error', data.error || 'Failed to update SSH settings');
        }
    })
    .catch(error => {
        console.error('Error updating SSH settings:', error);
        showAlert('Error', 'Failed to update SSH settings');
    });
}

function updateDefaultPolicies() {
    const incoming = document.getElementById('default-incoming').value;
    const outgoing = document.getElementById('default-outgoing').value;
    const forward = document.getElementById('default-forward').value;

    const policies = {
        incoming: incoming,
        outgoing: outgoing,
        forward: forward
    };

    fetch('/api/ufw/policies', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(policies)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', 'Default policies updated successfully');
            loadFirewallStatus();
        } else {
            showAlert('Error', data.error || 'Failed to update default policies');
        }
    })
    .catch(error => {
        console.error('Error updating default policies:', error);
        showAlert('Error', 'Failed to update default policies');
    });
}

function updateLoggingSettings() {
    const level = document.getElementById('logging-level').value;
    const logDenied = document.getElementById('log-denied').checked;
    const logAllowed = document.getElementById('log-allowed').checked;

    const settings = {
        level: level,
        log_denied: logDenied,
        log_allowed: logAllowed
    };

    fetch('/api/ufw/logging', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', 'Logging settings updated successfully');
        } else {
            showAlert('Error', data.error || 'Failed to update logging settings');
        }
    })
    .catch(error => {
        console.error('Error updating logging settings:', error);
        showAlert('Error', 'Failed to update logging settings');
    });
}

function updateSecuritySettings() {
    const rateLimit = document.getElementById('rate-limit').value;
    const connectionTimeout = document.getElementById('connection-timeout').value;
    const enableSynCookies = document.getElementById('enable-syn-cookies').checked;
    const enableConnectionTracking = document.getElementById('enable-connection-tracking').checked;
    const blockInvalidPackets = document.getElementById('block-invalid-packets').checked;

    const settings = {
        rate_limit: parseInt(rateLimit),
        connection_timeout: parseInt(connectionTimeout),
        enable_syn_cookies: enableSynCookies,
        enable_connection_tracking: enableConnectionTracking,
        block_invalid_packets: blockInvalidPackets
    };

    fetch('/api/firewall/security', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Success', 'Security settings updated successfully');
        } else {
            showAlert('Error', data.error || 'Failed to update security settings');
        }
    })
    .catch(error => {
        console.error('Error updating security settings:', error);
        showAlert('Error', 'Failed to update security settings');
    });
}

function showDnsSection(section) {
    // Hide all sections
    document.querySelectorAll('.dns-section').forEach(el => el.classList.add('hidden'));
    // Show selected section
    document.getElementById(section + '-section').classList.remove('hidden');
    
    // Reset all tab buttons to inactive state
    document.querySelectorAll('.dns-tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        btn.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    
    // Set active tab button
    const activeTab = document.getElementById(`dns-tab-${section}`);
    if (activeTab) {
        activeTab.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        activeTab.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
    }
}

async function loadDomainList() {
    try {
        const response = await fetch('/api/powerdns/domains');
        const data = await response.json();
        
        const domainList = document.getElementById('domain-list');
        
        if (data.success && data.domains.length > 0) {
            domainList.innerHTML = data.domains.map(domain => `
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${domain}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">Active</span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button onclick="viewDomainRecords('${domain}')" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-3">Records</button>
                        <button onclick="addDnsRecord('${domain}')" class="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 mr-3">Add Record</button>
                        <button onclick="deleteDomain('${domain}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                    </td>
                </tr>
            `).join('');
        } else {
            domainList.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                        ${data.message || 'No domains found. Add your first domain to get started.'}
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading domains:', error);
        const domainList = document.getElementById('domain-list');
        domainList.innerHTML = `
            <tr>
                <td colspan="3" class="px-6 py-4 text-center text-sm text-red-500 dark:text-red-400">
                    Error loading domains. Please check if PowerDNS is installed and running.
                </td>
            </tr>
        `;
    }
}

async function addDomainName() {
    const domain = await showPrompt('Enter domain name:', '', 'Add Domain');
    if (!domain) return;

    try {
        const response = await fetch('/api/powerdns/domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: domain })
        });

        const data = await response.json();
        if (data.success) {
            showAlert(`Domain ${domain} added successfully!`, 'Success');
            loadDomainList();
        } else {
            showAlert(data.message || 'Failed to add domain', 'Error');
        }
    } catch (error) {
        console.error('Error adding domain:', error);
        showAlert('Error adding domain', 'Error');
    }
}

async function loadDefaultNameServers() {
    try {
        const response = await fetch('/api/powerdns/default-ns');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('nameserver1').value = data.nameserver1;
            document.getElementById('nameserver2').value = data.nameserver2;
        }
    } catch (error) {
        console.error('Error loading default nameservers:', error);
    }
}

async function saveDefaultNameServers() {
    const nameserver1 = document.getElementById('nameserver1').value.trim();
    const nameserver2 = document.getElementById('nameserver2').value.trim();
    
    if (!nameserver1 || !nameserver2) {
        showAlert('Both nameservers are required', 'Error');
        return;
    }

    try {
        const response = await fetch('/api/powerdns/default-ns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                nameserver1: nameserver1,
                nameserver2: nameserver2
            })
        });

        const data = await response.json();
        if (data.success) {
            showAlert('Default nameservers saved successfully!', 'Success');
        } else {
            showAlert(data.message || 'Failed to save nameservers', 'Error');
        }
    } catch (error) {
        console.error('Error saving default nameservers:', error);
        showAlert('Error saving default nameservers', 'Error');
    }
}

async function deleteDomain(domain) {
    if (!(await showConfirm(`Are you sure you want to delete domain ${domain}?`, 'Konfirmasi Hapus Domain'))) return;

    try {
        const response = await fetch('/api/powerdns/delete-domain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: domain })
        });

        const data = await response.json();
        if (data.success) {
            showAlert(`Domain ${domain} deleted successfully!`, 'Success');
            loadDomainList();
        } else {
            showAlert(data.message || 'Failed to delete domain', 'Error');
        }
    } catch (error) {
        console.error('Error deleting domain:', error);
        showAlert('Error deleting domain', 'Error');
    }
}

async function addDnsRecord(domain) {
    const name = await showPrompt('Enter record name (e.g., www, mail):', '', 'Add DNS Record');
    if (!name) return;

    const type = await showPrompt('Enter record type (A, CNAME, MX, TXT):', 'A', 'Record Type');
    if (!type) return;

    const content = await showPrompt('Enter record content (e.g., IP address):', '', 'Record Content');
    if (!content) return;

    try {
        const response = await fetch('/api/powerdns/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                name: name,
                type: type,
                content: content
            })
        });

        const data = await response.json();
        if (data.success) {
            showAlert(`DNS record added successfully!`, 'Success');
        } else {
            showAlert(data.message || 'Failed to add DNS record', 'Error');
        }
    } catch (error) {
        console.error('Error adding DNS record:', error);
        showAlert('Error adding DNS record', 'Error');
    }
}

// DNS Records Modal Functions
let currentDomain = '';

function showDnsRecordsModal() {
    document.getElementById('dns-records-modal').classList.remove('hidden');
}

function hideDnsRecordsModal() {
    document.getElementById('dns-records-modal').classList.add('hidden');
}

async function viewDomainRecords(domain) {
    currentDomain = domain;
    document.getElementById('dns-records-title').textContent = `DNS Records for ${domain}`;
    showDnsRecordsModal();
    await loadDnsRecords(domain);
}

async function loadDnsRecords(domain) {
    try {
        const response = await fetch(`/api/powerdns/list-records/${domain}`);
        const data = await response.json();
        
        if (data.success) {
            let recordsHtml = `
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Name</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">TTL</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Type</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Content</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            `;
            
            data.records.forEach(record => {
                recordsHtml += `
                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${record.name}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${record.ttl}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                record.type === 'A' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                                record.type === 'NS' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' :
                                record.type === 'SOA' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300' :
                                record.type === 'CNAME' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300' :
                                record.type === 'MX' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300' :
                                'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
                            }">${record.type}</span>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-300 break-all">${record.content}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button onclick="editDnsRecord('${domain}', '${record.name}', '${record.type}', '${record.content}', '${record.ttl}')" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-2">Edit</button>
                            <button onclick="deleteDnsRecordInModal('${domain}', '${record.name}', '${record.type}', '${record.content}')" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Delete</button>
                        </td>
                    </tr>
                `;
            });
            
            recordsHtml += `
                            </tbody>
                        </table>
                </div>
            `;
            
            document.getElementById('dns-records-content').innerHTML = recordsHtml;
        } else {
            document.getElementById('dns-records-content').innerHTML = `
                <div class="p-6 text-center">
                    <p class="text-red-600 dark:text-red-400">${data.message || 'Failed to get domain records'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error getting domain records:', error);
        document.getElementById('dns-records-content').innerHTML = `
            <div class="p-6 text-center">
                <p class="text-red-600 dark:text-red-400">Error getting domain records</p>
            </div>
        `;
    }
}

async function restartPowerDNS() {
    try {
        const response = await fetch('/api/service/powerdns/restart', {
method: 'POST',
headers: {
    'Content-Type': 'application/json'
}
        });

        const data = await response.json();
        if (data.success) {
            showAlert('PowerDNS restarted successfully!', 'Success');
        } else {
            showAlert(data.message || 'Failed to restart PowerDNS', 'Error');
        }
    } catch (error) {
        console.error('Error restarting PowerDNS:', error);
        showAlert('Error restarting PowerDNS', 'Error');
    }
}

async function checkPowerDNSStatus() {
    try {
        const response = await fetch('/api/services/status');
        const data = await response.json();
        
        const statusDiv = document.getElementById('powerdns-status');
        const powerdnsStatus = data.powerdns;
        
        if (powerdnsStatus) {
            const statusColor = powerdnsStatus.running ? 'text-green-600' : 'text-red-600';
            const statusText = powerdnsStatus.running ? 'Running' : 'Stopped';
            const installedText = powerdnsStatus.installed ? 'Installed' : 'Not Installed';
            
            statusDiv.innerHTML = `
                <div class="space-y-2">
                    <p class="text-sm"><span class="font-medium">Status:</span> <span class="${statusColor}">${statusText}</span></p>
                    <p class="text-sm"><span class="font-medium">Installation:</span> ${installedText}</p>
                    ${powerdnsStatus.version ? `<p class="text-sm"><span class="font-medium">Version:</span> ${powerdnsStatus.version}</p>` : ''}
                    ${powerdnsStatus.pid ? `<p class="text-sm"><span class="font-medium">PID:</span> ${powerdnsStatus.pid}</p>` : ''}
                </div>
            `;
        } else {
            statusDiv.innerHTML = '<p class="text-sm text-red-600">PowerDNS status not available</p>';
        }
    } catch (error) {
        console.error('Error checking PowerDNS status:', error);
        document.getElementById('powerdns-status').innerHTML = '<p class="text-sm text-red-600">Error checking status</p>';
    }
}

// Edit DNS Record Functions
function editDnsRecord(domain, name, type, content, ttl) {
    // Populate the edit form with current values
    document.getElementById('editRecordDomain').value = domain;
    document.getElementById('editRecordOldName').value = name;
    document.getElementById('editRecordOldType').value = type;
    document.getElementById('editRecordOldContent').value = content;
    document.getElementById('editRecordOldTtl').value = ttl;
    
    document.getElementById('editRecordName').value = name;
    document.getElementById('editRecordType').value = type;
    document.getElementById('editRecordContent').value = content;
    document.getElementById('editRecordTtl').value = ttl;
    
    // Show the edit modal
    document.getElementById('editDnsRecordModal').classList.remove('hidden');
}

function closeEditDnsRecordModal() {
    document.getElementById('editDnsRecordModal').classList.add('hidden');
}

async function deleteDnsRecord(domain, name, type, content) {
if (!(await showConfirm(`Are you sure you want to delete the ${type} record "${name}" for ${domain}?`, 'Konfirmasi Hapus DNS Record'))) {
    return;
}
    
    try {
        const response = await fetch('/api/powerdns/record/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                name: name,
                type: type,
                content: content
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showAlert('DNS record deleted successfully!', 'Success');
            // Refresh the records view if it's currently open
            viewDomainRecords(domain);
        } else {
            showAlert(data.message || 'Failed to delete DNS record', 'Error');
        }
    } catch (error) {
        console.error('Error deleting DNS record:', error);
        showAlert('Error deleting DNS record', 'Error');
    }
}

async function deleteDnsRecordInModal(domain, name, type, content) {
if (!(await showConfirm(`Are you sure you want to delete the ${type} record "${name}" for ${domain}?`, 'Konfirmasi Hapus DNS Record'))) {
    return;
}
    
    try {
        const response = await fetch('/api/powerdns/record/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                domain: domain,
                name: name,
                type: type,
                content: content
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification('DNS record deleted successfully!', 'success');
            // Reload records in modal
            await loadDnsRecords(domain);
        } else {
            showAlert(data.message || 'Failed to delete DNS record', 'Error');
        }
    } catch (error) {
        console.error('Error deleting DNS record:', error);
        showAlert('Error deleting DNS record', 'Error');
    }
}


// Handle edit form submission
document.addEventListener('DOMContentLoaded', function() {
    const editForm = document.getElementById('editDnsRecordForm');
    if (editForm) {
        editForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(editForm);
            const data = {
                domain: formData.get('domain'),
                old_name: formData.get('old_name'),
                old_type: formData.get('old_type'),
                old_content: formData.get('old_content'),
                old_ttl: formData.get('old_ttl'),
                new_name: formData.get('name'),
                new_type: formData.get('type'),
                new_content: formData.get('content'),
                new_ttl: formData.get('ttl')
            };
            
            try {
                const response = await fetch('/api/powerdns/record/edit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                if (result.success) {
                    closeEditDnsRecordModal();
                    showNotification('DNS record updated successfully!', 'success');
                    // Reload records in modal if it's open
                    if (!document.getElementById('dns-records-modal').classList.contains('hidden')) {
                        await loadDnsRecords(data.domain);
                    }
                } else {
                    showAlert(result.message || 'Failed to update DNS record', 'Error');
                }
            } catch (error) {
                console.error('Error updating DNS record:', error);
                showAlert('Error updating DNS record', 'Error');
            }
        });
    }
});

async function loadPowerDNSLogs() {
    try {
        const response = await fetch('/api/service/powerdns/logs', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
        });

        const data = await response.json();
        const logsDiv = document.getElementById('powerdns-logs');
        
        if (data.success) {
            logsDiv.innerHTML = data.logs.split('\n').map(line => `<div>${line}</div>`).join('');
            logsDiv.scrollTop = logsDiv.scrollHeight;
        } else {
            logsDiv.innerHTML = `<div class="text-red-400">${data.message || 'Failed to load logs'}</div>`;
        }
    } catch (error) {
        console.error('Error loading PowerDNS logs:', error);
        document.getElementById('powerdns-logs').innerHTML = '<div class="text-red-400">Error loading logs</div>';
    }
}

async function saveDefaultNameServers() {
    const nameserver1 = document.getElementById('nameserver1').value;
    const nameserver2 = document.getElementById('nameserver2').value;
    
    if (!nameserver1 || !nameserver2) {
        showAlert('Please fill in both nameservers', 'Error');
        return;
    }
    
    try {
        const response = await fetch('/api/powerdns/default-ns', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nameserver1: nameserver1,
                nameserver2: nameserver2
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Default name servers saved successfully', 'Success');
        } else {
            showAlert(data.message || 'Failed to save default name servers', 'Error');
        }
    } catch (error) {
        console.error('Error saving default name servers:', error);
        showAlert('Error saving default name servers', 'Error');
    }
}

async function loadDefaultNameServers() {
    try {
        const response = await fetch('/api/powerdns/default-ns', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('nameserver1').value = data.nameserver1 || 'ns1.atila.co.id.';
            document.getElementById('nameserver2').value = data.nameserver2 || 'ns2.atila.co.id.';
        }
    } catch (error) {
        console.error('Error loading default name servers:', error);
    }
}

setInterval(updateServiceStatus, 3000);
setInterval(updateNetworkInfo, 3000);

// Fungsi untuk memperbarui status layanan
async function updateServiceStatus() {
    try {
        const response = await fetch('/api/services/status');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();

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
    }
}

// Network Configuration Modal Functions
function showNetworkConfigModal() {
    const modal = document.getElementById('network-config-modal');
    if (modal) {
        modal.classList.remove('hidden');
        loadNetworkInterfaces();
    }
}

function hideNetworkConfigModal() {
    const modal = document.getElementById('network-config-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function switchNetworkTab(tabName) {
    // Hide all sections
    document.querySelectorAll('.network-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.network-tab-btn').forEach(tab => {
        tab.classList.remove('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
        tab.classList.add('border-transparent', 'text-gray-500', 'dark:text-gray-400');
    });
    
    // Show selected section
    const section = document.getElementById(`${tabName}-section`);
    if (section) {
        section.classList.remove('hidden');
    }
    
    // Add active class to selected tab
    const tab = document.getElementById(`tab-${tabName}`);
    if (tab) {
        tab.classList.remove('border-transparent', 'text-gray-500', 'dark:text-gray-400');
        tab.classList.add('border-blue-500', 'text-blue-600', 'dark:text-blue-400');
    }
}

async function loadNetworkInterfaces() {
    try {
        const response = await fetch('/api/network/interfaces');
        const data = await response.json();
        
        if (data.success) {
            displayNetworkInterfaces(data.interfaces);
            populateInterfaceSelect(data.interfaces);
        } else {
            console.error('Failed to load network interfaces:', data.message);
        }
    } catch (error) {
        console.error('Error loading network interfaces:', error);
    }
}

function displayNetworkInterfaces(interfaces) {
    const container = document.getElementById('network-interfaces-list');
    if (!container) return;
    
    let html = `
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Interface</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">IP Address</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Netmask</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
    `;
    
    interfaces.forEach(iface => {
        const statusClass = iface.status === 'up' ? 'text-green-600' : 'text-red-600';
        html += `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${iface.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${iface.ip || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${iface.netmask || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm ${statusClass}">${iface.status}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="configureInterface('${iface.name}')" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-3">Configure</button>
                    <button onclick="toggleInterface('${iface.name}', '${iface.status}')" class="text-${iface.status === 'up' ? 'red' : 'green'}-600 hover:text-${iface.status === 'up' ? 'red' : 'green'}-900">
                        ${iface.status === 'up' ? 'Disable' : 'Enable'}
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

function populateInterfaceSelect(interfaces) {
    const select = document.getElementById('interface-select');
    if (!select) return;
    
    // Clear existing options except the first one
    select.innerHTML = '<option value="">Select Interface</option>';
    
    interfaces.forEach(iface => {
        const option = document.createElement('option');
        option.value = iface.name;
        option.textContent = `${iface.name} (${iface.ip || 'No IP'})`;
        select.appendChild(option);
    });
}

function configureInterface(interfaceName) {
    // Switch to static configuration tab
    switchNetworkTab('static');
    
    // Set the interface in the select
    const select = document.getElementById('interface-select');
    if (select) {
        select.value = interfaceName;
    }
}

async function toggleInterface(interfaceName, currentStatus) {
    const action = currentStatus === 'up' ? 'down' : 'up';
    
    try {
        const response = await fetch('/api/network/interface/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                interface: interfaceName,
                action: action
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Interface ${interfaceName} ${action === 'up' ? 'enabled' : 'disabled'} successfully`, 'success');
            loadNetworkInterfaces(); // Refresh the list
        } else {
            showNotification(`Failed to ${action} interface: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error toggling interface:', error);
        showNotification('Error toggling interface', 'error');
    }
}

function refreshNetworkInterfaces() {
    loadNetworkInterfaces();
}

function resetNetworkForm() {
    const form = document.getElementById('static-ip-form');
    if (form) {
        form.reset();
    }
}

// Handle static IP form submission
document.addEventListener('DOMContentLoaded', function() {
    const staticForm = document.getElementById('static-ip-form');
    if (staticForm) {
        staticForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(staticForm);
            const config = {
                interface: formData.get('interface'),
                ip_address: formData.get('ip_address'),
                netmask: formData.get('netmask'),
                broadcast: formData.get('broadcast'),
                gateway: formData.get('gateway'),
                dns_primary: formData.get('dns_primary'),
                dns_secondary: formData.get('dns_secondary'),
                mtu: formData.get('mtu')
            };
            
            try {
                const response = await fetch('/api/network/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('Network configuration applied successfully', 'success');
                    loadNetworkInterfaces(); // Refresh the interfaces
                } else {
                    showNotification(`Failed to apply configuration: ${data.message}`, 'error');
                }
            } catch (error) {
                console.error('Error applying network configuration:', error);
                showNotification('Error applying network configuration', 'error');
            }
        });
    }
});

function applyDhcpSettings() {
    const dhcpEnabled = document.getElementById('dhcp-enabled').checked;
    const hostname = document.getElementById('dhcp-hostname').value;
    const fallback = document.getElementById('dhcp-fallback').checked;
    
    const config = {
        enabled: dhcpEnabled,
        hostname: hostname,
        fallback: fallback
    };
    
    fetch('/api/network/dhcp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('DHCP settings applied successfully', 'success');
        } else {
            showNotification(`Failed to apply DHCP settings: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error applying DHCP settings:', error);
        showNotification('Error applying DHCP settings', 'error');
    });
}

// Update network information (now handled by SocketIO)
const updateNetworkInfo = async () => {
    try {
        const response = await fetch('/api/network-info');
        const data = await response.json();

        if (data.error) {
            console.error('Error fetching network info:', data.error);
            return;
        }

        // Update active connections and interfaces (non-real-time data)
        const activeConnections = document.getElementById('active-connections');
        if (activeConnections && data.connections !== undefined) {
            activeConnections.textContent = data.connections;
        }

        // Update network interfaces table
        const tableBody = document.getElementById('network-interfaces-table');
        if (tableBody) {
            tableBody.innerHTML = '';
        }

        if (data.interfaces && Array.isArray(data.interfaces)) {
            data.interfaces.forEach(interface => {
            // Only show interfaces that are up and have meaningful data
            if (interface.is_up && interface.addresses.length > 0) {
                const row = document.createElement('tr');
                row.className = 'hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200';
                row.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">${interface.name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 text-right">-</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            interface.is_up ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                        }">
                            ${interface.is_up ? 'Up' : 'Down'}
                        </span>
                    </td>
                `;
                if (tableBody) {
                    tableBody.appendChild(row);
                }
            }
            });
        }

        // Charts are now updated via SocketIO in updateNetworkCharts function
        // No need to update charts here as they use ECharts, not Chart.js

    } catch (error) {
        console.error('Error fetching network info:', error);
    }
};

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('network-config-modal');
    if (modal && event.target === modal) {
        hideNetworkConfigModal();
    }
});
