from pydantic import BaseModel, Field, field_validator
import datetime

class User(BaseModel):
    username: str = Field(min_length=1, max_length=100, pattern=r"^\S+$")
    password: str = Field(min_length=1)

    @field_validator('password')
    @classmethod
    def password_length(cls, value):
        if len(value.encode()) > 72:
            raise ValueError('Password must be at most 72 bytes for bcrypt.')
        return value

class ActiveSession(BaseModel):
    username:str
    access_token:str
    expiry_time:datetime.datetime

