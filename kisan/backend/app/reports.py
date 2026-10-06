from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .auth import current_user
from .db import get_db
from . import models as m

r = APIRouter(prefix="/api", tags=["reports"])
KG = {"kg": 1, "quintal": 100, "ton": 1000}

def tot(db, u, col, *where):
    return float(db.scalar(select(func.coalesce(func.sum(col), 0)).where(col.class_.user_id == u.id, *where)) or 0)

@r.get("/summary")
def summary(db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    f_inc = tot(db, u, m.FarmIncome.net_income)
    f_exp = tot(db, u, m.FarmExpense.amount)
    # "farming" source in household income is skipped: farm sales are already counted above
    h_inc = tot(db, u, m.HouseholdIncome.amount, m.HouseholdIncome.source != "farming")
    h_exp = tot(db, u, m.HouseholdExpense.amount)
    loans = db.scalars(select(m.Loan).where(m.Loan.user_id == u.id)).all()
    total_loan = sum(l.amount for l in loans); paid = sum(l.paid for l in loans)
    today = date.today()
    up = db.scalars(select(m.FutureExpense).where(m.FutureExpense.user_id == u.id, m.FutureExpense.due_date >= today)).all()
    emis = [{"loan": l.name, "emi": l.emi, "date": l.next_payment_date}
            for l in loans if l.next_payment_date and today <= l.next_payment_date <= today + timedelta(days=30)]
    farm = db.scalar(select(m.Farm).where(m.Farm.user_id == u.id))
    crop = db.scalar(select(m.Crop).where(m.Crop.user_id == u.id).order_by(m.Crop.id.desc()))
    return {
        "farming": {"income": f_inc, "expenses": f_exp, "profit": f_inc - f_exp,
                    "current_crop": crop.name if crop else None,
                    "land_area": farm.land_area if farm else 0, "unit": farm.unit if farm else "acres",
                    "upcoming_expenses": sum(x.amount for x in up)},
        "household": {"income": h_inc, "expenses": h_exp, "savings": h_inc - h_exp,
                      "outstanding_loans": total_loan - paid},
        "combined": {"total_income": f_inc + h_inc, "total_expenses": f_exp + h_exp,
                     "total_savings": (f_inc + h_inc) - (f_exp + h_exp),
                     "farming_profit": f_inc - f_exp, "available_balance": (f_inc + h_inc) - (f_exp + h_exp)},
        "upcoming_emis": emis,
    }

@r.get("/crops/{crop_id}/profit")
def crop_profit(crop_id: int, db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    c = db.scalar(select(m.Crop).where(m.Crop.id == crop_id, m.Crop.user_id == u.id))
    if not c: raise HTTPException(404, "Crop not found")
    by_cat = dict(db.execute(select(m.FarmExpense.category, func.sum(m.FarmExpense.amount))
                  .where(m.FarmExpense.user_id == u.id, m.FarmExpense.crop_id == c.id)
                  .group_by(m.FarmExpense.category)).all())
    cost = float(sum(by_cat.values()))
    sales = db.scalars(select(m.FarmIncome).where(m.FarmIncome.user_id == u.id, m.FarmIncome.crop_id == c.id)).all()
    gross = sum(s.gross_income for s in sales)
    qty_q = sum(s.quantity * KG[s.unit] for s in sales) / 100   # quintals
    a = c.area or 1
    return {"crop": c.name, "area": c.area, "cost_by_category": {k: float(v) for k, v in by_cat.items()},
            "total_cost": cost, "gross_income": gross, "net_profit": gross - cost,
            "cost_per_acre": cost / a, "income_per_acre": gross / a, "profit_per_acre": (gross - cost) / a,
            "quantity_quintal": qty_q, "break_even_price_per_quintal": (cost / qty_q) if qty_q else None}

@r.get("/reports/monthly")
def monthly(year: int, db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    out = {mm: {"month": f"{year}-{mm:02d}", "farm_income": 0, "farm_expense": 0, "house_income": 0, "house_expense": 0}
           for mm in range(1, 13)}
    for model, col, key, extra in [(m.FarmIncome, m.FarmIncome.net_income, "farm_income", None),
                                   (m.FarmExpense, m.FarmExpense.amount, "farm_expense", None),
                                   (m.HouseholdIncome, m.HouseholdIncome.amount, "house_income", m.HouseholdIncome.source != "farming"),
                                   (m.HouseholdExpense, m.HouseholdExpense.amount, "house_expense", None)]:
        q = select(func.extract("month", model.date), func.sum(col)).where(
            model.user_id == u.id, func.extract("year", model.date) == year).group_by(1)
        if extra is not None: q = q.where(extra)
        for mon, v in db.execute(q): out[int(mon)][key] = float(v)
    rows = list(out.values())
    for x in rows:
        x["income"] = x["farm_income"] + x["house_income"]
        x["expenses"] = x["farm_expense"] + x["house_expense"]
        x["savings"] = x["income"] - x["expenses"]
    return rows

@r.get("/budget-check/{month}")
def budget_check(month: str, db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    p = db.scalar(select(m.BudgetPlan).where(m.BudgetPlan.user_id == u.id, m.BudgetPlan.month == month, m.BudgetPlan.category == "total"))
    y, mo = int(month[:4]), int(month[5:])
    lo, hi = date(y, mo, 1), date(y + (mo == 12), mo % 12 + 1, 1)
    actual = tot(db, u, m.HouseholdExpense.amount, m.HouseholdExpense.date >= lo, m.HouseholdExpense.date < hi)
    if not p: return {"month": month, "actual_expense": actual, "plan": None}
    return {"month": month, "planned_expense": p.planned_expense, "actual_expense": actual,
            "planned_savings": p.planned_income - p.planned_expense,
            "over_budget": actual > p.planned_expense,
            "message": "Budget gap detected" if actual > p.planned_expense else "Within planned budget"}

@r.get("/future-check")
def future_check(db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    s = summary(db, u)
    items = db.scalars(select(m.FutureExpense).where(m.FutureExpense.user_id == u.id, m.FutureExpense.due_date >= date.today())).all()
    need = sum(i.amount for i in items); exp_inc = sum(i.expected_income for i in items)
    avail = s["combined"]["available_balance"]
    ok = need <= avail + exp_inc
    return {"upcoming_expenses": need, "available_balance": avail, "expected_income": exp_inc,
            "message": "Within planned budget" if ok else "Budget gap detected - additional funds may be required"}


from typing import Optional

@r.get("/loans/{loan_id}/interest")
def loan_interest(loan_id: int, from_date: Optional[date] = None, to_date: Optional[date] = None,
                  type: str = "simple", db: Session = Depends(get_db), u: m.User = Depends(current_user)):
    """Interest on the loan principal between two dates (default: loan start -> today).
    type=simple : P x rate x days / 365
    type=compound : yearly compounding, P x ((1+r)^t2 - (1+r)^t1), t in years from start date."""
    l = db.scalar(select(m.Loan).where(m.Loan.id == loan_id, m.Loan.user_id == u.id))
    if not l: raise HTTPException(404, "Loan not found")
    if type not in ("simple", "compound"): raise HTTPException(400, "type must be simple or compound")
    a = max(from_date or l.start_date, l.start_date)
    b = to_date or date.today()
    if b < a: raise HTTPException(400, "To date must be after From date")
    rate = l.interest_rate / 100
    def accrued(upto):  # total interest from loan start up to a date
        t = max((upto - l.start_date).days, 0) / 365
        return l.amount * rate * t if type == "simple" else l.amount * ((1 + rate) ** t - 1)
    between = accrued(b) - accrued(a)
    total = accrued(b)
    return {"loan": l.name, "principal": l.amount, "rate_percent": l.interest_rate, "type": type,
            "from": a, "to": b, "days": (b - a).days,
            "interest_between_dates": round(between, 2),
            "interest_since_start": round(total, 2),
            "total_payable_till_to_date": round(l.amount + total, 2),
            "note": "Estimate on full principal; part payments and bank-specific EMI rules are not applied."}
