import logging
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import models as m, schemas as s
from .auth import check_pw, current_user, hash_pw, make_token, read_token
from .crud import crud_router
from .db import Base, engine, get_db
from .reports import r as reports

log = logging.getLogger("kisan")
app = FastAPI(title="Kisan Budget Manager")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def init(): Base.metadata.create_all(engine)

auth = APIRouter(prefix="/api/auth", tags=["auth"])

@auth.post("/signup", status_code=201)
def signup(d: s.Signup, db: Session = Depends(get_db)):
    if db.scalar(select(m.User).where(m.User.email == d.email.lower())):
        raise HTTPException(400, "Email already registered")
    u = m.User(email=d.email.lower(), password_hash=hash_pw(d.password), name=d.name)
    db.add(u); db.commit()
    return {"token": make_token(u.id), "name": u.name}

@auth.post("/login")
def login(d: s.Login, db: Session = Depends(get_db)):
    u = db.scalar(select(m.User).where(m.User.email == d.email.lower()))
    if not u or not check_pw(d.password, u.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u.id), "name": u.name}

@auth.post("/forgot")
def forgot(d: s.Forgot, db: Session = Depends(get_db)):
    u = db.scalar(select(m.User).where(m.User.email == d.email.lower()))
    if u:  # TODO: send by email/SMS; for now it is logged for the admin
        log.warning("Password reset token for %s: %s", u.email, make_token(u.id, "reset", 30))
    return {"message": "If the email exists, a reset link has been sent"}

@auth.post("/reset")
def reset(d: s.Reset, db: Session = Depends(get_db)):
    u = db.get(m.User, read_token(d.token, "reset"))
    if not u: raise HTTPException(400, "Invalid token")
    u.password_hash = hash_pw(d.password); db.commit()
    return {"message": "Password changed"}

@auth.get("/me")
def me(u: m.User = Depends(current_user)):
    return {"id": u.id, "email": u.email, "name": u.name, "language": u.language}

@auth.put("/language/{lang}")
def lang(lang: str, db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    if lang not in ("en", "te", "hi"): raise HTTPException(400, "Unsupported language")
    u.language = lang; db.commit()
    return {"language": lang}

app.include_router(auth)
app.include_router(reports)
for path, Model, Schema in [
    ("farms", m.Farm, s.FarmIn), ("crops", m.Crop, s.CropIn),
    ("farm-expenses", m.FarmExpense, s.FarmExpenseIn), ("farm-incomes", m.FarmIncome, s.FarmIncomeIn),
    ("household-incomes", m.HouseholdIncome, s.HouseholdIncomeIn),
    ("household-expenses", m.HouseholdExpense, s.HouseholdExpenseIn),
    ("loans", m.Loan, s.LoanIn), ("budget-plans", m.BudgetPlan, s.BudgetPlanIn),
    ("future-expenses", m.FutureExpense, s.FutureExpenseIn), ("subsidies", m.Subsidy, s.SubsidyIn)]:
    app.include_router(crud_router(path, Model, Schema))

@app.get("/api/health")
def health(): return {"ok": True}

app.mount("/app", StaticFiles(directory=Path(__file__).parent.parent / "static", html=True), name="web")

@app.get("/", include_in_schema=False)
def root(): return RedirectResponse("/app/")
