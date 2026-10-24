import os

from dotenv import load_dotenv
from fastapi import HTTPException
from supabase import Client, create_client

load_dotenv()


def db(url: str, key: str) -> Client:
    return create_client(url, key)


url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = db(url, key) if url and key else None


def get_database() -> Client:
    if supabase is None:
        raise HTTPException(503, 'Set SUPABASE_URL and SUPABASE_KEY to enable account operations.')
    return supabase
