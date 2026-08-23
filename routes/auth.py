import bcrypt
from itsdangerous import URLSafeTimedSerializer
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from database import get_db
from models import User


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# Hackathon-simple signed token (no separate session store, nothing to
# expire/revoke server-side) — good enough to identify a logged-in user
# for the demo. Swap for real JWT/session auth, and enforce it on
# POST /observations, if there's time before submission.
SECRET_KEY = "precursor-hackathon-secret-change-me"
serializer = URLSafeTimedSerializer(SECRET_KEY)


class SignupInput(BaseModel):
    email: EmailStr
    password: str


class LoginInput(BaseModel):
    email: EmailStr
    password: str


def make_token(email: str) -> str:
    return serializer.dumps(email)


@router.post("/signup")
def signup(payload: SignupInput, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user = User(email=payload.email, password_hash=password_hash)

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"email": user.email, "token": make_token(user.email)}


@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not bcrypt.checkpw(payload.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    return {"email": user.email, "token": make_token(user.email)}
