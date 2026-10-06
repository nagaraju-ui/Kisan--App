"""python -m app.seed  ->  demo user ramesh@example.com / ramesh123"""
from datetime import date, timedelta as td
from sqlalchemy import select
from . import models as m
from .auth import hash_pw
from .db import Base, SessionLocal, engine

Base.metadata.create_all(engine)
db = SessionLocal()
if db.scalar(select(m.User).where(m.User.email == "ramesh@example.com")):
    print("Demo user already exists"); raise SystemExit
u = m.User(email="ramesh@example.com", password_hash=hash_pw("ramesh123"), name="Ramesh"); db.add(u); db.flush()
U = u.id; t = date.today(); d = lambda n: t - td(days=n)
db.add(m.Farm(user_id=U, farmer_name="Ramesh", village="Nandigama", district="Warangal", state="Telangana",
              ownership="own", land_area=5, unit="acres", irrigation="borewell"))
c = m.Crop(user_id=U, name="Paddy", variety="BPT 5204", season="Kharif", area=3, sowing_date=d(120),
           harvest_date=t + td(days=20), expected_production=60, expected_price=2200, expected_income=132000)
db.add(c); db.flush()
for dd, cat, desc, amt in [(120, "seeds", "Paddy seed 25 kg", 1800), (110, "fertilizers", "Urea 6 bags", 1700),
        (100, "fertilizers", "DAP 4 bags", 5400), (95, "labour", "Transplanting", 9000),
        (70, "pesticides", "Insecticide spray", 2600), (60, "irrigation", "Electricity/pump", 3000),
        (45, "labour", "Weeding", 4500), (30, "machinery", "Tractor ploughing", 6000),
        (10, "transportation", "Transport to mill", 2500)]:
    db.add(m.FarmExpense(user_id=U, crop_id=c.id, date=d(dd), category=cat, description=desc, amount=amt))
db.add(m.FarmIncome(user_id=U, crop_id=c.id, date=d(5), quantity=40, unit="quintal", price=2200, buyer="Warangal mandi",
                    transport_cost=2500, other_deductions=1000, gross_income=88000, net_income=84500))
for dd, src, amt in [(40, "dairy", 6000), (10, "dairy", 6200), (20, "salary", 12000), (3, "subsidy", 6000)]:
    db.add(m.HouseholdIncome(user_id=U, date=d(dd), source=src, amount=amt, description=src))
for dd, cat, desc, amt in [(25, "food", "Groceries", 6000), (5, "food", "Vegetables & milk", 2500),
        (30, "education", "School fees", 8000), (15, "healthcare", "Medicines", 1800),
        (12, "utilities", "Electricity bill", 900), (8, "transport", "Petrol", 1500), (2, "family", "Festival", 3000)]:
    db.add(m.HouseholdExpense(user_id=U, date=d(dd), category=cat, description=desc, amount=amt))
db.add(m.Loan(user_id=U, name="Crop loan", lender="SBI", amount=100000, interest_rate=7, start_date=d(200),
              duration_months=12, emi=8600, paid=40000, next_payment_date=t + td(days=7)))
db.add(m.BudgetPlan(user_id=U, month=t.strftime("%Y-%m"), planned_income=40000, planned_expense=25000))
db.add(m.FutureExpense(user_id=U, due_date=t + td(days=15), kind="harvesting", description="Harvester", amount=7000, expected_income=50000))
db.add(m.Subsidy(user_id=U, scheme="Sample scheme (verify on official site)", department="Agriculture", expected=6000, received=6000, status="received"))
db.commit(); print("Seeded: ramesh@example.com / ramesh123")
