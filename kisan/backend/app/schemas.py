from datetime import date
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

Money = Annotated[float, Field(ge=0, le=1e10)]
Pos = Annotated[float, Field(gt=0, le=1e10)]
Pay = Literal["cash", "upi", "bank", "card", "credit", "other"]

class Signup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    name: str = ""
class Login(BaseModel):
    email: EmailStr
    password: str
class Forgot(BaseModel):
    email: EmailStr
class Reset(BaseModel):
    token: str
    password: str = Field(min_length=6, max_length=100)

class FarmIn(BaseModel):
    farmer_name: str = ""; village: str = ""; district: str = ""; state: str = ""
    ownership: Literal["own", "leased", "both"] = "own"
    land_area: Pos
    unit: Literal["acres", "hectares"] = "acres"
    irrigation: Literal["borewell", "canal", "rainfed", "drip", "other"] = "rainfed"

class CropIn(BaseModel):
    name: str = Field(min_length=1); variety: str = ""; season: str = ""
    area: Pos
    sowing_date: Optional[date] = None; harvest_date: Optional[date] = None
    expected_production: Money = 0; expected_price: Money = 0
    expected_income: Money = 0
    @model_validator(mode="after")
    def calc(self):
        if not self.expected_income:
            self.expected_income = self.expected_production * self.expected_price
        return self

class FarmExpenseIn(BaseModel):
    date: date
    crop_id: Optional[int] = None
    category: Literal["seeds", "fertilizers", "pesticides", "labour", "machinery", "irrigation", "transportation", "other"]
    description: str = ""
    amount: Pos
    payment_method: Pay = "cash"
    notes: str = ""

class FarmIncomeIn(BaseModel):
    date: date
    crop_id: Optional[int] = None
    quantity: Pos
    unit: Literal["kg", "quintal", "ton"] = "quintal"
    price: Pos
    buyer: str = ""
    transport_cost: Money = 0
    other_deductions: Money = 0
    notes: str = ""
    gross_income: float = 0
    net_income: float = 0
    @model_validator(mode="after")
    def calc(self):
        self.gross_income = round(self.quantity * self.price, 2)
        self.net_income = round(self.gross_income - self.transport_cost - self.other_deductions, 2)
        if self.net_income < 0:
            raise ValueError("Deductions cannot be more than gross income")
        return self

class HouseholdIncomeIn(BaseModel):
    date: date
    source: Literal["farming", "salary", "dairy", "poultry", "livestock", "subsidy", "rental", "business", "other"]
    description: str = ""
    amount: Pos
    notes: str = ""

class HouseholdExpenseIn(BaseModel):
    date: date
    category: Literal["food", "education", "healthcare", "utilities", "transport", "house", "family", "other"]
    description: str = ""
    amount: Pos
    payment_method: Pay = "cash"
    notes: str = ""

class LoanIn(BaseModel):
    name: str = Field(min_length=1); lender: str = ""
    amount: Pos
    interest_rate: Annotated[float, Field(ge=0, le=100)] = 0
    start_date: date
    duration_months: Annotated[int, Field(ge=1, le=600)] = 12
    emi: Money = 0; paid: Money = 0
    next_payment_date: Optional[date] = None

class BudgetPlanIn(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    category: str = "total"
    planned_income: Money = 0; planned_expense: Money = 0

class FutureExpenseIn(BaseModel):
    due_date: date
    kind: str
    description: str = ""
    amount: Money = 0; expected_income: Money = 0

class SubsidyIn(BaseModel):
    scheme: str = Field(min_length=1); department: str = ""
    applied_on: Optional[date] = None
    expected: Money = 0; received: Money = 0
    status: Literal["applied", "approved", "pending", "received", "rejected"] = "applied"
    notes: str = ""
