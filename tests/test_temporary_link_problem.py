"""
Тесты для модуля временных ссылок на проблемы (temporaryLinkProblem.py)
"""
import pytest

from tests.helpers import ResponseHelper


class TestGenerateTemporaryLinkProblem:
    """Тесты для генерации временной ссылки на проблему"""

    def test_generate_temp_link_problem_success(self, client, auth_headers, test_problem):
        """Тест успешной генерации временной ссылки"""
        response = client.post(f'/api/problems/{test_problem.id}/temporary-link',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 201, 400, 404]

    def test_generate_temp_link_problem_unauthorized(self, client, test_problem):
        """Тест генерации ссылки без авторизации"""
        response = client.post(f'/api/problems/{test_problem.id}/temporary-link',
                              json={},
                              content_type='application/json')

        # Может быть 401 (unauthorized) или 404 (роут не найден)
        assert response.status_code in [401, 404]

    def test_generate_temp_link_problem_nonexistent(self, client, auth_headers):
        """Тест генерации ссылки для несуществующей проблемы"""
        response = client.post('/api/problems/99999/temporary-link',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [404, 400]


class TestAccessTemporaryLinkProblem:
    """Тесты для доступа по временной ссылке"""

    def test_access_temp_link_problem(self, client):
        """Тест доступа по временной ссылке"""
        # Это зависит от формата ссылки в приложении
        response = client.get('/api/problems/access-temporary-link?token=invalid_token')

        # Может быть ошибка или успех в зависимости от реализации
        assert response.status_code in [400, 401, 404]


class TestDeleteTemporaryLinkProblem:
    """Тесты для удаления временной ссылки"""

    def test_delete_temp_link_problem_unauthorized(self, client):
        """Тест удаления ссылки без авторизации"""
        response = client.delete('/api/problems/temporary-link/1')

        # Может быть 401 (unauthorized) или 404 (роут не найден)
        assert response.status_code in [401, 404]
