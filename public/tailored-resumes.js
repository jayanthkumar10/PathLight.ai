// ==========================================
// PATHLIGHT — APPLICATIONS PAGE
// Fetches from backend API, renders live data
// ==========================================

const API_BASE = '';

document.addEventListener('DOMContentLoaded', async () => {
    let applications = [];
    let currentFilter = 'All';
    let currentSort = 'date-desc';


    const tableBody   = document.getElementById('tr-table-body');
    const emptyState  = document.getElementById('tr-empty-state');
    const statTotal   = document.getElementById('stat-total');
    const statReady   = document.getElementById('stat-ready');
    const statApplied = document.getElementById('stat-applied');
    const statInterviewing = document.getElementById('stat-interviewing');
    const statOffers  = document.getElementById('stat-offers');
    const statRejected = document.getElementById('stat-rejected');

    // ------------------------------------------------
    // Status config
    // ------------------------------------------------
    const statusConfig = {
        'Processing':     { colorClass: 'status-color-orange', dot: 'bg-orange' },
        'Ready to Apply': { colorClass: 'status-color-purple', dot: 'bg-purple' },
        'Applied':        { colorClass: 'status-color-blue',   dot: 'bg-blue' },
        'HR Screening':   { colorClass: 'status-color-blue',   dot: 'bg-blue' },
        'OA Scheduled':   { colorClass: 'status-color-orange', dot: 'bg-orange' },
        'Interview':      { colorClass: 'status-color-orange', dot: 'bg-orange' },
        'Final Round':    { colorClass: 'status-color-orange', dot: 'bg-orange' },
        'Offer':          { colorClass: 'status-color-green',  dot: 'bg-green' },
        'Unmatched':       { colorClass: 'status-color-red',    dot: 'bg-red' },
        'Ghosted':        { colorClass: 'status-color-gray',   dot: 'bg-gray' },
        'Withdrawn':      { colorClass: 'status-color-gray',   dot: 'bg-gray' },
        'Archived':       { colorClass: 'status-color-gray',   dot: 'bg-gray' },
    };

    const statusOptionsHTML = Object.keys(statusConfig).map(status => {
        const conf = statusConfig[status];
        return `<button class="status-option" data-value="${status}">
                    <div class="status-dot ${conf.dot}"></div>${status}
                </button>`;
    }).join('');

    // ------------------------------------------------
    // Format helpers
    // ------------------------------------------------
    function formatDate(dateStr) {
        if (!dateStr) return 'Just now';
        try {
            return new Date(dateStr).toLocaleString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric',
                hour: 'numeric', minute: '2-digit', hour12: true
            });
        } catch { return 'Just now'; }
    }

    function mapStatus(backendStatus) {
        if (!backendStatus) return 'Ready to Apply';
        const lower = backendStatus.toLowerCase();
        if (lower === 'completed' || lower === 'ready' || lower === 'draft') return 'Ready to Apply';
        if (lower === 'failed' || lower === 'rejected') return 'Unmatched';
        if (lower === 'processing') return 'Processing';
        if (lower === 'applied') return 'Applied';
        
        // Check if capitalized version exists in config
        const cap = backendStatus.charAt(0).toUpperCase() + backendStatus.slice(1);
        if (statusConfig[cap]) return cap;
        return 'Ready to Apply';
    }

    // ------------------------------------------------
    // Render
    // ------------------------------------------------
    function renderApplications() {
        const q = searchInput && searchInput.value ? searchInput.value.toLowerCase() : '';
        
        let filtered = applications.filter(a => {
            const matchesSearch = a.company.toLowerCase().includes(q) ||
                                  a.role.toLowerCase().includes(q) ||
                                  a.location.toLowerCase().includes(q) ||
                                  a.status.toLowerCase().includes(q);
            
            let matchesFilter = true;
            if (currentFilter !== 'All') {
                if (currentFilter === 'Interview') {
                    matchesFilter = ['HR Screening', 'OA Scheduled', 'Interview', 'Final Round'].includes(a.status);
                } else if (currentFilter === 'Offer' || currentFilter === 'Unmatched' || currentFilter === 'Applied' || currentFilter === 'Ready to Apply') {
                    matchesFilter = (a.status === currentFilter);
                }
            }
            return matchesSearch && matchesFilter;
        });

        if (currentSort === 'date-desc') {
            filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        } else if (currentSort === 'date-asc') {
            filtered.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
        } else if (currentSort === 'company-asc') {
            filtered.sort((a, b) => a.company.localeCompare(b.company));
        } else if (currentSort === 'status') {
            filtered.sort((a, b) => a.status.localeCompare(b.status));
        }

        updateStats(applications);

        if (filtered.length === 0) {
            tableBody.style.display = 'none';
            emptyState.style.display = 'flex';
            return;
        }

        tableBody.style.display = 'table-row-group';
        emptyState.style.display = 'none';
        tableBody.innerHTML = '';

        filtered.forEach((item, index) => {
            const tr = document.createElement('tr');
            const conf = statusConfig[item.status] || statusConfig['Ready to Apply'];
            const applyLink = item.apply_link && item.apply_link !== '#'
                ? item.apply_link
                : null;

            tr.innerHTML = `
                <td data-label="Sr No"><b>${index + 1}</b></td>
                <td data-label="Company">
                    <div class="td-company">${escHtml(item.company)}</div>
                </td>
                <td data-label="Role" class="td-role">${escHtml(item.role)}</td>
                <td data-label="Location">${escHtml(item.location)}</td>
                <td data-label="Resume">
                    <div class="td-resume">
                        ${['Unmatched', 'Failed'].includes(item.status) ? 
                            '<span style="color:#888; font-style:italic;">N/A (No PDF Generated)</span>' :
                            `<span>Tailored Resume</span>
                             <button class="tr-btn-icon" title="Preview" aria-label="Preview Resume"
                                onclick="window.open('${API_BASE}/api/applications/${item.id}/download', '_blank')"
                                style="width:24px;height:24px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                    <circle cx="12" cy="12" r="3"></circle>
                                </svg>
                             </button>
                             <button class="tr-btn-icon" title="Download PDF" aria-label="Download PDF Resume"
                                onclick="downloadPDF('${item.id}', '${escHtml(item.company)}', '${escHtml(item.role)}')"
                                style="width:24px;height:24px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                    <polyline points="7 10 12 15 17 10"></polyline>
                                    <line x1="12" y1="15" x2="12" y2="3"></line>
                                </svg>
                             </button>`
                        }
                    </div>
                </td>
                <td data-label="Apply Link">
                    ${applyLink
                        ? `<a href="${escHtml(applyLink)}" target="_blank" rel="noopener noreferrer" class="tr-btn-primary">Open Job</a>`
                        : `<span style="color:#555;font-size:12px;">No link</span>`}
                </td>
                <td data-label="Status" style="overflow:visible;">
                    <div class="status-dropdown-wrapper" data-id="${item.id}">
                        <div class="status-badge-trigger ${conf.colorClass}">
                            <div class="status-dot ${conf.dot}"></div>
                            <span class="status-text">${item.status}</span>
                            <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"></polyline>
                            </svg>
                        </div>
                        <div class="status-dropdown-menu">${statusOptionsHTML}</div>
                    </div>
                </td>
                <td data-label="Last Updated">${item.date}</td>
                <td data-label="Actions" class="tr-actions-col">
                    <div class="tr-actions">
                        <div class="tr-more-wrapper">
                            <button class="tr-btn-icon btn-more" aria-label="More options">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="1"></circle>
                                    <circle cx="12" cy="5" r="1"></circle>
                                    <circle cx="12" cy="19" r="1"></circle>
                                </svg>
                            </button>
                            <div class="tr-more-menu">
                                <button class="tr-more-item" onclick="window.open('${API_BASE}/api/applications/${item.id}/download','_blank')">View Resume</button>
                                ${applyLink ? `<button class="tr-more-item" onclick="window.open('${escHtml(applyLink)}','_blank')">Apply Now</button>` : ''}
                                <button class="tr-more-item" onclick="deleteApplication('${item.id}', this)" style="color: var(--danger, #ff4c4c)">Delete</button>
                            </div>
                        </div>
                    </div>
                </td>`;
            tableBody.appendChild(tr);
        });
    }

    function escHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function updateStats(data) {
        if (!statTotal) return;
        statTotal.innerText = data.length;
        statReady.innerText = data.filter(a => a.status === 'Ready to Apply').length;
        statApplied.innerText = data.filter(a => a.status === 'Applied').length;
        statInterviewing.innerText = data.filter(a =>
            ['HR Screening','OA Scheduled','Interview','Final Round'].includes(a.status)).length;
        statOffers.innerText = data.filter(a => a.status === 'Offer').length;
        statRejected.innerText = data.filter(a => a.status === 'Unmatched').length;
    }

    // ------------------------------------------------
    // Event delegation for interactive elements
    // ------------------------------------------------
    document.addEventListener('click', async (e) => {
        // Status dropdown trigger
        const trigger = e.target.closest('.status-badge-trigger');
        if (trigger) {
            e.stopPropagation();
            const wrapper = trigger.closest('.status-dropdown-wrapper');
            document.querySelectorAll('.status-dropdown-wrapper.open').forEach(el => {
                if (el !== wrapper) el.classList.remove('open');
            });
            wrapper.classList.toggle('open');
            return;
        }

        // Status option selection
        const option = e.target.closest('.status-option');
        if (option) {
            e.stopPropagation();
            const wrapper = option.closest('.status-dropdown-wrapper');
            const id = wrapper.getAttribute('data-id');
            const newStatus = option.getAttribute('data-value');
            wrapper.classList.remove('open');

            const app = applications.find(a => a.id === id);
            if (app) {
                app.status = newStatus;
                renderApplications();

                // Persist status update to backend
                try {
                    await fetch(`${API_BASE}/api/applications/${id}/status`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ status: newStatus })
                    });
                } catch (err) {
                    console.warn('Failed to persist status update:', err);
                }
            }
            return;
        }

        // More menu trigger
        const moreBtn = e.target.closest('.btn-more');
        if (moreBtn) {
            e.stopPropagation();
            document.querySelectorAll('.tr-more-menu.active').forEach(m => m.classList.remove('active'));
            moreBtn.nextElementSibling?.classList.toggle('active');
            return;
        }

        // Sort and Filter menus
        const filterBtn = e.target.closest('#tr-filter-btn');
        if (filterBtn) {
            e.stopPropagation();
            const menu = document.getElementById('filter-dropdown');
            document.querySelectorAll('.tr-more-menu.active').forEach(m => { if (m !== menu) m.classList.remove('active'); });
            menu.classList.toggle('active');
            return;
        }
        
        const sortBtn = e.target.closest('#tr-sort-btn');
        if (sortBtn) {
            e.stopPropagation();
            const menu = document.getElementById('sort-dropdown');
            document.querySelectorAll('.tr-more-menu.active').forEach(m => { if (m !== menu) m.classList.remove('active'); });
            menu.classList.toggle('active');
            return;
        }

        const filterOpt = e.target.closest('.filter-opt');
        if (filterOpt) {
            currentFilter = filterOpt.getAttribute('data-val');
            document.getElementById('current-filter-label').innerText = filterOpt.innerText;
            document.getElementById('filter-dropdown').classList.remove('active');
            renderApplications();
            return;
        }

        const sortOpt = e.target.closest('.sort-opt');
        if (sortOpt) {
            currentSort = sortOpt.getAttribute('data-val');
            document.getElementById('sort-dropdown').classList.remove('active');
            renderApplications();
            return;
        }

        // Click outside — close all dropdowns
        document.querySelectorAll('.status-dropdown-wrapper.open').forEach(el => el.classList.remove('open'));
        document.querySelectorAll('.tr-more-menu.active').forEach(m => m.classList.remove('active'));
    });

    // ------------------------------------------------
    // Search
    // ------------------------------------------------
    const searchInput = document.getElementById('tr-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            renderApplications();
        });
    }

    // ------------------------------------------------
    // Initial data load
    // ------------------------------------------------
    try {
        const res = await fetch(`${API_BASE}/api/applications`);
        if (res.ok) {
            const data = await res.json();
            applications = data.map(app => ({
                id:         app.id,
                company:    app.company || 'Unknown Company',
                role:       app.job_title || 'Unknown Role',
                location:   app.location || 'Remote',
                apply_link: app.apply_link || '#',
                ats_score:  app.ats_score || null,
                date:       formatDate(app.created_at),
                created_at: app.created_at,
                status:     mapStatus(app.application_status)
            }));
        } else {
            console.error('Failed to fetch applications:', res.status);
        }
    } catch (error) {
        console.error('Failed to fetch applications (network error):', error);
    }

    renderApplications();

    window.deleteApplication = async function(appId, btnElement) {
        if (!confirm('Are you sure you want to delete this application?')) return;
        try {
            const res = await fetch(`${API_BASE}/api/applications/${appId}`, { method: 'DELETE' });
            if (res.ok) {
                // Update applications array and re-render
                applications = applications.filter(a => a.id !== appId);
                renderApplications();
            } else {
                alert('Failed to delete application.');
            }
        } catch (err) {
            console.error('Delete failed:', err);
            alert('Delete failed.');
        }
    };
});

// ─── PDF Download helper ────────────────────────────────────────────────────
async function downloadPDF(appId, company, role) {
    const btn = event.currentTarget;
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 1s linear infinite"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>`;

    try {
        const res = await fetch(`${API_BASE}/api/applications/${appId}/pdf`);
        if (!res.ok) throw new Error(`Server returned ${res.status}`);

        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `${role}_${company}_jayanth_resume.pdf`.replace(/[^a-zA-Z0-9._-]/g, '_');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (err) {
        console.error('PDF download failed:', err);
        alert('PDF generation failed. Try the preview button instead.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

