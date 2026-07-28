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

    let title = null;
    let company = null;
    let location = null;

    // STRATEGY A: JSON-LD Structured Data (Most Robust)
    try {
      const ldScripts = document.querySelectorAll('script[type="application/ld+json"]');
      for (let script of ldScripts) {
        const data = JSON.parse(script.textContent);
        if (data && data['@type'] === 'JobPosting') {
          if (data.title) title = data.title;
          if (data.hiringOrganization && data.hiringOrganization.name) company = data.hiringOrganization.name;
          if (data.jobLocation && data.jobLocation.address && data.jobLocation.address.addressLocality) {
            location = data.jobLocation.address.addressLocality;
            if (data.jobLocation.address.addressRegion) location += ', ' + data.jobLocation.address.addressRegion;
          }
          break;
        }
      }
    } catch (e) {}

    // STRATEGY B: Document Title Parsing
    // LinkedIn titles are often: "Software Engineer at Acme Corp | LinkedIn"
    if (!title || !company) {
      try {
        const docTitle = document.title || "";
        const parts = docTitle.split(' at ');
        if (parts.length >= 2) {
          if (!title) title = parts[0].trim();
          const compPart = parts[1].split(' | ')[0];
          if (!company && compPart) company = compPart.trim();
        } else {
            // Alternative: "Acme Corp hiring Software Engineer in New York..."
            const hiringParts = docTitle.split(' hiring ');
            if (hiringParts.length >= 2) {
                if (!company) company = hiringParts[0].trim();
                const titlePart = hiringParts[1].split(' in ')[0];
                if (!title && titlePart) title = titlePart.trim();
            }
        }
      } catch (e) {}
    }

    // Helper to find the active right pane
    function getActivePane() {
        const descEl = document.querySelector('.jobs-description__content, #job-details, .jobs-description__container, [class*="jobs-description"]');
        if (descEl) {
            return descEl.closest('.jobs-search__job-details--wrapper, .job-details-jobs-unified-top-card__container, .jobs-details__main-content, main') || document;
        }
        return document;
    }
    const activePane = getActivePane();

    // STRATEGY C: DOM Selectors (Fallback)
    if (!title) {
      title = getText([
        '.job-details-jobs-unified-top-card__job-title h1',
        '.job-details-jobs-unified-top-card__job-title',
        '.jobs-unified-top-card__job-title h1',
        '.jobs-unified-top-card__job-title',
        'h1[class*="job-title"]',
        'h2[class*="job-title"]'
      ], activePane) || "Unknown Title";
    }

    if (!company) {
      company = getText([
        '.job-details-jobs-unified-top-card__company-name a',
        '.job-details-jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__company-name a',
        '.jobs-unified-top-card__company-name',
        'a[class*="company-name"]'
      ], activePane) || "Unknown Company";
    }

    if (!location) {
      location = getText([
        '.job-details-jobs-unified-top-card__primary-description-container span.tvm__text',
        '.job-details-jobs-unified-top-card__bullet',
        '.jobs-unified-top-card__bullet',
        'span[class*="workplace-type"]',
        'span[class*="bullet"]'
      ], activePane) || "Unknown Location";
    }

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

