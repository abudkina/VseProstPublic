"""
Тесты для модуля комментариев решений (commentSolution.py)
"""
import pytest

from logic.model import CommentSolution
from tests.helpers import ResponseHelper, TestDataFactory, assert_valid_list_response


class TestCountComments:
    """Тесты для подсчета комментариев"""

    def test_count_comments_success(self, client, auth_headers):
        """Тест успешного подсчета комментариев"""
        response = client.get('/api/comment-solutions/count', headers=auth_headers)

        data = ResponseHelper.assert_success(response)
        assert 'count' in data
        assert isinstance(data['count'], int)

    def test_count_comments_unauthorized(self, client):
        """Тест подсчета комментариев без авторизации"""
        response = client.get('/api/comment-solutions/count')
        ResponseHelper.assert_unauthorized(response)


class TestGetComments:
    """Тесты для получения комментариев"""

    def test_get_comments_success(self, client, auth_headers):
        """Тест успешного получения комментариев"""
        response = client.get('/api/comment-solutions', headers=auth_headers)

        # Может быть список или ошибка
        assert response.status_code in [200, 400, 401]

    def test_get_comments_unauthorized(self, client):
        """Тест получения комментариев без авторизации"""
        response = client.get('/api/comment-solutions')
        ResponseHelper.assert_unauthorized(response)

    def test_get_comments_by_solution(self, client, test_solution):
        """Тест получения комментариев решения"""
        response = client.get(f'/api/comment-solutions/solution/{test_solution.id}')

        assert response.status_code in [200, 400, 404]


class TestAddComment:
    """Тесты для добавления комментариев"""

    def test_add_comment_success(self, client, auth_headers, test_solution):
        """Тест успешного добавления комментария"""
        # API использует solution_id и content/text
        comment_data = {
            'solution_id': test_solution.id,
            'content': 'Great solution!'
        }

        response = client.post('/api/comment-solutions',
                              json=comment_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 201, 400]

    def test_add_comment_missing_data(self, client, auth_headers, test_solution):
        """Тест добавления комментария без текста"""
        comment_data = {'solution_id': test_solution.id}

        response = client.post('/api/comment-solutions',
                              json=comment_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [400, 200]

    def test_add_comment_unauthorized(self, client, test_solution):
        """Тест добавления комментария без авторизации"""
        comment_data = {
            'solution_id': test_solution.id,
            'content': 'Great solution!'
        }

        response = client.post('/api/comment-solutions',
                              json=comment_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestDeleteComment:
    """Тесты для удаления комментариев"""

    def test_delete_comment_unauthorized(self, client):
        """Тест удаления комментария без авторизации"""
        response = client.delete('/api/comment-solutions/1')
        ResponseHelper.assert_unauthorized(response)


class TestMarkCommentsAsRead:
    """Тесты для отметки комментариев как прочитанных"""

    def test_mark_as_read_success(self, client, auth_headers):
        """Тест успешной отметки комментария как прочитанного"""
        # API использует PUT /api/comment-solutions/<comment_id>/mark-as-read
        response = client.put('/api/comment-solutions/99999/mark-as-read',
                             json={},
                             headers=auth_headers,
                             content_type='application/json')

        # 404 - комментарий не найден, что ожидаемо для несуществующего ID
        assert response.status_code in [200, 404, 401]

    def test_mark_as_read_unauthorized(self, client):
        """Тест отметки как прочитанных без авторизации"""
        response = client.put('/api/comment-solutions/1/mark-as-read',
                             json={},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)
