document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const jdInput = document.getElementById('jd-input');
    const jobUrlInput = document.getElementById('job-url-input');
    
    // UI Validation
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            if (!jdInput.value.trim()) {
                alert("Please paste the Job Description to tailor your resume.");
                jdInput.focus();
                return;
            }

            const jdText = jdInput.value.trim();
            const jobUrl = jobUrlInput ? jobUrlInput.value.trim() : "";
            
            // Get model from hidden input
            const modelSelect = document.getElementById('model-select');
            const model = modelSelect ? modelSelect.value : 'gemini-2.5-flash';

            const requestData = {
                job_description: jdText,
                job_url: jobUrl,
                selected_model: model
            };

            // Setup loading state on button
            const originalText = generateBtn.innerHTML;
            generateBtn.disabled = true;
            generateBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px;animation:spin 1s linear infinite;">
                    <line x1="12" y1="2" x2="12" y2="6"></line>
                    <line x1="12" y1="18" x2="12" y2="22"></line>
                    <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
                    <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
                    <line x1="2" y1="12" x2="6" y2="12"></line>
                    <line x1="18" y1="12" x2="22" y2="12"></line>
                    <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
                    <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
                </svg>
                Initializing Engine...
            `;
            generateBtn.style.opacity = '0.8';

            // Inject the dynamic animated modal
            const getStageConfig = (status) => {
                const s = (status || '').toLowerCase();
                if (s === 'preparing') return { idx: 0, label: 'Warming up Engine', detail: 'Connecting to Pathlight AI' };
                if (s === 'extracting details') return { idx: 1, label: 'Reading Job Description', detail: 'Extracting Title & Company' };
                if (s === 'tailoring') return { idx: 2, label: 'Tailoring Resume', detail: 'Aligning experiences to Job Description' };
                if (s === 'evaluating') return { idx: 3, label: 'ATS Evaluation', detail: 'Running match scoring algorithms' };
                if (s === 'generating pdf') return { idx: 4, label: 'Generating PDF', detail: 'Formatting professional resume' };
                if (s === 'completed') return { idx: 5, label: '✓ Tailoring Complete!', detail: 'Successfully generated your resume' };
                if (s === 'failed') return { idx: 5, label: '✗ Failed', detail: 'Something went wrong' };
                return { idx: 0, label: 'Processing', detail: '...' };
            };

            const buildProgressBar = (status) => {
                const conf = getStageConfig(status);
                const steps = ['Preparing', 'Extracting', 'Tailoring', 'Evaluating', 'PDF'];
                return `
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;position:relative;">
                        <div style="position:absolute;top:50%;left:0;right:0;height:2px;background:var(--border-subtle,#333);z-index:0;"></div>
                        ${steps.map((step, i) => {
                            const isPast = i < conf.idx;
                            const isCurr = i === conf.idx;
                            let bg = 'var(--bg-base,#111)';
                            let border = 'var(--border-subtle,#333)';
                            let color = 'var(--text-secondary,#888)';
                            if (isPast || isCurr) border = 'var(--accent-primary,#7c3aed)';
                            if (isPast) bg = 'var(--accent-primary,#7c3aed)';
                            if (isCurr) { bg = '#111'; color = '#fff'; }
                            
                            return `
                            <div style="position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:4px;">
                                <div style="width:16px;height:16px;border-radius:50%;background:${bg};border:2px solid ${border};transition:all 0.3s;"></div>
                                <span style="font-size:10px;color:${color};font-weight:${isCurr ? '600' : '400'};position:absolute;top:20px;white-space:nowrap;">
                                    ${step}
                                </span>
                            </div>`;
                        }).join('')}
                    </div>
                `;
            };

            const modalHtml = `
            <div id="dynamic-progress-modal" style="
                position:fixed;top:0;left:0;right:0;bottom:0;
                background:rgba(0,0,0,0.8);backdrop-filter:blur(4px);
                z-index:9999;display:flex;align-items:center;justify-content:center;
                font-family:'Inter',sans-serif;">
              <div style="
                background:var(--bg-elevated,#1e1e1e);padding:24px;
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
                    border-radius:8px;margin-bottom:2.5rem;">
                </div>

                <!-- Action Buttons (hidden until complete) -->
                <div id="modal-actions-container" style="display:none; flex-direction:column; gap:10px;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                        <button id="modal-view-btn" style="
                            padding:12px;
                            background:var(--bg-base,#111);color:#fff;border:1px solid var(--border-subtle,#333);
                            border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:background 0.2s;">
                            📄 View PDF
                        </button>
                        <button id="modal-download-btn" style="
                            padding:12px;
                            background:var(--bg-base,#111);color:#fff;border:1px solid var(--border-subtle,#333);
                            border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:background 0.2s;">
                            ⬇️ Download PDF
                        </button>
                    </div>
                    <button id="modal-apps-btn" style="
                        width:100%;padding:12px;
                        background:var(--accent-primary,#7c3aed);color:#fff;border:none;
                        border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity 0.2s;">
                        Go to Applications Dashboard →
                    </button>
                </div>

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
                #modal-view-btn:hover, #modal-download-btn:hover { background: var(--border-subtle, #333) !important; }
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

            setStages('Preparing');

            try {
                const res = await fetch('/api/tailor/single', {
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

                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`/api/tailor/${jobId}`);
                        const job = await statusRes.json();

                        const stage = getStageConfig(job.status);
                        setStatus(stage.label, stage.detail);
                        setStages(job.status);

                        if (job.status === 'Completed') {
                            clearInterval(pollInterval);
                            const spinner = document.getElementById('modal-spinner');
                            if (spinner) spinner.style.animation = 'none';
                            if (spinner) spinner.style.borderTopColor = '#10b981';

                            let pdfPath = '';
                            try {
                                const appRes = await fetch('/api/applications');
                                const apps = await appRes.json();
                                const recentApps = apps.filter(a => a.tailoring_job_id === jobId && a.application_status === 'completed');
                                if (recentApps.length > 0) {
                                    pdfPath = recentApps[0].generated_resume_path;
                                }
                            } catch (e) {
                                console.error("Could not fetch application link", e);
                            }

                            document.getElementById('modal-actions-container').style.display = 'flex';
                            
                            const viewBtn = document.getElementById('modal-view-btn');
                            const downloadBtn = document.getElementById('modal-download-btn');
                            const appsBtn = document.getElementById('modal-apps-btn');

                            viewBtn.addEventListener('click', () => {
                                if (pdfPath) window.open(`/api/resumes/download/${pdfPath.split('/').pop()}`, '_blank');
                                else alert('PDF not found.');
                            });

                            downloadBtn.addEventListener('click', () => {
                                if (pdfPath) {
                                    const a = document.createElement('a');
                                    a.href = `/api/resumes/download/${pdfPath.split('/').pop()}`;
                                    a.download = pdfPath.split('/').pop();
                                    a.click();
                                } else alert('PDF not found.');
                            });

                            appsBtn.addEventListener('click', () => {
                                window.location.href = '/tailored-resumes.html';
                            });

                            generateBtn.disabled = false;
                            generateBtn.innerHTML = originalText;
                        } else if (job.status === 'Failed') {
                            clearInterval(pollInterval);
                            const spinner = document.getElementById('modal-spinner');
                            if (spinner) spinner.style.animation = 'none';
                            if (spinner) spinner.style.borderTopColor = '#ef4444';
                            
                            document.getElementById('modal-error-btn').style.display = 'block';
                            generateBtn.disabled = false;
                            generateBtn.innerHTML = originalText;
                        }
                    } catch (pollErr) {
                        console.error('Polling error:', pollErr);
                    }
                }, 2000);

                document.getElementById('modal-error-btn').addEventListener('click', () => {
                    document.getElementById('dynamic-progress-modal').remove();
                });

            } catch (err) {
                setStatus('✗ Error', err.message);
                const spinner = document.getElementById('modal-spinner');
                if (spinner) spinner.style.animation = 'none';
                if (spinner) spinner.style.borderTopColor = '#ef4444';
                document.getElementById('modal-error-btn').style.display = 'block';
                document.getElementById('modal-error-btn').addEventListener('click', () => {
                    document.getElementById('dynamic-progress-modal').remove();
                });
                generateBtn.disabled = false;
                generateBtn.innerHTML = originalText;
            }
        });
    }
});
