from fastapi import APIRouter, Request, Form, HTTPException, responses
from fastapi.responses import HTMLResponse, RedirectResponse
from app.services.auth_service import AuthService
from app.utils import create_session_token
import os

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    # Serve static login page
    login_html_path = os.path.join("app", "static", "login.html")
    if os.path.exists(login_html_path):
        with open(login_html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<html><body><h1>Login</h1><form method='post'><input name='email'/><input type='password' name='password'/><button type='submit'>Sign in</button></form></body></html>"

@router.post("/login")
async def login_action(request: Request, email: str = Form(...), password: str = Form(...)):
    user = AuthService.authenticate(email, password)
    if not user:
        # If request expects json or header
        accept = request.headers.get("accept", "")
        if "application/json" in accept:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return HTMLResponse("<html><body><h1>Invalid email or password</h1><a href='/login'>Try again</a></body></html>", status_code=401)
    
    token = create_session_token(user["id"])
    response = RedirectResponse(url="/events", status_code=303)
    response.set_cookie(
        key="vibe_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False # Set True in production with HTTPS
    )
    return response

@router.post("/logout")
async def logout_action():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="vibe_session")
    return response
