from src.database.config import db

import os 
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from controllers.UserController import user_controller_router


app=FastAPI()
load_dotenv(override=True)

tags_metadata = [
    {"name":"Users","description":"Operations related to user managment."}
]

app.include_router(user_controller_router,prefix="/users",tags=["Users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ =="__main__":
    uvicorn.run("app:app",host=os.getenv("HOST"),port=os.getenv("PORT"),reload=True)
    