from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
from mock_data import MockDataSource
from models import Transaction, TransactionSummary, CategoryBreakdown, MonthlyTrend, TransactionCategory, TransactionType, DataSource
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TransactionService:
    """Business logic for transaction aggregation"""
    
    def __init__(self):
        self.data_source = MockDataSource()
        logger.info(f"Initialized with {len(self.data_source.transactions)} transactions")
    
    def get_transactions(
        self,
        customer_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[TransactionCategory] = None,
        source: Optional[DataSource] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """Retrieve filtered transactions"""
        transactions = self.data_source.transactions
        
        # Apply filters
        if customer_id:
            transactions = [t for t in transactions if t.customer_id == customer_id]
        
        if start_date:
            transactions = [t for t in transactions if t.timestamp >= start_date]
        
        if end_date:
            transactions = [t for t in transactions if t.timestamp <= end_date]
        
        if category:
            transactions = [t for t in transactions if t.category == category]
        
        if source:
            transactions = [t for t in transactions if t.source == source]
        
        if min_amount:
            transactions = [t for t in transactions if t.amount >= min_amount]
        
        if max_amount:
            transactions = [t for t in transactions if t.amount <= max_amount]
        
        # Pagination
        return transactions[offset:offset + limit]
    
    def get_summary(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TransactionSummary:
        """Generate transaction summary"""
        transactions = self.get_transactions(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        total_credits = sum(t.amount for t in transactions if t.type == TransactionType.CREDIT)
        total_debits = sum(t.amount for t in transactions if t.type == TransactionType.DEBIT)
        
        # Category breakdown
        categories = {}
        for txn in transactions:
            if txn.type == TransactionType.DEBIT:
                cat = txn.category.value
                if cat not in categories:
                    categories[cat] = {"amount": Decimal(0), "count": 0}
                categories[cat]["amount"] += txn.amount
                categories[cat]["count"] += 1
        
        return TransactionSummary(
            total_transactions=len(transactions),
            total_credits=total_credits,
            total_debits=total_debits,
            net_amount=total_credits - total_debits,
            categories=categories
        )
    
    def get_category_breakdown(
        self,
        customer_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CategoryBreakdown]:
        """Get spending by category"""
        transactions = self.get_transactions(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        # Only consider debits for spending breakdown
        debits = [t for t in transactions if t.type == TransactionType.DEBIT]
        total_spent = sum(t.amount for t in debits)
        
        category_data = {}
        for txn in debits:
            cat = txn.category
            if cat not in category_data:
                category_data[cat] = {"amount": Decimal(0), "count": 0}
            category_data[cat]["amount"] += txn.amount
            category_data[cat]["count"] += 1
        
        breakdown = []
        for category, data in category_data.items():
            percentage = (float(data["amount"]) / float(total_spent) * 100) if total_spent > 0 else 0
            breakdown.append(CategoryBreakdown(
                category=category,
                total_amount=data["amount"],
                transaction_count=data["count"],
                percentage=round(percentage, 2)
            ))
        
        return sorted(breakdown, key=lambda x: x.total_amount, reverse=True)
    
    def get_monthly_trends(
        self,
        customer_id: str,
        months: int = 6
    ) -> List[MonthlyTrend]:
        """Get monthly spending trends"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        transactions = self.get_transactions(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        monthly_data = {}
        for txn in transactions:
            key = (txn.timestamp.year, txn.timestamp.month)
            if key not in monthly_data:
                monthly_data[key] = {
                    "credits": Decimal(0),
                    "debits": Decimal(0),
                    "count": 0
                }
            
            if txn.type == TransactionType.CREDIT:
                monthly_data[key]["credits"] += txn.amount
            else:
                monthly_data[key]["debits"] += txn.amount
            monthly_data[key]["count"] += 1
        
        trends = []
        for (year, month), data in sorted(monthly_data.items()):
            month_name = datetime(year, month, 1).strftime("%B")
            trends.append(MonthlyTrend(
                month=month_name,
                year=year,
                total_credits=data["credits"],
                total_debits=data["debits"],
                net_amount=data["credits"] - data["debits"],
                transaction_count=data["count"]
            ))
        
        return trends

