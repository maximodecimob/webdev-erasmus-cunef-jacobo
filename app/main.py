from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routes import auth_routes, event_routes
from app.database import run_migrations

app = FastAPI(title="Vibe Tickets")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_routes.router)
app.include_router(event_routes.router)

@app.on_event("startup")
def startup_event():
    run_migrations()

@app.get("/")
def root():
    return RedirectResponse(url="/events", status_code=303)
