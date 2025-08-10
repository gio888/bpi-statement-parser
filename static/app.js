// BPI Statement Parser - Web Interface JavaScript

let selectedFiles = [];
let processId = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const fileListItems = document.getElementById('file-list-items');
const processBtn = document.getElementById('process-btn');
const clearBtn = document.getElementById('clear-btn');
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const resultsSection = document.getElementById('results-section');
const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');

// Event Listeners
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', handleDragOver);
dropZone.addEventListener('drop', handleDrop);
dropZone.addEventListener('dragenter', () => dropZone.classList.add('drag-over'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
fileInput.addEventListener('change', handleFileSelect);
processBtn.addEventListener('click', processFiles);
clearBtn.addEventListener('click', clearFiles);
document.getElementById('process-more-btn').addEventListener('click', resetInterface);
document.getElementById('download-all-btn').addEventListener('click', downloadAll);

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

// File Selection
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function addFiles(files) {
    // Filter for PDF files only
    const pdfFiles = files.filter(file => {
        if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
            return true;
        } else {
            console.warn(`Skipping non-PDF file: ${file.name}`);
            return false;
        }
    });
    
    if (pdfFiles.length === 0) {
        showError('Please select PDF files only');
        return;
    }
    
    // Check file sizes
    const oversizedFiles = pdfFiles.filter(file => file.size > 50 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
        showError(`File(s) too large (max 50MB): ${oversizedFiles.map(f => f.name).join(', ')}`);
        return;
    }
    
    // Add to selected files
    selectedFiles = [...selectedFiles, ...pdfFiles];
    updateFileList();
}

function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.style.display = 'none';
        return;
    }
    
    fileList.style.display = 'block';
    fileListItems.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <div>
                <span class="file-name">📄 ${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
            </div>
            <button onclick="removeFile(${index})" style="background: none; border: none; color: var(--error-color); cursor: pointer;">✕</button>
        `;
        fileListItems.appendChild(li);
    });
    
    processBtn.disabled = false;
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
}

function clearFiles() {
    selectedFiles = [];
    fileInput.value = '';
    updateFileList();
}

// File Processing
async function processFiles() {
    if (selectedFiles.length === 0) {
        showError('Please select at least one PDF file');
        return;
    }
    
    // Disable buttons and show processing
    processBtn.disabled = true;
    clearBtn.disabled = true;
    
    // Update button to show spinner
    const btnText = processBtn.querySelector('.btn-text');
    const spinner = processBtn.querySelector('.spinner');
    btnText.textContent = 'Processing...';
    spinner.style.display = 'inline-block';
    
    // Show progress section
    progressSection.style.display = 'block';
    updateProgress(10, 'Uploading files...');
    
    // Prepare form data
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    try {
        // Upload and process files
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(50, 'Processing transactions...');
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Processing failed');
        }
        
        updateProgress(100, 'Complete!');
        
        // Store process ID for downloads
        processId = data.process_id;
        
        // Show results
        setTimeout(() => {
            showResults(data);
        }, 500);
        
    } catch (error) {
        showError(`Processing failed: ${error.message}`);
        resetProcessButton();
    }
}

function resetProcessButton() {
    processBtn.disabled = false;
    clearBtn.disabled = false;
    const btnText = processBtn.querySelector('.btn-text');
    const spinner = processBtn.querySelector('.spinner');
    btnText.textContent = 'Process Statements';
    spinner.style.display = 'none';
}

// Progress Updates
function updateProgress(percent, message) {
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    progressFill.style.width = `${percent}%`;
    progressText.textContent = message;
}

// Results Display
function showResults(data) {
    // Hide other sections
    uploadSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    // Update statistics
    document.getElementById('stat-files').textContent = data.processed || 0;
    document.getElementById('stat-transactions').textContent = data.total_transactions || 0;
    document.getElementById('stat-errors').textContent = data.errors ? data.errors.length : 0;
    
    // Show errors if any
    if (data.errors && data.errors.length > 0) {
        const errorsContainer = document.getElementById('errors-container');
        const errorList = document.getElementById('error-list');
        
        errorsContainer.style.display = 'block';
        errorList.innerHTML = '';
        
        data.errors.forEach(error => {
            const li = document.createElement('li');
            li.textContent = `${error.file}: ${error.error}`;
            errorList.appendChild(li);
        });
    }
    
    // Create download buttons
    const downloadButtons = document.getElementById('download-buttons');
    downloadButtons.innerHTML = '';
    
    if (data.output_files && data.output_files.length > 0) {
        data.output_files.forEach(file => {
            const downloadBtn = document.createElement('a');
            downloadBtn.className = 'download-btn';
            downloadBtn.href = `/api/download/${processId}/${file.name}`;
            downloadBtn.download = file.name;
            
            // Determine file type label
            let fileTypeLabel = 'CSV Export';
            let fileIcon = 'CSV';
            if (file.type === 'main') {
                fileTypeLabel = 'Main transaction data with all details';
                fileIcon = 'ALL';
            } else if (file.name.includes('ECREDIT')) {
                fileTypeLabel = 'BPI e-Credit Card transactions';
                fileIcon = 'eCR';
            } else if (file.name.includes('GOLD')) {
                fileTypeLabel = 'BPI Gold Rewards Card transactions';
                fileIcon = 'GLD';
            } else if (file.name.includes('Both')) {
                fileTypeLabel = 'Combined file for accounting import';
                fileIcon = 'IMP';
            }
            
            downloadBtn.innerHTML = `
                <div class="file-info">
                    <div class="file-icon">${fileIcon}</div>
                    <div class="file-details">
                        <div class="file-name">${file.name}</div>
                        <div class="file-type">${fileTypeLabel}</div>
                    </div>
                </div>
                <svg class="download-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            `;
            
            downloadButtons.appendChild(downloadBtn);
        });
    } else {
        downloadButtons.innerHTML = '<p>No files were generated. Please check the errors above.</p>';
    }
}

// Download All Files
async function downloadAll() {
    if (!processId) {
        showError('No files to download');
        return;
    }
    
    window.location.href = `/api/download-all/${processId}`;
}

// Reset Interface
function resetInterface() {
    // Clean up temporary files on server
    if (processId) {
        fetch(`/api/cleanup/${processId}`, { method: 'DELETE' })
            .catch(err => console.error('Cleanup failed:', err));
    }
    
    // Reset UI
    selectedFiles = [];
    fileInput.value = '';
    processId = null;
    
    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    
    updateFileList();
    resetProcessButton();
    
    // Clear progress
    updateProgress(0, '');
    document.getElementById('progress-details').innerHTML = '';
    
    // Clear errors
    document.getElementById('errors-container').style.display = 'none';
}

// Error Handling
function showError(message) {
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
}

function closeErrorModal() {
    errorModal.style.display = 'none';
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Health Check on Load
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('BPI Parser Web Interface:', data);
    } catch (error) {
        console.error('Server connection failed:', error);
        showError('Unable to connect to server. Please ensure the Flask server is running.');
    }
});