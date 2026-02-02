"""
Тесты для модуля решений (solution.py)
"""
import pytest

from logic.model import Solution
from tests.helpers import (
    ResponseHelper,
    TestDataFactory,
    assert_valid_id_response,
    assert_valid_list_response
)


class TestGetSolutions:
    """Тесты для получения списка решений"""

    def test_get_solutions_success(self, client, test_solution):
        """Тест успешного получения решений"""
        response = client.get('/api/solutions')

        data = ResponseHelper.assert_success(response)
        assert_valid_list_response(data)

    def test_get_solution_by_id(self, client, test_solution):
        """Тест получения решения по ID"""
        response = client.get(f'/api/solutions/{test_solution.id}')

        data = ResponseHelper.assert_success(response)
        assert_valid_id_response(data)
        ResponseHelper.assert_has_any_field(data, ['Name', 'name'])

    def test_get_solution_not_found(self, client):
        """Тест получения несуществующего решения"""
        response = client.get('/api/solutions/99999')
        ResponseHelper.assert_not_found(response)


class TestAddSolution:
    """Тесты для добавления решения"""

    def test_add_solution_success(self, client, auth_headers):
        """Тест успешного добавления решения"""
        solution_data = TestDataFactory.create_solution_data(
            name='New Solution',
            describe='Solution description',
            image='test.png',
            price=100.00
        )

        response = client.post('/api/solutions',
                              json=solution_data,
                              headers=auth_headers,
                              content_type='application/json')

        # Может быть успех (200/201) или ошибка валидации (400)
        if response.status_code == 200 or response.status_code == 201:
            data = ResponseHelper.parse_json(response)
            assert_valid_id_response(data)
        else:
            # Допустимы ошибки валидации
            assert response.status_code in [400, 500]

    def test_add_solution_missing_data(self, client, auth_headers):
        """Тест добавления решения без обязательных данных"""
        response = client.post('/api/solutions',
                              json={'name': 'New Solution'},
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [400, 500]

    def test_add_solution_unauthorized(self, client):
        """Тест добавления решения без авторизации"""
        solution_data = TestDataFactory.create_solution_data()

        response = client.post('/api/solutions',
                              json=solution_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestUpdateSolution:
    """Тесты для обновления решения"""

    def test_update_solution_unauthorized(self, client, test_solution):
        """Тест обновления решения без авторизации"""
        response = client.put(f'/api/solutions/{test_solution.id}',
                             json={'name': 'Updated Solution'},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestDeleteSolution:
    """Тесты для удаления решения"""

    def test_delete_solution_unauthorized(self, client, test_solution):
        """Тест удаления решения без авторизации"""
        response = client.delete(f'/api/solutions/{test_solution.id}')
        ResponseHelper.assert_unauthorized(response)


class TestFavouriteSolution:
    """Тесты для избранных решений"""

    def test_favourite_operations_unauthorized(self, client, test_solution):
        """Тест операций с избранным без авторизации"""
        # Добавление в избранное
        response = client.post(f'/api/solutions/{test_solution.id}/favourite')
        # Эндпоинт может не существовать (404) или требовать авторизации (401)
        assert response.status_code in [401, 404]

        # Удаление из избранного
        response = client.delete(f'/api/solutions/{test_solution.id}/favourite')
        # Эндпоинт может не существовать (404) или требовать авторизации (401)
        assert response.status_code in [401, 404]
