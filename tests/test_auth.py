import os
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import app
from src.repositories.UserRepository import UserRepository


class Query:
    def __init__(self, rows):
        self.rows = rows
        self.filters = {}
        self.operation = 'select'

    def select(self, *args): return self
    def limit(self, *args): return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def insert(self, value):
        self.operation, self.value = 'insert', value
        return self
    def upsert(self, value, **kwargs):
        self.operation, self.value = 'upsert', value
        return self
    def delete(self):
        self.operation = 'delete'
        return self
    def execute(self):
        matches = [r for r in self.rows if all(r.get(k) == v for k, v in self.filters.items())]
        if self.operation == 'insert': self.rows.append(self.value.copy())
        if self.operation == 'upsert':
            self.rows[:] = [r for r in self.rows if r['username'] != self.value['username']]
            self.rows.append(self.value.copy())
        if self.operation == 'delete': self.rows[:] = [r for r in self.rows if r not in matches]
        return SimpleNamespace(data=matches)


class FakeDatabase:
    def __init__(self): self.rows = {}
    def table(self, name): return Query(self.rows.setdefault(name, []))


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.client = TestClient(app)
        self.env = patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key-that-is-at-least-32-bytes', 'ALGORITHM': 'HS256'})
        self.env.start()
        self.database = patch('src.database.config.supabase', self.db)
        self.database.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.database.stop)

    def register(self):
        return self.client.post('/users/register', json={'username': 'alice', 'password': 'correct-password'})

    def login(self, password='correct-password'):
        return self.client.post('/users/token', data={'username': 'alice', 'password': password})

    def test_complete_flow(self):
        self.assertEqual(self.register().status_code, 200)
        self.assertNotEqual(self.db.rows['user'][0]['password'], 'correct-password')
        self.assertEqual(len(self.db.rows['user']), 1)
        self.assertEqual(self.register().status_code, 422)
        self.assertEqual(self.login('wrong').status_code, 401)
        login = self.login()
        self.assertEqual(login.status_code, 200)
        token = login.json()['access_token']
        self.assertEqual(self.login().json()['access_token'], token)
        headers = {'Authorization': f'Bearer {token}'}
        self.assertEqual(self.client.get('/users/me', headers=headers).json(), {'username': 'alice'})
        self.assertEqual(self.client.post('/users/logout', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/users/me', headers=headers).status_code, 401)

    def test_missing_configuration_and_invalid_inputs(self):
        with patch('src.database.config.supabase', None):
            self.assertEqual(self.register().status_code, 503)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/users/me').status_code, 401)
        self.assertEqual(self.client.get('/users/me', headers={'Authorization': 'Bearer invalid'}).status_code, 401)
        self.assertEqual(self.client.post('/users/register', json={'username': '', 'password': ''}).status_code, 422)

    def test_tampered_token_and_missing_secret(self):
        self.register()
        token = self.login().json()['access_token']
        parts = token.split('.')
        parts[1] = 'eyJzdWIiOiJtYWxsb3J5In0'
        response = self.client.get('/users/me', headers={'Authorization': 'Bearer ' + '.'.join(parts)})
        self.assertEqual(response.status_code, 401)
        with patch.dict(os.environ, {'SECRET_KEY': ''}):
            self.assertEqual(self.login().status_code, 503)
        response = self.client.post('/users/register', json={'username': 'bob', 'password': 'é' * 37})
        self.assertEqual(response.status_code, 422)

    def test_database_error_is_not_exposed(self):
        from postgrest.exceptions import APIError
        with patch.object(FakeDatabase, 'table', side_effect=APIError({'code': '42501', 'message': 'private database detail'})):
            response = self.register()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('private database detail', response.text)

    def test_expired_session_is_removed(self):
        self.register()
        repo = UserRepository()
        token = repo.create_access_token({'sub': 'alice'}, timedelta(seconds=-1))
        self.db.rows['active_session'] = [{'username': 'alice', 'access_token': token}]
        self.assertFalse(repo.is_session_active('alice'))
        self.assertEqual(self.db.rows['active_session'], [])


if __name__ == '__main__':
    unittest.main()
