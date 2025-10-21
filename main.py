from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
import uvicorn
from transaction_service import TransactionService
from models import Transaction, TransactionSummary, CategoryBreakdown, MonthlyTrend, TransactionCategory, DataSource
from decimal import Decimal

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API SETUP
# ============================================================================

app = FastAPI(
    title="Capitec Transaction Aggregation API",
    description="Production-grade API for aggregating and analyzing customer transactions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
transaction_service = TransactionService()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Capitec Transaction Aggregation API",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/transactions", response_model=List[Transaction])
async def get_transactions(
    customer_id: Optional[str] = Query(None, description="Customer ID"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    category: Optional[TransactionCategory] = Query(None, description="Transaction category"),
    source: Optional[DataSource] = Query(None, description="Data source"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    limit: int = Query(100, ge=1, le=1000, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset")
):
    """
    Retrieve transactions with optional filtering
    
    - **customer_id**: Filter by customer
    - **start_date**: Filter transactions after this date
    - **end_date**: Filter transactions before this date
    - **category**: Filter by transaction category
    - **source**: Filter by data source
    - **min_amount**: Minimum transaction amount
    - **max_amount**: Maximum transaction amount
    - **limit**: Maximum number of results
    - **offset**: Number of results to skip
    """
    try:
        transactions = transaction_service.get_transactions(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
            source=source,
            min_amount=Decimal(str(min_amount)) if min_amount else None,
            max_amount=Decimal(str(max_amount)) if max_amount else None,
            limit=limit,
            offset=offset
        )
        logger.info(f"Retrieved {len(transactions)} transactions")
        return transactions
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str):
    """Get a specific transaction by ID"""
    try:
        transactions = transaction_service.data_source.transactions
        transaction = next((t for t in transactions if t.id == transaction_id), None)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/summary", response_model=TransactionSummary)
async def get_summary(
    customer_id: str = Query(..., description="Customer ID"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """
    Get transaction summary for a customer
    
    Includes total credits, debits, net amount, and category breakdown
    """
    try:
        summary = transaction_service.get_summary(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Generated summary for customer {customer_id}")
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/categories", response_model=List[CategoryBreakdown])
async def get_category_breakdown(
    customer_id: str = Query(..., description="Customer ID"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)")
):
    """
    Get spending breakdown by category
    
    Shows amount spent, transaction count, and percentage for each category
    """
    try:
        breakdown = transaction_service.get_category_breakdown(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Generated category breakdown for customer {customer_id}")
        return breakdown
    except Exception as e:
        logger.error(f"Error generating category breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/trends", response_model=List[MonthlyTrend])
async def get_monthly_trends(
    customer_id: str = Query(..., description="Customer ID"),
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze")
):
    """
    Get monthly spending trends
    
    Shows credits, debits, and net amount for each month
    """
    try:
        trends = transaction_service.get_monthly_trends(
            customer_id=customer_id,
            months=months
        )
        logger.info(f"Generated trends for customer {customer_id}")
        return trends
    except Exception as e:
        logger.error(f"Error generating trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/customers")
async def get_customers():
    """Get list of available customer IDs"""
    try:
        transactions = transaction_service.data_source.transactions
        customers = list(set(t.customer_id for t in transactions))
        return {"customers": sorted(customers)}
    except Exception as e:
        logger.error(f"Error retrieving customers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )