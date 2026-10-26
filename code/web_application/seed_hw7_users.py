"""Create the three local accounts needed to demonstrate HW7 roles."""

from getpass import getpass

from db import SessionLocal
from models import User
from routers.auth import password_hash

DEMO_USERS = {
    "reader_demo": "reader",
    "writer_demo": "writer",
    "moderator_demo": "moderator",
}


def create_or_update_user(db, username: str, role: str, password: str) -> None:
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        user = User(
            username=username,
            name=username,
            email=f"{username}@example.local",
            password_hash=password_hash.hash(password),
            role=role,
        )
        db.add(user)
    else:
        user.password_hash = password_hash.hash(password)
        user.role = role


def main() -> None:
    db = SessionLocal()
    try:
        for username, role in DEMO_USERS.items():
            password = getpass(f"Password for {username}: ")
            if not password:
                raise ValueError("A password is required for every demo account.")
            create_or_update_user(db, username, role, password)

        db.commit()
        print("Created or updated reader_demo, writer_demo, and moderator_demo.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
