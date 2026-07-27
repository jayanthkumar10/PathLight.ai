# Frontend Documentation

The Pathlight.ai frontend is designed to be lightweight, fast, and easy to deploy.

## Structure
All frontend code is located in the `public/` directory at the root of the repository.

- `public/index.html`: The main landing/dashboard page.
- `public/signin.html`: The authentication and onboarding flow.
- `public/css/`: Vanilla CSS stylesheets for styling the application without heavy frameworks.
- `public/js/`: Vanilla JavaScript handling DOM manipulation and API calls.
- `public/assets/`: Images, icons, and static assets.

## How it is Served
The frontend does not require a separate Node.js server (like Next.js or React scripts) to run in production. It is served directly by the FastAPI backend using `StaticFiles`. 

In `backend/main.py`:
```python
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public"))
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))
```

This ensures that the entire stack can be run and deployed as a single cohesive unit, reducing complexity in deployment pipelines.
