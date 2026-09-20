from urllib3.util import request
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from pathlib import Path
import time 
IDLE_TIMEOUT_SECONDS = 60 # temporary to test 
# Create a router object
# This behaves like a mini FastAPI app
router = APIRouter()

# Configure Jinja2 templates directory
APP_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)


# Hardcoded credentials for demo purposes only
# In real applications, credentials come from a database
VALID_USERNAME = "admin"
VALID_PASSWORD = "password"


@router.get("/")
def home(request: Request):
    """
    Home page route.

    - Checks if a user is logged in using the session
    - Passes user info to the template
    """
    user = request.session.get("user")

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user
        }
    )


@router.get("/login")
def login_page(request: Request):
    """
    Displays the login form.

    If the user is already logged in,
    the template can choose what to display.
    """
    user = request.session.get("user")
    error = request.session.pop("error", None)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "user": user,
            "error": error
        }
    )


@router.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    Handles login form submission.

    - Reads username and password from the form
    - Validates credentials
    - Stores user info in session if valid
    """
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        # Store logged-in user in session
        request.session["user"] = username
        request.session["last_activity"] = time.time()
        # Redirect user to dashboard
        return RedirectResponse(
            url="/dashboard",
            status_code=HTTP_302_FOUND
        )

    # If credentials are invalid:
    # Redirect back to login page
    request.session["error"] = "Invalid username or password"
    # NOTE:
    # No error message is shown intentionally.
    # Students are expected to add Bootstrap alerts.
    return RedirectResponse(
        url="/login",
        status_code=HTTP_302_FOUND
    )


@router.get("/dashboard")
def dashboard(request: Request):
    """
    Protected route.

    - Only accessible if user is logged in
    - Redirects to login page if session is missing
    """
    # user = request.session.get("user")
    user = get_active_user(request) # call the middleware function

    # If user is not logged in, block access
    if not user:
        return RedirectResponse(
            url="/login",
            status_code=HTTP_302_FOUND
        )

    # If user is logged in, render dashboard
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "user": user
        }
    )


@router.get("/logout")
def logout(request: Request):
    """
    Logs the user out.

    - Clears all session data
    - Redirects back to home page
    """
    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=HTTP_302_FOUND
    )


# Middleware helpers 
def get_active_user(request: Request):
    user = request.session.get("user") # checks if the user is logged in
    last_activity = request.session.get("last_activity") # checks when the user was last active 

    if not user or not last_activity:
        return None

    if time.time() - last_activity > IDLE_TIMEOUT_SECONDS:
        request.session.clear() # if user is inactive for too long, clear the session
        return None

    # Refresh activity time while the session is active
    request.session["last_activity"] = time.time() # if user is active, refresh the last activity time 

    return user