import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from main import app, TransactionService, TransactionCategory, DataSource

client = TestClient(app)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def transaction_service():
    return TransactionService()

# ============================================================================
# API TESTS
# ============================================================================

def test_root_endpoint():
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Capitec Transaction Aggregation API"
    assert data["status"] == "operational"
    assert "timestamp" in data

def test_get_transactions():
    """Test retrieving transactions"""
    response = client.get("/api/v1/transactions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10

def test_get_transactions_with_customer_filter():
    """Test filtering transactions by customer"""
    response = client.get("/api/v1/transactions?customer_id=CUST001&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for txn in data:
        assert txn["customer_id"] == "CUST001"

def test_get_transactions_with_category_filter():
    """Test filtering transactions by category"""
    response = client.get(f"/api/v1/transactions?category={TransactionCategory.GROCERIES.value}&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for txn in data:
        assert txn["category"] == TransactionCategory.GROCERIES.value

def test_get_transactions_with_date_range():
    """Test filtering transactions by date range"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    response = client.get(
        f"/api/v1/transactions?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}&limit=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_transactions_with_amount_filter():
    """Test filtering transactions by amount"""
    response = client.get("/api/v1/transactions?min_amount=100&max_amount=1000&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for txn in data:
        assert 100 <= txn["amount"] <= 1000

def test_get_transaction_by_id():
    """Test retrieving a specific transaction"""
    # First get a list of transactions
    response = client.get("/api/v1/transactions?limit=1")
    transactions = response.json()
    
    if transactions:
        txn_id = transactions[0]["id"]
        response = client.get(f"/api/v1/transactions/{txn_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == txn_id

def test_get_transaction_not_found():
    """Test retrieving non-existent transaction"""
    response = client.get("/api/v1/transactions/INVALID_ID")
    assert response.status_code == 404

def test_get_summary():
    """Test getting transaction summary"""
    response = client.get("/api/v1/summary?customer_id=CUST001")
    assert response.status_code == 200
    data = response.json()
    assert "total_transactions" in data
    assert "total_credits" in data
    assert "total_debits" in data
    assert "net_amount" in data
    assert "categories" in data

def test_get_summary_with_date_range():
    """Test getting summary with date filters"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    response = client.get(
        f"/api/v1/summary?customer_id=CUST001&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)

def test_get_category_breakdown():
    """Test getting category breakdown"""
    response = client.get("/api/v1/categories?customer_id=CUST001")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    for item in data:
        assert "category" in item
        assert "total_amount" in item
        assert "transaction_count" in item
        assert "percentage" in item

def test_get_monthly_trends():
    """Test getting monthly trends"""
    response = client.get("/api/v1/trends?customer_id=CUST001&months=6")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    for trend in data:
        assert "month" in trend
        assert "year" in trend
        assert "total_credits" in trend
        assert "total_debits" in trend
        assert "net_amount" in trend
        assert "transaction_count" in trend

def test_get_customers():
    """Test getting customer list"""
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    data = response.json()
    assert "customers" in data
    assert isinstance(data["customers"], list)
    assert len(data["customers"]) > 0

def test_pagination():
    """Test pagination works correctly"""
    # Get first page
    response1 = client.get("/api/v1/transactions?limit=10&offset=0")
    page1 = response1.json()
    
    # Get second page
    response2 = client.get("/api/v1/transactions?limit=10&offset=10")
    page2 = response2.json()
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Ensure pages are different
    if page1 and page2:
        assert page1[0]["id"] != page2[0]["id"]

def test_invalid_limit():
    """Test that invalid limit values are rejected"""
    response = client.get("/api/v1/transactions?limit=2000")
    assert response.status_code == 422  # Validation error

def test_invalid_date_format():
    """Test that invalid date formats are handled"""
    response = client.get("/api/v1/transactions?start_date=invalid-date")
    assert response.status_code == 422

# ============================================================================
# SERVICE LAYER TESTS
# ============================================================================

def test_service_get_transactions(transaction_service):
    """Test service layer transaction retrieval"""
    transactions = transaction_service.get_transactions(limit=10)
    assert len(transactions) <= 10
    assert all(hasattr(t, 'id') for t in transactions)

def test_service_filter_by_customer(transaction_service):
    """Test service layer customer filtering"""
    transactions = transaction_service.get_transactions(
        customer_id="CUST001",
        limit=50
    )
    assert all(t.customer_id == "CUST001" for t in transactions)

def test_service_filter_by_category(transaction_service):
    """Test service layer category filtering"""
    transactions = transaction_service.get_transactions(
        category=TransactionCategory.GROCERIES,
        limit=50
    )
    assert all(t.category == TransactionCategory.GROCERIES for t in transactions)

def test_service_filter_by_source(transaction_service):
    """Test service layer source filtering"""
    transactions = transaction_service.get_transactions(
        source=DataSource.BANK_ACCOUNT,
        limit=50
    )
    assert all(t.source == DataSource.BANK_ACCOUNT for t in transactions)

def test_service_summary_calculation(transaction_service):
    """Test service layer summary calculation"""
    summary = transaction_service.get_summary(customer_id="CUST001")
    
    assert summary.total_transactions > 0
    assert summary.total_credits >= 0
    assert summary.total_debits >= 0
    assert summary.net_amount == summary.total_credits - summary.total_debits

def test_service_category_breakdown(transaction_service):
    """Test service layer category breakdown"""
    breakdown = transaction_service.get_category_breakdown(customer_id="CUST001")
    
    assert isinstance(breakdown, list)
    total_percentage = sum(item.percentage for item in breakdown)
    assert 99.9 <= total_percentage <= 100.1  # Allow for rounding

def test_service_monthly_trends(transaction_service):
    """Test service layer monthly trends"""
    trends = transaction_service.get_monthly_trends(customer_id="CUST001", months=3)
    
    assert isinstance(trends, list)
    assert len(trends) <= 3
    
    for trend in trends:
        assert trend.net_amount == trend.total_credits - trend.total_debits

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_workflow():
    """Test complete workflow from API to service"""
    # Get customers
    response = client.get("/api/v1/customers")
    customers = response.json()["customers"]
    assert len(customers) > 0
    
    customer_id = customers[0]
    
    # Get transactions for customer
    response = client.get(f"/api/v1/transactions?customer_id={customer_id}&limit=10")
    assert response.status_code == 200
    transactions = response.json()
    
    # Get summary
    response = client.get(f"/api/v1/summary?customer_id={customer_id}")
    assert response.status_code == 200
    summary = response.json()
    
    # Get category breakdown
    response = client.get(f"/api/v1/categories?customer_id={customer_id}")
    assert response.status_code == 200
    categories = response.json()
    
    # Get trends
    response = client.get(f"/api/v1/trends?customer_id={customer_id}&months=3")
    assert response.status_code == 200
    trends = response.json()
    
    assert len(transactions) > 0
    assert summary["total_transactions"] > 0
    assert len(categories) > 0
    assert len(trends) > 0