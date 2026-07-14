document.addEventListener('DOMContentLoaded', () => {
    initTextSplitter();
    initScrollObserver();
    initNavbarScroll();
    initHeroParallax();
    init3DCards();
    initFAQ();
    initPasswordToggle();
    initSignUpValidation();
    initAuthAPI();
    
    // Handle /onboarding route
    if (window.location.pathname === '/onboarding' && window.switchAuthView) {
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step') || '1';
        const stepMap = {
            '1': 'view-onboarding',
            '2': 'view-career-profile',
            '3': 'view-career-goals',
            '4': 'view-skills',
            '5': 'view-resume',
            '6': 'view-connect-google',
            '7': 'view-ai-preferences',
            '8': 'view-ai-initialization'
        };
        const targetView = stepMap[step] || 'view-onboarding';
        window.switchAuthView(targetView);
    }
    
    checkSession();
});

// =========================================
// API CONFIGURATION
// =========================================
const API_BASE = '/api';
// 1. Text Splitter for Blur-to-Sharp Reveals
function initTextSplitter() {
    const textEls = document.querySelectorAll('[data-split-text]');
    textEls.forEach(el => {
        const text = el.innerText;
        const words = text.split(' ');
        el.innerHTML = '';
        words.forEach((word, idx) => {
            const span = document.createElement('span');
            span.className = 'word-span';
            span.innerHTML = word + '&nbsp;';
            span.style.transitionDelay = `${idx * 0.05}s`;
            el.appendChild(span);
        });
        el.classList.add('observe-text');
    });
}

// 2. Global Scroll Observer (Apple-style progressive reveals)
function initScrollObserver() {
    const observerOptions = { root: null, rootMargin: '0px 0px -15% 0px', threshold: 0.1 };
    
    // Flags to prevent re-running live animations
    let resumeAnimated = false;
    let emailAnimated = false;
    let mentorAnimated = false;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (entry.target.classList.contains('observe-fade')) {
                    entry.target.classList.add('revealed');
                }
                if (entry.target.classList.contains('observe-text')) {
                    const spans = entry.target.querySelectorAll('.word-span');
                    spans.forEach(span => span.classList.add('revealed'));
                }
                
                // Trigger Live Visualizers ONCE
                if (entry.target.querySelector('#resumeVisualizer') && !resumeAnimated) {
                    resumeAnimated = true;
                    animateResumeLive();
                }
                if (entry.target.querySelector('#emailVisualizer') && !emailAnimated) {
                    emailAnimated = true;
                    animateEmailLive();
                }
                if (entry.target.querySelector('#mentorVisualizer') && !mentorAnimated) {
                    mentorAnimated = true;
                    animateMentorLive();
                }
                
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.observe-fade, .observe-text, .bento-card').forEach(el => observer.observe(el));
}

// 3. Dynamic Navbar
function initNavbarScroll() {
    const nav = document.getElementById('navbar');
    if (!nav) return;
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    }, { passive: true });
}

// 4. Hero Parallax (Cinematic Depth)
function initHeroParallax() {
    const heroContent = document.querySelector('[data-parallax]');
    if (!heroContent) return;

    window.addEventListener('scroll', () => {
        const scrolled = window.scrollY;
        if (scrolled < 600) {
            const y = scrolled * 0.3;
            const z = scrolled * -0.2;
            const opacity = 1 - (scrolled / 500);
            heroContent.style.transform = `translate3d(0, ${y}px, ${z}px)`;
            heroContent.style.opacity = Math.max(opacity, 0);
        }
    }, { passive: true });
}

// 5. 3D Premium Cards (Hover Physics)
function init3DCards() {
    const cards = document.querySelectorAll('[data-tilt]');
    cards.forEach(card => {
        const glow = card.querySelector('.card-glow');
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            if (glow) {
                glow.style.left = `${x}px`;
                glow.style.top = `${y}px`;
            }
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const percentX = (x - centerX) / centerX;
            const percentY = -((y - centerY) / centerY);
            
            const maxTilt = 3;
            const rotateX = percentY * maxTilt;
            const rotateY = percentX * maxTilt;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
        });
    });
}

// 6. FAQ Accordion Logic
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const btn = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        
        btn.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            // Close all
            faqItems.forEach(i => {
                i.classList.remove('active');
                i.querySelector('.faq-answer').style.maxHeight = null;
            });
            // Open clicked if it wasn't active
            if (!isActive) {
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + "px";
            }
        });
    });
}

// 7. Password Visibility Toggle
function initPasswordToggle() {
    const toggleBtns = document.querySelectorAll('.password-toggle');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const passwordInput = btn.previousElementSibling;
            if (!passwordInput || passwordInput.tagName !== 'INPUT') return;
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            if (type === 'text') {
                btn.innerHTML = `<svg class="eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                </svg>`;
            } else {
                btn.innerHTML = `<svg class="eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>`;
            }
        });
    });
}

// 8. Auth View Switching
window.switchAuthView = function(targetId) {
    const views = document.querySelectorAll('.auth-view');
    views.forEach(view => {
        if (view.id === targetId) {
            view.classList.remove('view-hidden');
            view.classList.add('view-active');
        } else {
            view.classList.remove('view-active');
            view.classList.add('view-hidden');
        }
    });

    // Expand width for Onboarding views
    const authCard = document.querySelector('.auth-card');
    const onboardingViews = [
        'view-onboarding',
        'view-career-profile',
        'view-career-goals',
        'view-skills',
        'view-resume',
        'view-connect-google',
        'view-ai-preferences',
        'view-ai-initialization'
    ];
    
    if (onboardingViews.includes(targetId)) {
        authCard.classList.add('onboarding-card');
        localStorage.setItem('onboarding_step', targetId.replace('view-', ''));
    } else {
        authCard.classList.remove('onboarding-card');
    }

    if (targetId === 'view-onboarding') {
        setTimeout(() => {
            const spinner = document.querySelector('.onboarding-loading');
            if (spinner) spinner.style.opacity = 0;
        }, 2000);
    }
};

// 9. Sign Up Form Validation (Live)
function initSignUpValidation() {
    const passwordInput = document.getElementById('signup-password');
    const confirmInput = document.getElementById('confirm-password');
    const bars = [
        document.getElementById('strength-bar-1'),
        document.getElementById('strength-bar-2'),
        document.getElementById('strength-bar-3'),
        document.getElementById('strength-bar-4')
    ];
    const matchIcon = document.getElementById('match-icon');

    if (!passwordInput || !confirmInput) return;

    passwordInput.addEventListener('input', (e) => {
        const val = e.target.value;
        let score = 0;
        if (val.length > 5) score++;
        if (val.length > 8) score++;
        if (/[A-Z]/.test(val) && /[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;

        bars.forEach((bar, index) => {
            bar.className = 'password-strength-bar';
            if (index < score) {
                if (score === 1) bar.classList.add('strength-weak');
                else if (score === 2) bar.classList.add('strength-fair');
                else if (score === 3) bar.classList.add('strength-good');
                else if (score >= 4) bar.classList.add('strength-strong');
            }
        });
        checkMatch();
    });

    confirmInput.addEventListener('input', checkMatch);

    function checkMatch() {
        const p1 = passwordInput.value;
        const p2 = confirmInput.value;
        if (p1 && p2 && p1 === p2) {
            matchIcon.classList.add('valid');
        } else {
            matchIcon.classList.remove('valid');
        }
    }
}

/* =========================================
   LIVE PRODUCT BEHAVIORS (THE FINAL 5%)
   ========================================= */

// Live Resume Optimization (Score Count Up)
function animateResumeLive() {
    const linesContainer = document.getElementById('resumeLines');
    const numEl = document.getElementById('atsNumber');
    const ringEl = document.getElementById('atsRing');
    
    // Create initial lines
    for(let i=0; i<4; i++) {
        const row = document.createElement('div');
        row.className = 'resume-vis-row';
        row.style.width = '40%';
        linesContainer.appendChild(row);
    }
    
    // Expand lines over time
    const rows = linesContainer.querySelectorAll('.resume-vis-row');
    const targetWidths = ['100%', '85%', '95%', '90%'];
    
    setTimeout(() => {
        rows.forEach((row, idx) => {
            setTimeout(() => {
                row.style.width = targetWidths[idx];
                row.classList.add('active');
            }, idx * 300);
        });

        // Count up ATS Score
        let score = 45;
        const targetScore = 98;
        const duration = 1500; // ms
        const interval = 20;
        const step = (targetScore - score) / (duration / interval);
        
        const counter = setInterval(() => {
            score += step;
            if (score >= targetScore) {
                score = targetScore;
                clearInterval(counter);
            }
            numEl.innerText = Math.round(score);
        }, interval);

        // Spin the ring
        ringEl.style.transform = 'rotate(315deg)';
        
    }, 500);
}

// Live Email Arrival Simulation
function animateEmailLive() {
    const list = document.getElementById('emailList');
    const indicator = document.getElementById('emailTyping');
    
    const emails = [
        { title: "Stripe Team", sub: "Next steps for your application" },
        { title: "Linear", sub: "Availability for technical screen" }
    ];
    
    // Add existing emails
    emails.forEach(data => {
        const el = document.createElement('div');
        el.className = 'email-item visible';
        el.innerHTML = `<div class="email-title">${data.title}</div><div class="email-sub">${data.sub}</div>`;
        list.appendChild(el);
    });

    // Simulate new email arriving
    setTimeout(() => {
        indicator.classList.remove('hidden');
        indicator.style.opacity = 1;
        
        setTimeout(() => {
            indicator.style.opacity = 0;
            setTimeout(() => indicator.classList.add('hidden'), 300);
            
            const el = document.createElement('div');
            el.className = 'email-item';
            el.innerHTML = `<div class="email-title">Google Recruiter <span class="unread-dot"></span></div><div class="email-sub">Interview Invitation - Frontend</div>`;
            list.insertBefore(el, list.firstChild);
            
            // Trigger animation frame for CSS transition
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    el.classList.add('visible');
                });
            });
        }, 1500);
    }, 1000);
}

// Live Mentor Typing Simulation
function animateMentorLive() {
    const container = document.getElementById('mentorVisualizer');
    
    const messages = [
        { type: 'ai', text: "How would you optimize a large React list?" },
        { type: 'user', text: "I'd use a virtualizer like react-window." }
    ];
    
    // Setup initial static messages
    messages.forEach(data => {
        const el = document.createElement('div');
        el.className = `mentor-bubble bubble-${data.type} visible`;
        el.textContent = data.text;
        container.appendChild(el);
    });
    
    // Setup typing AI bubble
    setTimeout(() => {
        const aiBubble = document.createElement('div');
        aiBubble.className = 'mentor-bubble bubble-ai visible';
        container.appendChild(aiBubble);
        
        const finalString = "Great. What about state colocation?";
        let i = 0;
        
        // Add blinking cursor
        aiBubble.innerHTML = '<span class="cursor-blink"></span>';
        
        const typeInterval = setInterval(() => {
            if (i < finalString.length) {
                // Remove cursor, add char, add cursor back
                aiBubble.innerHTML = finalString.substring(0, i + 1) + '<span class="cursor-blink"></span>';
                i++;
            } else {
                clearInterval(typeInterval);
                aiBubble.innerHTML = finalString; // Remove cursor when done
            }
        }, 50); // Typing speed
    }, 1000);
}

// 12. Auth API Integration
function initAuthAPI() {
    const signInForm = document.getElementById('form-signin');
    const signUpForm = document.getElementById('form-signup');
    
    if (signInForm) {
        signInForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('[DEBUG] Sign In button clicked');
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const rememberMe = document.getElementById('remember-me')?.checked || false;
            
            const btn = signInForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0 auto;"></div>';
            btn.disabled = true;

            console.log('[DEBUG] Validation passed (native browser validation)');
            console.log('[DEBUG] API request started for Sign In');

            try {
                const res = await fetch(`${API_BASE}/auth/signin`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ email, password, rememberMe })
                });

                const data = await res.json();
                
                if (!res.ok) {
                    if (data.error?.details && data.error.details.length > 0) {
                        throw new Error(data.error.details[0].message);
                    }
                    throw new Error(data.error?.message || 'Invalid credentials');
                }

                // Successful login
                console.log('[DEBUG] Authentication successful. Let backend route.');
                window.location.href = '/dashboard';
            } catch (err) {
                // Show error message gracefully
                let errorMsg = signInForm.querySelector('.auth-error');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'auth-error';
                    errorMsg.style.color = '#ef4444';
                    errorMsg.style.fontSize = '0.875rem';
                    errorMsg.style.marginTop = '0.5rem';
                    errorMsg.style.textAlign = 'center';
                    signInForm.insertBefore(errorMsg, btn);
                }
                errorMsg.textContent = err.message;
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    if (signUpForm) {
        signUpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log('[DEBUG] Create Account clicked');
            const name = document.getElementById('fullname').value;
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            const btn = signUpForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;

            let errorMsg = signUpForm.querySelector('.auth-error');
            if (!errorMsg) {
                errorMsg = document.createElement('div');
                errorMsg.className = 'auth-error';
                errorMsg.style.color = '#ef4444';
                errorMsg.style.fontSize = '0.875rem';
                errorMsg.style.marginTop = '0.5rem';
                errorMsg.style.textAlign = 'center';
                signUpForm.insertBefore(errorMsg, btn);
            }
            errorMsg.textContent = ''; // Clear previous errors

            if (password !== confirmPassword) {
                errorMsg.textContent = 'Passwords do not match.';
                return;
            }

            console.log('[DEBUG] Validation passed');
            console.log('[DEBUG] Sending request');

            btn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0 auto;"></div>';
            btn.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/auth/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ name, email, password })
                });

                const data = await res.json();
                
                if (!res.ok) {
                    if (data.error?.details && data.error.details.length > 0) {
                        throw new Error(data.error.details[0].message);
                    }
                    throw new Error(data.error?.message || 'Failed to create account');
                }

                console.log('[DEBUG] Redirecting to Dashboard to let backend handle routing');
                window.location.href = '/dashboard';
            } catch (err) {
                errorMsg.textContent = err.message;
            } finally {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }

    // Google OAuth Handlers
    const googleSignIn = document.getElementById('btn-google-signin');
    const googleSignUp = document.getElementById('btn-google-signup');
    const handleGoogleAuth = () => {
        console.log('[DEBUG] Google button clicked');
        console.log('[DEBUG] API request started (Redirecting to Google)');
        window.location.href = `${API_BASE}/auth/google`;
    };
    if (googleSignIn) googleSignIn.addEventListener('click', handleGoogleAuth);
    if (googleSignUp) googleSignUp.addEventListener('click', handleGoogleAuth);

    // Forgot Password Handler
    const forgotForm = document.getElementById('form-forgot-password');
    if (forgotForm) {
        forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('forgot-email').value;
            const btn = forgotForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0 auto;"></div>';
            btn.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/auth/forgot-password`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ email })
                });

                const data = await res.json();
                
                if (!res.ok) {
                    throw new Error(data.error?.message || 'Failed to send reset link');
                }

                forgotForm.innerHTML = `<div style="text-align: center; padding: 2rem 0; color: #10b981;">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 1rem;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                    <h3 style="margin-bottom: 0.5rem; font-weight: 500;">Check your email</h3>
                    <p style="color: var(--text-secondary); font-size: 0.875rem;">We've sent a password reset link to ${email}</p>
                </div>`;
            } catch (err) {
                let errorMsg = forgotForm.querySelector('.auth-error');
                if (!errorMsg) {
                    errorMsg = document.createElement('div');
                    errorMsg.className = 'auth-error';
                    errorMsg.style.color = '#ef4444';
                    errorMsg.style.fontSize = '0.875rem';
                    errorMsg.style.marginTop = '0.5rem';
                    errorMsg.style.textAlign = 'center';
                    forgotForm.insertBefore(errorMsg, btn);
                }
                errorMsg.textContent = err.message;
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    }
}

// 13. Session Restoration
async function checkSession() {
    try {
        const res = await fetch(`${API_BASE}/auth/session`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        
        if (res.ok) {
            const data = await res.json();
            if (data.user) {
                console.log('[DEBUG] Authentication successful via Session.');
                // Backend handles all routing. If we are on public pages, we let backend route us.
                if (window.location.pathname === '/' || window.location.pathname === '/signin' || window.location.pathname === '/signup') {
                    // Force a navigation to /dashboard so backend can evaluate routing
                    window.location.href = '/dashboard';
                }
            }
        } else {
            // Handle unauthenticated state
            if (window.location.pathname === '/dashboard' || window.location.pathname === '/onboarding') {
                window.location.href = '/signin';
            }
        }
    } catch (err) {
        // Silently fail if no session
        if (window.location.pathname === '/dashboard' || window.location.pathname === '/onboarding') {
            window.location.href = '/signin';
        }
    }
}

    // Onboarding State Engine
    async function fetchOnboardingState() {
        try {
            const res = await fetch(`${API_BASE}/onboarding/state`, {
                method: 'GET',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' }
            });
            if (res.ok) {
                const state = await res.json();
                console.log('[DEBUG] Onboarding State:', state);
                
                // State-based routing
                const stepMap = {
                    1: 'view-onboarding', // Welcome
                    2: 'view-career-profile',
                    3: 'view-career-goals',
                    4: 'view-skills',
                    5: 'view-resume',
                    6: 'view-connect-google',
                    7: 'view-ai-preferences',
                    8: 'view-ai-initialization'
                };
                
                const targetView = stepMap[state.currentStep] || 'view-onboarding';
                window.switchAuthView(targetView);
                
                if (state.currentStep === 8 && typeof startCinematicSequence === 'function') {
                    startCinematicSequence();
                }
            } else {
                console.warn('Failed to fetch state, falling back to step 1');
                window.switchAuthView('view-onboarding');
            }
        } catch (e) {
            console.error('Error fetching state:', e);
            window.switchAuthView('view-onboarding');
        }
    }

// 14. Onboarding Start Handler
document.addEventListener('DOMContentLoaded', () => {
    const btnStartOnboarding = document.getElementById('btn-start-onboarding');
    if (btnStartOnboarding) {
        btnStartOnboarding.addEventListener('click', () => {
            console.log('[DEBUG] Continue button clicked');
            window.switchAuthView('view-career-profile');
        });
    }

    initOnboardingForms();
    initSkillSelector();
    initResumeUpload();
    initCityAutocomplete();
    initCompanyAutocomplete();
});

// 15. Onboarding Forms & Auto-save
function initOnboardingForms() {
    const steps = [
        { formId: 'form-career-profile', nextView: 'view-career-goals', indicatorId: 'save-indicator-2', stepNum: 2 },
        { formId: 'form-career-goals', nextView: 'view-skills', indicatorId: 'save-indicator-3', stepNum: 3 },
        { formId: 'form-skills', nextView: 'view-resume', indicatorId: 'save-indicator-4', stepNum: 4 },
        { formId: 'form-ai-preferences', nextView: 'view-ai-initialization', indicatorId: null, stepNum: 7 }
    ];

    steps.forEach(step => {
        const form = document.getElementById(step.formId);
        if (!form) return;

        // Simulate Auto-save
        if (step.indicatorId) {
            let timeout;
            form.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    const indicator = document.getElementById(step.indicatorId);
                    indicator.classList.add('visible');
                    setTimeout(() => indicator.classList.remove('visible'), 2000);
                }, 1000);
            });
        }

        // Form Submit -> API -> Next Step
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('button[type="submit"]');
            const orig = btn.innerHTML;
            btn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0 auto;"></div>';
            btn.disabled = true;

            try {
                const res = await fetch(`${API_BASE}/onboarding/step`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        stepNumber: step.stepNum,
                        stepData: {} // Gather form data in production
                    })
                });
                
                if (res.ok) {
                    window.switchAuthView(step.nextView);
                    if (step.nextView === 'view-ai-initialization') {
                        startCinematicSequence();
                    }
                } else {
                    console.error('Failed to save step');
                }
            } catch (err) {
                console.error(err);
            } finally {
                btn.innerHTML = orig;
                btn.disabled = false;
            }
        });
    });
}

// 16. Skill Selector (Step 4)
function initSkillSelector() {
    const input = document.getElementById('skill-search');
    const selectedContainer = document.getElementById('selected-skills-container');
    const suggestContainer = document.getElementById('suggested-skills-container');
    
    if (!input || !selectedContainer || !suggestContainer) return;

    let selectedSkills = new Set();
    const suggestions = ['Python', 'Java', 'React', 'Node.js', 'AWS', 'Azure', 'Docker', 'Kubernetes', 'LLMs', 'Prompt Engineering', 'SQL', 'GraphQL', 'TypeScript', 'Go'];

    const renderSelected = () => {
        selectedContainer.innerHTML = '';
        selectedSkills.forEach(skill => {
            const pill = document.createElement('div');
            pill.className = 'skill-pill selected';
            pill.innerHTML = `${skill} <svg class="remove-skill" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
            pill.addEventListener('click', () => {
                selectedSkills.delete(skill);
                renderSelected();
                renderSuggestions(input.value);
            });
            selectedContainer.appendChild(pill);
        });
    };

    const renderSuggestions = (query = '') => {
        suggestContainer.innerHTML = '';
        const q = query.toLowerCase();
        
        let matches = suggestions.filter(s => !selectedSkills.has(s) && s.toLowerCase().includes(q));
        
        if (q && !matches.find(m => m.toLowerCase() === q) && !selectedSkills.has(query)) {
            matches.unshift(query); // Allow custom
        }

        matches.slice(0, 8).forEach(skill => {
            const pill = document.createElement('div');
            pill.className = 'skill-pill';
            pill.textContent = skill === query ? `Add "${skill}"` : skill;
            pill.addEventListener('click', () => {
                selectedSkills.add(skill === query ? query : skill);
                input.value = '';
                renderSelected();
                renderSuggestions();
            });
            suggestContainer.appendChild(pill);
        });
    };

    input.addEventListener('input', (e) => renderSuggestions(e.target.value));
    
    // Initial Render
    renderSuggestions();
}

// 17. Resume Upload Drag & Drop (Step 5)
function initResumeUpload() {
    const zone = document.getElementById('resume-upload-zone');
    const fileInput = document.getElementById('resume-file');
    const title = document.getElementById('upload-title');
    const desc = document.getElementById('upload-desc');
    const progressCont = document.getElementById('upload-progress');
    const progressFill = document.getElementById('upload-progress-fill');
    const statusText = document.getElementById('upload-status-text');
    const btnContinue = document.getElementById('btn-resume-continue');
    
    if (!zone || !fileInput) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.classList.add('drag-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        zone.addEventListener(eventName, () => zone.classList.remove('drag-active'), false);
    });

    zone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files), false);

    function handleFiles(files) {
        if (!files || files.length === 0) return;
        const file = files[0];
        
        title.textContent = file.name;
        desc.style.display = 'none';
        zone.querySelector('.upload-icon').style.display = 'none';
        zone.querySelector('button').style.display = 'none';
        
        progressCont.classList.add('active');
        progressFill.style.width = '10%';
        btnContinue.disabled = true;

        const formData = new FormData();
        formData.append('resume', file);

        fetch(`${API_BASE}/onboarding/upload`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                statusText.textContent = "AI Analysis Complete!";
                statusText.style.color = "#10b981";
                progressFill.style.width = '100%';
                
                // Automatically transition after success
                setTimeout(() => {
                    fetchOnboardingState();
                }, 1500);
            } else {
                throw new Error(data.error || 'Upload failed');
            }
        })
        .catch(err => {
            statusText.textContent = err.message || "Upload failed. Please try again.";
            statusText.style.color = "#ef4444";
            progressFill.style.backgroundColor = "#ef4444";
            btnContinue.disabled = false;
        });
    }
}

window.skipGoogle = async function() {
    try {
        const res = await fetch(`${API_BASE}/onboarding/google-skip`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        if (res.ok) {
            fetchOnboardingState();
        }
    } catch (err) {
        console.error('Failed to skip Google:', err);
    }
};

// 18. Cinematic Sequence (Step 8)
function startCinematicSequence() {
    const steps = [
        document.getElementById('cinematic-step-1'),
        document.getElementById('cinematic-step-2'),
        document.getElementById('cinematic-step-3'),
        document.getElementById('cinematic-step-4')
    ];
    const loader = document.getElementById('cinematic-loader');
    const loaderFill = document.getElementById('cinematic-loader-fill');
    const text = document.getElementById('cinematic-text');

    if (!steps[0]) return;

    setTimeout(() => loader.classList.add('active'), 500);

    let delay = 1000;
    steps.forEach((step, index) => {
        setTimeout(() => {
            if (index > 0) {
                steps[index-1].classList.remove('active');
                steps[index-1].classList.add('completed');
            }
            step.classList.add('active');
            loaderFill.style.width = `${(index + 1) * 25}%`;
        }, delay);
        delay += 1800; // Time per step
    });

    // Finalize
    setTimeout(() => {
        steps[3].classList.remove('active');
        steps[3].classList.add('completed');
        text.textContent = "Your AI Career Agent is ready.";
        text.style.color = "#10b981";
        
        // Redirect to dashboard (Simulated)
        setTimeout(() => {
            window.location.href = "/dashboard";
        }, 1500);
    }, delay);
}

// 19. Autocomplete Modules (Indian Market)
function initCityAutocomplete() {
    const input = document.getElementById('ob-city');
    const list = document.getElementById('city-autocomplete');
    if (!input || !list) return;

    const cities = [
        "Bengaluru", "Hyderabad", "Pune", "Chennai", "Gurugram", 
        "Noida", "Mumbai", "Delhi", "Kolkata", "Ahmedabad"
    ];

    input.addEventListener('input', (e) => {
        const val = e.target.value.toLowerCase();
        list.innerHTML = '';
        if (!val) {
            list.classList.remove('active');
            return;
        }
        
        const matches = cities.filter(c => c.toLowerCase().includes(val));
        if (matches.length > 0) {
            list.classList.add('active');
            matches.forEach(match => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.textContent = match;
                item.addEventListener('click', () => {
                    input.value = match;
                    list.classList.remove('active');
                });
                list.appendChild(item);
            });
        } else {
            list.classList.remove('active');
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target !== input && e.target !== list) {
            list.classList.remove('active');
        }
    });
}

function initCompanyAutocomplete() {
    const input = document.getElementById('ob-companies-search');
    const list = document.getElementById('company-autocomplete');
    const container = document.getElementById('selected-companies-container');
    if (!input || !list || !container) return;

    const companies = [
        "Razorpay", "CRED", "Flipkart", "Swiggy", "Zomato", "PhonePe",
        "Google", "Microsoft", "Amazon", "Atlassian", "Uber", "Zerodha"
    ];
    let selected = new Set();

    const renderSelected = () => {
        container.innerHTML = '';
        selected.forEach(comp => {
            const pill = document.createElement('div');
            pill.className = 'skill-pill selected';
            pill.innerHTML = `${comp} <svg class="remove-skill" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
            pill.addEventListener('click', () => {
                selected.delete(comp);
                renderSelected();
            });
            container.appendChild(pill);
        });
    };

    input.addEventListener('input', (e) => {
        const val = e.target.value.toLowerCase();
        list.innerHTML = '';
        if (!val) {
            list.classList.remove('active');
            return;
        }

        let matches = companies.filter(c => !selected.has(c) && c.toLowerCase().includes(val));
        if (!matches.find(m => m.toLowerCase() === val) && !selected.has(e.target.value)) {
            matches.unshift(e.target.value); // Custom addition
        }

        if (matches.length > 0) {
            list.classList.add('active');
            matches.slice(0, 6).forEach(match => {
                const item = document.createElement('div');
                item.className = 'autocomplete-item';
                item.textContent = match === e.target.value ? `Add "${match}"` : match;
                item.addEventListener('click', () => {
                    selected.add(match === e.target.value ? e.target.value : match);
                    input.value = '';
                    list.classList.remove('active');
                    renderSelected();
                });
                list.appendChild(item);
            });
        }
    });

    document.addEventListener('click', (e) => {
        if (e.target !== input && e.target !== list) {
            list.classList.remove('active');
        }
    });
}
