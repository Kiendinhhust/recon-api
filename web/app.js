// ========================================
//   Recon API Dashboard - JavaScript
// ========================================

const API_BASE_URL = 'http://localhost:8000/api/v1';

let currentFilter = 'all';
let currentScanData = null;
let progressInterval = null;

// ========================================
//   Initialize
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    loadScans();
    
    // Auto-refresh every 10 seconds
    setInterval(() => {
        if (!document.getElementById('scan-details-section').style.display || 
            document.getElementById('scan-details-section').style.display === 'none') {
            loadScans();
        }
    }, 10000);
});

// ========================================
//   Load Scans List
// ========================================

async function loadScans() {
    const scansListEl = document.getElementById('scans-list');
    
    try {
        const response = await fetch(`${API_BASE_URL}/scans`);
        const scans = await response.json();
        
        if (scans.length === 0) {
            scansListEl.innerHTML = '<div class="loading">No scans found. Create a scan to get started!</div>';
            return;
        }
        
        scansListEl.innerHTML = scans.map(scan => `
            <div class="scan-card">
                <div onclick="loadScanDetails('${scan.job_id}')" style="cursor: pointer;">
                    <div class="scan-card-header">
                        <div class="scan-domain">${scan.domain}</div>
                        <div class="scan-status status-${scan.status}">
                            ${scan.status}
                        </div>
                    </div>
                    ${scan.status === 'running' ? `
                        <div class="progress-bar" id="progress-${scan.job_id}">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                    ` : ''}
                    <div class="scan-stats">
                        <div class="stat-item">
                            <span class="stat-icon">🌐</span>
                            <span><span class="stat-value">${scan.subdomains_count}</span> subdomains</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-icon">📸</span>
                            <span><span class="stat-value">${scan.screenshots_count}</span> screenshots</span>
                        </div>
                    </div>
                    <div class="stat-item" style="margin-top: 0.5rem; font-size: 0.85rem;">
                        <span class="stat-icon">🕒</span>
                        <span>${formatDate(scan.created_at)}</span>
                    </div>
                </div>
                <div class="scan-card-actions">
                    <button class="btn btn-small btn-primary" onclick="event.stopPropagation(); loadScanDetails('${scan.job_id}')">
                        <span class="btn-icon">👁</span> View
                    </button>
                    <button class="btn btn-small btn-success" onclick="event.stopPropagation(); exportResults('${scan.job_id}', '${scan.domain}')">
                        <span class="btn-icon">💾</span> Export
                    </button>
                    ${scan.status === 'running' ? `
                        <button class="btn btn-small btn-secondary" onclick="event.stopPropagation(); startProgressMonitoring('${scan.job_id}')">
                            <span class="btn-icon">📊</span> Monitor
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');

        // Start monitoring for running scans
        scans.filter(s => s.status === 'running').forEach(scan => {
            startProgressMonitoring(scan.job_id);
        });
        
    } catch (error) {
        console.error('Error loading scans:', error);
        scansListEl.innerHTML = '<div class="loading">Error loading scans. Make sure API is running!</div>';
    }
}

// ========================================
//   Load Scan Details
// ========================================

async function loadScanDetails(jobId) {
    const detailsSection = document.getElementById('scan-details-section');
    detailsSection.style.display = 'block';
    
    // Scroll to details
    detailsSection.scrollIntoView({ behavior: 'smooth' });
    
    try {
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}`);
        const scan = await response.json();
        
        currentScanData = scan;
        
        // Update scan info
        document.getElementById('detail-domain').textContent = scan.domain;
        document.getElementById('detail-status').innerHTML = `<span class="scan-status status-${scan.status}">${scan.status}</span>`;
        document.getElementById('detail-subdomains-count').textContent = scan.subdomains.length;
        document.getElementById('detail-screenshots-count').textContent = scan.screenshots.length;
        document.getElementById('detail-created').textContent = formatDate(scan.created_at);
        document.getElementById('detail-completed').textContent = scan.completed_at ? formatDate(scan.completed_at) : 'In progress...';
        
        // Load subdomains
        displaySubdomains(scan.subdomains);
        
        // Load screenshots
        displayScreenshots(scan.screenshots, jobId);
        
    } catch (error) {
        console.error('Error loading scan details:', error);
        alert('Error loading scan details!');
    }
}

// ========================================
//   Display Subdomains
// ========================================

function displaySubdomains(subdomains) {
    const tbody = document.getElementById('subdomains-tbody');
    
    if (subdomains.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No subdomains found</td></tr>';
        return;
    }
    
    tbody.innerHTML = subdomains.map(sub => `
        <tr class="subdomain-row" data-status="${sub.is_live ? 'live' : 'dead'}">
            <td>${sub.subdomain}</td>
            <td>
                <span class="status-badge status-${sub.is_live ? 'live' : 'dead'}">
                    ${sub.is_live ? '✓ Live' : '✗ Dead'}
                </span>
            </td>
            <td>${sub.http_status || '-'}</td>
            <td>${sub.response_time ? sub.response_time + 'ms' : '-'}</td>
            <td>${sub.discovered_by || '-'}</td>
        </tr>
    `).join('');
}

// ========================================
//   Display Screenshots
// ========================================

function displayScreenshots(screenshots, jobId) {
    const gallery = document.getElementById('screenshots-gallery');
    
    if (screenshots.length === 0) {
        gallery.innerHTML = '<div class="loading">No screenshots available</div>';
        return;
    }
    
    gallery.innerHTML = screenshots.map(shot => `
        <div class="screenshot-card" onclick="openScreenshot('${shot.file_path}')">
            <img src="${API_BASE_URL.replace('/api/v1', '')}/${shot.file_path}" 
                 alt="${shot.url}" 
                 class="screenshot-img"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22200%22%3E%3Crect fill=%22%231a1a2e%22 width=%22300%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%23a1a1aa%22%3EImage not found%3C/text%3E%3C/svg%3E'">
            <div class="screenshot-info">
                <div class="screenshot-url">${shot.url}</div>
            </div>
        </div>
    `).join('');
}

// ========================================
//   Filter Subdomains
// ========================================

function filterSubdomains() {
    const searchTerm = document.getElementById('subdomain-search').value.toLowerCase();
    const rows = document.querySelectorAll('.subdomain-row');
    
    rows.forEach(row => {
        const subdomain = row.cells[0].textContent.toLowerCase();
        const status = row.dataset.status;
        
        const matchesSearch = subdomain.includes(searchTerm);
        const matchesFilter = currentFilter === 'all' || status === currentFilter;
        
        row.style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    });
}

function setFilter(filter) {
    currentFilter = filter;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });
    
    filterSubdomains();
}

// ========================================
//   Close Scan Details
// ========================================

function closeScanDetails() {
    document.getElementById('scan-details-section').style.display = 'none';
    currentScanData = null;
    
    // Scroll back to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ========================================
//   Open Screenshot
// ========================================

function openScreenshot(filePath) {
    const url = `${API_BASE_URL.replace('/api/v1', '')}/${filePath}`;
    window.open(url, '_blank');
}

// ========================================
//   Utility Functions
// ========================================

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// ========================================
//   New Scan Modal
// ========================================

function showNewScanModal() {
    const modal = document.getElementById('newScanModal');
    modal.classList.add('show');
    document.getElementById('newScanDomain').value = '';
    document.getElementById('newScanError').classList.remove('show');
}

function closeNewScanModal() {
    const modal = document.getElementById('newScanModal');
    modal.classList.remove('show');
}

async function submitNewScan() {
    const domain = document.getElementById('newScanDomain').value.trim();
    const errorEl = document.getElementById('newScanError');

    if (!domain) {
        errorEl.textContent = 'Please enter a domain';
        errorEl.classList.add('show');
        return;
    }

    if (!domain.includes('.')) {
        errorEl.textContent = 'Please enter a valid domain (e.g., example.com)';
        errorEl.classList.add('show');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scans`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domain: domain })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        closeNewScanModal();
        loadScans();

        // Show success message
        alert(`✅ Scan started for ${domain}\nJob ID: ${data.job_id}`);

    } catch (error) {
        console.error('Error creating scan:', error);
        errorEl.textContent = `Error: ${error.message}`;
        errorEl.classList.add('show');
    }
}

// ========================================
//   Bulk Scan Modal
// ========================================

function showBulkScanModal() {
    const modal = document.getElementById('bulkScanModal');
    modal.classList.add('show');
    document.getElementById('bulkScanDomains').value = '';
    document.getElementById('bulkScanError').classList.remove('show');
}

function closeBulkScanModal() {
    const modal = document.getElementById('bulkScanModal');
    modal.classList.remove('show');
}

async function submitBulkScan() {
    const domainsText = document.getElementById('bulkScanDomains').value.trim();
    const errorEl = document.getElementById('bulkScanError');

    if (!domainsText) {
        errorEl.textContent = 'Please enter at least one domain';
        errorEl.classList.add('show');
        return;
    }

    const domains = domainsText.split('\n')
        .map(d => d.trim())
        .filter(d => d && d.includes('.'));

    if (domains.length === 0) {
        errorEl.textContent = 'No valid domains found';
        errorEl.classList.add('show');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scans/bulk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ domains: domains })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        closeBulkScanModal();
        loadScans();

        // Show success message
        alert(`✅ Bulk scan started!\n${data.total_submitted} domains submitted for scanning.`);

    } catch (error) {
        console.error('Error creating bulk scan:', error);
        errorEl.textContent = `Error: ${error.message}`;
        errorEl.classList.add('show');
    }
}

// ========================================
//   Delete Scan
// ========================================

async function deleteScan(jobId, domain) {
    if (!confirm(`Are you sure you want to delete scan for ${domain}?`)) {
        return;
    }

    try {
        // Note: DELETE endpoint may not exist yet
        // For now, just show a message
        alert('Delete functionality will be implemented soon!');

        // Uncomment when DELETE endpoint is ready:
        /*
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        loadScans();
        alert(`✅ Scan deleted for ${domain}`);
        */

    } catch (error) {
        console.error('Error deleting scan:', error);
        alert(`Error deleting scan: ${error.message}`);
    }
}

// ========================================
//   Export Results
// ========================================

async function exportResults(jobId, domain) {
    try {
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}`);
        const data = await response.json();

        // Create JSON file
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        // Download
        const a = document.createElement('a');
        a.href = url;
        a.download = `recon_${domain}_${jobId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error exporting results:', error);
        alert(`Error exporting results: ${error.message}`);
    }
}

// ========================================
//   Real-time Progress
// ========================================

async function startProgressMonitoring(jobId) {
    // Clear any existing interval
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    // Update progress every 2 seconds
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/scans/${jobId}/progress`);
            const data = await response.json();

            // Update progress bar if exists
            const progressBar = document.getElementById(`progress-${jobId}`);
            if (progressBar && data.progress) {
                const percentage = data.progress.current || 0;
                progressBar.querySelector('.progress-fill').style.width = `${percentage}%`;
            }

            // Stop monitoring if completed
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(progressInterval);
                loadScans(); // Refresh scan list
            }

        } catch (error) {
            console.error('Error fetching progress:', error);
        }
    }, 2000);
}

function stopProgressMonitoring() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const newScanModal = document.getElementById('newScanModal');
    const bulkScanModal = document.getElementById('bulkScanModal');

    if (event.target === newScanModal) {
        closeNewScanModal();
    }
    if (event.target === bulkScanModal) {
        closeBulkScanModal();
    }
}

