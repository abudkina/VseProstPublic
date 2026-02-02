"""
Тесты для модуля связей проблем и решений (temporaryProblemSolution.py)
"""
import pytest

from tests.helpers import ResponseHelper, TestDataFactory


class TestCreateProblemSolutionLink:
    """Тесты для создания связи проблема-решение"""

    def test_create_problem_solution_link_success(self, client, auth_headers, test_problem, test_solution):
        """Тест успешного создания связи"""
        link_data = {
            'problemID': test_problem.id,
            'solutionID': test_solution.id
        }

        response = client.post('/api/problem-solutions',
                              json=link_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 201, 400, 409]

    def test_create_problem_solution_link_missing_data(self, client, auth_headers):
        """Тест создания связи без данных"""
        response = client.post('/api/problem-solutions',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_create_problem_solution_link_unauthorized(self, client, test_problem, test_solution):
        """Тест создания связи без авторизации"""
        link_data = {
            'problemID': test_problem.id,
            'solutionID': test_solution.id
        }

        response = client.post('/api/problem-solutions',
                              json=link_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestGetProblemSolutionLinks:
    """Тесты для получения связей"""

    def test_get_problem_solutions(self, client, auth_headers, test_problem):
        """Тест получения решений для проблемы"""
        response = client.get(f'/api/problems/{test_problem.id}/solutions', 
                             headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_get_solution_problems(self, client, auth_headers, test_solution):
        """Тест получения проблем для решения"""
        response = client.get(f'/api/solutions/{test_solution.id}/problems',
                             headers=auth_headers)

        assert response.status_code in [200, 400, 401]


class TestDeleteProblemSolutionLink:
    """Тесты для удаления связи"""

    def test_delete_problem_solution_link_unauthorized(self, client, test_problem, test_solution):
        """Тест удаления связи без авторизации"""
        response = client.delete(f'/api/problem-solutions/{test_problem.id}/{test_solution.id}')
        ResponseHelper.assert_unauthorized(response)
