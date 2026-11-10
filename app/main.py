import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.errors import AppError
from app.routes import auth_routes, event_routes, google_routes, organizer_routes, page_routes, ticket_routes
from app.database import ping, run_migrations

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


@app.get("/health")
def health():
    try:
        ping()
    except Exception:
        logging.exception("health check: database is down")
        return JSONResponse(status_code=503, content={"status": "error", "db": "down"})
    return {"status": "ok", "db": "ok"}


@app.exception_handler(StarletteHTTPException)
def http_error_handler(request: Request, exc: StarletteHTTPException):
    message = "Page not found" if exc.status_code == 404 else str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": message})


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    if any(e["type"] == "json_invalid" for e in exc.errors()):
        return JSONResponse(status_code=400, content={"error": "The request body is not valid JSON"})
    return JSONResponse(status_code=422, content={"error": "Some of the data sent is missing or not valid"})


@app.exception_handler(Exception)
def unexpected_error_handler(request: Request, exc: Exception):
    logging.exception("unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"error": "Something went wrong on our side. Please try again."})
