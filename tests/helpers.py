"""
Вспомогательные утилиты для тестов
"""
import json
from typing import Any, Dict, List, Optional
from flask.testing import FlaskClient


class ResponseHelper:
    """Вспомогательный класс для работы с ответами API"""

    @staticmethod
    def parse_json(response) -> Dict[str, Any]:
        """Парсит JSON из ответа"""
        return json.loads(response.data)

    @staticmethod
    def assert_success(response, expected_status: int = 200):
        """Проверяет успешный ответ"""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.data}"
        return ResponseHelper.parse_json(response)

    @staticmethod
    def assert_error(response, expected_status: int = 400):
        """Проверяет ответ с ошибкой"""
        assert response.status_code == expected_status, \
            f"Expected status {expected_status}, got {response.status_code}. Response: {response.data}"
        data = ResponseHelper.parse_json(response)
        assert 'error' in data, "Error response should contain 'error' field"
        return data

    @staticmethod
    def assert_unauthorized(response):
        """Проверяет неавторизованный ответ"""
        return ResponseHelper.assert_error(response, 401)

    @staticmethod
    def assert_forbidden(response):
        """Проверяет запрещенный ответ"""
        return ResponseHelper.assert_error(response, 403)

    @staticmethod
    def assert_not_found(response):
        """Проверяет ответ 404"""
        return ResponseHelper.assert_error(response, 404)

    @staticmethod
    def assert_has_fields(data: Dict, fields: List[str]):
        """Проверяет наличие полей в данных"""
        for field in fields:
            assert field in data, f"Field '{field}' not found in response data"

    @staticmethod
    def assert_has_any_field(data: Dict, fields: List[str]):
        """Проверяет наличие хотя бы одного из полей"""
        found = any(field in data for field in fields)
        assert found, f"None of fields {fields} found in response data"


class APITestHelper:
    """Базовый класс для тестирования API"""

    def __init__(self, client: FlaskClient):
        self.client = client
        self.response_helper = ResponseHelper()

    def get(self, url: str, headers: Optional[Dict] = None, expected_status: int = 200):
        """GET запрос с проверкой статуса"""
        response = self.client.get(url, headers=headers)
        assert response.status_code == expected_status
        return ResponseHelper.parse_json(response)

    def post(self, url: str, data: Dict, headers: Optional[Dict] = None, expected_status: int = 200):
        """POST запрос с проверкой статуса"""
        response = self.client.post(url, json=data, headers=headers, content_type='application/json')
        assert response.status_code == expected_status
        return ResponseHelper.parse_json(response)

    def put(self, url: str, data: Dict, headers: Optional[Dict] = None, expected_status: int = 200):
        """PUT запрос с проверкой статуса"""
        response = self.client.put(url, json=data, headers=headers, content_type='application/json')
        assert response.status_code == expected_status
        return ResponseHelper.parse_json(response)

    def delete(self, url: str, headers: Optional[Dict] = None, expected_status: int = 200):
        """DELETE запрос с проверкой статуса"""
        response = self.client.delete(url, headers=headers)
        assert response.status_code == expected_status
        if response.data:
            return ResponseHelper.parse_json(response)
        return None


class TestDataFactory:
    """Фабрика для создания тестовых данных"""

    @staticmethod
    def create_user_data(username: str = "testuser", email: str = "test@example.com",
                        password: str = "testpassword123") -> Dict[str, str]:
        """Создает данные пользователя для регистрации"""
        return {
            'username': username,
            'email': email,
            'password': password
        }

    @staticmethod
    def create_login_data(login: str = "testuser", password: str = "testpassword123") -> Dict[str, str]:
        """Создает данные для входа"""
        return {
            'login': login,
            'password': password
        }

    @staticmethod
    def create_problem_data(name: str = "Test Problem", describe: str = "Test description",
                           category: int = 1, image: str = "test.png") -> Dict[str, Any]:
        """Создает данные проблемы"""
        return {
            'name': name,
            'describe': describe,
            'category': category,
            'image': image
        }

    @staticmethod
    def create_solution_data(name: str = "Test Solution", describe: str = "Test description",
                            image: str = "test.png", price: float = 100.00) -> Dict[str, Any]:
        """Создает данные решения"""
        return {
            'name': name,
            'describe': describe,
            'image': image,
            'price': price
        }

    @staticmethod
    def create_category_data(name: str = "Test Category") -> Dict[str, str]:
        """Создает данные категории"""
        return {'name': name}


def assert_valid_token_response(data: Dict):
    """Проверяет корректность ответа с токеном"""
    ResponseHelper.assert_has_fields(data, ['message', 'accessExpiry'])
    # Опционально могут быть userID и username


def assert_valid_user_response(data: Dict):
    """Проверяет корректность ответа с данными пользователя"""
    # ID может быть в разных форматах
    ResponseHelper.assert_has_any_field(data, ['id', 'ID', 'userID'])


def assert_valid_list_response(data):
    """Проверяет, что ответ - это список"""
    assert isinstance(data, list), f"Expected list, got {type(data)}"


def assert_valid_id_response(data: Dict):
    """Проверяет наличие ID в ответе"""
    ResponseHelper.assert_has_any_field(data, ['id', 'ID'])
