"""
Тесты для middleware (middleware.py)
"""
import pytest
import os
import jwt
from datetime import datetime, timedelta

from logic.middleware import is_valid_jwt_format
from tests.helpers import ResponseHelper
from tests.conftest import TEST_JWT_SECRET


class TestJWTFormat:
    """Тесты для проверки формата JWT"""

    def test_valid_jwt_format(self):
        """Тест валидного формата JWT"""
        token = jwt.encode(
            {'userID': 1, 'exp': datetime.utcnow() + timedelta(hours=1)},
            TEST_JWT_SECRET,
            algorithm='HS256'
        )
        assert is_valid_jwt_format(token) is True

    def test_invalid_jwt_format_short(self):
        """Тест невалидного формата (слишком короткий)"""
        assert is_valid_jwt_format('invalid') is False

    def test_invalid_jwt_format_wrong_parts(self):
        """Тест невалидного формата (неправильное количество частей)"""
        assert is_valid_jwt_format('part1.part2') is False

    def test_invalid_jwt_format_null(self):
        """Тест невалидного формата (null)"""
        assert is_valid_jwt_format('null') is False

    def test_invalid_jwt_format_undefined(self):
        """Тест невалидного формата (undefined)"""
        assert is_valid_jwt_format('undefined') is False

    def test_invalid_jwt_format_empty(self):
        """Тест невалидного формата (пустая строка)"""
        assert is_valid_jwt_format('') is False
        assert is_valid_jwt_format(None) is False


class TestTokenRequired:
    """Тесты для декоратора token_required"""

    def test_token_required_success(self, client, auth_headers):
        """Тест успешной проверки токена"""
        # Используем защищенный эндпоинт
        response = client.get('/api/users', headers=auth_headers)
        # Может быть 200 или 403 в зависимости от прав
        assert response.status_code in [200, 403]

    def test_token_required_missing(self, client):
        """Тест без токена"""
        response = client.get('/api/users')

        data = ResponseHelper.assert_unauthorized(response)
        assert 'error' in data

    def test_token_required_invalid(self, client):
        """Тест с невалидным токеном"""
        response = client.get('/api/users',
                             headers={'Authorization': 'Bearer invalid_token'})

        ResponseHelper.assert_unauthorized(response)

    def test_token_required_expired(self, client):
        """Тест с истекшим токеном"""
        expired_token = jwt.encode(
            {'userID': 1, 'exp': datetime.utcnow() - timedelta(hours=1)},
            TEST_JWT_SECRET,
            algorithm='HS256'
        )

        response = client.get('/api/users',
                             headers={'Authorization': f'Bearer {expired_token}'})

        ResponseHelper.assert_unauthorized(response)
