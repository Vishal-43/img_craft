from typing import Union
import re
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

# Assuming the corrected database class is in database.py
# Import the new PasswordManager

# --- Configuration and Initialization ---

SECRET_KEY = "@tuzi$layki$nahi$bhava@" # Replace with a strong, randomly generated key in production
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$")
STRONG_PASSWORD_MESSAGE = "Password must be at least 8 characters long and include one uppercase letter, one lowercase letter, one number, and one special character."

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
# Assuming 'static' directory exists in the same location as your website.py
app.mount("/static", StaticFiles(directory="static"), name="static")

# Assuming 'templates' directory exists in the same location as your website.py
templates = Jinja2Templates(directory="templates")


# --- Helper Functions and Dependencies ---

def is_strong_password(password: str) -> bool:
    """Validates the strength of a given password."""
    return bool(PASSWORD_REGEX.match(password))

def get_session_email(request: Request, key: str = "unverified_email") -> str:
    """Dependency to get a required email from the session."""
    email = request.session.get(key)
    if not email:
        # Redirect to signup if the session is invalid or has expired
        raise HTTPException(status_code=HTTP_303_SEE_OTHER, detail="Session expired.", headers={"Location": "/signup"})
    return email

def get_current_user(request: Request) -> dict:
    """Dependency to get the current authenticated user from the session."""
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=HTTP_303_SEE_OTHER, detail="Not authenticated.", headers={"Location": "/login"})
    return user

# --- Route Handlers ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Renders the root page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
def get_signup(request: Request):
    """Renders the signup page."""
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def post_signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handles new user registration."""
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match."})
    
    if not is_strong_password(password):
        return templates.TemplateResponse("signup.html", {"request": request, "error": STRONG_PASSWORD_MESSAGE})

    is_success, message = db.create_user(username=username, email=email, password=password)
    
    if not is_success:
        return templates.TemplateResponse("signup.html", {"request": request, "error": message})

    verification_code = sendmail.send_verification_code(email=email)
    request.session['verification_code'] = verification_code
    request.session['unverified_email'] = email
    
    return RedirectResponse(url="/verify", status_code=HTTP_303_SEE_OTHER)

@app.get("/verify", response_class=HTMLResponse)
def get_verification_page(request: Request, email: str = Depends(get_session_email)):
    """Renders the email verification page."""
    return templates.TemplateResponse("verify.html", {"request": request, "email": email})

@app.post("/verify")
async def post_verification(
    request: Request,
    code: str = Form(...),
    email: str = Depends(get_session_email)
):
    """Handles email verification code submission."""
    status = db.check_verification_status(email=email)
    
    if status == "verified":
        return templates.TemplateResponse("verify.html", {"request": request, "message": "Email already verified."})
    
    session_code = request.session.get('verification_code')
    if session_code != code:
        return templates.TemplateResponse("verify.html", {"request": request, "message": "Invalid verification code."})

    db.update_verification_status(email=email, status="verified")
    request.session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    """Renders the login page."""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def post_login(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handles user login."""
    is_valid, user_data_or_error = db.get_user_for_login(email=email, password=password)
    
    if not is_valid:
        return templates.TemplateResponse("login.html", {"request": request, "error": user_data_or_error})
    
    request.session['user'] = user_data_or_error
    return RedirectResponse(url="/dashboard", status_code=HTTP_303_SEE_OTHER)


@app.get("/forgot_passsword", response_class=HTMLResponse)
def get_forgot_password(request: Request):
    """Renders the forgot password page."""
    return templates.TemplateResponse("forgotpassword.html", {"request": request})

@app.post("/forgot_passsword")
async def post_forgot_password(request: Request, email: str = Form(...)):
    """Handles the forgot password request and sends a reset code."""
    if not db.get_user(email=email):
        return templates.TemplateResponse("forgotpassword.html", {"request": request, "message": "Email not found."})
    
    reset_code = sendmail.send_password_reset_code(email=email)
    request.session['reset_code'] = reset_code
    request.session['reset_email'] = email
    return RedirectResponse(url="/reset_password_verify", status_code=HTTP_303_SEE_OTHER)

@app.get("/reset_password_verify", response_class=HTMLResponse)
def get_reset_password_verify(request: Request):
    """Renders the reset password code verification page."""
    return templates.TemplateResponse("reset_password_code_verification.html", {"request": request})

@app.post("/reset_password_verify")
async def post_reset_password_verify(
    request: Request,
    reset_code: str = Form(...),
    email: str = Depends(lambda r: get_session_email(r, "reset_email"))
):
    """Handles the reset password code verification submission."""
    session_code = request.session.get('reset_code')
    if session_code != reset_code:
        return templates.TemplateResponse("reset_password_code_verification.html", {"request": request, "message": "Invalid code."})
    
    return RedirectResponse(url="/reset_password", status_code=HTTP_303_SEE_OTHER)

@app.get("/reset_password", response_class=HTMLResponse)
def get_reset_password(request: Request):
    """Renders the reset password page."""
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.post("/reset_password")
async def post_reset_password(
    request: Request,
    new_password: str = Form(...),
    email: str = Depends(lambda r: get_session_email(r, "reset_email")) # Ensure email is present
):
    """Handles setting the new password."""
    if not is_strong_password(new_password):
        return templates.TemplateResponse("reset_password.html", {"request": request, "error": STRONG_PASSWORD_MESSAGE})

    db.update_user_password(email=email, password=new_password)
    # Clear the specific session keys used for password reset
    request.session.pop('reset_code', None)
    request.session.pop('reset_email', None)
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(request: Request):
    """Handles user logout."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=HTTP_303_SEE_OTHER)

