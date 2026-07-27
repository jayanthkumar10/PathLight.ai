function extractJobFromDOM() {
  try {
    const getText = (selectors, root = document) => {
      for (const selector of selectors) {
        const el = root.querySelector(selector);
        if (el && el.textContent.trim()) {
          return el.textContent.trim().replace(/\s+/g, ' ');
        }
      }
      return null;
    };

    // 1. Click "See More" if available to expand description
    try {
      const seeMoreSelectors = [
        'button[aria-label*="Click to see more"]',
        '.jobs-description__footer-button',
        'button.jobs-description-content__button',
        'button[class*="see-more"]'
      ];
      for (const selector of seeMoreSelectors) {
        const btn = document.querySelector(selector);
        if (btn) {
          btn.click();
          break; // Only click the first one we find
        }
      }
    } catch (e) {}

    // Try to find the active job card in the search list as a highly robust fallback
    let cardTitle = null, cardCompany = null, cardLocation = null;
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const currentJobId = urlParams.get('currentJobId');
      if (currentJobId) {
        const card = document.querySelector(`[data-job-id="${currentJobId}"]`) || 
                     document.querySelector(`[data-occludable-job-id="${currentJobId}"]`) ||
                     document.querySelector(`[data-job-id*="${currentJobId}"]`) ||
                     document.querySelector(`[data-occludable-job-id*="${currentJobId}"]`) ||
                     document.querySelector(`[data-entity-urn*="${currentJobId}"]`);
        if (card) {
          const tEl = card.querySelector('.job-card-list__title, .job-card-container__link strong, a[class*="job-card"] strong, [class*="job-title"]');
          if (tEl) cardTitle = tEl.textContent.trim();
          
          const cEl = card.querySelector('.job-card-container__company-name, .job-card-container__primary-description, .artdeco-entity-lockup__subtitle, [class*="company-name"], [class*="subtitle"]');
          if (cEl) {
            cardCompany = cEl.textContent.trim();
          } else {
            const logo = card.querySelector('img[alt]');
            if (logo && logo.alt) cardCompany = logo.alt.replace(/ logo$/i, '').trim();
          }
          
          const lEl = card.querySelector('.job-card-container__metadata-item, [class*="metadata-item"], [class*="location"]');
          if (lEl) cardLocation = lEl.textContent.trim();
        }
      }
    } catch (e) {}

    // Helper to find the active right pane
    function getActivePane() {
        // Find the description container, which is definitely in the right pane
        const descEl = document.querySelector('.jobs-description__content, #job-details, .jobs-description__container, [class*="jobs-description"]');
        if (descEl) {
            // Go up a few levels to get the whole right pane
            return descEl.closest('.jobs-search__job-details--wrapper, .job-details-jobs-unified-top-card__container, .jobs-details__main-content, main') || document;
        }
        return document;
    }
    
    const activePane = getActivePane();

    // 2. Title Extraction
    let title = null;
    
    // First try strict selectors inside the active pane
    const titleSelectors = [
      '.job-details-jobs-unified-top-card__job-title h1',
      '.job-details-jobs-unified-top-card__job-title',
      '.jobs-unified-top-card__job-title h1',
      '.jobs-unified-top-card__job-title',
      'h1[class*="job-title"]',
      'h2[class*="job-title"]',
      'div[class*="job-title"]',
      'h1.t-24',
      'h1',
      'h2'
    ];
    
    for (let sel of titleSelectors) {
        const el = activePane.querySelector(sel);
        if (el && el.textContent.trim().length > 0) {
            title = el.textContent.trim();
            break;
        }
    }
    
    title = title || cardTitle || "Unknown Title";

    // 3. Company Extraction
    let company = null;
    const compSelectors = [
      '.job-details-jobs-unified-top-card__company-name a',
      '.job-details-jobs-unified-top-card__company-name',
      '.jobs-unified-top-card__company-name a',
      '.jobs-unified-top-card__company-name',
      'a[class*="company-name"]',
      'div[class*="company-name"]',
      '.job-details-jobs-unified-top-card__primary-description-container a'
    ];
    
    for (let sel of compSelectors) {
        const el = activePane.querySelector(sel);
        if (el && el.textContent.trim().length > 0) {
            company = el.textContent.trim();
            break;
        }
    }
    
    // Fallback for Company
    if (!company) {
        // Find all links to company pages INSIDE the active pane
        const companyLinks = Array.from(activePane.querySelectorAll('a[href*="/company/"]'))
            .filter(a => a.textContent.trim().length > 0 && a.textContent.trim().length < 60 && !a.textContent.includes('LinkedIn'));
            
        if (companyLinks.length > 0) {
            company = companyLinks[0].textContent.trim();
        } else {
            // Try to find an image with "logo" in alt near the top of the active pane
            const logos = Array.from(activePane.querySelectorAll('img[alt*="logo" i]'));
            if (logos.length > 0) {
                company = logos[0].alt.replace(/ logo$/i, '').trim();
            }
        }
    }
    company = company || cardCompany || "Unknown Company";

    // 4. Location Extraction
    let location = getText([
      '.job-details-jobs-unified-top-card__primary-description-container span.tvm__text',
      '.job-details-jobs-unified-top-card__bullet',
      '.jobs-unified-top-card__bullet',
      'span[class*="workplace-type"]',
      'span[class*="bullet"]',
      '[class*="metadata-item"]',
      '[class*="location"]'
    ]) || cardLocation || "Unknown Location";

    // 5. Highly Robust Description Extraction (Heuristic based)
    let descriptionText = "";
    
    // First try standard selectors
    descriptionText = getText([
      '#job-details',
      '.jobs-description-content__text',
      '.jobs-description__container',
      '.jobs-description__content .jobs-box__html-content',
      '[class*="jobs-description"]'
    ]);

    // If standard selectors fail, use structural text-density heuristic
    if (!descriptionText) {
      let bestEl = null;
      let bestLen = 0;
      
      // Look for the block element with the most text that doesn't contain other major blocks
      const candidates = document.querySelectorAll('article, section, div');
      for (const el of candidates) {
        if (['NAV', 'HEADER', 'FOOTER'].includes(el.tagName)) continue;
        if (el.querySelector('nav, header, footer')) continue;
        
        const len = (el.textContent || '').trim().length;
        const childBlocks = el.querySelectorAll('article, section').length;
        
        if (len > bestLen && len < 50000 && childBlocks === 0) {
          bestLen = len;
          bestEl = el;
        }
      }
      
      if (bestEl) {
        descriptionText = bestEl.textContent.trim().replace(/\s+/g, ' ');
      }
    }

    // 6. Validation and Detailed Error Reporting
    if (title === "Unknown Title" && !descriptionText) {
      return { error: "V3_ERROR: Extractor could not find any job details. Ensure a job is selected. If LinkedIn updated its UI, please report this bug." };
    }
    if (!descriptionText) {
       return { error: "V3_ERROR: Title found (" + title + "), but Description is missing. It might not be loaded yet." };
    }

    return {
      title,
      company,
      location,
      url: window.location.href.split('?')[0],
      descriptionText,
      employmentType: "Full-time"
    };

  } catch (globalError) {
    return { error: "Fatal V3 parsing error: " + globalError.toString() };
  }
}

// Production-grade auto-apply injector
function triggerAutoApplyDOM() {
  const applyBtn = document.querySelector('.jobs-apply-button--top-card button');
  if (applyBtn) {
    applyBtn.click();
    return { status: "Auto-apply process started" };
  } else {
    return { status: "Easy Apply button not found" };
  }
}

document.getElementById('scrapeBtn').addEventListener('click', async () => {
  const mainActions = document.getElementById('main-actions');
  const loadingContainer = document.getElementById('loading-container');
  const resultActions = document.getElementById('result-actions');
  const statusEl = document.getElementById('status');
  
  mainActions.classList.add('hidden');
  loadingContainer.classList.remove('hidden');
  resultActions.classList.add('hidden');
  statusEl.innerText = "Extracting job details...";
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab.url.includes("linkedin.com/jobs")) {
    statusEl.innerText = "Please navigate to a LinkedIn job post.";
    loadingContainer.classList.add('hidden');
    mainActions.classList.remove('hidden');
    return;
  }
  
  // Use scripting API to inject the code dynamically (prevents "Receiving end does not exist" errors)
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: extractJobFromDOM,
  }, (results) => {
    if (chrome.runtime.lastError || !results || !results[0]) {
      statusEl.innerText = "Injection error. Please refresh the page.";
      loadingContainer.classList.add('hidden');
      mainActions.classList.remove('hidden');
      return;
    }
    
    const response = results[0].result;
    
    if (response.error) {
      statusEl.innerText = response.error;
      loadingContainer.classList.add('hidden');
      mainActions.classList.remove('hidden');
      return;
    }
    
    statusEl.innerText = "Sending to Pathlight.ai...";
    
    // Send to background script for API request
    chrome.runtime.sendMessage({ action: "SEND_TO_BACKEND", payload: response }, (bgResponse) => {
      if (bgResponse && bgResponse.success) {
        statusEl.innerText = "Tailoring your ATS-optimized resume...";
        
        const jobId = bgResponse.data.id;
        
        // Poll for completion
        const pollInterval = setInterval(async () => {
          try {
            const res = await fetch(`http://localhost:8000/api/tailor/${jobId}`);
            if (res.ok) {
              const jobData = await res.json();
              
              if (jobData.status.toLowerCase() === 'completed') {
                clearInterval(pollInterval);
                loadingContainer.classList.add('hidden');
                resultActions.classList.remove('hidden');
                
                if (jobData.applications && jobData.applications.length > 0) {
                  const appId = jobData.applications[0].id;
                  
                  document.getElementById('downloadBtn').onclick = () => {
                    window.open(`http://localhost:8000/api/applications/${appId}/pdf`, '_blank');
                  };
                } else {
                  document.getElementById('downloadBtn').disabled = true;
                  document.getElementById('downloadBtn').innerText = 'PDF Not Available';
                }
                
                document.getElementById('dashboardBtn').onclick = () => {
                  window.open('http://localhost:8000/tailored-resumes.html', '_blank');
                };
              } else if (jobData.status.toLowerCase() === 'failed') {
                clearInterval(pollInterval);
                statusEl.innerText = "Tailoring failed.";
                loadingContainer.classList.add('hidden');
                mainActions.classList.remove('hidden');
              }
            }
          } catch (e) {
            console.error("Polling error", e);
          }
        }, 2000);
      } else {
        statusEl.innerText = "Error: " + (bgResponse ? bgResponse.error : "Failed to contact backend.");
        loadingContainer.classList.add('hidden');
        mainActions.classList.remove('hidden');
      }
    });
  });
});

document.getElementById('applyBtn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: triggerAutoApplyDOM,
  }, (results) => {
    if (chrome.runtime.lastError || !results || !results[0]) {
      statusEl.innerText = "Error communicating with page.";
      return;
    }
    statusEl.innerText = results[0].result.status;
  });
});
