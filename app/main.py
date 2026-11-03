from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.errors import AppError
from app.routes import auth_routes, event_routes, google_routes, organizer_routes, page_routes, ticket_routes
from app.database import run_migrations

app = FastAPI(title="Vibe Tickets")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth_routes.router)
app.include_router(google_routes.router)
app.include_router(event_routes.router)
app.include_router(ticket_routes.router)
app.include_router(organizer_routes.router)
app.include_router(page_routes.router)

@app.on_event("startup")
def startup_event():
    run_migrations()

@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={"error": exc.message})
