from supabase import create_client, Client
import os
from dotenv import load_dotenv
import time

# Supabase credentials
SUPABASE_URL = "https://wcviuqikbxjkrmjecasu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indjdml1cWlrYnhqa3JtamVjYXN1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTA2NDgwOCwiZXhwIjoyMDUwNjQwODA4fQ.LobS_8PlchtU9zZR52pGX3e9YZgk_VbY3SXz-BxiqiY"

# Global client variable
db_client = None

def initialize_client():
    """Initialize the Supabase client with retries"""
    global db_client
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Client for database operations (using service role key)
            db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Set schema explicitly
            db_client.postgrest.schema('public')
            
            # Test the connection by making a simple query
            test = db_client.table('business_parameters').select('*').limit(1).execute()
            print(f"Database client initialized successfully (attempt {attempt + 1})")
            return db_client
        except Exception as e:
            print(f"\n=== Supabase Client Error (attempt {attempt + 1}) ===")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise e

def get_supabase():
    """Get the database client for operations"""
    global db_client
    if db_client is None:
        db_client = initialize_client()
    return db_client 