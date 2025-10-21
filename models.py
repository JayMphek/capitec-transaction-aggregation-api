from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from decimal import Decimal

class TransactionCategory(str, Enum):
    GROCERIES = "Groceries"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    SHOPPING = "Shopping"
    DINING = "Dining"
    TRANSFER = "Transfer"
    SALARY = "Salary"
    INVESTMENT = "Investment"
    OTHER = "Other"

class TransactionType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class DataSource(str, Enum):
    BANK_ACCOUNT = "bank_account"
    CREDIT_CARD = "credit_card"
    MOBILE_WALLET = "mobile_wallet"

class Transaction(BaseModel):
    id: str
    customer_id: str
    amount: Decimal
    type: TransactionType
    category: TransactionCategory
    description: str
    merchant: Optional[str] = None
    timestamp: datetime
    source: DataSource
    balance_after: Optional[Decimal] = None

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class TransactionSummary(BaseModel):
    total_transactions: int
    total_credits: Decimal
    total_debits: Decimal
    net_amount: Decimal
    categories: dict
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class CategoryBreakdown(BaseModel):
    category: TransactionCategory
    total_amount: Decimal
    transaction_count: int
    percentage: float

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class MonthlyTrend(BaseModel):
    month: str
    year: int
    total_credits: Decimal
    total_debits: Decimal
    net_amount: Decimal
    transaction_count: int

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

