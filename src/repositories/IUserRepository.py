from abc import ABC, abstractmethod

from src.DTO.User import User


class IUserRepository(ABC):
    @abstractmethod
    def register(self, user: User): pass

    @abstractmethod
    def create_access_token(self, data: dict, expires_delta): pass

    @abstractmethod
    def get_user(self, username: str): pass

    @abstractmethod
    def get_access_token(self, form_data): pass

    @abstractmethod
    def authenticate(self, token: str): pass

    @abstractmethod
    def is_password_correct(self, form_data) -> bool: pass

    @abstractmethod
    def register_token_in_session(self, token: str): pass

    @abstractmethod
    def logout(self, token: str): pass

    @abstractmethod
    def is_session_active(self, username: str): pass

    @abstractmethod
    def get_access_token_from_active_session(self, username: str): pass
