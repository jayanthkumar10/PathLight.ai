# API Documentation

Pathlight exposes a RESTful API powered by FastAPI. 
> Note: For interactive API documentation, run the application and visit `http://localhost:8000/docs` (Swagger UI).

## Core Endpoints

### Health & Status
- **`GET /api/health`**
  - **Description**: Returns the operational status of the API and the configuration status of external AI providers.
  - **Response**: `{"status": "ok", "gemini_configured": true, ...}`

### Tailoring & AI Generation
- **`POST /api/tailor`**
  - **Description**: Starts a background tailoring job based on user parameters.
  - **Request Body**: `TailoringJobCreate` (Target Role, Selected Model, etc.)
  - **Response**: `TailoringJobResponse` (Includes the newly created Job ID for polling).

- **`POST /api/tailor/single`**
  - **Description**: Starts a single tailoring job passing raw Job Description text.

- **`POST /api/extension/tailor`**
  - **Description**: Endpoint used specifically by the Chrome extension to pass scraped job data.

- **`GET /api/tailor/{job_id}`**
  - **Description**: Polls the status of an ongoing tailoring job.

### Applications & Resumes
- **`GET /api/applications`**
  - **Description**: Fetches all generated applications/resumes for the dashboard.

- **`GET /api/applications/{app_id}/download`**
  - **Description**: Returns the generated HTML of a tailored resume for browser preview.

- **`GET /api/applications/{app_id}/pdf`**
  - **Description**: Returns the finalized, downloadable PDF version of the tailored resume.

- **`PATCH /api/applications/{app_id}/status`**
  - **Description**: Updates the pipeline status (e.g., "Applied", "Interviewing", "Rejected").

- **`DELETE /api/applications/{app_id}`**
  - **Description**: Removes the application and deletes the corresponding PDF from disk.

### Master Profile
- **`GET /api/studio/master-profile`**
  - **Description**: Retrieves the user's master profile information.
- **`POST /api/studio/master-profile`**
  - **Description**: Updates the master profile with new work experience or skills.
