// Plugin List Functions
async function loadPlugins() {
    const pluginsGrid = document.getElementById('plugins-grid');
    
    try {
        const response = await fetch('/api/plugins');
        const data = await response.json();
        
        if (data.success && data.plugins) {
            renderPlugins(data.plugins);
        } else {
            pluginsGrid.innerHTML = '<div class="col-span-full text-center text-gray-500 dark:text-gray-400 py-8">No plugins found</div>';
        }
    } catch (error) {
        console.error('Error loading plugins:', error);
        pluginsGrid.innerHTML = '<div class="col-span-full text-center text-red-500 py-8">Error loading plugins</div>';
    }
}

function renderPlugins(plugins) {
    const pluginsGrid = document.getElementById('plugins-grid');
    
    if (plugins.length === 0) {
        pluginsGrid.innerHTML = '<div class="col-span-full text-center text-gray-500 dark:text-gray-400 py-8">No plugins installed</div>';
        return;
    }
    
    const pluginCards = plugins.map(plugin => {
        const statusColor = plugin.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
        const statusIcon = plugin.status === 'active' ? '●' : '○';
        
        return `
            <div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4 hover:shadow-md transition-shadow flex flex-col h-full">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                            ${plugin.icon ? 
                                `<img src="/static/icon/${plugin.icon}" alt="${plugin.name}" class="w-6 h-6 text-blue-600 dark:text-blue-300" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"><span class="text-blue-600 dark:text-blue-300 text-lg" style="display:none;">🔌</span>` :
                                '<span class="text-blue-600 dark:text-blue-300 text-lg">🔌</span>'
                            }
                        </div>
                        <div>
                            <h4 class="text-sm font-semibold text-gray-900 dark:text-white">${plugin.name}</h4>
                            <p class="text-xs text-gray-500 dark:text-gray-400">v${plugin.version}</p>
                        </div>
                    </div>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusColor}">
                        ${statusIcon} ${plugin.status}
                    </span>
                </div>
                
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2 flex-grow">${plugin.description}</p>
                
                <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-3">
                    <span>Category: ${plugin.category}</span>
                    <span>Size: ${plugin.size}</span>
                </div>
                
                <div class="flex items-center justify-between mt-auto">
                    <div class="flex items-center space-x-2">
                        <div class="flex items-center">
                            <span class="text-yellow-400">★</span>
                            <span class="text-xs text-gray-600 dark:text-gray-300 ml-1">${plugin.rating}</span>
                        </div>
                        <span class="text-xs text-gray-500 dark:text-gray-400">${plugin.downloads} downloads</span>
                    </div>
                    <div class="flex flex-wrap gap-1">
                        ${plugin.installed === true ? 
                            `<button onclick="window.location.href='/plugins/${plugin.id}'" class="px-2 py-1 text-sm bg-purple-300 text-purple-700 rounded hover:bg-purple-200 dark:bg-purple-900 dark:text-purple-200">Manage</button>` :
                            `<button onclick="downloadPlugin('${plugin.id}')" class="px-2 py-1 text-sm bg-cyan-300 text-cyan-700 rounded hover:bg-cyan-200 dark:bg-cyan-900 dark:text-cyan-200">Download</button>`
                        }
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    pluginsGrid.innerHTML = pluginCards;
}

async function refreshPlugins() {
    await loadPlugins();
}

async function togglePlugin(pluginName, action) {
    try {
        const response = await fetch('/api/plugins/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                plugin: pluginName,
                action: action
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            await loadPlugins(); // Refresh the plugin list
            showNotification(`Plugin ${pluginName} ${action}d successfully`, 'success');
        } else {
            showNotification(`Failed to ${action} plugin: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error toggling plugin:', error);
        showNotification(`Error ${action}ing plugin`, 'error');
    }
}

function configurePlugin(pluginName) {
    showNotification(`Configuration for ${pluginName} - Feature coming soon!`, 'info');
}

async function downloadPlugin(pluginName) {
    try {
        showNotification(`Downloading ${pluginName}...`, 'info');
        
        const response = await fetch('/api/plugins/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                plugin_name: pluginName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`${pluginName} downloaded successfully!`, 'success');
            await refreshPlugins();
        } else {
            showNotification(`Failed to download ${pluginName}: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error('Error downloading plugin:', error);
        showNotification(`Error downloading ${pluginName}`, 'error');
    }
}

function installPlugin(pluginName) {
    showNotification(`Installing ${pluginName}...`, 'info');
    // TODO: Implement install functionality
    setTimeout(() => {
        showNotification(`${pluginName} installed successfully!`, 'success');
        refreshPlugins();
    }, 3000);
}

function uninstallPlugin(pluginName) {
    if (confirm(`Are you sure you want to uninstall ${pluginName}?`)) {
        showNotification(`Uninstalling ${pluginName}...`, 'info');
        // TODO: Implement uninstall functionality
        setTimeout(() => {
            showNotification(`${pluginName} uninstalled successfully!`, 'success');
            refreshPlugins();
        }, 2000);
    }
}

loadPlugins();