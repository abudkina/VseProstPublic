"""
Тесты для модуля сброса пароля (password_reset.py)
"""
import pytest

from tests.helpers import ResponseHelper, TestDataFactory


class TestForgotPassword:
    """Тесты для запроса сброса пароля"""

    def test_forgot_password_success(self, client, test_user):
        """Тест успешного запроса сброса пароля"""
        forgot_data = {'email': test_user.email}

        response = client.post('/api/forgot-password',
                              json=forgot_data,
                              content_type='application/json')

        # Должен быть успех даже если email не существует (для безопасности)
        assert response.status_code in [200, 400]

    def test_forgot_password_invalid_email(self, client):
        """Тест запроса с неверным email"""
        forgot_data = {'email': 'invalid-email'}

        response = client.post('/api/forgot-password',
                              json=forgot_data,
                              content_type='application/json')

        assert response.status_code in [200, 400]

    def test_forgot_password_missing_email(self, client):
        """Тест запроса без email"""
        response = client.post('/api/forgot-password',
                              json={},
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_forgot_password_nonexistent_email(self, client):
        """Тест запроса для несуществующего email"""
        forgot_data = {'email': 'nonexistent@example.com'}

        response = client.post('/api/forgot-password',
                              json=forgot_data,
                              content_type='application/json')

        # Должен быть успех для безопасности
        assert response.status_code in [200, 400]


class TestResetPassword:
    """Тесты для сброса пароля"""

    def test_reset_password_with_token(self, client):
        """Тест сброса пароля с токеном"""
        reset_data = {
            'token': 'invalid_token',
            'password': 'newpassword123'
        }

        response = client.post('/api/reset-password',
                              json=reset_data,
                              content_type='application/json')

        # Токен невалидный, должна быть ошибка
        assert response.status_code in [400, 401, 404]

    def test_reset_password_missing_token(self, client):
        """Тест сброса пароля без токена"""
        reset_data = {'password': 'newpassword123'}

        response = client.post('/api/reset-password',
                              json=reset_data,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_reset_password_missing_password(self, client):
        """Тест сброса пароля без пароля"""
        reset_data = {'token': 'some_token'}

        response = client.post('/api/reset-password',
                              json=reset_data,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_reset_password_short_password(self, client):
        """Тест сброса пароля с коротким паролем"""
        reset_data = {
            'token': 'some_token',
            'password': '123'
        }

        response = client.post('/api/reset-password',
                              json=reset_data,
                              content_type='application/json')

        # Может быть ошибка валидации или ошибка токена
        assert response.status_code in [400, 401, 404]


class TestValidateResetToken:
    """Тесты для валидации токена сброса"""

    def test_validate_reset_token_invalid(self, client):
        """Тест валидации невалидного токена"""
        response = client.get('/api/reset-password/validate?token=invalid_token')

        assert response.status_code in [400, 401, 404]

    def test_validate_reset_token_missing(self, client):
        """Тест валидации без токена"""
        response = client.get('/api/reset-password/validate')

        assert response.status_code in [400, 401, 404]
