// ==========================================
// RESUME STUDIO - DYNAMIC FORM BUILDER
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initResumeStudio();
    bindGlobalNavigation();
});

function bindGlobalNavigation() {
    // Sidebar toggle
    const sidebarToggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Mobile menu toggle
    const mobileMenuBtn = document.getElementById('mobile-menu-toggle');
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // Profile menu toggle
    const profileTrigger = document.getElementById('profile-menu-trigger');
    if (profileTrigger) {
        profileTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            profileTrigger.classList.toggle('active');
        });
        document.addEventListener('click', () => {
            profileTrigger.classList.remove('active');
        });
    }
}

function initResumeStudio() {
    // Buttons
    const addExperienceBtn = document.getElementById('add-experience-btn');
    const addProjectBtn = document.getElementById('add-project-btn');
    const addEducationBtn = document.getElementById('add-education-btn');
    const saveBtn = document.getElementById('save-resume-btn');

    // Container Lists
    const expList = document.getElementById('experience-list');
    const projectList = document.getElementById('project-list');
    const eduList = document.getElementById('education-list');

    // Event Listeners for Adding Sections
    addExperienceBtn.addEventListener('click', () => {
        expList.appendChild(createExperienceItem());
    });

    addProjectBtn.addEventListener('click', () => {
        projectList.appendChild(createProjectItem());
    });

    addEducationBtn.addEventListener('click', () => {
        eduList.appendChild(createEducationItem());
    });

    const addAchievementBtn = document.getElementById('add-achievement-btn');
    const achievementList = document.getElementById('achievement-list');
    
    if(addAchievementBtn) {
        addAchievementBtn.addEventListener('click', (e) => {
            e.preventDefault();
            achievementList.appendChild(createAchievementItem());
        });
    }


    // API Save Functionality
    saveBtn.addEventListener('click', async () => {
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = `<div class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;margin-right:8px;vertical-align:middle;"></div> Saving...`;
        saveBtn.disabled = true;

        const payload = scrapeFormData();

        try {
            const token = localStorage.getItem('pathlight_token');
            const res = await fetch('/api/studio', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if(res.ok) {
                saveBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:inline-block;margin-right:8px;vertical-align:middle;"><polyline points="20 6 9 17 4 12"></polyline></svg> Saved!`;
                saveBtn.classList.replace('btn-primary', 'btn-success');
                
                setTimeout(() => {
                    saveBtn.innerHTML = originalText;
                    saveBtn.classList.replace('btn-success', 'btn-primary');
                    saveBtn.disabled = false;
                }, 2000);
            } else {
                throw new Error("Failed to save");
            }
        } catch(err) {
            console.error(err);
            saveBtn.innerHTML = `Error`;
            saveBtn.classList.replace('btn-primary', 'btn-danger');
            setTimeout(() => {
                saveBtn.innerHTML = originalText;
                saveBtn.classList.replace('btn-danger', 'btn-primary');
                saveBtn.disabled = false;
            }, 2000);
        }
    });

    // Load Data from API
    fetchStudioData();
}

// ----------------------------------------------------
// Data Scraper
// ----------------------------------------------------
function scrapeFormData() {
    const contactInfo = {
        name: document.getElementById('rs-name').value,
        email: document.getElementById('rs-email').value,
        phone: document.getElementById('rs-phone').value,
        location: document.getElementById('rs-location').value,
        linkedin: document.getElementById('rs-linkedin').value,
        github: document.getElementById('rs-github').value,
        portfolio: document.getElementById('rs-portfolio').value,
        summary: document.getElementById('rs-summary').value
    };

    const targetTitles = [
        document.getElementById('rs-subtitle-1').value,
        document.getElementById('rs-subtitle-2').value,
        document.getElementById('rs-subtitle-3').value
    ].filter(v => v.trim() !== "");

    const workExperience = [];
    document.querySelectorAll('#experience-list .dynamic-item').forEach(item => {
        const inputs = item.querySelectorAll('input');
        const textareas = item.querySelectorAll('textarea');
        const bullets = Array.from(textareas).map(ta => ta.value).filter(v => v.trim() !== "");
        workExperience.push({
            title: inputs[0].value,
            company: inputs[1].value,
            date: inputs[2].value,
            bullets: bullets
        });
    });

    const projects = [];
    document.querySelectorAll('#project-list .dynamic-item').forEach(item => {
        const inputs = item.querySelectorAll('input');
        const textareas = item.querySelectorAll('textarea');
        const bullets = Array.from(textareas).map(ta => ta.value).filter(v => v.trim() !== "");
        projects.push({
            name: inputs[0].value,
            tech: inputs[1].value,
            link: inputs[2].value,
            bullets: bullets
        });
    });

    const education = [];
    document.querySelectorAll('#education-list .dynamic-item').forEach(item => {
        const inputs = item.querySelectorAll('input');
        education.push({
            degree: inputs[0].value,
            school: inputs[1].value,
            date: inputs[2].value,
            cgpa: inputs[3] ? inputs[3].value : ""
        });
    });

    const achievements = [];
    document.querySelectorAll('#achievement-list .dynamic-item').forEach(item => {
        const inputs = item.querySelectorAll('input');
        const textarea = item.querySelector('textarea');
        achievements.push({
            title: inputs[0].value,
            date: inputs[1].value,
            description: textarea.value
        });
    });

    const skills = {
        hard_skills: document.getElementById('rs-hard-skills').value,
        soft_skills: document.getElementById('rs-soft-skills').value
    };

    return {
        contactInfo, targetTitles, workExperience, projects, education, achievements, skills
    };
}

// ----------------------------------------------------
// UI Element Creators
// ----------------------------------------------------

function createExperienceItem(data = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item';
    
    // Fallback data
    const title = data.title || '';
    const company = data.company || '';
    const date = data.date || '';
    const bullets = data.bullets || [''];

    div.innerHTML = `
        <div class="item-header">
            <div class="item-title">Experience Role</div>
            <button class="remove-btn" title="Remove Role">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <div class="form-grid">
            <div class="form-group">
                <label>Job Title</label>
                <input type="text" placeholder="e.g. Senior Software Engineer" value="${title}">
            </div>
            <div class="form-group">
                <label>Company</label>
                <input type="text" placeholder="e.g. Acme Corp" value="${company}">
            </div>
            <div class="form-group">
                <label>Dates</label>
                <input type="text" placeholder="e.g. Jan 2020 - Present" value="${date}">
            </div>
        </div>
        <div class="form-group mt-md">
            <label>Accomplishment Bullets</label>
            <div class="bullet-list">
                <!-- Bullets injected dynamically -->
            </div>
            <button class="btn btn-secondary btn-sm add-bullet-btn mt-sm">+ Add Bullet</button>
        </div>
    `;

    // Remove functionality
    div.querySelector('.remove-btn').addEventListener('click', () => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        setTimeout(() => div.remove(), 200);
    });

    // Bullets functionality
    const bulletList = div.querySelector('.bullet-list');
    const addBulletBtn = div.querySelector('.add-bullet-btn');
    
    bullets.forEach(b => bulletList.appendChild(createBulletItem(b)));
    
    addBulletBtn.addEventListener('click', () => {
        bulletList.appendChild(createBulletItem(''));
    });

    return div;
}

function createProjectItem(data = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item';
    
    const name = data.name || '';
    const tech = data.tech || '';
    const link = data.link || '';
    const bullets = data.bullets || [''];

    div.innerHTML = `
        <div class="item-header">
            <div class="item-title">Project</div>
            <button class="remove-btn" title="Remove Project">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <div class="form-grid">
            <div class="form-group">
                <label>Project Name</label>
                <input type="text" placeholder="e.g. AI Resume Builder" value="${name}">
            </div>
            <div class="form-group">
                <label>Technologies Used</label>
                <input type="text" placeholder="e.g. React, Node.js, OpenAI" value="${tech}">
            </div>
            <div class="form-group">
                <label>Link (Optional)</label>
                <input type="url" placeholder="e.g. github.com/project" value="${link}">
            </div>
        </div>
        <div class="form-group mt-md">
            <label>Project Details / Bullets</label>
            <div class="bullet-list">
                <!-- Bullets injected dynamically -->
            </div>
            <button class="btn btn-secondary btn-sm add-bullet-btn mt-sm">+ Add Bullet</button>
        </div>
    `;

    div.querySelector('.remove-btn').addEventListener('click', () => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        setTimeout(() => div.remove(), 200);
    });

    const bulletList = div.querySelector('.bullet-list');
    const addBulletBtn = div.querySelector('.add-bullet-btn');
    
    bullets.forEach(b => bulletList.appendChild(createBulletItem(b)));
    
    addBulletBtn.addEventListener('click', () => {
        bulletList.appendChild(createBulletItem(''));
    });

    return div;
}

function createEducationItem(data = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item';
    
    const degree = data.degree || '';
    const school = data.school || '';
    const date = data.date || '';

    div.innerHTML = `
        <div class="item-header">
            <div class="item-title">Education</div>
            <button class="remove-btn" title="Remove Education">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <div class="form-grid">
            <div class="form-group">
                <label>Degree</label>
                <input type="text" placeholder="e.g. B.S. Computer Science" value="${degree}">
            </div>
            <div class="form-group">
                <label>University / School</label>
                <input type="text" placeholder="e.g. Stanford University" value="${school}">
            </div>
            <div class="form-group">
                <label>Dates</label>
                <input type="text" placeholder="e.g. 2018 - 2022" value="${date}">
            </div>
            <div class="form-group">
                <label>CGPA</label>
                <input type="text" placeholder="e.g. 3.8 / 4.0" value="${data.cgpa || ''}">
            </div>
        </div>
    `;

    div.querySelector('.remove-btn').addEventListener('click', () => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        setTimeout(() => div.remove(), 200);
    });

    return div;
}

function createAchievementItem(data = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item';
    
    const title = data.title || '';
    const date = data.date || '';
    const description = data.description || '';

    div.innerHTML = `
        <div class="item-header">
            <div class="item-title">Achievement / Award</div>
            <button type="button" class="remove-btn" title="Remove Achievement">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <div class="form-grid">
            <div class="form-group">
                <label>Title</label>
                <input type="text" placeholder="e.g. Published Patent" value="${title}">
            </div>
            <div class="form-group">
                <label>Date (Optional)</label>
                <input type="text" placeholder="e.g. 2023" value="${date}">
            </div>
        </div>
        <div class="form-group mt-md">
            <label>Description</label>
            <textarea rows="3" placeholder="Describe the achievement...">${description}</textarea>
        </div>
    `;

    div.querySelector('.remove-btn').addEventListener('click', () => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-10px)';
        setTimeout(() => div.remove(), 200);
    });

    return div;
}


function createBulletItem(content = '') {
    const div = document.createElement('div');
    div.className = 'bullet-item';
    
    div.innerHTML = `
        <textarea placeholder="Describe your accomplishment...">${content}</textarea>
        <button class="remove-btn" title="Remove Bullet">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;

    div.querySelector('.remove-btn').addEventListener('click', () => {
        div.remove();
    });

    return div;
}

// ----------------------------------------------------
// Mock Data Loader
// ----------------------------------------------------

function loadMockData() {
    document.getElementById('rs-name').value = "Jayanth Kumar Pillajetti";
    document.getElementById('rs-email').value = "pillajettijayanth@gmail.com";
    document.getElementById('rs-phone').value = "+91 9133985109";
    document.getElementById('rs-location').value = "India";
    document.getElementById('rs-linkedin').value = "linkedin.com/in/jayanth";
    document.getElementById('rs-github').value = "github.com/jayanth";
    document.getElementById('rs-portfolio').value = "jayanthkumar10.github.io";

    document.getElementById('rs-subtitle-1').value = "AI Engineer";
    document.getElementById('rs-subtitle-2').value = "AI Automation";
    document.getElementById('rs-subtitle-3').value = "Agentic AI";
    
    document.getElementById('rs-summary').value = "Dedicated AI Engineer with a strong background in developing Agentic AI solutions and scalable automation pipelines.";

    const expList = document.getElementById('experience-list');
    expList.appendChild(createExperienceItem({
        title: "AI Engineer",
        company: "Tech Innovators",
        date: "2023 - Present",
        bullets: [
            "Architected and deployed multi-agent LLM systems reducing manual support tickets by 40%.",
            "Built a retrieval-augmented generation (RAG) pipeline to query 10,000+ company documents in real-time."
        ]
    }));

    const projectList = document.getElementById('project-list');
    projectList.appendChild(createProjectItem({
        name: "Pathlight.ai",
        tech: "Python, FastAPI, Postgres, React",
        link: "github.com/jayanth/pathlight",
        bullets: [
            "Developed an AI-powered resume tailoring platform handling end-to-end job application pipelines.",
            "Integrated Celery and Redis to handle asynchronous Web Scraping and LLM generation."
        ]
    }));

    const eduList = document.getElementById('education-list');
    eduList.appendChild(createEducationItem({
        degree: "Bachelor of Technology",
        school: "Example University",
        date: "2019 - 2023",
        cgpa: "3.9 / 4.0"
    }));

    const achievementList = document.getElementById('achievement-list');
    if(achievementList) {
        achievementList.appendChild(createAchievementItem({
            title: "Published Patent: 'System and Method for Heart Disease Prediction'",
            date: "2023",
            description: "Engineered a unified dataset by merging multiple clinical data sources..."
        }));
    }

    document.getElementById('rs-hard-skills').value = "Python, SQL, RESTful APIs, Git, Generative AI, Large Language Models (LLMs), Agentic AI, Multi-Agent Systems";

    document.getElementById('rs-soft-skills').value = "Problem-solving, Attention to Detail, Communication";
}

async function fetchStudioData() {
    try {
        const token = localStorage.getItem('pathlight_token');
        const res = await fetch('/api/studio', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await res.json();
        
        if (data.status === 'none') {
            loadMockData();
            return;
        }
        
        const profile = data.profile;
        
        // Populate Contact
        document.getElementById('rs-name').value = profile.contactInfo?.name || "";
        document.getElementById('rs-email').value = profile.contactInfo?.email || "";
        document.getElementById('rs-phone').value = profile.contactInfo?.phone || "";
        document.getElementById('rs-location').value = profile.contactInfo?.location || "";
        document.getElementById('rs-linkedin').value = profile.contactInfo?.linkedin || "";
        document.getElementById('rs-github').value = profile.contactInfo?.github || "";
        document.getElementById('rs-portfolio').value = profile.contactInfo?.portfolio || "";
        document.getElementById('rs-summary').value = profile.contactInfo?.summary || "";
        
        // Populate Titles
        if (profile.targetTitles) {
            document.getElementById('rs-subtitle-1').value = profile.targetTitles[0] || "";
            document.getElementById('rs-subtitle-2').value = profile.targetTitles[1] || "";
            document.getElementById('rs-subtitle-3').value = profile.targetTitles[2] || "";
        }
        
        // Populate Experience
        const expList = document.getElementById('experience-list');
        expList.innerHTML = '';
        if (profile.workExperience && profile.workExperience.length > 0) {
            profile.workExperience.forEach(exp => expList.appendChild(createExperienceItem(exp)));
        }
        
        // Populate Projects
        const projectList = document.getElementById('project-list');
        projectList.innerHTML = '';
        if (profile.projects && profile.projects.length > 0) {
            profile.projects.forEach(proj => projectList.appendChild(createProjectItem(proj)));
        }
        
        // Populate Education
        const eduList = document.getElementById('education-list');
        eduList.innerHTML = '';
        if (profile.education && profile.education.length > 0) {
            profile.education.forEach(edu => eduList.appendChild(createEducationItem(edu)));
        }
        
        // Populate Achievements
        const achievementList = document.getElementById('achievement-list');
        if (achievementList) {
            achievementList.innerHTML = '';
            if (profile.achievements && profile.achievements.length > 0) {
                profile.achievements.forEach(ach => achievementList.appendChild(createAchievementItem(ach)));
            }
        }
        
        // Populate Skills
        document.getElementById('rs-hard-skills').value = profile.skills?.hard_skills || "";
        document.getElementById('rs-soft-skills').value = profile.skills?.soft_skills || "";

    } catch(err) {
        console.error("Failed to fetch studio data:", err);
        loadMockData();
    }
}
