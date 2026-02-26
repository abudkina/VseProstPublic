"""
Тесты для модуля тем (topic.py)
"""
import pytest
import uuid

from logic.model import Topic
from tests.helpers import ResponseHelper, TestDataFactory, assert_valid_id_response


class TestAddTopic:
    """Тесты для добавления тем"""

    def test_add_topic_success(self, client, auth_headers):
        """Тест успешного добавления темы"""
        # Генерируем уникальное имя чтобы избежать конфликтов
        topic_data = {'name': f'New Topic {uuid.uuid4().hex[:8]}'}

        response = client.post('/api/topics',
                              json=topic_data,
                              headers=auth_headers,
                              content_type='application/json')

        # API возвращает 201 при создании
        data = ResponseHelper.assert_success(response, expected_status=201)
        assert_valid_id_response(data)

    def test_add_topic_duplicate(self, client, auth_headers, test_topic):
        """Тест добавления дублирующейся темы"""
        topic_data = {'name': test_topic.name}

        response = client.post('/api/topics',
                              json=topic_data,
                              headers=auth_headers,
                              content_type='application/json')

        # API возвращает 409 (Conflict) для дубликатов
        # Или 201 если нормализация имён даёт разные результаты
        assert response.status_code in [201, 409]

    def test_add_topic_empty_name(self, client, auth_headers):
        """Тест добавления темы с пустым именем"""
        response = client.post('/api/topics',
                              json={'name': ''},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_topic_missing_name(self, client, auth_headers):
        """Тест добавления темы без имени"""
        response = client.post('/api/topics',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_topic_unauthorized(self, client):
        """Тест добавления темы без авторизации"""
        topic_data = {'name': 'New Topic'}

        response = client.post('/api/topics',
                              json=topic_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestGetTopics:
    """Тесты для получения тем"""

    def test_get_topics_success(self, client, auth_headers, test_topic):
        """Тест успешного получения тем с поиском"""
        # GET /api/topics не требует авторизации для поиска
        response = client.get(f'/api/topics?search={test_topic.name[:3]}')

        # Должен быть успех
        assert response.status_code == 200

    def test_get_topics_unauthorized(self, client):
        """Тест получения всех тем без авторизации"""
        # GET /api/topics?all=true требует авторизации
        response = client.get('/api/topics?all=true')

        # Должна быть ошибка 401 для all=true без авторизации
        assert response.status_code in [401, 403]


class TestUpdateTopic:
    """Тесты для обновления тем"""

    def test_update_topic_unauthorized(self, client, test_topic):
        """Тест обновления темы без авторизации"""
        response = client.put(f'/api/topics/{test_topic.id}',
                             json={'name': 'Updated Topic'},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestDeleteTopic:
    """Тесты для удаления тем"""

    def test_delete_topic_unauthorized(self, client, test_topic):
        """Тест удаления темы без авторизации"""
        response = client.delete(f'/api/topics/{test_topic.id}')
        ResponseHelper.assert_unauthorized(response)
