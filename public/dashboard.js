// ==========================================
// PATHLIGHT DASHBOARD - PRODUCTION ROUTER
// ==========================================

const DashboardApp = {
    user: null,
    activeResumeId: null,
    
    // View mapped routes
    routes: [
        { triggerId: 'nav-home', viewId: 'view-dashboard-home' },
        { triggerId: 'nav-profile', viewId: 'view-profile' }
    ],


    async init() {
        console.log("DashboardApp: Initialization started");
        
        // 1. Bind Navigation Controller
        this.bindGlobalNavigation();
        
        // 2. Hydrate Session
        try {
            const res = await fetch('/api/auth/session', { credentials: 'include' });
            if (res.status === 401) {
                window.location.href = '/signin';
                return;
            }
            const data = await res.json();
            this.user = data.user;
        } catch (e) {
            console.error('DashboardApp: Failed to init dashboard session', e);
            window.location.href = '/signin';
            return;
        }

        // 3. Initialize Independent Modules
        this.safeExecute(() => this.hydrateUserContext(), 'Hydrate User Context');
        this.safeExecute(() => this.bindGlobalSearch(), 'Global Search');
        this.safeExecute(() => this.bindProfileMenu(), 'Profile Menu');
        this.safeExecute(() => this.bindSidebarControls(), 'Sidebar Controls');

        this.safeExecute(() => this.bindAIWorkspaceControls(), 'AI Workspace Controls');
        this.safeExecute(() => this.bindResumeControls(), 'Resume Controls');
    },

    safeExecute(fn, moduleName) {
        try {
            fn.call(this);
        } catch (e) {
            console.error(`DashboardApp: Module [${moduleName}] crashed:`, e);
        }
    },

    // ==========================================
    // ROUTING CONTROLLER
    // ==========================================

    bindGlobalSearch() {
        // OS Detection for shortcut display
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const shortcutKeyElem = document.getElementById('search-shortcut-key');
        if (shortcutKeyElem) {
            shortcutKeyElem.textContent = isMac ? '?' : 'Ctrl';
        }

        // Global Keydown listener for Cmd+K / Ctrl+K
        const desktopSearchInput = document.getElementById('global-search-input');
        const mobileSearchInput = document.getElementById('mobile-search-input');
        
        document.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault(); // Prevent browser default (e.g., Firefox search box)
                
                // If on mobile (modal is an option), open modal if search bar is hidden
                const searchContainer = document.getElementById('global-search-container');
                if (searchContainer && window.getComputedStyle(searchContainer).display === 'none') {
                    openMobileSearch();
                } else if (desktopSearchInput) {
                    desktopSearchInput.focus();
                }
            }
        });

        // Mobile Modal Logic
        const mobileToggleBtn = document.getElementById('mobile-search-toggle');
        const mobileModal = document.getElementById('mobile-search-modal');
        const mobileCloseBtn = document.getElementById('mobile-search-close');

        const openMobileSearch = () => {
            if (mobileModal) {
                mobileModal.classList.add('active');
                document.body.style.overflow = 'hidden';
                if (mobileSearchInput) {
                    setTimeout(() => mobileSearchInput.focus(), 100);
                }
            }
        };

        const closeMobileSearch = () => {
            if (mobileModal) {
                mobileModal.classList.remove('active');
                document.body.style.overflow = '';
            }
        };

        if (mobileToggleBtn) {
            mobileToggleBtn.addEventListener('click', openMobileSearch);
        }
        if (mobileCloseBtn) {
            mobileCloseBtn.addEventListener('click', closeMobileSearch);
        }
    },

    bindProfileMenu() {
        const trigger = document.getElementById('profile-menu-trigger');
        const signoutBtn = document.getElementById('sign-out-btn');
        
        if (trigger) {
            // Toggle dropdown
            trigger.addEventListener('click', (e) => {
                // Prevent bubbling to document so outside click doesn't instantly close it
                e.stopPropagation();
                trigger.classList.toggle('active');
                
                // Focus trap / Arrow navigation setup could go here if expanded
                if (trigger.classList.contains('active')) {
                    const firstItem = trigger.querySelector('.dropdown-item');
                    if (firstItem) firstItem.focus();
                }
            });

            // Keyboard navigation (ESC, Arrows)
            trigger.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    trigger.classList.remove('active');
                    trigger.focus();
                }
                if (trigger.classList.contains('active')) {
                    const items = Array.from(trigger.querySelectorAll('.dropdown-item'));
                    const currentIndex = items.indexOf(document.activeElement);
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        const nextIndex = (currentIndex + 1) % items.length;
                        items[nextIndex].focus();
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        const prevIndex = (currentIndex - 1 + items.length) % items.length;
                        items[prevIndex].focus();
                    }
                }
            });
        }

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (trigger && !trigger.contains(e.target)) {
                trigger.classList.remove('active');
            }
        });

        // Sign Out Logic
        if (signoutBtn) {
            signoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.executeLogout();
            });
        }
    },

    executeLogout() {
        // Clear Storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        localStorage.removeItem('profile');
        localStorage.removeItem('workspace');
        localStorage.removeItem('pathlight-sidebar-collapsed');
        localStorage.clear();
        
        sessionStorage.clear();
        
        // Clear memory
        this.user = null;
        
        // Prevent Back Navigation
        history.replaceState(null, '', '/signin.html');
        window.location.replace('/signin.html');
    },

    bindGlobalNavigation() {
        // Ensure static IDs are present
        const homeLink = document.querySelector('a[href="/dashboard"]');
        if (homeLink && !homeLink.id) homeLink.id = 'nav-home';
        
        const profileAvatar = document.querySelector('.profile-avatar');
        if (profileAvatar && !profileAvatar.id) profileAvatar.id = 'nav-profile';

        // Listen for all clicks and delegate to the router
        document.addEventListener('click', (e) => {
            const navItem = e.target.closest('.nav-item');
            const avatar = e.target.closest('.profile-avatar');
            
            const triggerEl = navItem || avatar;
            
            if (triggerEl) {
                const href = triggerEl.getAttribute('href');
                if (href && href !== '#' && !href.startsWith('/dashboard')) {
                    // Normal link, let the browser handle it.
                    return;
                }
                
                e.preventDefault();
                
                const triggerId = triggerEl.id;
                console.log(`DashboardApp: Intercepted navigation click for [${triggerId || 'unknown-nav'}]`);
                
                const route = this.routes.find(r => r.triggerId === triggerId);
                
                if (route && document.getElementById(route.viewId)) {
                    this.navigateToView(route.viewId, triggerEl);
                } else if (navItem) {
                    // It's a sidebar item without a concrete view yet
                    console.log(`DashboardApp: No view found for [${triggerId}]. Simulating active state.`);
                    this.hideAllViews();
                    this.clearActiveNavs();
                    navItem.classList.add('active');
                    this.showToast('This module is coming in the next sprint.', 'info');
                }
            }
        });
    },

    hideAllViews() {
        document.querySelectorAll('.dashboard-view').forEach(view => {
            view.classList.remove('view-active');
            view.classList.add('view-hidden');
        });
    },

    clearActiveNavs() {
        document.querySelectorAll('.nav-item').forEach(nav => {
            nav.classList.remove('active');
        });
    },

    navigateToView(viewId, triggerEl) {
        console.log(`Opening ${viewId}`);
        
        this.hideAllViews();
        this.clearActiveNavs();
        
        // Show target view
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.remove('view-hidden');
            targetView.classList.add('view-active');
        } else {
            console.error(`Target view ${viewId} not found in DOM`);
        }
        
        // Update Sidebar UI
        if (triggerEl && triggerEl.classList.contains('nav-item')) {
            triggerEl.classList.add('active');
        }

        // View specific lifecycle hooks
        if (viewId === 'view-profile') {
            this.loadCurrentResume();
        }

        console.log(`${viewId} Loaded`);
    },

    bindSidebarControls() {
        const layout = document.querySelector('.app-layout');
        const sidebar = document.querySelector('.sidebar');
        const toggleBtn = document.getElementById('sidebar-toggle');
        const mobileBtn = document.getElementById('mobile-menu-toggle');
        const overlay = document.getElementById('sidebar-overlay');

        // Desktop Collapse Logic
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isCollapsed = document.documentElement.classList.toggle('sidebar-collapsed');
                localStorage.setItem('pathlight-sidebar-collapsed', isCollapsed);
            });
        }

        // Mobile Drawer Logic
        const toggleMobile = () => {
            if (sidebar) sidebar.classList.toggle('mobile-open');
            if (overlay) overlay.classList.toggle('mobile-open');
        };

        const closeMobile = () => {
            if (sidebar) sidebar.classList.remove('mobile-open');
            if (overlay) overlay.classList.remove('mobile-open');
        };

        if (mobileBtn) mobileBtn.addEventListener('click', toggleMobile);
        if (overlay) overlay.addEventListener('click', closeMobile);

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeMobile();
        });
    },

    // ==========================================
    // UI MODULES
    // ==========================================

    hydrateUserContext() {
        console.log('DashboardApp: Hydrating user context for', this.user);
        
        const hour = new Date().getHours();
        let timeGreeting = 'Evening';
        if (hour < 12) timeGreeting = 'Morning';
        else if (hour < 17) timeGreeting = 'Afternoon';

        const greetingEl = document.getElementById('dynamic-greeting');
        if (greetingEl) {
            greetingEl.textContent = `Good ${timeGreeting}, ${this.user.firstName || 'User'} 👋`;
        }
        this.hydrateDashboardStats();
    },

    async hydrateDashboardStats() {
        try {
            const overviewPromise = fetch('/api/dashboard/overview', { credentials: 'include' }).then(r => r.json());
            const applicationsPromise = fetch('/api/dashboard/applications', { credentials: 'include' }).then(r => r.json());
            const resumesPromise = fetch('/api/dashboard/resumes', { credentials: 'include' }).then(r => r.json());

            const [overview, apps, resumes] = await Promise.all([overviewPromise, applicationsPromise, resumesPromise]);
            
            const stats = document.querySelectorAll('.widget-stat .empty-value');
            if (stats.length >= 3) {
                stats[0].textContent = overview.applicationsActive || '0';
                stats[1].textContent = overview.interviewsUpcoming || '0';
                stats[2].textContent = overview.recruiterResponses || '0';
            }
            
            const healthWidget = document.querySelector('.widget-health');
            if (healthWidget) {
                healthWidget.querySelector('.skeleton-block')?.remove();
                healthWidget.querySelector('.empty-content').innerHTML = `
                    <div style="font-size: 3rem; font-weight: 700; color: var(--primary-color); margin-top: 1rem;">${overview.healthScore || 0}%</div>
                    <p style="color: var(--text-secondary); margin-top: 0.5rem;">Looking excellent.</p>
                `;
            }

            const atsWidget = document.querySelector('.widget-ats');
            if (atsWidget) {
                atsWidget.querySelector('.skeleton-circle')?.remove();
                atsWidget.innerHTML += `
                    <div style="display:flex; justify-content:center; align-items:center; height:100%;">
                        <div style="font-size: 2.5rem; font-weight: 700; color: #10B981;">${resumes.atsScore || 0}</div>
                    </div>
                `;
            }
        } catch (err) {
            console.error('DashboardApp: Failed to hydrate dashboard stats', err);
        }
    },



    // ==========================================
    // AI WORKSPACE CONTROLS
    // ==========================================

    bindAIWorkspaceControls() {
        const stepperMinus = document.getElementById('stepper-minus');
        const stepperPlus = document.getElementById('stepper-plus');
        const jobsCountVal = document.getElementById('jobs-count-val');
        const projectedCount = document.getElementById('projected-count');

        if (stepperMinus && stepperPlus && jobsCountVal && projectedCount) {
            let count = 25;
            
            const updateStepper = () => {
                jobsCountVal.textContent = count;
                projectedCount.textContent = `≈ ${count} Tailored Resumes`;
            };

            stepperMinus.addEventListener('click', () => {
                if (count > 5) {
                    count -= 5;
                    updateStepper();
                }
            });

            stepperPlus.addEventListener('click', () => {
                if (count < 100) {
                    count += 5;
                    updateStepper();
                }
            });
        }

        const timeChips = document.querySelectorAll('.chip-time');
        timeChips.forEach(chip => {
            chip.addEventListener('click', () => {
                timeChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            });
        });

        const startBtn = document.getElementById('start-ai-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                const btnText = startBtn.querySelector('.btn-text');
                const spinner = startBtn.querySelector('.spinner');
                
                if (btnText && spinner) {
                    startBtn.disabled = true;
                    btnText.textContent = 'Initializing AI Pipeline...';
                    spinner.classList.remove('hidden');
                    
                    setTimeout(() => {
                        btnText.textContent = 'Pipeline Active';
                        spinner.classList.add('hidden');
                        startBtn.classList.remove('glow-btn');
                        startBtn.classList.add('btn-secondary');
                        this.showToast('AI Tailoring Mission Started', 'success');
                    }, 1500);
                }
            });
        }
    },

    // ==========================================
    // RESUME CONTROLS
    // ==========================================

    bindResumeControls() {
        const uploadInput = document.getElementById('resume-upload-input');
        const replaceInput = document.getElementById('resume-replace-input');
        const downloadBtn = document.getElementById('resume-download-btn');
        
        if (uploadInput) uploadInput.addEventListener('change', (e) => this.handleResumeUpload(e, false));
        if (replaceInput) replaceInput.addEventListener('change', (e) => this.handleResumeUpload(e, true));
        
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                if (this.activeResumeId) {
                    window.location.href = '/api/resume/download/' + this.activeResumeId;
                }
            });
        }
    },

    async loadCurrentResume() {
        try {
            const res = await fetch('/api/resume/current', { credentials: 'include' });
            if (!res.ok) return;
            const data = await res.json();
            
            const emptyState = document.getElementById('resume-empty-state');
            const activeState = document.getElementById('resume-active-state');
            const progressState = document.getElementById('resume-upload-progress');
            const badge = document.getElementById('resume-badge');
            
            if (progressState) progressState.classList.add('hidden');
            
            if (data.status === 'none') {
                if(emptyState) emptyState.classList.remove('hidden');
                if(activeState) activeState.classList.add('hidden');
                if(badge) badge.classList.add('hidden');
            } else {
                if(emptyState) emptyState.classList.add('hidden');
                if(activeState) activeState.classList.remove('hidden');
                if(badge) badge.classList.remove('hidden');
                
                const resume = data.resume;
                this.activeResumeId = resume.id;
                
                const metaName = document.getElementById('resume-meta-name');
                if (metaName) metaName.textContent = resume.fileName;
                
                const metaSize = document.getElementById('resume-meta-size');
                if (metaSize) metaSize.textContent = (resume.fileSize / 1024).toFixed(1) + ' KB';
                
                const metaDate = document.getElementById('resume-meta-date');
                if (metaDate) metaDate.textContent = new Date(resume.createdAt).toLocaleDateString();
                
                const metaPages = document.getElementById('resume-meta-pages');
                if (metaPages) metaPages.textContent = resume.pageCount || '-';
                
                const metaStatus = document.getElementById('resume-meta-status');
                if (metaStatus) metaStatus.textContent = resume.processingStatus;
                
                const metaArchived = document.getElementById('resume-meta-archived');
                if (metaArchived) metaArchived.textContent = resume.archivedCount + ' older versions';
                
                if (badge) {
                    if (resume.version1_ready) {
                        badge.textContent = 'Version 1 - Ready';
                        badge.className = 'badge badge-success';
                        badge.style = '';
                    } else if(resume.processingStatus === 'FAILED' || resume.processingStatus === 'ERROR') {
                        badge.textContent = 'Extraction Failed';
                        badge.className = 'badge badge-error';
                        badge.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                        badge.style.color = '#ef4444';
                    } else {
                        badge.textContent = 'Processing...';
                        badge.className = 'badge badge-warning';
                        badge.style.backgroundColor = 'rgba(245, 158, 11, 0.2)';
                        badge.style.color = '#f59e0b';
                    }
                }
            }
        } catch (e) {
            console.error('DashboardApp: Failed to load resume:', e);
        }
    },

    async handleResumeUpload(event, isReplace=false) {
        const file = event.target.files[0];
        if (!file) return;
        
        const emptyState = document.getElementById('resume-empty-state');
        const activeState = document.getElementById('resume-active-state');
        const progressState = document.getElementById('resume-upload-progress');
        
        if(emptyState) emptyState.classList.add('hidden');
        if(activeState) activeState.classList.add('hidden');
        if(progressState) progressState.classList.remove('hidden');
        
        const formData = new FormData();
        formData.append('resume', file);
        
        try {
            const endpoint = isReplace ? '/api/resume/replace' : '/api/resume/upload';
            const method = isReplace ? 'PUT' : 'POST';
            
            const res = await fetch(endpoint, {
                method: method,
                body: formData,
                credentials: 'include'
            });
            
            const data = await res.json();
            if (data.success) {
                setTimeout(() => this.loadCurrentResume(), 1000);
            } else {
                alert(data.detail || 'Upload failed');
                this.loadCurrentResume();
            }
        } catch (e) {
            console.error('DashboardApp: Upload error:', e);
            alert('Upload failed. Please try again.');
            this.loadCurrentResume();
        }
        
        event.target.value = '';
    },

    // ==========================================
    // UTILITIES
    // ==========================================

    showToast(msg, type='success') {
        if (window.showToastFn) {
            window.showToastFn(msg, type);
            return;
        }

        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.position = 'fixed';
            container.style.bottom = '2rem';
            container.style.right = '2rem';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.gap = '1rem';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        // Limit concurrent toasts to 3 to prevent overwhelming UI
        if (container.children.length >= 3) {
            container.removeChild(container.firstChild);
        }

        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.background = type === 'success' ? '#10b981' : (type === 'info' ? '#3b82f6' : '#ef4444');
        toast.style.color = '#fff';
        toast.style.padding = '1rem 2rem';
        toast.style.borderRadius = 'var(--radius-sm, 8px)';
        toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.2)';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
        toast.style.fontWeight = '500';

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateY(0)';
            });
        });

        // Auto remove
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'scale(0.95)';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
};

// ==========================================
// BOOTSTRAP
// ==========================================

// ==========================================
// CUSTOM SELECT COMPONENT LOGIC
// ==========================================
function initCustomSelects() {
    const customSelects = document.querySelectorAll('.custom-select-wrapper');
    customSelects.forEach(wrapper => {
        const trigger = wrapper.querySelector('.custom-select-trigger');
        const options = wrapper.querySelectorAll('.custom-select-option');
        const textElement = trigger.querySelector('.selected-text');
        const hiddenInput = wrapper.querySelector('input[type="hidden"]');

        if (trigger) {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                // Close other open selects
                customSelects.forEach(other => {
                    if (other !== wrapper) other.classList.remove('open');
                });
                wrapper.classList.toggle('open');
            });
        }

        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                // Remove selected from all
                options.forEach(opt => opt.classList.remove('selected'));
                // Add to clicked
                option.classList.add('selected');
                // Update text
                if (textElement) {
                    textElement.textContent = option.textContent;
                }
                // Update hidden input
                if (hiddenInput) {
                    hiddenInput.value = option.dataset.value;
                    hiddenInput.dispatchEvent(new Event('change'));
                }
                // Store value on wrapper dataset
                wrapper.dataset.value = option.dataset.value;
                
                // Close dropdown
                wrapper.classList.remove('open');
            });
        });
    });

    // Close on outside click
    document.addEventListener('click', () => {
        customSelects.forEach(wrapper => wrapper.classList.remove('open'));
    });
}

// Ensure there is only ONE initialization entry point
function bootstrapDashboard() {
    console.log("Bootstrap Dashboard triggered");
    DashboardApp.init();
    initCustomSelects();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrapDashboard);
} else {
    bootstrapDashboard();
}


