from pydantic import ValidationError
from supabase import create_client,Client
import os 
from dotenv import load_dotenv


load_dotenv(override=True)

url = os.getenv('')
key = os.getenv('')

def db(url,key)->Client:
    try:
        supabase=create_client(url,key)
    except Exception as error:
        raise ValidationError("could not validate either url or key")
    return supabase

supabase = db(url,key)