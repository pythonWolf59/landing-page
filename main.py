import os
import uuid
from typing import List, Dict, Any

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
# This ensures that the data sent to your API is correctly structured.
class CaseData(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: str
    type_of_issue: str
    scam_type: str
    amount_lost: float | None = None
    description: str

# Adding CORS middleware to allow requests from any origin.
app = FastAPI()

# List of allowed origins
origins = [
    "http://localhost:5173",  # React local dev
    "http://127.0.0.1:5173",
     # production frontend
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # allow all headers
)
# --- Supabase Initialization ---
# Retrieve Supabase credentials from environment variables.
# These should be configured in your deployment environment (e.g., Koyeb)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Check if credentials are set
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Supabase URL and anonymous key must be set as environment variables.")

# Create a Supabase client instance
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# --- API Endpoint ---
@app.post("/data")
async def save_case_data(case_data: CaseData):
    """
    Receives JSON data, saves it to a Supabase database table,
    and returns a unique UUID as a Case ID.
    """
    
    # Generate a unique UUID for the new case
    case_id = str(uuid.uuid4())
    
    # Convert the Pydantic model to a dictionary.
    # The dictionary keys will match the Supabase table column names.
    new_case = case_data.model_dump()
    new_case["case_id"] = case_id
    
    try:
        # Insert the new case data into the 'cases' table.
        # The `insert()` method automatically handles creating the new row.
        response = supabase.table("cases").insert(new_case).execute()

        # Check for any errors from the Supabase response
        # The `execute()` call will raise an exception on an API error,
        # so this part is more for checking the content.
        # Note: If the Supabase request itself fails, an exception will be raised,
        # which is handled by the `except` block.
        if response.data:
            return JSONResponse(content={"case_id": case_id})
        else:
            print("Supabase insert failed with no data returned.")
            raise HTTPException(status_code=500, detail="Failed to save data to Supabase.")

    except Exception as e:
        print(f"An error occurred while saving to Supabase: {e}")
        # Return a 500 status code with a helpful error message
        raise HTTPException(status_code=500, detail="Failed to save data to Supabase.")
