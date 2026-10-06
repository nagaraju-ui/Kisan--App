import os, time, bcrypt, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

SECRET = os.getenv("SECRET_KEY", "dev-secret-change-me")
MINUTES = int(os.getenv("TOKEN_MINUTES", "720"))
bearer = HTTPBearer(auto_error=False)

def hash_pw(p: str) -> str: return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_pw(p: str, h: str) -> bool: return bcrypt.checkpw(p.encode(), h.encode())

def make_token(uid: int, kind="access", minutes=MINUTES) -> str:
    return jwt.encode({"sub": str(uid), "kind": kind, "exp": int(time.time()) + minutes * 60}, SECRET, "HS256")

def read_token(t: str, kind="access") -> int:
    try:
        d = jwt.decode(t, SECRET, algorithms=["HS256"])
        if d.get("kind") != kind: raise ValueError
        return int(d["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")

def current_user(cred=Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred: raise HTTPException(401, "Please log in")
    u = db.get(User, read_token(cred.credentials))
    if not u: raise HTTPException(401, "User not found")
    return u
