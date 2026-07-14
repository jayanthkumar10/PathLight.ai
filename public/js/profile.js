document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Global Edit State Logic ---
    const profileContainer = document.getElementById('profile-container');
    const btnGlobalEdit = document.getElementById('btn-global-edit');
    const btnGlobalCancel = document.getElementById('btn-global-cancel');
    const btnGlobalSave = document.getElementById('btn-global-save');

    if (btnGlobalEdit && profileContainer) {
        btnGlobalEdit.addEventListener('click', () => {
            profileContainer.classList.add('edit-mode');
        });
    }

    if (btnGlobalCancel && profileContainer) {
        btnGlobalCancel.addEventListener('click', () => {
            profileContainer.classList.remove('edit-mode');
        });
    }

    if (btnGlobalSave && profileContainer) {
        btnGlobalSave.addEventListener('click', () => {
            const originalText = btnGlobalSave.innerHTML;
            
            // Success State
            btnGlobalSave.style.background = 'var(--accent-primary)';
            btnGlobalSave.style.color = '#fff';
            btnGlobalSave.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Saved';
            
            setTimeout(() => {
                profileContainer.classList.remove('edit-mode');
                
                setTimeout(() => {
                    // Revert button styling
                    btnGlobalSave.style.background = '';
                    btnGlobalSave.style.color = '';
                    btnGlobalSave.innerHTML = originalText;
                }, 400); // Wait for sticky bar to animate down
            }, 800);
        });
    }


    // --- 2. AI Readiness Progress Animation ---
    const meter = document.querySelector('.circular-progress .meter');
    if (meter) {
        // 70% of 283 (stroke-dasharray) = 198.1. Dashoffset = 283 - 198.1 = 84.9
        // We set it to 283 in CSS or JS initially, then animate to 85.
        
        // Initial state
        meter.style.strokeDashoffset = '283';
        
        // Trigger reflow
        meter.getBoundingClientRect();
        
        // Animate
        setTimeout(() => {
            meter.style.strokeDashoffset = '85';
        }, 300);
    }


    // --- 3. Topbar Profile Dropdown ---
    const profileTrigger = document.getElementById('profile-menu-trigger');
    const profileDropdown = document.getElementById('profile-dropdown');

    if (profileTrigger && profileDropdown) {
        profileTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = profileTrigger.getAttribute('aria-expanded') === 'true';
            profileTrigger.setAttribute('aria-expanded', !isExpanded);
            profileDropdown.classList.toggle('show');
        });

        profileTrigger.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                profileTrigger.click();
            }
        });

        document.addEventListener('click', (e) => {
            if (!profileTrigger.contains(e.target)) {
                profileTrigger.setAttribute('aria-expanded', 'false');
                profileDropdown.classList.remove('show');
            }
        });
    }


    // --- 4. Mobile Menu Toggle ---
    const mobileMenuBtn = document.getElementById('mobile-menu-trigger');
    const sidebar = document.querySelector('.sidebar');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('mobile-open') && 
                !sidebar.contains(e.target) && 
                !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }

    // --- 5. Sign Out Button ---
    const signOutBtn = document.getElementById('sign-out-btn');
    if (signOutBtn) {
        signOutBtn.addEventListener('click', () => {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('onboarding_step');
            window.location.href = '/signin.html';
        });
    }

});
