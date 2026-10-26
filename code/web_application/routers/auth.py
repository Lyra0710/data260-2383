"""JWT authentication and role-based authorization for the fixtures API."""

import os
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from db import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User
from pwdlib import PasswordHash
from schemas import CurrentUserResponse, TokenResponse
from sqlalchemy.orm import Session as DbSession

router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    return secret


def create_access_token(username: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": username, "exp": expires_at},
        jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: DbSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            token,
            jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
        )
        username = payload.get("sub")
        if not isinstance(username, str):
            raise credentials_exception()
    except jwt.InvalidTokenError as error:
        raise credentials_exception() from error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception()

    return user


def require_roles(allowed_roles: set[str]) -> Callable:
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role privileges",
            )
        return user

    return role_checker


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: DbSession = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if user is None or not password_hash.verify(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user.username),
        "token_type": "bearer",
    }


@router.get("/me", response_model=CurrentUserResponse)
def current_user(user: User = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}
