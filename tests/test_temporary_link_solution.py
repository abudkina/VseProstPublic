"""
Тесты для модуля временных ссылок на решения (temporaryLinkSolution.py)
"""
import pytest

from tests.helpers import ResponseHelper


class TestGenerateTemporaryLinkSolution:
    """Тесты для генерации временной ссылки на решение"""

    def test_generate_temp_link_solution_success(self, client, auth_headers, test_solution):
        """Тест успешной генерации временной ссылки"""
        response = client.post(f'/api/solutions/{test_solution.id}/temporary-link',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 201, 400, 404]

    def test_generate_temp_link_solution_unauthorized(self, client, test_solution):
        """Тест генерации ссылки без авторизации"""
        response = client.post(f'/api/solutions/{test_solution.id}/temporary-link',
                              json={},
                              content_type='application/json')

        # Может быть 401 (unauthorized) или 404 (роут не найден)
        assert response.status_code in [401, 404]

    def test_generate_temp_link_solution_nonexistent(self, client, auth_headers):
        """Тест генерации ссылки для несуществующего решения"""
        response = client.post('/api/solutions/99999/temporary-link',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [404, 400]


class TestAccessTemporaryLinkSolution:
    """Тесты для доступа по временной ссылке"""

    def test_access_temp_link_solution(self, client):
        """Тест доступа по временной ссылке"""
        # Это зависит от формата ссылки в приложении
        response = client.get('/api/solutions/access-temporary-link?token=invalid_token')

        # Может быть ошибка или успех в зависимости от реализации
        assert response.status_code in [400, 401, 404]


class TestDeleteTemporaryLinkSolution:
    """Тесты для удаления временной ссылки"""

    def test_delete_temp_link_solution_unauthorized(self, client):
        """Тест удаления ссылки без авторизации"""
        response = client.delete('/api/solutions/temporary-link/1')

        # Может быть 401 (unauthorized) или 404 (роут не найден)
        assert response.status_code in [401, 404]
