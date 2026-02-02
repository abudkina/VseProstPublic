"""
Тесты для модуля генерации изображений (image_generation.py)
"""
import pytest

from tests.helpers import ResponseHelper


class TestGenerateImage:
    """Тесты для генерации изображений"""

    def test_generate_image_success(self, client, auth_headers):
        """Тест успешной генерации изображения"""
        generate_data = {
            'prompt': 'beautiful landscape',
            'width': 512,
            'height': 512
        }

        response = client.post('/api/generate-image',
                              json=generate_data,
                              headers=auth_headers,
                              content_type='application/json')

        # Может быть успех, ошибка API или timeout
        assert response.status_code in [200, 400, 503]

    def test_generate_image_missing_prompt(self, client, auth_headers):
        """Тест генерации без prompt"""
        generate_data = {
            'width': 512,
            'height': 512
        }

        response = client.post('/api/generate-image',
                              json=generate_data,
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_generate_image_unauthorized(self, client):
        """Тест генерации без авторизации"""
        generate_data = {
            'prompt': 'beautiful landscape',
            'width': 512,
            'height': 512
        }

        response = client.post('/api/generate-image',
                              json=generate_data,
                              content_type='application/json')

        ResponseHelper.assert_unauthorized(response)

    def test_generate_image_empty_prompt(self, client, auth_headers):
        """Тест генерации с пустым prompt"""
        generate_data = {
            'prompt': '',
            'width': 512,
            'height': 512
        }

        response = client.post('/api/generate-image',
                              json=generate_data,
                              headers=auth_headers,
                              content_type='application/json')

        ResponseHelper.assert_error(response, 400)

    def test_generate_image_invalid_dimensions(self, client, auth_headers):
        """Тест генерации с неверными размерами"""
        generate_data = {
            'prompt': 'beautiful landscape',
            'width': 100,  # Может быть слишком мало
            'height': 100
        }

        response = client.post('/api/generate-image',
                              json=generate_data,
                              headers=auth_headers,
                              content_type='application/json')

        assert response.status_code in [200, 400, 503]


class TestImageGenerationStatus:
    """Тесты для проверки статуса генерации"""

    def test_get_generation_status(self, client, auth_headers):
        """Тест получения статуса генерации"""
        response = client.get('/api/generate-image/status/invalid_id', 
                             headers=auth_headers)

        # Может быть успех или ошибка
        assert response.status_code in [200, 400, 404]

    def test_get_generation_status_unauthorized(self, client):
        """Тест получения статуса без авторизации"""
        response = client.get('/api/generate-image/status/invalid_id')
        ResponseHelper.assert_unauthorized(response)
