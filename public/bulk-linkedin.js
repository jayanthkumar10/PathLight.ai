// ==========================================
// PATHLIGHT — BULK LINKEDIN CONTROLS
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    bindAIWorkspaceControls();
    bindAITailoringFlow();
});

function bindAIWorkspaceControls() {
    // 1. Stepper Logic
    const stepperMinus = document.getElementById('stepper-minus');
    const stepperPlus = document.getElementById('stepper-plus');
    const stepperInput = document.getElementById('stepper-input');
    const helperText = document.getElementById('stepper-helper-text');

    if (stepperMinus && stepperPlus && stepperInput && helperText) {
        const MIN_VAL = 10;
        const MAX_VAL = 100;
        const STEP = 5;

        const updateStepper = (newVal) => {
            if (newVal < MIN_VAL) newVal = MIN_VAL;
            if (newVal > MAX_VAL) newVal = MAX_VAL;
            newVal = Math.round(newVal / STEP) * STEP;
            if (newVal < MIN_VAL) newVal = MIN_VAL;
            if (newVal > MAX_VAL) newVal = MAX_VAL;

            stepperInput.value = newVal;
            helperText.textContent = `${newVal} resumes will be generated`;
            helperText.classList.remove('animate-fade');
            void helperText.offsetHeight;
            helperText.classList.add('animate-fade');

            stepperMinus.disabled = (newVal <= MIN_VAL);
            stepperPlus.disabled  = (newVal >= MAX_VAL);
            stepperMinus.style.opacity = (newVal <= MIN_VAL) ? '0.3' : '1';
            stepperMinus.style.cursor  = (newVal <= MIN_VAL) ? 'not-allowed' : 'pointer';
            stepperPlus.style.opacity  = (newVal >= MAX_VAL) ? '0.3' : '1';
            stepperPlus.style.cursor   = (newVal >= MAX_VAL) ? 'not-allowed' : 'pointer';
        };

        stepperMinus.addEventListener('click', () => {
            let current = parseInt(stepperInput.value, 10) || MIN_VAL;
            updateStepper(current - STEP);
        });
        stepperPlus.addEventListener('click', () => {
            let current = parseInt(stepperInput.value, 10) || MIN_VAL;
            updateStepper(current + STEP);
        });
        stepperInput.addEventListener('change', (e) => {
            let val = parseInt(e.target.value, 10);
            if (isNaN(val)) val = MIN_VAL;
            updateStepper(val);
        });
        stepperInput.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                updateStepper((parseInt(stepperInput.value, 10) || MIN_VAL) + STEP);
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                updateStepper((parseInt(stepperInput.value, 10) || MIN_VAL) - STEP);
            }
        });
        updateStepper(parseInt(stepperInput.value, 10) || MIN_VAL);
    }

    // 2. Chip selection logic
    const timeChips = document.querySelectorAll('.bulk-linkedin-chip');
    timeChips.forEach(chip => {
        chip.addEventListener('click', () => {
            timeChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        });
    });
}

// ==========================================
// STAGE DEFINITIONS
// ==========================================
const PIPELINE_STAGES = [
    { key: 'Preparing',     label: 'Preparing',          detail: 'Loading master resume and configuration...' },
    { key: 'Scraping',      label: 'Scraping Jobs',       detail: 'Searching LinkedIn for matching positions...' },
    { key: 'Filtering',     label: 'Filtering',           detail: 'Applying experience filters...' },
    { key: 'Tailoring',     label: 'Tailoring Resumes',   detail: 'AI is generating ATS-optimized resumes...' },
    { key: 'Evaluating',    label: 'Evaluating',          detail: 'Scoring resumes against ATS criteria...' },
    { key: 'Generating PDF',label: 'Generating PDFs',     detail: 'Rendering final resume documents...' },
    { key: 'Saving',        label: 'Saving',              detail: 'Saving to your Applications page...' },
    { key: 'Completed',     label: 'Completed!',          detail: 'All done. Your resumes are ready.' },
    { key: 'Failed',        label: 'Failed',              detail: 'Something went wrong. Please try again.' },
];

function getStageConfig(status) {
    return PIPELINE_STAGES.find(s => s.key === status) || { label: status, detail: 'Processing...' };
}

function buildProgressBar(currentStatus) {
    const orderedKeys = ['Preparing','Scraping','Filtering','Tailoring','Evaluating','Generating PDF','Saving','Completed'];
    const currentIdx = orderedKeys.indexOf(currentStatus);

    return orderedKeys.map((key, idx) => {
        const isDone    = idx < currentIdx;
        const isActive  = idx === currentIdx;
        const dotColor  = isDone ? '#10b981' : isActive ? 'var(--accent-primary, #7c3aed)' : '#333';
        const textColor = isDone ? '#10b981' : isActive ? '#fff' : '#666';
        const dot       = isDone ? '✓' : (idx + 1).toString();
        return `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                <div style="width:22px;height:22px;border-radius:50%;background:${dotColor};color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;">${dot}</div>
                <span style="font-size:12px;color:${textColor};${isActive ? 'font-weight:600;' : ''}">${getStageConfig(key).label}</span>
            </div>`;
    }).join('');
}

function bindAITailoringFlow() {
    const startBtn = document.getElementById('start-tailoring-btn');
    if (!startBtn) return;

    startBtn.addEventListener('click', async () => {
        // Collect UI values
        const roleInput   = document.getElementById('role-input');
        const locationInput = document.getElementById('location-input');
        const timeChip    = document.querySelector('.bulk-linkedin-chip.active');
        const stepperInput = document.getElementById('stepper-input');
        const modelSelect  = document.getElementById('model-select');

        const targetRole = (roleInput && roleInput.value.trim()) ? roleInput.value.trim() : 'AI Engineer';
        const location   = (locationInput && locationInput.value.trim()) ? locationInput.value.trim() : '';
        const model      = modelSelect ? modelSelect.value : 'gemini-2.5-flash';

        const requestData = {
            target_role:    targetRole,
            location:       location,
            posted_within:  timeChip ? timeChip.textContent.trim() : '24H',
            requested_jobs: stepperInput ? parseInt(stepperInput.value, 10) : 10,
            selected_model: model
        };

        // ======================================================
        // Build and inject Processing Modal
        // ======================================================
        const modalHtml = `
            <div id="processing-modal" style="
                position:fixed;top:0;left:0;width:100%;height:100%;
                background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);
                z-index:9999;display:flex;align-items:center;justify-content:center;
                font-family:var(--font-ui,'Inter',sans-serif);">
              <div style="
                background:var(--bg-surface,#1a1a2e);padding:2.5rem;
                border-radius:16px;border:1px solid var(--border-subtle,#333);
                width:460px;max-width:95vw;">
                <!-- Header -->
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:1.5rem;">
                    <div id="modal-spinner" class="spinner" style="
                        width:36px;height:36px;border:3px solid var(--border-subtle,#333);
                        border-top-color:var(--accent-primary,#7c3aed);
                        border-radius:50%;animation:spin 0.8s linear infinite;flex-shrink:0;"></div>
                    <div>
                        <h2 id="modal-status" style="font-size:1.25rem;font-weight:700;margin:0 0 2px;">
                            Preparing...</h2>
                        <p id="modal-details" style="font-size:12px;color:var(--text-secondary,#888);margin:0;">
                            Connecting to AI Engine</p>
                    </div>
                </div>

                <!-- Stage progress -->
                <div id="modal-stages" style="
                    background:var(--bg-base,#111);padding:1rem;
                    border-radius:8px;margin-bottom:1.25rem;">
                </div>

                <!-- Live stats -->
                <div id="modal-stats" style="
                    display:grid;grid-template-columns:repeat(3,1fr);gap:8px;
                    margin-bottom:1.5rem;">
                    <div style="background:var(--bg-base,#111);padding:10px;border-radius:8px;text-align:center;">
                        <div id="stat-scanned" style="font-size:1.5rem;font-weight:700;color:var(--accent-primary,#7c3aed)">0</div>
                        <div style="font-size:10px;color:#666;margin-top:2px;">Scanned</div>
                    </div>
                    <div style="background:var(--bg-base,#111);padding:10px;border-radius:8px;text-align:center;">
                        <div id="stat-matched" style="font-size:1.5rem;font-weight:700;color:#3b82f6">0</div>
                        <div style="font-size:10px;color:#666;margin-top:2px;">Matched</div>
                    </div>
                    <div style="background:var(--bg-base,#111);padding:10px;border-radius:8px;text-align:center;">
                        <div id="stat-generated" style="font-size:1.5rem;font-weight:700;color:#10b981">0</div>
                        <div style="font-size:10px;color:#666;margin-top:2px;">Generated</div>
                    </div>
                </div>

                <!-- Done button (hidden until complete) -->
                <button id="modal-done-btn" style="
                    display:none;width:100%;padding:12px;
                    background:var(--accent-primary,#7c3aed);color:#fff;
                    border:none;border-radius:8px;font-size:14px;font-weight:600;
                    cursor:pointer;transition:opacity 0.2s;">
                    View Applications →
                </button>

                <!-- Error dismiss (hidden) -->
                <button id="modal-error-btn" style="
                    display:none;width:100%;padding:12px;
                    background:#ef4444;color:#fff;border:none;border-radius:8px;
                    font-size:14px;font-weight:600;cursor:pointer;">
                    Close
                </button>
              </div>
            </div>
            <style>
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>`;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const setStatus = (label, detail) => {
            const el = document.getElementById('modal-status');
            const dl = document.getElementById('modal-details');
            if (el) el.textContent = label;
            if (dl) dl.textContent = detail;
        };

        const setStages = (status) => {
            const el = document.getElementById('modal-stages');
            if (el) el.innerHTML = buildProgressBar(status);
        };

        const setStats = (scanned, matched, generated) => {
            const s = document.getElementById('stat-scanned');
            const m = document.getElementById('stat-matched');
            const g = document.getElementById('stat-generated');
            if (s) s.textContent = scanned;
            if (m) m.textContent = matched;
            if (g) g.textContent = generated;
        };

        setStages('Preparing');

        try {
            // Kick off tailoring job
            const res = await fetch('/api/tailor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!res.ok) {
                const err = await res.text();
                throw new Error(`Server error ${res.status}: ${err}`);
            }

            const data = await res.json();
            const jobId = data.id;

            // Poll for status updates
            let lastGeneratedCount = 0;
            const pollInterval = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/tailor/${jobId}`);
                    const job = await statusRes.json();

                    const stage = getStageConfig(job.status);
                    
                    // Dynamic SlideShow Tracker
                    if (['Tailoring', 'Evaluating', 'Generating PDF'].includes(job.status)) {
                        try {
                            const appRes = await fetch('/api/applications');
                            const apps = await appRes.json();
                            const recentApps = apps.filter(a => a.tailoring_job_id === jobId && a.application_status === 'completed');
                            
                            if (recentApps.length > lastGeneratedCount) {
                                lastGeneratedCount = recentApps.length;
                                const latest = recentApps[0]; // First is newest due to desc sort
                                setStatus('✨ Just Generated!', `${latest.job_title} at ${latest.company}`);
                            } else if (lastGeneratedCount === 0) {
                                setStatus(stage.label, stage.detail);
                            }
                        } catch (e) {
                            setStatus(stage.label, stage.detail);
                        }
                    } else {
                        setStatus(stage.label, stage.detail);
                    }

                    setStages(job.status);
                    setStats(
                        job.scanned_jobs || job.requested_jobs || 0,
                        job.matched_jobs || 0,
                        job.generated_resumes || 0
                    );

                    if (job.status === 'Completed') {
                        clearInterval(pollInterval);
                        const spinner = document.getElementById('modal-spinner');
                        if (spinner) spinner.style.animation = 'none';
                        if (spinner) spinner.style.borderTopColor = '#10b981';

                        setStatus(
                            '✓ Tailoring Complete!',
                            `${job.scanned_jobs || 0} scanned · ${job.matched_jobs || 0} matched · ${job.generated_resumes || 0} resumes generated`
                        );

                        const doneBtn = document.getElementById('modal-done-btn');
                        if (doneBtn) {
                            doneBtn.style.display = 'block';
                            doneBtn.onclick = () => {
                                window.location.href = '/tailored-resumes.html';
                            };
                        }
                    }

                    if (job.status === 'Failed') {
                        clearInterval(pollInterval);
                        const spinner = document.getElementById('modal-spinner');
                        if (spinner) spinner.style.borderTopColor = '#ef4444';
                        if (spinner) spinner.style.animation = 'none';

                        setStatus('Pipeline Failed', 'An error occurred. Check the backend logs.');

                        const errBtn = document.getElementById('modal-error-btn');
                        if (errBtn) {
                            errBtn.style.display = 'block';
                            errBtn.onclick = () => {
                                document.getElementById('processing-modal')?.remove();
                            };
                        }
                    }

                } catch (pollErr) {
                    console.error('Polling error:', pollErr);
                }
            }, 1500);  // Poll every 1.5 seconds

        } catch (error) {
            console.error('Start tailoring error:', error);
            setStatus('Connection Error', `Could not reach backend: ${error.message}`);
            const spinner = document.getElementById('modal-spinner');
            if (spinner) { spinner.style.animation = 'none'; spinner.style.borderTopColor = '#ef4444'; }

            const errBtn = document.getElementById('modal-error-btn');
            if (errBtn) {
                errBtn.style.display = 'block';
                errBtn.onclick = () => document.getElementById('processing-modal')?.remove();
            }
        }
    });
}
