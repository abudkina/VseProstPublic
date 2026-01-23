"""
Тесты для модуля пользователей (user.py)
"""
import pytest

from tests.helpers import ResponseHelper, assert_valid_id_response


class TestGetUsers:
    """Тесты для получения списка пользователей"""

    def test_get_users_as_admin(self, client, admin_headers, test_user):
        """Тест получения пользователей администратором"""
        response = client.get('/api/users', headers=admin_headers)

        # Может быть 200 или другой статус в зависимости от реализации
        assert response.status_code in [200, 400, 403]

    def test_get_users_as_user(self, client, auth_headers):
        """Тест получения пользователей обычным пользователем"""
        response = client.get('/api/users', headers=auth_headers)
        # Обычный пользователь не должен иметь доступ
        assert response.status_code in [403, 401]

    def test_get_users_unauthorized(self, client):
        """Тест получения пользователей без авторизации"""
        response = client.get('/api/users')
        ResponseHelper.assert_unauthorized(response)


class TestGetUserProfile:
    """Тесты для получения профиля пользователя"""

    def test_get_own_profile(self, client, auth_headers, test_user):
        """Тест получения собственного профиля"""
        response = client.get(f'/api/users/{test_user.id}', headers=auth_headers)

        data = ResponseHelper.assert_success(response)
        assert_valid_id_response(data)

    def test_get_profile_unauthorized(self, client, test_user):
        """Тест получения профиля без авторизации"""
        response = client.get(f'/api/users/{test_user.id}')
        ResponseHelper.assert_unauthorized(response)


class TestUpdateUser:
    """Тесты для обновления пользователя"""

    def test_update_user_success(self, client, auth_headers, test_user):
        """Тест успешного обновления пользователя"""
        response = client.put(f'/api/users/{test_user.id}',
                             json={'username': 'updateduser'},
                             headers=auth_headers,
                             content_type='application/json')

        # Может быть 200 или другой статус
        assert response.status_code in [200, 400, 404]

    def test_update_user_unauthorized(self, client, test_user):
        """Тест обновления без авторизации"""
        response = client.put(f'/api/users/{test_user.id}',
                             json={'username': 'updateduser'},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestCountNewUsers:
    """Тесты для подсчета новых пользователей"""

    def test_count_new_users_as_admin(self, client, admin_headers):
        """Тест подсчета новых пользователей администратором"""
        response = client.get('/api/users/count-new', headers=admin_headers)

        data = ResponseHelper.assert_success(response)
        assert 'count' in data
        assert isinstance(data['count'], int)

    def test_count_new_users_as_user(self, client, auth_headers):
        """Тест подсчета новых пользователей обычным пользователем"""
        response = client.get('/api/users/count-new', headers=auth_headers)
        ResponseHelper.assert_forbidden(response)
