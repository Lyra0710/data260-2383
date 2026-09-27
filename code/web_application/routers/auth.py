from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from db import get_db
from models import Session, User


router = APIRouter()

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

SESSION_COOKIE_NAME = "s2383_session"
SESSION_DURATION = timedelta(hours=1)


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


def get_current_user(
    request: Request,
    db: DbSession = Depends(get_db),
) -> User:
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    session_record = db.get(Session, session_token)

    if not session_record:
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    if session_record.expires_at <= datetime.utcnow():
        db.delete(session_record)
        db.commit()

        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    return session_record.user


@router.post("/api/register")
def register(
    request_data: RegisterRequest,
    db: DbSession = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == request_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    user = User(
        name=request_data.name,
        email=request_data.email,
        password_hash=password_context.hash(
            request_data.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.post("/api/login")
def login(
    request_data: LoginRequest,
    response: Response,
    db: DbSession = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request_data.email)
        .first()
    )

    if not user or not password_context.verify(
        request_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    session_token = secrets.token_urlsafe(32)

    session_record = Session(
        id=session_token,
        user_id=user.id,
        expires_at=datetime.utcnow() + SESSION_DURATION,
    )

    db.add(session_record)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=int(SESSION_DURATION.total_seconds()),
    )

    return {
        "message": "Login successful",
        "name": user.name,
        "email": user.email,
    }


@router.post("/api/logout")
def logout(
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
):
    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if session_token:
        session_record = db.get(Session, session_token)

        if session_record:
            db.delete(session_record)
            db.commit()

    response.delete_cookie(SESSION_COOKIE_NAME)

    return {"message": "Logged out"}


@router.get("/api/me")
def current_user(
    user: User = Depends(get_current_user),
):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }

# -------------- HOMEWORK 3 old demo-style login----------------------------------------------

# from urllib3.util import request
# from fastapi import APIRouter, Request, Form
# from fastapi.responses import RedirectResponse
# from fastapi.templating import Jinja2Templates
# from starlette.status import HTTP_302_FOUND
# from pathlib import Path
# import time 
# # IDLE_TIMEOUT_SECONDS = 60 # temporary to test 
# IDLE_TIMEOUT_SECONDS = 3600

# # Create a router object
# # This behaves like a mini FastAPI app
# router = APIRouter()

# # Configure Jinja2 templates directory
# APP_DIR = Path(__file__).resolve().parent.parent
# templates = Jinja2Templates(
#     directory=str(APP_DIR / "templates")
# )


# # Hardcoded credentials for demo purposes only
# # In real applications, credentials come from a database
# VALID_USERNAME = "admin"
# VALID_PASSWORD = "password"


# @router.get("/")
# def home(request: Request):
#     """
#     Home page route.

#     - Checks if a user is logged in using the session
#     - Passes user info to the template
#     """
#     user = request.session.get("user")

#     return templates.TemplateResponse(
#         request=request,
#         name="index.html",
#         context={
#             "user": user
#         }
#     )


# @router.get("/login")
# def login_page(request: Request):
#     """
#     Displays the login form.

#     If the user is already logged in,
#     the template can choose what to display.
#     """
#     user = request.session.get("user")
#     error = request.session.pop("error", None)

#     return templates.TemplateResponse(
#         request=request,
#         name="login.html",
#         context={
#             "request": request,
#             "user": user,
#             "error": error
#         }
#     )


# @router.post("/login")
# def login(request: Request, username: str = Form(...), password: str = Form(...)):
#     """
#     Handles login form submission.

#     - Reads username and password from the form
#     - Validates credentials
#     - Stores user info in session if valid
#     """
#     if username == VALID_USERNAME and password == VALID_PASSWORD:
#         # Store logged-in user in session
#         request.session["user"] = username
#         request.session["last_activity"] = time.time()
#         # Redirect user to dashboard
#         return RedirectResponse(
#             url="/dashboard",
#             status_code=HTTP_302_FOUND
#         )

#     # If credentials are invalid:
#     # Redirect back to login page
#     request.session["error"] = "Invalid username or password"
#     # NOTE:
#     # No error message is shown intentionally.
#     # Students are expected to add Bootstrap alerts.
#     return RedirectResponse(
#         url="/login",
#         status_code=HTTP_302_FOUND
#     )


# @router.get("/dashboard")
# def dashboard(request: Request):
#     """
#     Protected route.

#     - Only accessible if user is logged in
#     - Redirects to login page if session is missing
#     """
#     # user = request.session.get("user")
#     user = get_active_user(request) # call the middleware function

#     # If user is not logged in, block access
#     if not user:
#         return RedirectResponse(
#             url="/login",
#             status_code=HTTP_302_FOUND
#         )

#     # If user is logged in, render dashboard
#     return templates.TemplateResponse(
#         request=request,
#         name="dashboard.html",
#         context={
#             "request": request,
#             "user": user
#         }
#     )


# @router.get("/logout")
# def logout(request: Request):
#     """
#     Logs the user out.

#     - Clears all session data
#     - Redirects back to home page
#     """
#     request.session.clear()

#     return RedirectResponse(
#         url="/",
#         status_code=HTTP_302_FOUND
#     )


# # Middleware helpers 
# def get_active_user(request: Request):
#     user = request.session.get("user") # checks if the user is logged in
#     last_activity = request.session.get("last_activity") # checks when the user was last active 

#     if not user or not last_activity:
#         return None

#     if time.time() - last_activity > IDLE_TIMEOUT_SECONDS:
#         request.session.clear() # if user is inactive for too long, clear the session
#         return None

#     # Refresh activity time while the session is active
#     request.session["last_activity"] = time.time() # if user is active, refresh the last activity time 

#     return user

