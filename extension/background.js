chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "SEND_TO_BACKEND") {
    const jobPayload = request.payload;
    
    // Send to local backend server
    fetch("http://localhost:8000/api/extension/tailor", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(jobPayload)
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ success: true, data: data });
    })
    .catch(error => {
      sendResponse({ success: false, error: error.toString() });
    });
    
    return true; // Keep the message channel open for async fetch
  }
});
