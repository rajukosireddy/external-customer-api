

import os

import secrets
 
from fastapi import FastAPI, HTTPException, Depends

from fastapi.security import APIKeyHeader
 
from pymongo import MongoClient

from pymongo.errors import PyMongoError, DuplicateKeyError
 
from dotenv import load_dotenv

from pydantic import BaseModel, EmailStr
 
 
# --------------------------------------------------

# 1. Load environment variables

# --------------------------------------------------
 
load_dotenv()
 
MONGODB_URI = os.getenv("MONGODB_URI")

DATABASE_NAME = os.getenv("DATABASE_NAME")

API_KEY = os.getenv("API_KEY")
 
if not MONGODB_URI or not DATABASE_NAME:

    raise RuntimeError(

        "MongoDB configuration missing. Check your .env file."

    )
 
if not API_KEY:

    raise RuntimeError(

        "API_KEY is missing. Check your .env file."

    )
 
 
# --------------------------------------------------

# 2. Connect to MongoDB Atlas

# --------------------------------------------------
 
client = MongoClient(

    MONGODB_URI,

    serverSelectionTimeoutMS=5000

)
 
db = client[DATABASE_NAME]

customers = db["customers"]
 
 
# --------------------------------------------------

# 3. FastAPI application

# --------------------------------------------------
 
app = FastAPI(

    title="My External Customer API",

    description="Secure Customer API using MongoDB Atlas",

    version="1.0.0"

)
 
 
# --------------------------------------------------

# 4. API Key Authentication

# --------------------------------------------------
 
api_key_header = APIKeyHeader(

    name="X-API-Key",

    auto_error=False

)
 
 
def verify_api_key(

    api_key: str = Depends(api_key_header)

):
 
    if not api_key or not secrets.compare_digest(

        api_key,

        API_KEY

    ):

        raise HTTPException(

            status_code=401,

            detail="Invalid or missing API key"

        )
 
    return True
 
 
# --------------------------------------------------

# 5. Request data models

# --------------------------------------------------
 
class Screening(BaseModel):

    pep: str

    sanctions: str

    adverse_news: str
 
 
class Customer(BaseModel):

    customer_id: str

    name: str

    email: EmailStr

    country: str

    risk_level: str

    screening: Screening
 
 
# --------------------------------------------------

# 6. Home API

# --------------------------------------------------
 
@app.get("/")

def home():
 
    return {

        "message": "External Customer API is running",

        "database": DATABASE_NAME

    }
 
 
# --------------------------------------------------

# 7. MongoDB health check

# --------------------------------------------------
 
@app.get("/health")

def health():
 
    try:
 
        client.admin.command("ping")
 
        return {

            "status": "success",

            "message": "MongoDB Atlas connected successfully"

        }
 
    except PyMongoError:
 
        raise HTTPException(

            status_code=503,

            detail="MongoDB connection failed"

        )
 
 
# --------------------------------------------------

# 8. GET customer by customer ID

# --------------------------------------------------
 
@app.get(

    "/api/customers/{customer_id}",

    dependencies=[Depends(verify_api_key)]

)

def get_customer(customer_id: str):
 
    try:
 
        customer = customers.find_one(

            {"customer_id": customer_id},

            {"_id": 0}

        )
 
        if customer is None:
 
            raise HTTPException(

                status_code=404,

                detail="Customer not found"

            )
 
        return {

            "status": "success",

            "data": customer

        }
 
    except HTTPException:

        raise
 
    except PyMongoError:
 
        raise HTTPException(

            status_code=500,

            detail="Unable to retrieve customer from database"

        )
 
 
# --------------------------------------------------

# 9. POST create new customer

# --------------------------------------------------
 
@app.post(

    "/api/customers",

    status_code=201,

    dependencies=[Depends(verify_api_key)]

)

def create_customer(customer: Customer):
 
    try:
 
        existing_customer = customers.find_one(

            {"customer_id": customer.customer_id}

        )
 
        if existing_customer:
 
            raise HTTPException(

                status_code=409,

                detail="Customer already exists"

            )
 
        customer_data = customer.model_dump()
 
        customers.insert_one(customer_data)
 
        return {

            "status": "success",

            "message": "Customer created successfully",

            "customer_id": customer.customer_id

        }
 
    except HTTPException:

        raise
 
    except DuplicateKeyError:
 
        raise HTTPException(

            status_code=409,

            detail="Customer already exists"

        )
 
    except PyMongoError:
 
        raise HTTPException(

            status_code=500,

            detail="Unable to create customer in database"

        )
 
 
# --------------------------------------------------

# 10. GET all customers

# --------------------------------------------------
 
@app.get(

    "/api/customers",

    dependencies=[Depends(verify_api_key)]

)

def get_all_customers():
 
    try:
 
        customer_list = list(

            customers.find({}, {"_id": 0})

        )
 
        return {

            "status": "success",

            "total_records": len(customer_list),

            "data": customer_list

        }
 
    except PyMongoError:
 
        raise HTTPException(

            status_code=500,

            detail="Unable to retrieve customers"

        )

 