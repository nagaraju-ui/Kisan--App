from datetime import date, datetime
from sqlalchemy import String, Float, Date, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(100), default="")
    language: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Owned:
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

def S(n=100, **k): return mapped_column(String(n), **k)
def F(**k): return mapped_column(Float, default=0, **k)
def D(**k): return mapped_column(Date, default=date.today, **k)
def T(): return mapped_column(Text, default="")

class Farm(Owned, Base):
    __tablename__ = "farms"
    farmer_name: Mapped[str] = S(default="")
    village: Mapped[str] = S(default="")
    district: Mapped[str] = S(default="")
    state: Mapped[str] = S(default="")
    ownership: Mapped[str] = S(20, default="own")          # own|leased|both
    land_area: Mapped[float] = F()
    unit: Mapped[str] = S(10, default="acres")             # acres|hectares
    irrigation: Mapped[str] = S(20, default="rainfed")

class Crop(Owned, Base):
    __tablename__ = "crops"
    name: Mapped[str] = S()
    variety: Mapped[str] = S(default="")
    season: Mapped[str] = S(20, default="")
    area: Mapped[float] = F()                              # in acres
    sowing_date: Mapped[date] = mapped_column(Date, nullable=True)
    harvest_date: Mapped[date] = mapped_column(Date, nullable=True)
    expected_production: Mapped[float] = F()               # quintals
    expected_price: Mapped[float] = F()                    # Rs per quintal
    expected_income: Mapped[float] = F()

class FarmExpense(Owned, Base):
    __tablename__ = "farm_expenses"
    date: Mapped[date] = D()
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = S(30)       # seeds|fertilizers|pesticides|labour|machinery|irrigation|transportation|other
    description: Mapped[str] = S(200, default="")
    amount: Mapped[float] = F()
    payment_method: Mapped[str] = S(20, default="cash")
    notes: Mapped[str] = T()

class FarmIncome(Owned, Base):
    __tablename__ = "farm_incomes"
    date: Mapped[date] = D()
    crop_id: Mapped[int] = mapped_column(ForeignKey("crops.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[float] = F()
    unit: Mapped[str] = S(10, default="quintal")           # kg|quintal|ton
    price: Mapped[float] = F()
    buyer: Mapped[str] = S(100, default="")
    transport_cost: Mapped[float] = F()
    other_deductions: Mapped[float] = F()
    gross_income: Mapped[float] = F()
    net_income: Mapped[float] = F()
    notes: Mapped[str] = T()

class HouseholdIncome(Owned, Base):
    __tablename__ = "household_incomes"
    date: Mapped[date] = D()
    source: Mapped[str] = S(30)  # farming|salary|dairy|poultry|livestock|subsidy|rental|business|other
    description: Mapped[str] = S(200, default="")
    amount: Mapped[float] = F()
    notes: Mapped[str] = T()

class HouseholdExpense(Owned, Base):
    __tablename__ = "household_expenses"
    date: Mapped[date] = D()
    category: Mapped[str] = S(30)  # food|education|healthcare|utilities|transport|house|family|other
    description: Mapped[str] = S(200, default="")
    amount: Mapped[float] = F()
    payment_method: Mapped[str] = S(20, default="cash")
    notes: Mapped[str] = T()

class Loan(Owned, Base):
    __tablename__ = "loans"
    name: Mapped[str] = S()
    lender: Mapped[str] = S(100, default="")
    amount: Mapped[float] = F()
    interest_rate: Mapped[float] = F()
    start_date: Mapped[date] = D()
    duration_months: Mapped[int] = mapped_column(Integer, default=12)
    emi: Mapped[float] = F()
    paid: Mapped[float] = F()
    next_payment_date: Mapped[date] = mapped_column(Date, nullable=True)

class BudgetPlan(Owned, Base):   # monthly household budget; month = "YYYY-MM"
    __tablename__ = "budget_plans"
    month: Mapped[str] = S(7)
    category: Mapped[str] = S(30, default="total")
    planned_income: Mapped[float] = F()
    planned_expense: Mapped[float] = F()

class FutureExpense(Owned, Base):
    __tablename__ = "future_expenses"
    due_date: Mapped[date] = D()
    kind: Mapped[str] = S(30)
    description: Mapped[str] = S(200, default="")
    amount: Mapped[float] = F()
    expected_income: Mapped[float] = F()

class Subsidy(Owned, Base):
    __tablename__ = "subsidies"
    scheme: Mapped[str] = S(150)
    department: Mapped[str] = S(100, default="")
    applied_on: Mapped[date] = mapped_column(Date, nullable=True)
    expected: Mapped[float] = F()
    received: Mapped[float] = F()
    status: Mapped[str] = S(10, default="applied")  # applied|approved|pending|received|rejected
    notes: Mapped[str] = T()
