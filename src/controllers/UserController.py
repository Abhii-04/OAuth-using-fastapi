from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.DTO.User import User
from src.services.UserServices import UserService

user_controller_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/users/token')


@user_controller_router.post('/register')
def register(user: User, service: UserService = Depends()):
    if service.register(user) is False:
        raise HTTPException(422, 'User already exists.')
    return {'status_code': 200, 'message': f'User {user.username} registered successfully.'}


@user_controller_router.post('/token')
def get_access_token(form_data: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends()):
    return service.get_access_token(form_data)


@user_controller_router.get('/me')
def current_user(token: str = Depends(oauth2_scheme), service: UserService = Depends()):
    return {'username': service.authenticate(token)}


@user_controller_router.post('/logout')
def logout(token: str = Depends(oauth2_scheme), service: UserService = Depends()):
    service.logout(token)
    return {'status_code': 200, 'message': 'Logged out successfully.'}
