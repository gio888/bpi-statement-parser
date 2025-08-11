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
const reviewSection = document.getElementById('review-section');
const errorModal = document.getElementById('error-modal');
const errorMessage = document.getElementById('error-message');

// Global variables for review interface
let reviewData = null;
let validAccounts = [];
let filteredTransactions = [];
let currentSort = { column: null, direction: 'asc' };

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

// Review interface event listeners
document.getElementById('start-review-btn')?.addEventListener('click', startReview);
document.getElementById('save-corrections-btn')?.addEventListener('click', saveCorrections);
document.getElementById('skip-review-btn')?.addEventListener('click', skipReview);
document.getElementById('cancel-review-btn')?.addEventListener('click', cancelReview);
document.getElementById('confidence-filter')?.addEventListener('change', filterTransactions);
document.getElementById('description-search')?.addEventListener('input', filterTransactions);

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
    reviewSection.style.display = 'none';
    
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
    const downloadInfo = document.getElementById('download-info');
    downloadButtons.innerHTML = '';
    
    // Handle review prompt if available
    const reviewPrompt = document.getElementById('review-prompt');
    const downloadAllBtn = document.getElementById('download-all-btn');
    const downloadAllBtnFallback = document.getElementById('download-all-btn-fallback');
    
    if (data.has_review_data && data.review_summary) {
        // Show review prompt
        reviewPrompt.style.display = 'block';
        downloadAllBtnFallback.style.display = 'none';
        
        // Update confidence summary
        const summary = data.review_summary;
        const total = summary.total_transactions;
        const highPct = total > 0 ? Math.round((summary.high_confidence / total) * 100) : 0;
        const mediumPct = total > 0 ? Math.round((summary.medium_confidence / total) * 100) : 0;
        const lowPct = total > 0 ? Math.round((summary.low_confidence / total) * 100) : 0;
        
        document.getElementById('confidence-summary').innerHTML = 
            `<strong>${highPct}% high confidence</strong>, ${mediumPct}% medium, ${lowPct}% low confidence`;
    } else {
        // No review data, show regular download button
        reviewPrompt.style.display = 'none';
        downloadAllBtnFallback.style.display = 'inline-flex';
    }
    
    if (data.output_files && data.output_files.length > 0) {
        // Update the file count dynamically
        const fileCount = data.output_files.length;
        downloadInfo.textContent = `${fileCount} CSV file${fileCount !== 1 ? 's have' : ' has'} been generated for easy import to your accounting software:`;
        
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
        // No files generated - show appropriate message
        downloadInfo.textContent = 'No CSV files were generated.';
        if (downloadAllBtn) downloadAllBtn.style.display = 'none';
        if (downloadAllBtnFallback) downloadAllBtnFallback.style.display = 'none';
        
        if (data.total_transactions === 0) {
            downloadButtons.innerHTML = '<p>No transactions were found in the uploaded statement(s). Please verify the PDF format is supported.</p>';
        } else {
            downloadButtons.innerHTML = '<p>Files could not be generated. Please check the errors above.</p>';
        }
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

// Review Interface Functions
async function startReview() {
    try {
        if (!processId) {
            showError('No process ID available');
            return;
        }
        
        // Fetch review data
        const response = await fetch(`/api/review/${processId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load review data');
        }
        
        reviewData = data;
        validAccounts = data.valid_accounts;
        filteredTransactions = data.transactions;
        
        // Debug: Log accounts loaded for dropdown
        console.log(`Loaded ${validAccounts.length} accounts for autocomplete:`, validAccounts.slice(0, 10));
        
        showReviewInterface();
        
    } catch (error) {
        showError(`Review loading failed: ${error.message}`);
    }
}

function showReviewInterface() {
    // Hide results section and show review
    resultsSection.style.display = 'none';
    reviewSection.style.display = 'block';
    
    // Update summary statistics
    document.getElementById('review-total').textContent = reviewData.total_transactions;
    document.getElementById('review-high').textContent = reviewData.high_confidence;
    document.getElementById('review-medium').textContent = reviewData.medium_confidence;
    document.getElementById('review-low').textContent = reviewData.low_confidence;
    
    // Initialize table
    renderReviewTable();
    
    // Set up event handlers for table interactions
    setupTableSorting();
}

function renderReviewTable() {
    const tableBody = document.getElementById('review-table-body');
    tableBody.innerHTML = '';
    
    filteredTransactions.forEach((transaction, index) => {
        const row = createTransactionRow(transaction, index);
        tableBody.appendChild(row);
    });
}

function createTransactionRow(transaction, index) {
    const row = document.createElement('tr');
    row.className = getConfidenceClass(transaction.confidence);
    
    row.innerHTML = `
        <td class="col-date">${transaction.date}</td>
        <td class="col-description" title="${transaction.description}">${transaction.description}</td>
        <td class="col-amount">${formatAmount(transaction.amount)}</td>
        <td class="col-card">${transaction.card}</td>
        <td class="col-prediction" title="${transaction.current_account}">${transaction.current_account}</td>
        <td class="col-confidence">
            <span class="confidence-badge ${getConfidenceClass(transaction.confidence)}">
                ${transaction.confidence}%
            </span>
        </td>
        <td class="col-correction">
            <div class="account-selector">
                <input 
                    type="text" 
                    id="correction_${transaction.id}" 
                    value="${transaction.current_account}"
                    placeholder="Type to search accounts..."
                    class="account-input"
                    data-transaction-id="${transaction.id}"
                    autocomplete="off"
                />
                <div id="suggestions_${transaction.id}" class="account-suggestions"></div>
            </div>
        </td>
    `;
    
    // Setup autocomplete for this row
    setTimeout(() => setupAutocomplete(transaction.id), 50);
    
    return row;
}

function setupAutocomplete(transactionId) {
    const input = document.getElementById(`correction_${transactionId}`);
    const suggestions = document.getElementById(`suggestions_${transactionId}`);
    
    if (!input || !suggestions) return;
    
    let currentMatches = [];
    let selectedIndex = -1;
    
    function updateHighlight() {
        const items = suggestions.querySelectorAll('.suggestion-item');
        items.forEach((item, index) => {
            item.classList.toggle('highlighted', index === selectedIndex);
        });
    }
    
    function selectCurrentItem() {
        if (selectedIndex >= 0 && selectedIndex < currentMatches.length) {
            selectAccount(transactionId, currentMatches[selectedIndex]);
        }
    }
    
    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        selectedIndex = -1; // Reset selection on new input
        
        if (query.length < 1) {
            suggestions.style.display = 'none';
            currentMatches = [];
            return;
        }
        
        // Smart filtering: prioritize accounts that start with query, then contains query
        const startsWithMatches = validAccounts.filter(account => 
            account.toLowerCase().startsWith(query)
        ).slice(0, 8);
        
        const containsMatches = validAccounts.filter(account => 
            account.toLowerCase().includes(query) && !account.toLowerCase().startsWith(query)
        ).slice(0, 7);
        
        currentMatches = [...startsWithMatches, ...containsMatches].slice(0, 15);
        
        if (currentMatches.length === 0) {
            suggestions.style.display = 'none';
            return;
        }
        
        suggestions.innerHTML = '';
        currentMatches.forEach((account, index) => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            
            // Highlight the matching part for better visibility
            const parts = account.split(':');
            const lastPart = parts[parts.length - 1];
            const parentParts = parts.slice(0, -1).join(':');
            
            if (parentParts) {
                suggestionItem.innerHTML = `<span class="account-parent">${parentParts}:</span><span class="account-name">${lastPart}</span>`;
            } else {
                suggestionItem.textContent = account;
            }
            
            suggestionItem.onclick = () => selectAccount(transactionId, account);
            suggestions.appendChild(suggestionItem);
        });
        
        suggestions.style.display = 'block';
        updateHighlight();
    });
    
    input.addEventListener('keydown', (e) => {
        if (suggestions.style.display === 'none' || currentMatches.length === 0) {
            return;
        }
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, currentMatches.length - 1);
                updateHighlight();
                break;
            
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                updateHighlight();
                break;
            
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0) {
                    selectCurrentItem();
                }
                break;
            
            case 'Escape':
                e.preventDefault();
                suggestions.style.display = 'none';
                selectedIndex = -1;
                break;
        }
    });
    
    input.addEventListener('blur', () => {
        // Delay hiding to allow click on suggestions
        setTimeout(() => {
            suggestions.style.display = 'none';
            selectedIndex = -1;
        }, 200);
    });
}

function selectAccount(transactionId, account) {
    const input = document.getElementById(`correction_${transactionId}`);
    const suggestions = document.getElementById(`suggestions_${transactionId}`);
    
    if (input) {
        input.value = account;
        input.classList.add('modified');
    }
    if (suggestions) {
        suggestions.style.display = 'none';
    }
}

function filterTransactions() {
    const confidenceFilter = document.getElementById('confidence-filter').value;
    const searchQuery = document.getElementById('description-search').value.toLowerCase();
    
    filteredTransactions = reviewData.transactions.filter(transaction => {
        // Apply confidence filter
        let passesConfidenceFilter = true;
        if (confidenceFilter === 'low' && transaction.confidence >= 50) passesConfidenceFilter = false;
        if (confidenceFilter === 'medium' && (transaction.confidence < 50 || transaction.confidence >= 70)) passesConfidenceFilter = false;
        if (confidenceFilter === 'high' && transaction.confidence < 70) passesConfidenceFilter = false;
        
        // Apply search filter
        const passesSearchFilter = !searchQuery || 
            transaction.description.toLowerCase().includes(searchQuery) ||
            transaction.current_account.toLowerCase().includes(searchQuery);
        
        return passesConfidenceFilter && passesSearchFilter;
    });
    
    renderReviewTable();
}

function setupTableSorting() {
    const headers = document.querySelectorAll('#review-table th.sortable');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-column');
            sortTransactions(column);
        });
    });
}

function sortTransactions(column) {
    const direction = (currentSort.column === column && currentSort.direction === 'asc') ? 'desc' : 'asc';
    
    filteredTransactions.sort((a, b) => {
        let valueA = a[column];
        let valueB = b[column];
        
        // Handle numeric columns
        if (column === 'amount' || column === 'confidence') {
            valueA = parseFloat(valueA) || 0;
            valueB = parseFloat(valueB) || 0;
        } else {
            valueA = String(valueA).toLowerCase();
            valueB = String(valueB).toLowerCase();
        }
        
        if (direction === 'asc') {
            return valueA > valueB ? 1 : -1;
        } else {
            return valueA < valueB ? 1 : -1;
        }
    });
    
    currentSort = { column, direction };
    
    // Update UI to show sort direction
    document.querySelectorAll('#review-table th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    document.querySelector(`#review-table th[data-column="${column}"]`)?.classList.add(`sort-${direction}`);
    
    renderReviewTable();
}

async function saveCorrections() {
    try {
        // Collect all corrections
        const corrections = [];
        
        reviewData.transactions.forEach(transaction => {
            const input = document.getElementById(`correction_${transaction.id}`);
            if (input && input.value !== transaction.current_account) {
                corrections.push({
                    id: transaction.id,
                    account: input.value
                });
            }
        });
        
        // Show progress
        const saveBtn = document.getElementById('save-corrections-btn');
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<span class="spinner"></span> Saving corrections...';
        saveBtn.disabled = true;
        
        // Send corrections to server
        const response = await fetch(`/api/review/${processId}/corrections`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ corrections })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Failed to save corrections');
        }
        
        // Show success and update UI
        document.getElementById('corrections-message').textContent = 
            `${result.corrections_applied} corrections applied successfully. Final files have been generated.`;
        document.getElementById('correction-summary').style.display = 'block';
        
        // Update results section with new files
        if (result.output_files) {
            updateResultsWithCorrectedFiles(result.output_files);
        }
        
        setTimeout(() => {
            showResults({ 
                ...reviewData, 
                output_files: result.output_files,
                has_review_data: false  // Hide review prompt after corrections
            });
        }, 2000);
        
    } catch (error) {
        showError(`Save failed: ${error.message}`);
    } finally {
        const saveBtn = document.getElementById('save-corrections-btn');
        if (saveBtn) {
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
        }
    }
}

function updateResultsWithCorrectedFiles(outputFiles) {
    const downloadButtons = document.getElementById('download-buttons');
    downloadButtons.innerHTML = '';
    
    outputFiles.forEach(file => {
        const downloadBtn = document.createElement('a');
        downloadBtn.className = 'download-btn';
        downloadBtn.href = `/api/download/${processId}/${file.name}`;
        downloadBtn.download = file.name;
        
        let fileTypeLabel = 'Corrected CSV Export';
        let fileIcon = 'CSV';
        if (file.type === 'main') {
            fileTypeLabel = 'Corrected main transaction data';
            fileIcon = 'ALL';
        } else if (file.name.includes('ECREDIT')) {
            fileTypeLabel = 'Corrected e-Credit Card transactions';
            fileIcon = 'eCR';
        } else if (file.name.includes('GOLD')) {
            fileTypeLabel = 'Corrected Gold Rewards Card transactions';
            fileIcon = 'GLD';
        } else if (file.name.includes('Both')) {
            fileTypeLabel = 'Corrected combined file for accounting';
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
}

async function skipReview() {
    // Use current classifications without corrections and generate files
    await saveCorrections(); // This will save with no corrections
}

function cancelReview() {
    // Return to results section
    reviewSection.style.display = 'none';
    resultsSection.style.display = 'block';
}

// Utility Functions for Review Interface
function getConfidenceClass(confidence) {
    if (confidence >= 70) return 'confidence-high';
    if (confidence >= 50) return 'confidence-medium';
    return 'confidence-low';
}

function formatAmount(amount) {
    const num = parseFloat(amount) || 0;
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
    reviewSection.style.display = 'none';
    
    // Reset review data
    reviewData = null;
    validAccounts = [];
    filteredTransactions = [];
    
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