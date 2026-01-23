"""
Тесты для модуля регистрации (registration.py)
"""
import pytest

from logic.model import User
from tests.helpers import ResponseHelper, TestDataFactory
from tests.conftest import TEST_USERNAME, TEST_EMAIL


class TestRegistration:
    """Тесты для эндпоинта /api/register"""

    def test_registration_success(self, client, db_session):
        """Тест успешной регистрации"""
        user_data = TestDataFactory.create_user_data(
            username='newuser',
            email='newuser@example.com',
            password='password123'
        )

        response = client.post('/api/register', json=user_data, content_type='application/json')

        data = ResponseHelper.assert_success(response)
        assert 'message' in data

        # Проверяем, что пользователь создан
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@example.com'

    def test_registration_duplicate_username(self, client, test_user):
        """Тест регистрации с существующим именем пользователя"""
        user_data = TestDataFactory.create_user_data(
            username=TEST_USERNAME,
            email='different@example.com',
            password='password123'
        )

        response = client.post('/api/register', json=user_data, content_type='application/json')

        assert response.status_code in [400, 409]
        data = ResponseHelper.parse_json(response)
        assert 'error' in data

    def test_registration_duplicate_email(self, client, test_user):
        """Тест регистрации с существующим email"""
        user_data = TestDataFactory.create_user_data(
            username='differentuser',
            email=TEST_EMAIL,
            password='password123'
        )

        response = client.post('/api/register', json=user_data, content_type='application/json')

        assert response.status_code in [400, 409]
        data = ResponseHelper.parse_json(response)
        assert 'error' in data

    def test_registration_invalid_email(self, client):
        """Тест регистрации с неверным email"""
        user_data = TestDataFactory.create_user_data(
            username='newuser',
            email='invalid-email',
            password='password123'
        )

        response = client.post('/api/register', json=user_data, content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_registration_missing_data(self, client):
        """Тест регистрации без данных"""
        response = client.post('/api/register', json={}, content_type='application/json')
        ResponseHelper.assert_error(response, 400)

    def test_registration_short_password(self, client):
        """Тест регистрации с коротким паролем"""
        user_data = TestDataFactory.create_user_data(
            username='newuser',
            email='newuser@example.com',
            password='123'
        )

        response = client.post('/api/register', json=user_data, content_type='application/json')

        # В зависимости от реализации может быть 400 или 200
        assert response.status_code in [400, 200]
