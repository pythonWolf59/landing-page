# main.py

import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import the Supabase client library
from supabase import create_client, Client

from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from a .env file
load_dotenv()

# Define the data model for the incoming JSON payload.
class CaseData(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: str
    type_of_issue: str
    scam_type: str
    amount_lost: float | None = None
    description: str

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://fundhunt.net" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and anonymous key must be set as environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- Add this new handler ---
@app.options("/data")
async def options_handler():
    """
    Explicitly handles the OPTIONS preflight request.
    This will ensure a correct response is sent, bypassing the 400 error.
    """
    return JSONResponse(content={}, status_code=204) # 204 No Content is standard

# --- Your existing POST endpoint ---
@app.post("/data")
async def save_case_data(case_data: CaseData):
    """
    Receives JSON data, saves it to a Supabase database table,
    and returns a unique UUID as a Case ID.
    """
    
    case_id = str(uuid.uuid4())
    
    new_case = case_data.model_dump()
    new_case["case_id"] = case_id
    
    try:
        response = supabase.table("cases").insert(new_case).execute()

        if response.data:
            return JSONResponse(content={"case_id": case_id})
        else:
            print("Supabase insert failed with no data returned.")
            raise HTTPException(status_code=500, detail="Failed to save data to Supabase.")

    except Exception as e:
        print(f"An error occurred while saving to Supabase: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data to Supabase.")