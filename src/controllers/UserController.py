from fastapi import HTTPException,Depends,Header
from fastapi.security import OAuth2PasswordRequestForm
from services.UserServices import UserService
from DTO.User import User
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from DTOs.CustomResponseMessage import CustomResponseMessage
from database.config import supabase
import os 

user_controller_router = InferringRouter()



@cbv(user_controller_router)
class UserController:
    def __init__(self):
        self.userService=UserService()

    @user_controller_router.post("/register")
    def register(self,user:User):
        try:
            usr=self.userService.register(user)
            if usr is not False:
                supabase.table("user").insert({"username":user.username,"password":user.password}).execute()
                return CustomResponseMessage(status_code = 200,message=f"User {user.username} registered succesfully.")
            else:
                raise HTTPException(status_code=422,detail="User already exists.")
        except Exception as e:
            raise HTTPException(status_code=e.status_code,detail=str(e.detail))

    @user_controller_router.post("/token")
    def get_access_token(self,form_data:OAuth2PasswordRequestForm=Depends()):
        try:
            access_token = self.userService.get_access_token(form_data)
            if access_token["access_token"] is None:
                raise HTTPException(status_code=400,detail=["Incorrect username or password."])
            return access_token
        except Exception as e:
            raise HTTPException(status_code=e.status_code,detail = str(e.detail))

    @user_controller_router.post("/logout")
    def logout(self, token:str|None=Header(None)):
        try:
            if token is None:
                raise HTTPException(status_code=401,detail = "Invalid token")
            self.userService.logout(token)
            return CustomResponseMessage(status_code=200,message="logged out succesfully")
        except Exception as e:
            raise HTTPException(status_code = e.status_code,detail = str(e.detail))