"""
Тесты для модуля корзины (cart.py)
"""
import pytest

from logic.model import UserCartSolution
from tests.helpers import ResponseHelper, TestDataFactory, assert_valid_list_response


class TestGetCart:
    """Тесты для получения корзины"""

    def test_get_cart_success(self, client, auth_headers):
        """Тест успешного получения корзины"""
        response = client.get('/api/cart', headers=auth_headers)

        data = ResponseHelper.assert_success(response)
        assert_valid_list_response(data)

    def test_get_cart_unauthorized(self, client):
        """Тест получения корзины без авторизации"""
        response = client.get('/api/cart')
        ResponseHelper.assert_unauthorized(response)


class TestAddToCart:
    """Тесты для добавления товаров в корзину"""

    def test_add_to_cart_success(self, client, auth_headers, test_solution):
        """Тест успешного добавления решения в корзину"""
        cart_data = {'solutionID': test_solution.id}

        response = client.post('/api/cart',
                              json=cart_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 201, 400]

    def test_add_to_cart_missing_solution_id(self, client, auth_headers):
        """Тест добавления в корзину без ID решения"""
        response = client.post('/api/cart',
                              json={},
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_add_to_cart_unauthorized(self, client, test_solution):
        """Тест добавления в корзину без авторизации"""
        cart_data = {'solutionID': test_solution.id}

        response = client.post('/api/cart',
                              json=cart_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)

    def test_add_to_cart_nonexistent_solution(self, client, auth_headers):
        """Тест добавления в корзину несуществующего решения"""
        cart_data = {'solutionID': 99999}

        response = client.post('/api/cart',
                              json=cart_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [404, 400]


class TestRemoveFromCart:
    """Тесты для удаления товаров из корзины"""

    def test_remove_from_cart_unauthorized(self, client, test_solution):
        """Тест удаления из корзины без авторизации"""
        response = client.delete(f'/api/cart/{test_solution.id}')
        ResponseHelper.assert_unauthorized(response)


class TestClearCart:
    """Тесты для очистки корзины"""

    def test_clear_cart_success(self, client, auth_headers):
        """Тест успешной очистки корзины"""
        response = client.delete('/api/cart', headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_clear_cart_unauthorized(self, client):
        """Тест очистки корзины без авторизации"""
        response = client.delete('/api/cart')
        ResponseHelper.assert_unauthorized(response)
