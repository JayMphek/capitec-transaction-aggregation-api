from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
from models import Transaction, TransactionType, TransactionCategory, DataSource

class MockDataSource:
    """Mock data source simulating different banking channels"""
    
    def __init__(self):
        self.transactions = self._generate_mock_data()
    
    def _generate_mock_data(self) -> List[Transaction]:
        """Generate realistic mock transaction data"""
        base_date = datetime.now()
        transactions = []
        
        # Mock data for 3 customers over 90 days
        customers = ["CUST001", "CUST002", "CUST003"]
        
        mock_transactions = [
            # Bank Account Transactions
            {"amount": 25000.00, "type": TransactionType.CREDIT, "category": TransactionCategory.SALARY, 
             "description": "Salary Payment", "merchant": "Employer Corp", "source": DataSource.BANK_ACCOUNT},
            {"amount": 1250.50, "type": TransactionType.DEBIT, "category": TransactionCategory.GROCERIES, 
             "description": "Checkers Payment", "merchant": "Checkers", "source": DataSource.BANK_ACCOUNT},
            {"amount": 850.00, "type": TransactionType.DEBIT, "category": TransactionCategory.UTILITIES, 
             "description": "Electricity Payment", "merchant": "City Power", "source": DataSource.BANK_ACCOUNT},
            {"amount": 450.00, "type": TransactionType.DEBIT, "category": TransactionCategory.TRANSPORT, 
             "description": "Petrol Purchase", "merchant": "Shell", "source": DataSource.BANK_ACCOUNT},
            
            # Credit Card Transactions
            {"amount": 599.99, "type": TransactionType.DEBIT, "category": TransactionCategory.SHOPPING, 
             "description": "Online Purchase", "merchant": "Takealot", "source": DataSource.CREDIT_CARD},
            {"amount": 280.00, "type": TransactionType.DEBIT, "category": TransactionCategory.DINING, 
             "description": "Restaurant Payment", "merchant": "Wimpy", "source": DataSource.CREDIT_CARD},
            {"amount": 1500.00, "type": TransactionType.DEBIT, "category": TransactionCategory.ENTERTAINMENT, 
             "description": "Movie & Concert", "merchant": "Ster Kinekor", "source": DataSource.CREDIT_CARD},
            
            # Mobile Wallet Transactions
            {"amount": 50.00, "type": TransactionType.DEBIT, "category": TransactionCategory.TRANSPORT, 
             "description": "Taxi Fare", "merchant": "Bolt", "source": DataSource.MOBILE_WALLET},
            {"amount": 150.00, "type": TransactionType.DEBIT, "category": TransactionCategory.DINING, 
             "description": "Food Delivery", "merchant": "Uber Eats", "source": DataSource.MOBILE_WALLET},
            {"amount": 500.00, "type": TransactionType.CREDIT, "category": TransactionCategory.TRANSFER, 
             "description": "Transfer from Friend", "merchant": None, "source": DataSource.MOBILE_WALLET},
            
            # Healthcare
            {"amount": 350.00, "type": TransactionType.DEBIT, "category": TransactionCategory.HEALTHCARE, 
             "description": "Doctor Consultation", "merchant": "Medi Clinic", "source": DataSource.BANK_ACCOUNT},
            
            # Investment
            {"amount": 2000.00, "type": TransactionType.DEBIT, "category": TransactionCategory.INVESTMENT, 
             "description": "Unit Trust Purchase", "merchant": "Capitec Investment", "source": DataSource.BANK_ACCOUNT},
        ]
        
        balance = 30000.00
        txn_id = 1
        
        for customer in customers:
            customer_balance = balance
            for day_offset in range(90):
                # Generate 2-5 transactions per day
                import random
                num_txns = random.randint(2, 5)
                
                for _ in range(num_txns):
                    txn_data = random.choice(mock_transactions)
                    txn_date = base_date - timedelta(days=day_offset, hours=random.randint(0, 23))
                    
                    amount = Decimal(str(txn_data["amount"]))
                    if txn_data["type"] == TransactionType.DEBIT:
                        customer_balance -= float(amount)
                    else:
                        customer_balance += float(amount)
                    
                    transaction = Transaction(
                        id=f"TXN{txn_id:08d}",
                        customer_id=customer,
                        amount=amount,
                        type=txn_data["type"],
                        category=txn_data["category"],
                        description=txn_data["description"],
                        merchant=txn_data.get("merchant"),
                        timestamp=txn_date,
                        source=txn_data["source"],
                        balance_after=Decimal(str(round(customer_balance, 2)))
                    )
                    transactions.append(transaction)
                    txn_id += 1
        
        return sorted(transactions, key=lambda x: x.timestamp, reverse=True)

