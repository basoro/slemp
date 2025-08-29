// File Manager Functions
let currentPath = '/';
let allFiles = []; // Store all files for search functionality
let isSearchActive = false;

async function loadFiles(path = '/opt/slemp/data/www') {
    try {
        const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
        const files = await response.json();
        currentPath = path;
        allFiles = files; // Store files for search
        document.getElementById('current-path').textContent = path;

        // Clear search if active
        if (isSearchActive) {
            clearSearch();
        }

        renderFileList(files);
    } catch (error) {
        console.error('Error loading files:', error);
        showAlert('Error loading files', 'Error');
    }
}

function renderFileList(files) {
    const fileList = document.getElementById('file-list');
    fileList.innerHTML = '';

    if (currentPath !== '/' && !isSearchActive) {
        // Add parent directory link
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
        fileList.innerHTML += `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-blue-600 dark:text-blue-400 cursor-pointer" onclick="loadFiles('${parentPath}')">..</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">-</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 text-right">-</td>
            </tr>`;
    }

    files.sort((a, b) => {
        if (a.is_dir && !b.is_dir) return -1;
        if (!a.is_dir && b.is_dir) return 1;
        return a.name.localeCompare(b.name);
    }).forEach(file => {
        const icon = file.is_dir ? '📁' : '📄';
        fileList.innerHTML += `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors duration-200">
                <td class="px-6 py-4 whitespace-nowrap text-sm ${file.is_dir ? 'text-blue-600 dark:text-blue-400 cursor-pointer' : 'text-gray-900 dark:text-white'}" ${file.is_dir ? `onclick="loadFiles('${file.path}')"` : ''}>
                    ${icon} ${file.name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${formatFileSize(file.size)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${formatDate(file.modified)}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 font-mono">${file.permissions || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">${file.owner || '-'}:${file.group || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300 text-right">
                    <div class="relative inline-block text-left">
                        <button onclick="toggleDropdown('${file.path}')" class="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-xs font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                            Actions
                            <svg class="-mr-1 ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>
                        <div id="dropdown-${file.path.replace(/[^a-zA-Z0-9]/g, '_')}" class="hidden origin-top-right fixed right-0 mt-2 w-48 rounded-md shadow-lg bg-white dark:bg-gray-700 ring-1 ring-black ring-opacity-5 z-[9999]">
                            <div class="py-1" role="menu">
                                ${!file.is_dir ? `<button onclick="openEditor('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                                    </svg>
                                    Edit
                                </button>` : ''}
                                ${!file.is_dir ? `<button onclick="downloadFile('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    Download
                                </button>` : ''}
                                <button onclick="compressFile('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                                    </svg>
                                    Compress
                                </button>
                                ${file.name.endsWith('.zip') || file.name.endsWith('.tar') || file.name.endsWith('.tar.gz') || file.name.endsWith('.tgz') || file.name.endsWith('.tar.bz2') ? `<button onclick="uncompressFile('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
                                    </svg>
                                    Extract
                                </button>` : ''}
                                <hr class="my-1 border-gray-200 dark:border-gray-600">
                                <button onclick="openChmodDialog('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                                    </svg>
                                    Permissions
                                </button>
                                <button onclick="openChownDialog('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                    </svg>
                                    Ownership
                                </button>
                                <hr class="my-1 border-gray-200 dark:border-gray-600">
                                <button onclick="renameFile('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                                    </svg>
                                    Rename
                                </button>
                                <button onclick="deleteFile('${file.path}'); hideDropdown('${file.path}')" class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900 flex items-center">
                                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                    </svg>
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>`;
    });
}

function searchFiles(query) {
    const searchInput = document.getElementById('file-search');
    const clearBtn = document.getElementById('clear-search-btn');
    
    if (query.trim() === '') {
        clearSearch();
        return;
    }
    
    isSearchActive = true;
    clearBtn.style.display = 'block';
    
    // Filter files based on search query
    const filteredFiles = allFiles.filter(file => 
        file.name.toLowerCase().includes(query.toLowerCase())
    );
    
    // Update current path display to show search mode
    document.getElementById('current-path').textContent = `Search results for "${query}" in ${currentPath}`;
    
    renderFileList(filteredFiles);
}

function clearSearch() {
    const searchInput = document.getElementById('file-search');
    const clearBtn = document.getElementById('clear-search-btn');
    
    searchInput.value = '';
    clearBtn.style.display = 'none';
    isSearchActive = false;
    
    // Restore original path display
    document.getElementById('current-path').textContent = currentPath;
    
    // Show all files again
    renderFileList(allFiles);
}

async function createDirectory() {
    const dirName = await showPrompt('Enter directory name:', '', 'Create Directory');
    if (!dirName) return;

    try {
        const response = await fetch('/api/files/create-directory', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentPath + '/' + dirName
            })
        });

        if (response.ok) {
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error creating directory', 'Error');
        }
    } catch (error) {
        console.error('Error creating directory:', error);
        showAlert('Error creating directory', 'Error');
    }
}

async function createNewFile() {
    const fileName = await showPrompt('Enter file name:', '', 'Create File');
    if (!fileName) return;

    try {
        const response = await fetch('/api/files/new', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentPath,
                name: fileName
            })
        });

        if (response.ok) {
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error creating file', 'Error');
        }
    } catch (error) {
        console.error('Error creating file:', error);
        showAlert('Error creating file', 'Error');
    }
}

async function uploadFile(file) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', currentPath);

    try {
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error uploading file', 'Error');
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        showAlert('Error uploading file', 'Error');
    }
}

async function deleteFile(path) {
    if (!(await showConfirm('Are you sure you want to delete this item?', 'Konfirmasi Hapus'))) return;

    try {
        const response = await fetch('/api/files/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });

        if (response.ok) {
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error deleting item', 'Error');
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        showAlert('Error deleting item', 'Error');
    }
}

async function renameFile(oldPath) {
    const newName = await showPrompt('Enter new name:', oldPath.split('/').pop(), 'Rename Item');
    if (!newName) return;

    const newPath = oldPath.split('/').slice(0, -1).concat(newName).join('/');

    try {
        const response = await fetch('/api/files/rename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                old_path: oldPath,
                new_path: newPath
            })
        });

        if (response.ok) {
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error renaming item', 'Error');
        }
    } catch (error) {
        console.error('Error renaming item:', error);
        showAlert('Error renaming item', 'Error');
    }
}

async function downloadFile(path) {
    try {
        const response = await fetch(`/api/files/download?path=${encodeURIComponent(path)}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = path.split('/').pop();
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showAlert('File downloaded successfully', 'Success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error downloading file', 'Error');
        }
    } catch (error) {
        console.error('Error downloading file:', error);
        showAlert('Error downloading file', 'Error');
    }
}

async function compressFile(path) {
    const archiveName = await showPrompt('Enter archive name (without extension):', path.split('/').pop() + '_archive', 'Compress File/Folder');
    if (!archiveName) return;

    try {
        const response = await fetch('/api/files/compress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paths: [path],
                archive_name: archiveName
            })
        });

        if (response.ok) {
            const result = await response.json();
            showAlert(result.message, 'Success');
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error compressing file', 'Error');
        }
    } catch (error) {
        console.error('Error compressing file:', error);
        showAlert('Error compressing file', 'Error');
    }
}

async function uncompressFile(path) {
    const extractTo = await showPrompt('Extract to directory (leave empty for current directory):', '', 'Extract Archive');
    if (extractTo === null) return; // User cancelled

    try {
        const response = await fetch('/api/files/uncompress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path,
                extract_to: extractTo || undefined
            })
        });

        if (response.ok) {
            const result = await response.json();
            showAlert(result.message, 'Success');
            loadFiles(currentPath);
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error extracting archive', 'Error');
        }
    } catch (error) {
        console.error('Error extracting archive:', error);
        showAlert('Error extracting archive', 'Error');
    }
}

function toggleDropdown(filePath) {
    const dropdownId = 'dropdown-' + filePath.replace(/[^a-zA-Z0-9]/g, '_');
    const dropdown = document.getElementById(dropdownId);
    
    // Hide all other dropdowns
    document.querySelectorAll('[id^="dropdown-"]').forEach(dd => {
        if (dd.id !== dropdownId) {
            dd.classList.add('hidden');
        }
    });
    
    // Toggle current dropdown
    if (dropdown.classList.contains('hidden')) {
        // Find the button that triggered this dropdown
        const button = dropdown.previousElementSibling;
        const buttonRect = button.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        // Position dropdown relative to button
        dropdown.style.left = (buttonRect.right - 192) + 'px'; // 192px = w-48
        
        // Check if dropdown would be cut off at bottom
        const estimatedDropdownHeight = 200; // Approximate height
        if (buttonRect.bottom + estimatedDropdownHeight > viewportHeight - 20) {
            // Position above button
            dropdown.style.top = (buttonRect.top - estimatedDropdownHeight) + 'px';
            dropdown.classList.remove('origin-top-right', 'mt-2');
            dropdown.classList.add('origin-bottom-right');
        } else {
            // Position below button
            dropdown.style.top = (buttonRect.bottom + 8) + 'px'; // 8px = mt-2
            dropdown.classList.add('origin-top-right');
            dropdown.classList.remove('origin-bottom-right');
        }
        
        dropdown.classList.remove('hidden');
    } else {
        dropdown.classList.add('hidden');
    }
}

function hideDropdown(filePath) {
    const dropdownId = 'dropdown-' + filePath.replace(/[^a-zA-Z0-9]/g, '_');
    const dropdown = document.getElementById(dropdownId);
    dropdown.classList.add('hidden');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.relative')) {
        document.querySelectorAll('[id^="dropdown-"]').forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
    }
});

// Monaco Editor Setup
let editor = null;
let currentEditingFile = null;
let editorTabs = [];
let activeTabIndex = -1;
let isSettingContent = false;

require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});
require(['vs/editor/editor.main'], function() {
    editor = monaco.editor.create(document.getElementById('monaco-editor'), {
        value: '',
        language: 'plaintext',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: { enabled: true },
        scrollBeyondLastLine: false,
        fontSize: 14,
        lineNumbers: 'on',
        renderWhitespace: 'selection',
        tabSize: 4
    });
    
    // Add event listener for content changes
    editor.onDidChangeModelContent(() => {
        // Ignore changes when we're setting content programmatically
        if (isSettingContent) return;
        
        if (activeTabIndex >= 0 && editorTabs[activeTabIndex]) {
            const currentContent = editor.getValue();
            // Compare with the original content when file was first loaded
            const tab = editorTabs[activeTabIndex];
            if (!tab.originalContent) {
                tab.originalContent = tab.content;
            }
            const isModified = currentContent !== tab.originalContent;
            
            if (tab.modified !== isModified) {
                tab.modified = isModified;
                renderTabs();
            }
        }
    });
});

function getFileExtension(filename) {
    return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
}

function getLanguageFromExtension(ext) {
    const languageMap = {
        'js': 'javascript',
        'py': 'python',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'md': 'markdown',
        'sql': 'sql',
        'php': 'php',
        'sh': 'shell',
        'bash': 'shell',
        'txt': 'plaintext'
    };
    return languageMap[ext] || 'plaintext';
}

async function openEditor(path) {
    try {
        // Open the editor modal first
        document.getElementById('editor-modal').classList.remove('hidden');
        
        // Initialize sidebar when opening editor
        initializeEditorSidebar();
        
        // Open the file in a new tab
        await openEditorFile(path);
    } catch (error) {
        console.error('Error opening editor:', error);
        showAlert('Error opening editor', 'Error');
    }
}

async function closeEditor() {
    // Check for unsaved changes in any tab
    const unsavedTabs = editorTabs.filter(tab => tab.modified);
    if (unsavedTabs.length > 0) {
        const fileNames = unsavedTabs.map(tab => tab.name).join(', ');
        if (!(await showConfirm(`You have unsaved changes in: ${fileNames}. Close anyway?`, 'Konfirmasi Tutup Editor'))) {
            return;
        }
    }
    
    document.getElementById('editor-modal').classList.add('hidden');
    currentEditingFile = null;
    editorTabs = [];
    activeTabIndex = -1;
    
    // Clear editor content
    if (editor) {
        editor.setValue('');
    }
}

// Editor toolbar functions
function editorAction(action) {
    if (!editor) return;
    
    switch(action) {
        case 'undo':
            editor.trigger('keyboard', 'undo', null);
            break;
        case 'redo':
            editor.trigger('keyboard', 'redo', null);
            break;
        case 'find':
            editor.trigger('keyboard', 'actions.find', null);
            break;
        case 'replace':
            editor.trigger('keyboard', 'editor.action.startFindReplaceAction', null);
            break;
        case 'format':
            editor.trigger('keyboard', 'editor.action.formatDocument', null);
            break;
        case 'comment':
            editor.trigger('keyboard', 'editor.action.commentLine', null);
            break;
    }
}

function toggleFullscreen() {
    const modal = document.getElementById('editor-modal');
    const modalContent = modal.querySelector('.inline-block');
    const editorLayout = modalContent.querySelector('.flex.border.border-gray-300');
    
    if (modalContent.classList.contains('fullscreen-editor')) {
        // Exit fullscreen
        modalContent.classList.remove('fullscreen-editor');
        modalContent.classList.add('w-full', 'max-w-sm', 'sm:max-w-2xl', 'md:max-w-5xl', 'lg:max-w-7xl', 'xl:max-w-screen-xl', 'mx-4');
        editorLayout.style.height = '500px';
        document.getElementById('monaco-editor').style.height = '100%';
        document.getElementById('monaco-editor').className = '';
    } else {
        // Enter fullscreen
        modalContent.classList.add('fullscreen-editor');
        modalContent.classList.remove('w-full', 'max-w-sm', 'sm:max-w-2xl', 'md:max-w-5xl', 'lg:max-w-7xl', 'xl:max-w-screen-xl', 'mx-4');
        editorLayout.style.height = 'calc(100vh - 150px)';
        document.getElementById('monaco-editor').style.height = '100%';
        document.getElementById('monaco-editor').className = '';
    }
    
    // Force complete editor refresh after fullscreen toggle
    setTimeout(() => {
        if (editor) {
            // Store current content and cursor position
            const currentContent = editor.getValue();
            const currentPosition = editor.getPosition();
            const currentLanguage = editor.getModel().getLanguageId();
            
            // Dispose current editor
            editor.dispose();
            
            // Recreate editor
            require(['vs/editor/editor.main'], function () {
                editor = monaco.editor.create(document.getElementById('monaco-editor'), {
                    value: currentContent,
                    language: currentLanguage,
                    theme: 'vs-dark',
                    automaticLayout: true,
                    minimap: { enabled: true },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    lineNumbers: 'on',
                    renderWhitespace: 'selection',
                    tabSize: 4
                });
                
                // Restore cursor position
                if (currentPosition) {
                    editor.setPosition(currentPosition);
                }
                
                // Re-add content change listener
                editor.onDidChangeModelContent(() => {
                    if (isSettingContent) return;
                    
                    if (activeTabIndex >= 0 && editorTabs[activeTabIndex]) {
                        const currentContent = editor.getValue();
                        const tab = editorTabs[activeTabIndex];
                        if (!tab.originalContent) {
                            tab.originalContent = tab.content;
                        }
                        const isModified = currentContent !== tab.originalContent;
                        
                        if (tab.modified !== isModified) {
                            tab.modified = isModified;
                            renderTabs();
                        }
                    }
                });
            });
        }
    }, 100);
}

function changeTheme(theme) {
    if (editor) {
        monaco.editor.setTheme(theme);
    }
}

function changeFontSize(size) {
    if (editor) {
        editor.updateOptions({ fontSize: parseInt(size) });
    }
}

async function saveFile() {
    if (!currentEditingFile) return;

    try {
        const content = editor.getValue();
        const response = await fetch('/api/files/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentEditingFile,
                content: content
            })
        });

        if (response.ok) {
            // Mark tab as saved
            if (editorTabs[activeTabIndex]) {
                isSettingContent = true; // Prevent change detection during save
                editorTabs[activeTabIndex].modified = false;
                editorTabs[activeTabIndex].content = content;
                editorTabs[activeTabIndex].originalContent = content;
                renderTabs();
                isSettingContent = false;
            }
            showAlert('File saved successfully', 'Success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error saving file', 'Error');
        }
    } catch (error) {
        console.error('Error saving file:', error);
        showAlert('Error saving file', 'Error');
    }
}

// Editor Sidebar Functions
async function saveEditorFile() {
    if (!currentEditingFile || activeTabIndex < 0) return;

    try {
        const content = editor.getValue();
        const response = await fetch('/api/files/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentEditingFile,
                content: content
            })
        });

        if (response.ok) {
            // Mark tab as saved
            if (editorTabs[activeTabIndex]) {
                isSettingContent = true; // Prevent change detection during save
                editorTabs[activeTabIndex].modified = false;
                editorTabs[activeTabIndex].content = content;
                editorTabs[activeTabIndex].originalContent = content;
                renderTabs();
                isSettingContent = false;
            }
            showAlert('File saved successfully', 'Success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error saving file', 'Error');
        }
    } catch (error) {
        console.error('Error saving file:', error);
        showAlert('Error saving file', 'Error');
    }
}

async function refreshEditorSidebar() {
    await loadEditorFileTree();
}

async function loadEditorFileTree() {
    try {
        const pathParam = currentPath || '/';
        const response = await fetch(`/api/files?path=${encodeURIComponent(pathParam)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const files = await response.json();
            // Convert the response format to match our expected format
            const formattedFiles = files.map(file => ({
                name: file.name,
                path: file.path,
                type: file.is_dir ? 'directory' : 'file'
            }));
            renderEditorFileTree(formattedFiles, pathParam);
            document.getElementById('editor-current-path').textContent = pathParam;
        } else {
            console.error('Error loading file tree');
        }
    } catch (error) {
        console.error('Error loading file tree:', error);
    }
}

function renderEditorFileTree(files, currentPath) {
    const fileTree = document.getElementById('editor-file-tree');
    fileTree.innerHTML = '';

    // Add back button if not in root
    if (currentPath !== '/') {
        const backItem = document.createElement('div');
        backItem.className = 'flex items-center p-2 hover:bg-gray-200 dark:hover:bg-gray-600 cursor-pointer rounded';
        backItem.innerHTML = `
            <svg class="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
            </svg>
            <span class="text-gray-600 dark:text-gray-300">..</span>
        `;
        backItem.onclick = () => navigateEditorPath('..');
        fileTree.appendChild(backItem);
    }

    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'flex items-center p-2 hover:bg-gray-200 dark:hover:bg-gray-600 cursor-pointer rounded';
        
        const isDirectory = file.type === 'directory';
        const icon = isDirectory ? 
            `<svg class="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2z"></path>
            </svg>` :
            `<svg class="w-4 h-4 mr-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>`;
        
        fileItem.innerHTML = `
            ${icon}
            <span class="text-gray-900 dark:text-white truncate">${file.name}</span>
        `;
        
        if (isDirectory) {
            fileItem.onclick = () => navigateEditorPath(file.name);
        } else {
            fileItem.onclick = () => openEditorFile(file.path);
        }
        
        fileTree.appendChild(fileItem);
    });
}

async function navigateEditorPath(path) {
    if (path === '..') {
        // Go back to parent directory
        const pathParts = currentPath.split('/').filter(p => p);
        pathParts.pop();
        currentPath = '/' + pathParts.join('/');
        if (currentPath === '/') currentPath = '/';
    } else {
        // Navigate to subdirectory
        currentPath = currentPath.endsWith('/') ? currentPath + path : currentPath + '/' + path;
    }
    await loadEditorFileTree();
}

async function openEditorFile(filePath) {
    console.log('DEBUG: Opening file:', filePath);
    
    // Check if file is already open in a tab
    const existingTabIndex = editorTabs.findIndex(tab => tab.path === filePath);
    if (existingTabIndex !== -1) {
        switchToTab(existingTabIndex);
        return;
    }

    try {
        console.log('DEBUG: Sending request to /api/files/read');
        const response = await fetch('/api/files/read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path: filePath })
        });

        console.log('DEBUG: Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('DEBUG: Response data:', data);
            console.log('DEBUG: Content length:', data.content ? data.content.length : 'no content');
            
            // Create new tab
            const newTab = {
                path: filePath,
                name: filePath.split('/').pop(),
                content: data.content || '',
                originalContent: data.content || '',
                language: getLanguageFromExtension(getFileExtension(filePath)),
                modified: false
            };
            
            console.log('DEBUG: Created tab:', newTab);
            
            editorTabs.push(newTab);
            activeTabIndex = editorTabs.length - 1;
            
            renderTabs();
            
            // Ensure editor is initialized before switching to tab
            if (!editor) {
                console.log('DEBUG: Editor not initialized, waiting...');
                // Wait for editor to be initialized
                const waitForEditorInit = () => {
                    if (editor) {
                        console.log('DEBUG: Editor ready, switching to tab');
                        switchToTab(activeTabIndex);
                    } else {
                        setTimeout(waitForEditorInit, 100);
                    }
                };
                waitForEditorInit();
            } else {
                console.log('DEBUG: Editor ready, switching to tab immediately');
                switchToTab(activeTabIndex);
            }
        } else {
            console.log('DEBUG: Response not ok:', response.status);
            const error = await response.json();
            console.log('DEBUG: Error response:', error);
            showAlert(error.error || 'Error reading file', 'Error');
        }
    } catch (error) {
        console.error('Error opening file:', error);
        showAlert('Error opening file', 'Error');
    }
}

// Tab Management Functions
function renderTabs() {
    const tabsContainer = document.getElementById('editor-tabs');
    const tabBar = document.getElementById('tab-bar');
    
    tabsContainer.innerHTML = '';
    
    // Show/hide tab bar based on number of tabs
    if (editorTabs.length === 0) {
        tabBar.style.display = 'none';
        return;
    } else {
        tabBar.style.display = 'block';
    }
    
    editorTabs.forEach((tab, index) => {
        const tabElement = document.createElement('div');
        tabElement.className = `flex items-center px-3 py-2 border-r border-gray-300 dark:border-gray-600 cursor-pointer ${
            index === activeTabIndex ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
        }`;
        
        tabElement.innerHTML = `
            <span class="text-sm truncate max-w-32" title="${tab.path}">${tab.name}</span>
            ${tab.modified ? '<span class="ml-1 text-xs text-orange-500">●</span>' : ''}
            <button onclick="(async () => await closeTab(${index}))()" class="ml-2 p-1 hover:bg-gray-300 dark:hover:bg-gray-600 rounded">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        tabElement.onclick = (e) => {
            if (e.target.tagName !== 'BUTTON' && !e.target.closest('button')) {
                switchToTab(index);
            }
        };
        
        tabsContainer.appendChild(tabElement);
    });
}

function switchToTab(index) {
    console.log('DEBUG: Switching to tab:', index);
    if (index < 0 || index >= editorTabs.length) return;
    
    // Save current tab content if there's an active tab and it's different from the new tab
    if (activeTabIndex >= 0 && activeTabIndex < editorTabs.length && editor && activeTabIndex !== index) {
        editorTabs[activeTabIndex].content = editor.getValue();
        console.log('DEBUG: Saved content from previous tab:', activeTabIndex);
    }
    
    activeTabIndex = index;
    const tab = editorTabs[activeTabIndex];
    
    console.log('DEBUG: Tab data:', tab);
    console.log('DEBUG: Tab content length:', tab.content ? tab.content.length : 'no content');
    
    currentEditingFile = tab.path;
    document.getElementById('editor-title').textContent = `Edit File: ${tab.path}`;
    
    // Wait for editor to be ready if it's not initialized yet
    if (editor && editor.getModel()) {
        console.log('DEBUG: Editor ready, setting content');
        isSettingContent = true;
        monaco.editor.setModelLanguage(editor.getModel(), tab.language);
        editor.setValue(tab.content);
        console.log('DEBUG: Editor content set, length:', editor.getValue().length);
        isSettingContent = false;
    } else {
        console.log('DEBUG: Editor not ready, waiting...');
        // If editor is not ready, wait for it to be initialized
        const waitForEditor = () => {
            if (editor && editor.getModel()) {
                console.log('DEBUG: Editor ready after wait, setting content');
                isSettingContent = true;
                monaco.editor.setModelLanguage(editor.getModel(), tab.language);
                editor.setValue(tab.content);
                console.log('DEBUG: Editor content set after wait, length:', editor.getValue().length);
                isSettingContent = false;
            } else {
                setTimeout(waitForEditor, 100);
            }
        };
        waitForEditor();
    }
    
    renderTabs();
}

async function closeTab(index) {
    if (index < 0 || index >= editorTabs.length) return;
    
    const tab = editorTabs[index];
    
    // Check if tab has unsaved changes
    if (tab.modified) {
        if (!(await showConfirm(`File "${tab.name}" has unsaved changes. Close anyway?`, 'Konfirmasi Tutup Tab'))) {
            return;
        }
    }
    
    editorTabs.splice(index, 1);
    
    // Adjust active tab index
    if (activeTabIndex >= index && activeTabIndex > 0) {
        activeTabIndex--;
    } else if (editorTabs.length === 0) {
        activeTabIndex = -1;
        currentEditingFile = null;
        document.getElementById('editor-title').textContent = 'Code Editor';
        if (editor) {
            editor.setValue('');
        }
    }
    
    renderTabs();
    
    // Switch to the new active tab if there are tabs remaining
    if (editorTabs.length > 0 && activeTabIndex >= 0) {
        switchToTab(activeTabIndex);
    }
}

// Initialize editor sidebar when modal opens
function initializeEditorSidebar() {
    loadEditorFileTree();
}

// Function to open terminal
function openTerminal() {
    // Open terminal in a new window/tab
    const terminalUrl = '/terminal';
    const terminalWindow = window.open(terminalUrl, 'terminal', 'width=1000,height=600,scrollbars=yes,resizable=yes');
    
    if (!terminalWindow) {
        // If popup was blocked, show notification
        showNotification('Please allow popups to open terminal', 'info');
    }
}

// Chmod and Chown functions
function openChmodDialog(filePath) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Change Permissions</h3>
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">File: ${filePath}</p>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Permissions (octal)</label>
                    <input type="text" id="chmod-mode" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" placeholder="755" maxlength="3">
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Examples: 755 (rwxr-xr-x), 644 (rw-r--r--)</p>
                </div>
                <div class="flex justify-end space-x-3">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                    <button onclick="changePermissions('${filePath}')" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Apply</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('chmod-mode').focus();
}

function openChownDialog(filePath) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Change Ownership</h3>
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">File: ${filePath}</p>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Owner</label>
                    <input type="text" id="chown-owner" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" placeholder="username or uid">
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Group</label>
                    <input type="text" id="chown-group" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white" placeholder="groupname or gid">
                </div>
                <div class="flex justify-end space-x-3">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500">Cancel</button>
                    <button onclick="changeOwnership('${filePath}')" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">Apply</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('chown-owner').focus();
}

async function changePermissions(filePath) {
    const mode = document.getElementById('chmod-mode').value;
    if (!mode || !/^[0-7]{3}$/.test(mode)) {
        showAlert('Please enter a valid 3-digit octal permission (e.g., 755)', 'Error');
        return;
    }

    try {
        const response = await fetch('/api/files/chmod', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: filePath,
                mode: mode
            })
        });

        const result = await response.json();
        if (response.ok) {
            showAlert('Permissions changed successfully', 'Success');
            document.querySelector('.fixed').remove();
            loadFiles(currentPath); // Refresh file list
        } else {
            showAlert(result.error || 'Failed to change permissions', 'Error');
        }
    } catch (error) {
        console.error('Error changing permissions:', error);
        showAlert('Error changing permissions', 'Error');
    }
}

async function changeOwnership(filePath) {
    const owner = document.getElementById('chown-owner').value;
    const group = document.getElementById('chown-group').value;
    
    if (!owner && !group) {
        showAlert('Please specify at least owner or group', 'Error');
        return;
    }

    try {
        const response = await fetch('/api/files/chown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: filePath,
                owner: owner || null,
                group: group || null
            })
        });

        const result = await response.json();
        if (response.ok) {
            showAlert('Ownership changed successfully', 'Success');
            document.querySelector('.fixed').remove();
            loadFiles(currentPath); // Refresh file list
        } else {
            showAlert(result.error || 'Failed to change ownership', 'Error');
        }
    } catch (error) {
        console.error('Error changing ownership:', error);
        showAlert('Error changing ownership', 'Error');
    }
}

loadFiles();
