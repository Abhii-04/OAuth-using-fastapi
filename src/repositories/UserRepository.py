from typing_extensions import deprecated
from repositories.IUserRepository import IUserRepository
from database.config import supabase
from DTO.User import User,ActiveSession
import os 
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from fastapi import Depends
from passlib.context import CryptContext
from passlib.hash import bcrypt
from datetime import timedelta
import jwt
from jwt import PyJWTError
from fastapi import HTTPException

load_dotenv(override=True)

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")


class UserRepository(IUserRepository):
    def __init__(self):
        self.em=supabase.get_collection(os.getenv('USER_COLLECTION'))
        self.active_session = supabase.get_collection(os.getenv("SESSION"))

    def register(self,user:User):
        usr=self.em.find_one({"username":user.username})
        if usr is None:
            self.em.insert_one(
                {
                    "username":user.username,
                    "pasword":bcrypt.using(rounds=12).hash(user.password)
                }
            )
            return user
        else:
            return False
        
    def create_access_token(self, data: dict, expires_delta):
        to_encode=data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode,os.getenv("SECRET_KEY"),algorithm=os.getenv("ALGORITHM")  )     
        return encoded_jwt
        
