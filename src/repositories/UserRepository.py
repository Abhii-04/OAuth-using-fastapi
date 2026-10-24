import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException
from postgrest.exceptions import APIError

from src.database.config import get_database
from src.DTO.User import ActiveSession, User
from src.repositories.IUserRepository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self):
        self.database = get_database()
        self.user_table = os.getenv('USER_COLLECTION', 'user')
        self.session_table = os.getenv('SESSION', 'active_session')

    def register(self, user: User):
        if self.get_user(user.username) is not None:
            return False
        password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt(rounds=12)).decode()
        try:
            self.database.table(self.user_table).insert({'username': user.username, 'password': password}).execute()
        except APIError as error:
            if error.code == '23505':
                return False
            raise
        return user

    def _jwt_settings(self):
        secret = os.getenv('SECRET_KEY')
        if not secret:
            raise HTTPException(503, 'Set SECRET_KEY to enable login.')
        return secret, os.getenv('ALGORITHM', 'HS256')

    def create_access_token(self, data: dict, expires_delta):
        secret, algorithm = self._jwt_settings()
        payload = {**data, 'exp': datetime.now(timezone.utc) + expires_delta, 'jti': str(uuid4())}
        return jwt.encode(payload, secret, algorithm=algorithm)

    def _decode_token(self, token: str):
        secret, algorithm = self._jwt_settings()
        try:
            return jwt.decode(token, secret, algorithms=[algorithm], options={'require': ['sub', 'exp']})
        except jwt.PyJWTError as error:
            raise HTTPException(401, 'Invalid or expired token.') from error

    def get_user(self, username: str):
        rows = self.database.table(self.user_table).select('username,password').eq('username', username).limit(1).execute().data
        return User(**rows[0]) if rows else None

    def is_password_correct(self, form_data) -> bool:
        user = self.get_user(form_data.username)
        if user is None:
            return False
        try:
            return bcrypt.checkpw(form_data.password.encode(), user.password.encode())
        except ValueError:
            return False

    def get_access_token(self, form_data):
        expires = timedelta(minutes=int(os.getenv('ACCESS_TOKEN_EXPIRATION_TIME', '30')))
        return self.create_access_token({'sub': form_data.username}, expires)

    def authenticate(self, token: str):
        payload = self._decode_token(token)
        rows = self.database.table(self.session_table).select('username').eq('username', payload['sub']).eq('access_token', token).limit(1).execute().data
        if not rows:
            raise HTTPException(401, 'User session not found.')
        return payload['sub']

    def register_token_in_session(self, token: str):
        payload = self._decode_token(token)
        session = ActiveSession(username=payload['sub'], access_token=token,
                                expiry_time=datetime.fromtimestamp(payload['exp'], timezone.utc))
        self.database.table(self.session_table).upsert(session.model_dump(mode='json'), on_conflict='username').execute()

    def logout(self, token: str):
        self.authenticate(token)
        self.database.table(self.session_table).delete().eq('access_token', token).execute()

    def is_session_active(self, username: str):
        token = self.get_access_token_from_active_session(username)
        if token is None:
            return False
        try:
            return self._decode_token(token)['sub'] == username
        except HTTPException as error:
            if error.status_code != 401:
                raise
            self.database.table(self.session_table).delete().eq('username', username).execute()
            return False

    def get_access_token_from_active_session(self, username: str):
        rows = self.database.table(self.session_table).select('access_token').eq('username', username).limit(1).execute().data
        return rows[0]['access_token'] if rows else None
