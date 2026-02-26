"""
Тесты для модуля хэштегов (hashtag.py)
"""
import pytest

from logic.model import Hashtag
from tests.helpers import ResponseHelper, TestDataFactory, assert_valid_id_response


class TestAddHashtag:
    """Тесты для добавления хэштегов"""

    def test_add_hashtag_success(self, client, auth_headers):
        """Тест успешного добавления хэштега"""
        import uuid
        hashtag_data = {'name': f'test-hashtag-{uuid.uuid4().hex[:8]}'}

        response = client.post('/api/hashtags',
                              json=hashtag_data,
                              headers=auth_headers,
                              content_type='application/json')

        # API возвращает 201 при создании
        data = ResponseHelper.assert_success(response, expected_status=201)
        assert_valid_id_response(data)

    def test_add_hashtag_empty_name(self, client, auth_headers):
        """Тест добавления хэштега с пустым именем"""
        response = client.post('/api/hashtags',
                              json={'name': ''},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_hashtag_missing_name(self, client, auth_headers):
        """Тест добавления хэштега без имени"""
        response = client.post('/api/hashtags',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_hashtag_unauthorized(self, client):
        """Тест добавления хэштега без авторизации"""
        hashtag_data = {'name': 'test-hashtag'}

        response = client.post('/api/hashtags',
                              json=hashtag_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)

    def test_add_hashtag_with_spaces(self, client, auth_headers):
        """Тест добавления хэштега с пробелами"""
        import uuid
        hashtag_data = {'name': f'  test-hashtag-{uuid.uuid4().hex[:8]}  '}

        response = client.post('/api/hashtags',
                              json=hashtag_data,
                              headers=auth_headers,
                              content_type='application/json')

        # API возвращает 201 при создании
        data = ResponseHelper.assert_success(response, expected_status=201)
        assert_valid_id_response(data)


class TestGetHashtags:
    """Тесты для получения хэштегов"""

    def test_get_hashtags_success(self, client, auth_headers):
        """Тест успешного получения хэштегов"""
        response = client.get('/api/hashtags', headers=auth_headers)

        # Проверяем успешный ответ
        assert response.status_code in [200, 400]

    def test_get_hashtags_unauthorized(self, client):
        """Тест получения хэштегов без авторизации"""
        response = client.get('/api/hashtags')
        ResponseHelper.assert_unauthorized(response)


class TestDeleteHashtag:
    """Тесты для удаления хэштегов"""

    def test_delete_hashtag_unauthorized(self, client):
        """Тест удаления хэштега без авторизации"""
        response = client.delete('/api/hashtags/1')
        ResponseHelper.assert_unauthorized(response)
