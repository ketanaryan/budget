from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Enums
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Currency(str, Enum):
    INR = "INR"
    USD = "USD"

class TransactionCategory(str, Enum):
    # Income categories
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    INVESTMENT = "investment"
    OTHER_INCOME = "other_income"
    
    # Expense categories
    FOOD = "food"
    TRANSPORTATION = "transportation"
    HOUSING = "housing"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SHOPPING = "shopping"
    OTHER_EXPENSE = "other_expense"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Budget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    category: TransactionCategory
    budget_amount: float
    currency: Currency = Currency.INR
    month: str  # Format: "YYYY-MM"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BudgetCreate(BaseModel):
    category: TransactionCategory
    budget_amount: float
    currency: Currency = Currency.INR
    month: str

class BudgetResponse(BaseModel):
    id: str
    category: TransactionCategory
    budget_amount: float
    month: str
    spent_amount: float
    remaining_amount: float
    percentage_used: float

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: TransactionType
    category: TransactionCategory
    amount: float
    currency: Currency = Currency.INR
    description: str
    date: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    is_recurring: bool = False
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    next_occurrence: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TransactionCreate(BaseModel):
    type: TransactionType
    category: TransactionCategory
    amount: float
    currency: Currency = Currency.INR
    description: str
    date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    is_recurring: bool = False
    recurrence_type: RecurrenceType = RecurrenceType.NONE

class TransactionResponse(BaseModel):
    id: str
    type: TransactionType
    category: TransactionCategory
    amount: float
    currency: Currency
    description: str
    date: datetime
    tags: List[str]
    is_recurring: bool
    recurrence_type: RecurrenceType
    next_occurrence: Optional[datetime]
    created_at: datetime

class MonthlySummary(BaseModel):
    month: str
    year: int
    total_income: float
    total_expense: float
    net_amount: float
    transactions_count: int

class CategorySummary(BaseModel):
    category: TransactionCategory
    type: TransactionType
    total_amount: float
    transactions_count: int

class DailyTrend(BaseModel):
    date: str
    income: float
    expense: float
    net: float

class SearchFilters(BaseModel):
    query: Optional[str] = None
    category: Optional[TransactionCategory] = None
    type: Optional[TransactionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    tags: List[str] = Field(default_factory=list)

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def calculate_next_occurrence(date: datetime, recurrence_type: RecurrenceType) -> Optional[datetime]:
    if recurrence_type == RecurrenceType.NONE:
        return None
    elif recurrence_type == RecurrenceType.DAILY:
        return date + timedelta(days=1)
    elif recurrence_type == RecurrenceType.WEEKLY:
        return date + timedelta(weeks=1)
    elif recurrence_type == RecurrenceType.MONTHLY:
        # Add one month
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1)
        else:
            return date.replace(month=date.month + 1)
    elif recurrence_type == RecurrenceType.YEARLY:
        return date.replace(year=date.year + 1)
    return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_obj = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    
    await db.users.insert_one(user_obj.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user: UserLogin):
    # Verify user credentials
    db_user = await db.users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "created_at": current_user["created_at"]
    }

# Transaction Routes
@api_router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(transaction: TransactionCreate, current_user: dict = Depends(get_current_user)):
    transaction_date = transaction.date or datetime.utcnow()
    next_occurrence = None
    
    if transaction.is_recurring and transaction.recurrence_type != RecurrenceType.NONE:
        next_occurrence = calculate_next_occurrence(transaction_date, transaction.recurrence_type)
    
    transaction_obj = Transaction(
        user_id=current_user["id"],
        type=transaction.type,
        category=transaction.category,
        amount=transaction.amount,
        description=transaction.description,
        date=transaction_date,
        tags=transaction.tags,
        is_recurring=transaction.is_recurring,
        recurrence_type=transaction.recurrence_type,
        next_occurrence=next_occurrence
    )
    
    await db.transactions.insert_one(transaction_obj.dict())
    
    return TransactionResponse(
        id=transaction_obj.id,
        type=transaction_obj.type,
        category=transaction_obj.category,
        amount=transaction_obj.amount,
        description=transaction_obj.description,
        date=transaction_obj.date,
        tags=transaction_obj.tags,
        is_recurring=transaction_obj.is_recurring,
        recurrence_type=transaction_obj.recurrence_type,
        next_occurrence=transaction_obj.next_occurrence,
        created_at=transaction_obj.created_at
    )

@api_router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(current_user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": current_user["id"]}).sort("date", -1).to_list(1000)
    return [TransactionResponse(**transaction) for transaction in transactions]

@api_router.post("/transactions/search", response_model=List[TransactionResponse])
async def search_transactions(filters: SearchFilters, current_user: dict = Depends(get_current_user)):
    query = {"user_id": current_user["id"]}
    
    # Add filters to query
    if filters.category:
        query["category"] = filters.category
    if filters.type:
        query["type"] = filters.type
    if filters.start_date or filters.end_date:
        date_query = {}
        if filters.start_date:
            date_query["$gte"] = filters.start_date
        if filters.end_date:
            date_query["$lte"] = filters.end_date
        query["date"] = date_query
    if filters.min_amount or filters.max_amount:
        amount_query = {}
        if filters.min_amount:
            amount_query["$gte"] = filters.min_amount
        if filters.max_amount:
            amount_query["$lte"] = filters.max_amount
        query["amount"] = amount_query
    if filters.tags:
        query["tags"] = {"$in": filters.tags}
    
    # Text search in description
    if filters.query:
        query["description"] = {"$regex": filters.query, "$options": "i"}
    
    transactions = await db.transactions.find(query).sort("date", -1).to_list(1000)
    return [TransactionResponse(**transaction) for transaction in transactions]

@api_router.get("/transactions/summary/monthly")
async def get_monthly_summary(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"}
            },
            "transactions": {"$push": "$$ROOT"}
        }},
        {"$sort": {"_id.year": -1, "_id.month": -1}}
    ]
    
    monthly_data = await db.transactions.aggregate(pipeline).to_list(12)
    
    summaries = []
    for month_data in monthly_data:
        total_income = sum(t["amount"] for t in month_data["transactions"] if t["type"] == "income")
        total_expense = sum(t["amount"] for t in month_data["transactions"] if t["type"] == "expense")
        
        summaries.append(MonthlySummary(
            month=f"{month_data['_id']['year']}-{month_data['_id']['month']:02d}",
            year=month_data["_id"]["year"],
            total_income=total_income,
            total_expense=total_expense,
            net_amount=total_income - total_expense,
            transactions_count=len(month_data["transactions"])
        ))
    
    return summaries

@api_router.get("/transactions/summary/categories")
async def get_category_summary(current_user: dict = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {
            "_id": {
                "category": "$category",
                "type": "$type"
            },
            "total_amount": {"$sum": "$amount"},
            "count": {"$sum": 1}
        }}
    ]
    
    category_data = await db.transactions.aggregate(pipeline).to_list(100)
    
    summaries = []
    for cat_data in category_data:
        summaries.append(CategorySummary(
            category=cat_data["_id"]["category"],
            type=cat_data["_id"]["type"],
            total_amount=cat_data["total_amount"],
            transactions_count=cat_data["count"]
        ))
    
    return summaries

@api_router.get("/transactions/trends/daily")
async def get_daily_trends(days: int = 30, current_user: dict = Depends(get_current_user)):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    pipeline = [
        {"$match": {
            "user_id": current_user["id"],
            "date": {"$gte": start_date, "$lte": end_date}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$date"},
                "month": {"$month": "$date"},
                "day": {"$dayOfMonth": "$date"}
            },
            "income": {"$sum": {"$cond": [{"$eq": ["$type", "income"]}, "$amount", 0]}},
            "expense": {"$sum": {"$cond": [{"$eq": ["$type", "expense"]}, "$amount", 0]}}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    
    daily_data = await db.transactions.aggregate(pipeline).to_list(days)
    
    trends = []
    for day_data in daily_data:
        date_str = f"{day_data['_id']['year']}-{day_data['_id']['month']:02d}-{day_data['_id']['day']:02d}"
        income = day_data.get("income", 0)
        expense = day_data.get("expense", 0)
        
        trends.append(DailyTrend(
            date=date_str,
            income=income,
            expense=expense,
            net=income - expense
        ))
    
    return trends

# Budget Routes
@api_router.post("/budgets", response_model=BudgetResponse)
async def create_budget(budget: BudgetCreate, current_user: dict = Depends(get_current_user)):
    # Check if budget already exists for this category and month
    existing_budget = await db.budgets.find_one({
        "user_id": current_user["id"],
        "category": budget.category,
        "month": budget.month
    })
    
    if existing_budget:
        # Update existing budget
        await db.budgets.update_one(
            {"id": existing_budget["id"]},
            {"$set": {"budget_amount": budget.budget_amount}}
        )
        budget_obj = existing_budget
        budget_obj["budget_amount"] = budget.budget_amount
    else:
        # Create new budget
        budget_obj = Budget(
            user_id=current_user["id"],
            category=budget.category,
            budget_amount=budget.budget_amount,
            month=budget.month
        )
        await db.budgets.insert_one(budget_obj.dict())
        budget_obj = budget_obj.dict()
    
    # Calculate spent amount
    start_date = datetime.strptime(budget.month + "-01", "%Y-%m-%d")
    if start_date.month == 12:
        end_date = start_date.replace(year=start_date.year + 1, month=1)
    else:
        end_date = start_date.replace(month=start_date.month + 1)
    
    spent_amount = 0
    if budget.category:
        transactions = await db.transactions.find({
            "user_id": current_user["id"],
            "category": budget.category,
            "type": "expense",
            "date": {"$gte": start_date, "$lt": end_date}
        }).to_list(1000)
        spent_amount = sum(t["amount"] for t in transactions)
    
    remaining_amount = budget.budget_amount - spent_amount
    percentage_used = (spent_amount / budget.budget_amount * 100) if budget.budget_amount > 0 else 0
    
    return BudgetResponse(
        id=budget_obj["id"],
        category=budget_obj["category"],
        budget_amount=budget_obj["budget_amount"],
        month=budget_obj["month"],
        spent_amount=spent_amount,
        remaining_amount=remaining_amount,
        percentage_used=percentage_used
    )

@api_router.get("/budgets", response_model=List[BudgetResponse])
async def get_budgets(month: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"user_id": current_user["id"]}
    if month:
        query["month"] = month
    
    budgets = await db.budgets.find(query).to_list(100)
    
    budget_responses = []
    for budget in budgets:
        # Calculate spent amount
        start_date = datetime.strptime(budget["month"] + "-01", "%Y-%m-%d")
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1)
        
        transactions = await db.transactions.find({
            "user_id": current_user["id"],
            "category": budget["category"],
            "type": "expense",
            "date": {"$gte": start_date, "$lt": end_date}
        }).to_list(1000)
        
        spent_amount = sum(t["amount"] for t in transactions)
        remaining_amount = budget["budget_amount"] - spent_amount
        percentage_used = (spent_amount / budget["budget_amount"] * 100) if budget["budget_amount"] > 0 else 0
        
        budget_responses.append(BudgetResponse(
            id=budget["id"],
            category=budget["category"],
            budget_amount=budget["budget_amount"],
            month=budget["month"],
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            percentage_used=percentage_used
        ))
    
    return budget_responses

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.transactions.delete_one({"id": transaction_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

@api_router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, transaction: TransactionCreate, current_user: dict = Depends(get_current_user)):
    # Check if transaction exists and belongs to user
    existing_transaction = await db.transactions.find_one({"id": transaction_id, "user_id": current_user["id"]})
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction
    updated_data = {
        "type": transaction.type,
        "category": transaction.category,
        "amount": transaction.amount,
        "description": transaction.description,
        "date": transaction.date or datetime.utcnow()
    }
    
    await db.transactions.update_one(
        {"id": transaction_id, "user_id": current_user["id"]},
        {"$set": updated_data}
    )
    
    # Return updated transaction
    updated_transaction = await db.transactions.find_one({"id": transaction_id})
    return TransactionResponse(**updated_transaction)

# Process recurring transactions (would be called by a scheduled job)
@api_router.post("/transactions/process-recurring")
async def process_recurring_transactions():
    current_date = datetime.utcnow()
    
    # Find all recurring transactions that are due
    recurring_transactions = await db.transactions.find({
        "is_recurring": True,
        "next_occurrence": {"$lte": current_date}
    }).to_list(1000)
    
    new_transactions = []
    for recurring_transaction in recurring_transactions:
        # Create new transaction
        new_transaction = Transaction(
            user_id=recurring_transaction["user_id"],
            type=recurring_transaction["type"],
            category=recurring_transaction["category"],
            amount=recurring_transaction["amount"],
            description=f"{recurring_transaction['description']} (Auto-generated)",
            date=recurring_transaction["next_occurrence"],
            tags=recurring_transaction["tags"],
            is_recurring=False,  # The new transaction is not recurring itself
            recurrence_type=RecurrenceType.NONE
        )
        
        new_transactions.append(new_transaction.dict())
        
        # Update the next occurrence for the original recurring transaction
        next_occurrence = calculate_next_occurrence(
            recurring_transaction["next_occurrence"], 
            recurring_transaction["recurrence_type"]
        )
        
        await db.transactions.update_one(
            {"id": recurring_transaction["id"]},
            {"$set": {"next_occurrence": next_occurrence}}
        )
    
    # Insert all new transactions
    if new_transactions:
        await db.transactions.insert_many(new_transactions)
    
    return {"message": f"Processed {len(new_transactions)} recurring transactions"}

# Basic routes
@api_router.get("/")
async def root():
    return {"message": "Budget Planner API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()