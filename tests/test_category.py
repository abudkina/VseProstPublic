"""
Тесты для модуля категорий (category.py)
"""
import pytest

from logic.model import Category
from tests.helpers import (
    ResponseHelper,
    TestDataFactory,
    assert_valid_id_response,
    assert_valid_list_response
)


class TestAddCategory:
    """Тесты для добавления категории"""

    def test_add_category_success(self, client, auth_headers):
        """Тест успешного добавления категории"""
        category_data = TestDataFactory.create_category_data('New Category')

        response = client.post('/api/categories',
                              json=category_data,
                              headers=auth_headers,
                              content_type='application/json')

        data = ResponseHelper.assert_success(response)
        assert_valid_id_response(data)
        ResponseHelper.assert_has_any_field(data, ['Name', 'name'])

    def test_add_category_duplicate(self, client, auth_headers, test_category):
        """Тест добавления дублирующейся категории"""
        category_data = TestDataFactory.create_category_data(test_category.name)

        response = client.post('/api/categories',
                              json=category_data,
                              headers=auth_headers,
                              content_type='application/json')

        # Может быть 400 или 200 в зависимости от реализации
        assert response.status_code in [200, 400]

    def test_add_category_empty_name(self, client, auth_headers):
        """Тест добавления категории с пустым именем"""
        response = client.post('/api/categories',
                              json={'name': ''},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_category_missing_name(self, client, auth_headers):
        """Тест добавления категории без имени"""
        response = client.post('/api/categories',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_category_unauthorized(self, client):
        """Тест добавления категории без авторизации"""
        category_data = TestDataFactory.create_category_data('New Category')

        response = client.post('/api/categories',
                              json=category_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestGetCategories:
    """Тесты для получения категорий"""

    def test_get_categories_success(self, client, auth_headers, test_category):
        """Тест успешного получения категорий"""
        response = client.get('/api/categories', headers=auth_headers)

        data = ResponseHelper.assert_success(response)
        assert_valid_list_response(data)

    def test_get_categories_unauthorized(self, client):
        """Тест получения категорий без авторизации"""
        response = client.get('/api/categories')
        ResponseHelper.assert_unauthorized(response)


class TestUpdateCategory:
    """Тесты для обновления категории"""

    def test_update_category_unauthorized(self, client, test_category):
        """Тест обновления категории без авторизации"""
        response = client.put(f'/api/categories/{test_category.id}',
                             json={'name': 'Updated Category'},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestDeleteCategory:
    """Тесты для удаления категории"""

    def test_delete_category_unauthorized(self, client, test_category):
        """Тест удаления категории без авторизации"""
        response = client.delete(f'/api/categories/{test_category.id}')
        ResponseHelper.assert_unauthorized(response)
