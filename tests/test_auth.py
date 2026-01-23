"""
Тесты для модуля авторизации (authorization.py)
"""
import pytest
import os
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash

from logic.model import RefreshToken
from tests.helpers import (
    ResponseHelper, TestDataFactory,
    assert_valid_token_response
)
from tests.conftest import TEST_JWT_SECRET, TEST_USERNAME, TEST_PASSWORD


class TestLogin:
    """Тесты для эндпоинта /api/login"""

    def test_login_success(self, client, db_session, test_user):
        """Тест успешной авторизации"""
        # Убеждаемся, что пароль установлен правильно
        test_user.password_hash = generate_password_hash(TEST_PASSWORD)
        db_session.commit()

        login_data = TestDataFactory.create_login_data(TEST_USERNAME, TEST_PASSWORD)
        response = client.post('/api/login', json=login_data, content_type='application/json')

        data = ResponseHelper.assert_success(response)
        assert_valid_token_response(data)
        assert data.get('userID') == test_user.id
        assert data.get('username') == TEST_USERNAME

    def test_login_invalid_username(self, client):
        """Тест авторизации с неверным именем пользователя"""
        login_data = TestDataFactory.create_login_data('nonexistent', 'password123')
        response = client.post('/api/login', json=login_data, content_type='application/json')

        ResponseHelper.assert_unauthorized(response)

    def test_login_invalid_password(self, client, db_session, test_user):
        """Тест авторизации с неверным паролем"""
        test_user.password_hash = generate_password_hash(TEST_PASSWORD)
        db_session.commit()

        login_data = TestDataFactory.create_login_data(TEST_USERNAME, 'wrongpassword')
        response = client.post('/api/login', json=login_data, content_type='application/json')

        ResponseHelper.assert_unauthorized(response)

    def test_login_missing_data(self, client):
        """Тест авторизации без данных"""
        response = client.post('/api/login', json={}, content_type='application/json')
        ResponseHelper.assert_error(response, 400)

    def test_login_missing_username(self, client):
        """Тест авторизации без имени пользователя"""
        response = client.post('/api/login', json={'password': 'password123'},
                              content_type='application/json')
        assert response.status_code == 400

    def test_login_missing_password(self, client):
        """Тест авторизации без пароля"""
        response = client.post('/api/login', json={'login': TEST_USERNAME},
                              content_type='application/json')
        assert response.status_code == 400


def _create_refresh_token(user_id: int, db_session) -> str:
    """Вспомогательная функция для создания refresh token"""
    refresh_token = jwt.encode(
        {'userID': user_id, 'exp': datetime.utcnow() + timedelta(days=30)},
        TEST_JWT_SECRET,
        algorithm='HS256'
    )

    rt = RefreshToken(
        user_id=user_id,
        token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db_session.add(rt)
    db_session.commit()
    return refresh_token


class TestRefreshToken:
    """Тесты для обновления токена"""

    def test_refresh_token_success(self, client, db_session, test_user):
        """Тест успешного обновления токена"""
        refresh_token = _create_refresh_token(test_user.id, db_session)

        response = client.post('/api/refreshToken',
                              cookies={'refresh_token': refresh_token},
                              content_type='application/json')

        data = ResponseHelper.assert_success(response)
        ResponseHelper.assert_has_fields(data, ['message', 'accessExpiry'])

    def test_refresh_token_missing(self, client):
        """Тест обновления без токена"""
        response = client.post('/api/refreshToken', content_type='application/json')
        ResponseHelper.assert_unauthorized(response)


class TestLogout:
    """Тесты для выхода из системы"""

    def test_logout_success(self, client, db_session, test_user):
        """Тест успешного выхода"""
        refresh_token = _create_refresh_token(test_user.id, db_session)

        response = client.post('/api/logout',
                              cookies={'refresh_token': refresh_token},
                              content_type='application/json')

        data = ResponseHelper.assert_success(response)
        assert 'message' in data

        # Проверяем, что токен удален из БД
        rt_check = RefreshToken.query.filter_by(token=refresh_token).first()
        assert rt_check is None

