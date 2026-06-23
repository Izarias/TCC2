from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from passlib.context import CryptContext

# ----------------------------
# Config
# ----------------------------

DATABASE_URL = "sqlite:///./app.db"

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------
# DB Models
# ----------------------------

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


Base.metadata.create_all(bind=engine)


# ----------------------------
# Schemas
# ----------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


# ----------------------------
# Dependencies
# ----------------------------

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------
# Validation / Utilities
# ----------------------------

def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_username(username: str) -> str:
    return username.strip()


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.fullmatch(username))


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.fullmatch(email))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# ----------------------------
# App
# ----------------------------

app = FastAPI(title="Simple Registration API", version="1.0.0")


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    username = normalize_username(payload.username)
    email = normalize_email(payload.email)

    if not is_valid_username(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid username. Use 3-32 chars: letters, numbers, underscore.",
        )

    if not is_valid_email(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )

    # Pre-check to return friendly errors (still keep DB constraints as the source of truth)
    existing = db.execute(
        select(User).where((User.username == username) | (User.email == email))
    ).scalars().first()

    if existing is not None:
        if existing.username == username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # If a race happened, present a consistent error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered.")
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)