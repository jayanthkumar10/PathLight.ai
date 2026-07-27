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
            
            // Premium micro-animation
            helperText.style.display = 'inline-block';
            helperText.style.transform = 'scale(1.05)';
            helperText.style.color = 'var(--accent-primary)';
            helperText.style.transition = 'all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            setTimeout(() => {
                helperText.style.transform = 'scale(1)';
                helperText.style.color = 'inherit';
            }, 200);

            stepperMinus.disabled = (newVal <= MIN_VAL);
            stepperPlus.disabled  = (newVal >= MAX_VAL);
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
        const model      = modelSelect ? modelSelect.value : 'mistral-small-latest';

        const requestData = {
            target_role:    targetRole,
            location:       location,
            posted_within:  timeChip ? timeChip.textContent.trim() : '24H',
            requested_jobs: stepperInput ? parseInt(stepperInput.value, 10) : 10,
            selected_model: model
        };

        // ======================================================
        // Build and inject Immersive AI Processing HUD
        // ======================================================
        const modalHtml = `
            <div id="processing-modal" style="
                position:fixed;top:0;left:0;width:100%;height:100%;
                background:rgba(5, 5, 8, 0.95);backdrop-filter:blur(20px);
                z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;
                font-family:var(--font-ui,'Inter',sans-serif);
                animation: fadeIn 0.5s ease-out;">
              
              <!-- Background Ambient Glows -->
              <div style="position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);width:600px;height:600px;background:radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);pointer-events:none;"></div>
              
              <div style="
                position:relative;
                background:rgba(15, 15, 20, 0.7);padding:3rem;
                border-radius:24px;border:1px solid rgba(255,255,255,0.05);
                box-shadow: 0 24px 64px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05);
                width:520px;max-width:95vw;
                display:flex;flex-direction:column;gap:2rem;">
                
                <!-- HUD Header -->
                <div style="display:flex;flex-direction:column;align-items:center;gap:16px;text-align:center;">
                    <div style="position:relative;width:64px;height:64px;">
                        <div id="modal-spinner" style="
                            position:absolute;top:0;left:0;width:100%;height:100%;
                            border:3px solid rgba(139, 92, 246, 0.1);
                            border-top-color:var(--accent-primary,#7c3aed);
                            border-radius:50%;animation:spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;"></div>
                        <div style="
                            position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);
                            width:32px;height:32px;background:var(--accent-primary);
                            border-radius:50%;filter:blur(8px);opacity:0.5;animation:pulse 2s infinite;"></div>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" style="position:absolute;top:50%;left:50%;transform:translate(-50%, -50%);z-index:2;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path></svg>
                    </div>
                    <div>
                        <h2 id="modal-status" style="font-size:1.5rem;font-weight:600;letter-spacing:-0.02em;margin:0 0 4px;color:#fff;">
                            Initializing AI Engine</h2>
                        <p id="modal-details" style="font-size:0.9375rem;color:var(--text-secondary,#a1a1aa);margin:0;font-family:monospace;">
                            Establishing secure connection...</p>
                    </div>
                </div>

                <!-- Live stats -->
                <div id="modal-stats" style="
                    display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);padding:16px;border-radius:16px;text-align:center;">
                        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#666;margin-bottom:8px;">Scanned</div>
                        <div id="stat-scanned" style="font-size:2rem;font-weight:300;color:var(--text-primary);font-family:monospace;">0</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);padding:16px;border-radius:16px;text-align:center;position:relative;overflow:hidden;">
                        <div style="position:absolute;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,#3b82f6,transparent);opacity:0.5;"></div>
                        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#666;margin-bottom:8px;">Matched</div>
                        <div id="stat-matched" style="font-size:2rem;font-weight:300;color:#3b82f6;font-family:monospace;text-shadow:0 0 16px rgba(59,130,246,0.4);">0</div>
                    </div>
                    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);padding:16px;border-radius:16px;text-align:center;position:relative;overflow:hidden;">
                        <div style="position:absolute;top:0;left:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,#10b981,transparent);opacity:0.5;"></div>
                        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;color:#666;margin-bottom:8px;">Generated</div>
                        <div id="stat-generated" style="font-size:2rem;font-weight:600;color:#10b981;font-family:monospace;text-shadow:0 0 24px rgba(16,185,129,0.5);">0</div>
                    </div>
                </div>

                <!-- Stage progress -->
                <div id="modal-stages" style="
                    background:rgba(0,0,0,0.3);padding:1.5rem;
                    border-radius:16px;border:1px solid rgba(255,255,255,0.03);">
                </div>

                <!-- Done button (hidden until complete) -->
                <button id="modal-done-btn" style="
                    display:none;width:100%;padding:16px;
                    background:linear-gradient(135deg, var(--accent-primary) 0%, #5b21b6 100%);color:#fff;
                    border:none;border-radius:12px;font-size:16px;font-weight:600;
                    cursor:pointer;transition:all 0.3s var(--ease-apple);
                    box-shadow: 0 8px 24px rgba(139,92,246,0.3);">
                    View Applications →
                </button>

                <!-- Error dismiss (hidden) -->
                <button id="modal-error-btn" style="
                    display:none;width:100%;padding:16px;
                    background:rgba(239, 68, 68, 0.1);color:#ef4444;border:1px solid rgba(239,68,68,0.2);border-radius:12px;
                    font-size:16px;font-weight:600;cursor:pointer;">
                    Close
                </button>
              </div>
            </div>
            <style>
                @keyframes spin { to { transform: rotate(360deg); } }
                @keyframes pulse { 0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); } 50% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.5); } }
                @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
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
