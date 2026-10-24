from fastapi import HTTPException

from src.repositories.UserRepository import UserRepository


class UserService:
    def __init__(self):
        self.userRepository = UserRepository()

    def register(self, user):
        return self.userRepository.register(user)

    def get_access_token(self, form_data):
        if not self.userRepository.is_password_correct(form_data):
            raise HTTPException(401, 'Incorrect username or password.')
        if self.is_session_active(form_data.username):
            token = self.userRepository.get_access_token_from_active_session(form_data.username)
        else:
            token = self.userRepository.get_access_token(form_data)
            self.register_token_in_session(token)
        return {'access_token': token, 'token_type': 'bearer'}

    def authenticate(self, token: str):
        return self.userRepository.authenticate(token)

    def register_token_in_session(self, token: str):
        self.userRepository.register_token_in_session(token)

    def logout(self, token: str):
        self.userRepository.logout(token)

    def is_session_active(self, username: str):
        return self.userRepository.is_session_active(username)
