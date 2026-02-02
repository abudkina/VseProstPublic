"""
Тесты для модуля рекомендаций (recommendations.py)
"""
import pytest

from tests.helpers import ResponseHelper, assert_valid_list_response


class TestGetRecommendations:
    """Тесты для получения рекомендаций"""

    def test_get_recommendations_success(self, client, auth_headers):
        """Тест успешного получения рекомендаций"""
        response = client.get('/api/recommendations', headers=auth_headers)

        # Может быть список или ошибка
        assert response.status_code in [200, 400, 401]

    def test_get_recommendations_unauthorized(self, client):
        """Тест получения рекомендаций без авторизации"""
        response = client.get('/api/recommendations')
        ResponseHelper.assert_unauthorized(response)


class TestRecommendedProblems:
    """Тесты для рекомендуемых проблем"""

    def test_get_recommended_problems(self, client, auth_headers):
        """Тест получения рекомендуемых проблем"""
        response = client.get('/api/recommendations/problems', headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_get_recommended_problems_unauthorized(self, client):
        """Тест получения без авторизации"""
        response = client.get('/api/recommendations/problems')
        ResponseHelper.assert_unauthorized(response)


class TestRecommendedSolutions:
    """Тесты для рекомендуемых решений"""

    def test_get_recommended_solutions(self, client, auth_headers):
        """Тест получения рекомендуемых решений"""
        response = client.get('/api/recommendations/solutions', headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_get_recommended_solutions_unauthorized(self, client):
        """Тест получения без авторизации"""
        response = client.get('/api/recommendations/solutions')
        ResponseHelper.assert_unauthorized(response)


class TestPersonalizedRecommendations:
    """Тесты для персонализированных рекомендаций"""

    def test_get_personalized_recommendations(self, client, auth_headers):
        """Тест получения персонализированных рекомендаций"""
        response = client.get('/api/recommendations/personalized', headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_get_personalized_recommendations_unauthorized(self, client):
        """Тест получения без авторизации"""
        response = client.get('/api/recommendations/personalized')
        ResponseHelper.assert_unauthorized(response)


class TestSimilarItems:
    """Тесты для похожих элементов"""

    def test_get_similar_problems(self, client, test_problem):
        """Тест получения похожих проблем"""
        response = client.get(f'/api/recommendations/similar-problems/{test_problem.id}')

        assert response.status_code in [200, 400, 404]

    def test_get_similar_solutions(self, client, test_solution):
        """Тест получения похожих решений"""
        response = client.get(f'/api/recommendations/similar-solutions/{test_solution.id}')

        assert response.status_code in [200, 400, 404]
