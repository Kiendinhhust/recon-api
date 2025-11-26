// ========================================
//   Recon API Dashboard - JavaScript
// ========================================

// API Configuration
// For development: use 'http://localhost:8000/api/v1'
// For production: use 'http://YOUR_VPS_IP:8000/api/v1' or configure via environment
const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000/api/v1'
    : `${window.location.protocol}//${window.location.hostname}:8000/api/v1`;

let currentFilter = 'all';
let currentScanData = null;
let progressInterval = null;
let currentScansPage = 0;
let scansPerPage = 100;

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
        const offset = currentScansPage * scansPerPage;
        const response = await fetch(`${API_BASE_URL}/scans?limit=${scansPerPage}&offset=${offset}`);
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
                    ${scan.status === 'running' || scan.status === 'pending' ? `
                        <button class="btn btn-small btn-warning" onclick="event.stopPropagation(); stopScan('${scan.job_id}')">
                            <span class="btn-icon">⏸</span> Stop
                        </button>
                    ` : ''}
                    ${scan.status === 'completed' || scan.status === 'failed' || scan.status === 'cancelled' ? `
                        <button class="btn btn-small btn-danger" onclick="event.stopPropagation(); deleteScan('${scan.job_id}', '${scan.domain}')">
                            <span class="btn-icon">🗑</span> Delete
                        </button>
                    ` : ''}
                    ${scan.status === 'running' || scan.status === 'pending' ? `
                        <button class="btn btn-small btn-danger" onclick="event.stopPropagation(); forceDeleteScan('${scan.job_id}', '${scan.domain}')">
                            <span class="btn-icon">⚠</span> Force Delete
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

        // Load WAF detections
        displayWafDetections(scan.waf_detections || []);

        // Load leak detections
        displayLeakDetections(scan.leak_detections || []);

        // Load screenshots
        displayScreenshots(scan.screenshots, jobId);

        // Load selective scan URLs
        loadSelectiveScanUrls(scan);

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
        tbody.innerHTML = '<tr><td colspan="9" class="loading">No subdomains found</td></tr>';
        return;
    }

    // Debug: Log first subdomain to console
    if (subdomains.length > 0) {
        console.log('First subdomain data:', subdomains[0]);
        console.log('Webserver:', subdomains[0].webserver);
        console.log('Technologies:', subdomains[0].technologies);
    }

    tbody.innerHTML = subdomains.map(sub => {
        // Format technologies
        const techDisplay = sub.technologies && sub.technologies.length > 0
            ? sub.technologies.slice(0, 2).map(t => t.name).join(', ') + (sub.technologies.length > 2 ? '...' : '')
            : '-';

        // Format response time
        const responseTime = sub.response_time || '-';

        return `
            <tr class="subdomain-row" data-status="${sub.is_live ? 'live' : 'dead'}">
                <td>${sub.url ? `<a href="${sub.url}" target="_blank" rel="noopener">${sub.subdomain}</a>` : sub.subdomain}</td>
                <td>
                    <span class="status-badge status-${sub.is_live ? 'live' : 'dead'}">
                        ${sub.is_live ? '✓ Live' : '✗ Dead'}
                    </span>
                </td>
                <td>${sub.http_status || '-'}</td>
                <td title="${sub.title || ''}">${sub.title ? (sub.title.length > 30 ? sub.title.substring(0, 30) + '...' : sub.title) : '-'}</td>
                <td>${sub.webserver || '-'}</td>
                <td>${sub.cdn_name || '-'}</td>
                <td title="${techDisplay}">${techDisplay}</td>
                <td>${responseTime}</td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="showSubdomainDetails(${sub.id})">
                        <span class="btn-icon">👁</span> Details
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// ========================================
//   Show Subdomain Details Modal
// ========================================

function showSubdomainDetails(subdomainId) {
    const subdomain = currentScanData.subdomains.find(s => s.id === subdomainId);
    if (!subdomain) {
        alert('Subdomain not found!');
        return;
    }

    // Populate modal fields
    document.getElementById('modal-subdomain').textContent = subdomain.subdomain || '-';

    // URL
    const urlEl = document.getElementById('modal-url');
    if (subdomain.url) {
        urlEl.href = subdomain.url;
        urlEl.textContent = subdomain.url;
    } else {
        urlEl.href = '#';
        urlEl.textContent = '-';
    }

    // Status
    const statusHtml = `<span class="status-badge status-${subdomain.is_live ? 'live' : 'dead'}">
        ${subdomain.is_live ? '✓ Live' : '✗ Dead'}
    </span>`;
    document.getElementById('modal-status').innerHTML = statusHtml;

    // HTTP Status
    document.getElementById('modal-http-status').textContent = subdomain.http_status || '-';

    // Title
    document.getElementById('modal-title').textContent = subdomain.title || '-';

    // Webserver
    document.getElementById('modal-webserver').textContent = subdomain.webserver || '-';

    // CDN
    document.getElementById('modal-cdn').textContent = subdomain.cdn_name || '-';

    // Content Type
    document.getElementById('modal-content-type').textContent = subdomain.content_type || '-';

    // Content Length
    const contentLength = subdomain.content_length
        ? `${(subdomain.content_length / 1024).toFixed(2)} KB (${subdomain.content_length} bytes)`
        : '-';
    document.getElementById('modal-content-length').textContent = contentLength;

    // Response Time
    document.getElementById('modal-response-time').textContent = subdomain.response_time || '-';

    // Primary IP (host)
    document.getElementById('modal-host').textContent = subdomain.host || '-';

    // Final URL
    const finalUrlEl = document.getElementById('modal-final-url');
    if (subdomain.final_url) {
        finalUrlEl.href = subdomain.final_url;
        finalUrlEl.textContent = subdomain.final_url;
    } else {
        finalUrlEl.href = '#';
        finalUrlEl.textContent = '-';
    }

    // IPv4 Addresses
    const ipv4Html = subdomain.ipv4_addresses && subdomain.ipv4_addresses.length > 0
        ? subdomain.ipv4_addresses.map(ip => `<span class="ip-badge">${ip}</span>`).join(' ')
        : '-';
    document.getElementById('modal-ipv4').innerHTML = ipv4Html;

    // IPv6 Addresses
    const ipv6Html = subdomain.ipv6_addresses && subdomain.ipv6_addresses.length > 0
        ? subdomain.ipv6_addresses.map(ip => `<span class="ip-badge">${ip}</span>`).join(' ')
        : '-';
    document.getElementById('modal-ipv6').innerHTML = ipv6Html;

    // Redirect Chain (chain_status_codes)
    const chainHtml = subdomain.chain_status_codes && subdomain.chain_status_codes.length > 0
        ? subdomain.chain_status_codes.map((code, idx) =>
            `<span class="chain-badge">${code}</span>${idx < subdomain.chain_status_codes.length - 1 ? '<span class="chain-arrow">→</span>' : ''}`
          ).join('')
        : '-';
    document.getElementById('modal-chain').innerHTML = chainHtml;

    // Technologies
    const techHtml = subdomain.technologies && subdomain.technologies.length > 0
        ? subdomain.technologies.map(t => `<span class="tech-badge">${t.name}</span>`).join(' ')
        : '-';
    document.getElementById('modal-technologies').innerHTML = techHtml;

    // Discovered By
    document.getElementById('modal-discovered-by').textContent = subdomain.discovered_by || '-';

    // Show modal
    document.getElementById('subdomainDetailsModal').classList.add('show');
}

function closeSubdomainDetailsModal() {
    document.getElementById('subdomainDetailsModal').classList.remove('show');
}

// ========================================
//   Display WAF Detections
// ========================================

function displayWafDetections(detections) {
    const tbody = document.getElementById('waf-tbody');

    if (!detections || detections.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="loading">No WAF detections</td></tr>';
        return;
    }

    tbody.innerHTML = detections.map(waf => `
        <tr>
            <td><a href="${waf.url}" target="_blank" rel="noopener">${waf.url}</a></td>
            <td>
                <span class="status-badge status-${waf.has_waf ? 'live' : 'dead'}">
                    ${waf.has_waf ? '✓ Yes' : '✗ No'}
                </span>
            </td>
            <td>${waf.waf_name || '-'}</td>
            <td>${waf.waf_manufacturer || '-'}</td>
        </tr>
    `).join('');
}

// ========================================
//   Display Leak Detections
// ========================================

function displayLeakDetections(leaks) {
    const tbody = document.getElementById('leaks-tbody');

    if (!leaks || leaks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No leaks found</td></tr>';
        return;
    }

    tbody.innerHTML = leaks.map(leak => {
        // Format HTTP status with color coding
        let statusBadge = '-';
        if (leak.http_status) {
            let statusClass = 'status-other';
            if (leak.http_status === 200) {
                statusClass = 'status-200';
            } else if (leak.http_status === 403) {
                statusClass = 'status-403';
            }
            statusBadge = `<span class="status-badge ${statusClass}">${leak.http_status}</span>`;
        }

        return `
            <tr>
                <td><a href="${leak.base_url}" target="_blank" rel="noopener">${leak.base_url}</a></td>
                <td><a href="${leak.leaked_file_url}" target="_blank" rel="noopener">${leak.leaked_file_url.slice(0, 50)}...</a></td>
                <td>${statusBadge}</td>
                <td>${leak.file_type || '-'}</td>
                <td><span class="severity-badge severity-${leak.severity || 'medium'}">${leak.severity || 'medium'}</span></td>
                <td>${leak.file_size ? (leak.file_size / 1024).toFixed(2) + ' KB' : '-'}</td>
            </tr>
        `;
    }).join('');
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
//   Job Management Functions
// ========================================

/**
 * Stop a running scan
 */
async function stopScan(jobId) {
    if (!confirm('Are you sure you want to stop this scan?\n\nPartial results will be preserved.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        alert(`✅ ${result.message}`);

        // Reload scans list
        loadScans();

        // If scan details are open, reload them
        if (document.getElementById('scan-details-section').style.display !== 'none') {
            loadScanDetails(jobId);
        }

    } catch (error) {
        console.error('Error stopping scan:', error);
        alert(`❌ Error stopping scan: ${error.message}`);
    }
}

/**
 * Delete a completed/failed scan
 */
async function deleteScan(jobId, domain) {
    if (!confirm(`Are you sure you want to delete scan for ${domain}?\n\nThis will permanently delete:\n- All subdomains\n- All screenshots\n- All WAF detections\n- All leak detections\n\nThis action cannot be undone!`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        alert(`✅ ${result.message}\n\nDeleted:\n- ${result.deleted_items.subdomains} subdomains\n- ${result.deleted_items.screenshots} screenshots\n- ${result.deleted_items.waf_detections} WAF detections\n- ${result.deleted_items.leak_detections} leak detections`);

        // Reload scans list
        loadScans();

        // If scan details are open, close them
        if (document.getElementById('scan-details-section').style.display !== 'none') {
            document.getElementById('scan-details-section').style.display = 'none';
        }

    } catch (error) {
        console.error('Error deleting scan:', error);
        alert(`❌ Error deleting scan: ${error.message}`);
    }
}

/**
 * Force delete a scan (stop + delete in one operation)
 */
async function forceDeleteScan(jobId, domain) {
    if (!confirm(`⚠️ WARNING: FORCE DELETE\n\nAre you sure you want to FORCE DELETE scan for ${domain}?\n\nThis will:\n1. Forcefully terminate the running scan\n2. Permanently delete all data\n\nThis action cannot be undone!`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scans/${jobId}/force`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        alert(`✅ ${result.message}\n\nDeleted:\n- ${result.deleted_items.subdomains} subdomains\n- ${result.deleted_items.screenshots} screenshots\n- ${result.deleted_items.waf_detections} WAF detections\n- ${result.deleted_items.leak_detections} leak detections\n- Task revoked: ${result.deleted_items.task_revoked}`);

        // Reload scans list
        loadScans();

        // If scan details are open, close them
        if (document.getElementById('scan-details-section').style.display !== 'none') {
            document.getElementById('scan-details-section').style.display = 'none';
        }

    } catch (error) {
        console.error('Error force deleting scan:', error);
        alert(`❌ Error force deleting scan: ${error.message}`);
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

// ========================================
//   Selective Leak Scanning
// ========================================

let selectedUrls = new Set();
let selectiveScanInterval = null;
let currentJobId = null;

// Toggle selective scan form visibility
function toggleSelectiveScanForm() {
    const form = document.getElementById('selective-scan-form');
    const toggleIcon = document.getElementById('selective-scan-toggle-icon');
    const toggleText = document.getElementById('selective-scan-toggle-text');

    if (form.style.display === 'none') {
        form.style.display = 'block';
        toggleIcon.textContent = '▲';
        toggleText.textContent = 'Hide';
    } else {
        form.style.display = 'none';
        toggleIcon.textContent = '▼';
        toggleText.textContent = 'Show';
    }
}

// Load available URLs for selective scanning
function loadSelectiveScanUrls(scanData) {
    const section = document.getElementById('selective-scan-section');
    const urlList = document.getElementById('url-selection-list');

    // Only show for completed scans
    if (scanData.status !== 'completed') {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    currentJobId = scanData.job_id;

    // Get live hosts
    const liveHosts = scanData.subdomains.filter(sub => sub.is_live);

    if (liveHosts.length === 0) {
        urlList.innerHTML = '<div class="loading">No live hosts available for scanning</div>';
        return;
    }

    // Build WAF-protected URLs set
    const wafUrls = new Set();
    if (scanData.waf_detections) {
        scanData.waf_detections.forEach(waf => {
            if (waf.has_waf) {
                wafUrls.add(waf.url);
            }
        });
    }

    // Filter out WAF-protected URLs
    const availableUrls = liveHosts.filter(host => {
        const url = `https://${host.subdomain}`;
        const urlHttp = `http://${host.subdomain}`;
        return !wafUrls.has(url) && !wafUrls.has(urlHttp);
    });

    if (availableUrls.length === 0) {
        urlList.innerHTML = '<div class="loading">No URLs available (all are WAF-protected)</div>';
        return;
    }

    // Render URL checkboxes
    urlList.innerHTML = availableUrls.map((host, index) => {
        const url = `https://${host.subdomain}`;
        return `
            <div class="url-checkbox-item">
                <label>
                    <input type="checkbox"
                           class="url-checkbox"
                           value="${url}"
                           onchange="updateSelectedUrls()">
                    <span class="url-text">${url}</span>
                    <span class="url-meta">(${host.http_status || 'unknown status'})</span>
                </label>
            </div>
        `;
    }).join('');

    updateSelectedUrls();
}

// Update selected URLs count
function updateSelectedUrls() {
    const checkboxes = document.querySelectorAll('.url-checkbox:checked');
    selectedUrls = new Set(Array.from(checkboxes).map(cb => cb.value));

    const countEl = document.getElementById('selected-urls-count');
    countEl.textContent = `${selectedUrls.size} URL${selectedUrls.size !== 1 ? 's' : ''} selected`;
}

// Select all URLs
function selectAllUrls() {
    const checkboxes = document.querySelectorAll('.url-checkbox');
    checkboxes.forEach(cb => cb.checked = true);
    updateSelectedUrls();
}

// Deselect all URLs
function deselectAllUrls() {
    const checkboxes = document.querySelectorAll('.url-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    updateSelectedUrls();
}

// Submit selective scan
async function submitSelectiveScan() {
    const errorEl = document.getElementById('selective-scan-error');
    const submitBtn = document.getElementById('selective-scan-submit-btn');
    const mode = document.getElementById('scan-mode-select').value;

    // Clear previous error
    errorEl.textContent = '';

    // Validate selection
    if (selectedUrls.size === 0) {
        errorEl.textContent = 'Please select at least one URL to scan';
        return;
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Starting...';

    try {
        const response = await fetch(`${API_BASE_URL}/scans/${currentJobId}/leak-scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                urls: Array.from(selectedUrls),
                mode: mode
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start scan');
        }

        const result = await response.json();

        // Hide form, show progress
        document.getElementById('selective-scan-form').style.display = 'none';
        document.getElementById('selective-scan-progress').style.display = 'block';
        document.getElementById('selective-scan-results').style.display = 'none';

        // Update progress info
        document.getElementById('selective-scan-task-id').textContent = result.task_id;
        document.getElementById('selective-scan-urls-count').textContent = result.urls_to_scan;
        document.getElementById('selective-scan-mode').textContent = result.mode;
        document.getElementById('selective-scan-status').textContent = result.message;

        // Start monitoring progress
        startSelectiveScanMonitoring(result.task_id);

    } catch (error) {
        console.error('Error starting selective scan:', error);
        errorEl.textContent = error.message;

        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🚀</span> Start Selective Leak Scan';
    }
}

// Monitor selective scan progress
function startSelectiveScanMonitoring(taskId) {
    let checkCount = 0;
    const maxChecks = 2800; // 2 minutes max (2 second intervals)

    selectiveScanInterval = setInterval(async () => {
        checkCount++;

        try {
            // Check scan results
            const response = await fetch(`${API_BASE_URL}/scans/${currentJobId}`);
            const scanData = await response.json();

            // Update progress bar (estimate based on time)
            const progress = Math.min(95, (checkCount / maxChecks) * 100);
            document.getElementById('selective-scan-progress-bar').style.width = `${progress}%`;
            document.getElementById('selective-scan-percentage').textContent = `${Math.round(progress)}%`;

            // Check if new leaks appeared (simple heuristic)
            const currentLeakCount = scanData.leak_detections ? scanData.leak_detections.length : 0;

            // If we've been checking for a while and have results, consider it done
            if (checkCount > 10 && currentLeakCount > 0) {
                stopSelectiveScanMonitoring();
                showSelectiveScanResults(scanData);
            }

            // Timeout after max checks
            if (checkCount >= maxChecks) {
                stopSelectiveScanMonitoring();
                showSelectiveScanResults(scanData);
            }

        } catch (error) {
            console.error('Error checking selective scan progress:', error);
        }
    }, 2000);
}

// Stop monitoring
function stopSelectiveScanMonitoring() {
    if (selectiveScanInterval) {
        clearInterval(selectiveScanInterval);
        selectiveScanInterval = null;
    }
}

// Show scan results
function showSelectiveScanResults(scanData) {
    // Hide progress, show results
    document.getElementById('selective-scan-progress').style.display = 'none';
    document.getElementById('selective-scan-results').style.display = 'block';

    // Update progress bar to 100%
    document.getElementById('selective-scan-progress-bar').style.width = '100%';
    document.getElementById('selective-scan-percentage').textContent = '100%';

    // Update results
    const leakCount = scanData.leak_detections ? scanData.leak_detections.length : 0;
    document.getElementById('result-urls-scanned').textContent = selectedUrls.size;
    document.getElementById('result-leaks-found').textContent = leakCount;

    // Re-enable submit button
    const submitBtn = document.getElementById('selective-scan-submit-btn');
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span class="btn-icon">🚀</span> Start Selective Leak Scan';
}

// Reload scan details
function reloadScanDetails() {
    if (currentJobId) {
        loadScanDetails(currentJobId);

        // Reset selective scan UI
        document.getElementById('selective-scan-form').style.display = 'none';
        document.getElementById('selective-scan-progress').style.display = 'none';
        document.getElementById('selective-scan-results').style.display = 'none';

        // Reset toggle
        document.getElementById('selective-scan-toggle-icon').textContent = '▼';
        document.getElementById('selective-scan-toggle-text').textContent = 'Show';
    }
}

// ========================================
//   Manual Subdomain Addition
// ========================================

// Toggle manual subdomain form visibility
function toggleManualSubdomainForm() {
    const form = document.getElementById('manual-subdomain-form');
    const toggleIcon = document.getElementById('manual-subdomain-toggle-icon');
    const toggleText = document.getElementById('manual-subdomain-toggle-text');

    if (form.style.display === 'none') {
        form.style.display = 'block';
        toggleIcon.textContent = '▲';
        toggleText.textContent = 'Hide';
    } else {
        form.style.display = 'none';
        toggleIcon.textContent = '▼';
        toggleText.textContent = 'Show';
    }
}

// Add subdomain manually
async function addSubdomainManually() {
    const errorEl = document.getElementById('manual-subdomain-error');
    const successEl = document.getElementById('manual-subdomain-success');
    const submitBtn = document.getElementById('add-subdomain-btn');

    // Clear previous messages
    errorEl.textContent = '';
    successEl.textContent = '';

    // Get form values
    const subdomain = document.getElementById('manual-subdomain-input').value.trim();
    const isLiveValue = document.getElementById('manual-is-live').value;
    const httpStatus = document.getElementById('manual-http-status').value;

    // Validate subdomain
    if (!subdomain) {
        errorEl.textContent = 'Please enter a subdomain';
        return;
    }

    // Prepare request body
    const requestBody = {
        subdomain: subdomain
    };

    // Add optional fields if provided
    if (isLiveValue !== '') {
        requestBody.is_live = isLiveValue === 'true';
    }

    if (httpStatus) {
        requestBody.http_status = parseInt(httpStatus);
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Adding...';

    try {
        const response = await fetch(`${API_BASE_URL}/scans/${currentJobId}/subdomains`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add subdomain');
        }

        const result = await response.json();

        // Show success message
        successEl.textContent = result.message;

        // Clear form
        document.getElementById('manual-subdomain-input').value = '';
        document.getElementById('manual-is-live').value = '';
        document.getElementById('manual-http-status').value = '';

        // Reload scan details to show new subdomain
        setTimeout(() => {
            loadScanDetails(currentJobId);
            successEl.textContent = '';
        }, 2000);

    } catch (error) {
        console.error('Error adding subdomain:', error);
        errorEl.textContent = error.message;
    } finally {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">➕</span> Add Subdomain';
    }
}
