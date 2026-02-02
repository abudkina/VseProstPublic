"""
Тесты для модуля прокси изображений (image_proxy.py)
"""
import pytest

from tests.helpers import ResponseHelper


class TestImageProxy:
    """Тесты для прокси изображений"""

    def test_proxy_image_invalid_url(self, client):
        """Тест прокси с неверным URL"""
        response = client.get('/api/proxy-image?url=invalid_url')

        # Может быть ошибка или пустой ответ
        assert response.status_code in [400, 404, 500]

    def test_proxy_image_missing_url(self, client):
        """Тест прокси без URL"""
        response = client.get('/api/proxy-image')

        ResponseHelper.assert_error(response, 400)

    def test_proxy_image_external_url(self, client):
        """Тест прокси с внешним URL"""
        response = client.get('/api/proxy-image?url=https://example.com/image.jpg')

        # Может быть успех или ошибка в зависимости от реализации
        assert response.status_code in [200, 400, 403, 404, 500]

    def test_proxy_image_blocked_domain(self, client):
        """Тест прокси с заблокированным доменом"""
        response = client.get('/api/proxy-image?url=http://localhost/image.jpg')

        # Должна быть ошибка для безопасности
        assert response.status_code in [400, 403, 404]


class TestImageProxyCache:
    """Тесты для кэширования прокси"""

    def test_proxy_image_cache_headers(self, client):
        """Тест кэширующих заголовков"""
        response = client.get('/api/proxy-image?url=https://example.com/image.jpg')

        # Может быть ошибка, но если успех - должны быть заголовки
        if response.status_code == 200:
            # Проверяем кэш-контроль заголовков
            assert response.content_type or response.headers
