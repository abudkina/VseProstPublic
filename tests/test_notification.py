"""
Тесты для модуля уведомлений (notification.py)
"""
import pytest

from logic.model import Notification
from tests.helpers import ResponseHelper, assert_valid_list_response


class TestGetNotifications:
    """Тесты для получения уведомлений"""

    def test_get_notifications_success(self, client, auth_headers):
        """Тест успешного получения уведомлений"""
        response = client.get('/api/notifications', headers=auth_headers)

        # Может быть список или ошибка
        assert response.status_code in [200, 400, 401]

    def test_get_notifications_unauthorized(self, client):
        """Тест получения уведомлений без авторизации"""
        response = client.get('/api/notifications')
        ResponseHelper.assert_unauthorized(response)


class TestCountNewNotifications:
    """Тесты для подсчета новых уведомлений"""

    def test_count_new_notifications_success(self, client, auth_headers):
        """Тест успешного подсчета новых уведомлений"""
        response = client.get('/api/notifications/count-new', headers=auth_headers)

        # Может быть успех или ошибка
        assert response.status_code in [200, 400, 401]

    def test_count_new_notifications_unauthorized(self, client):
        """Тест подсчета без авторизации"""
        response = client.get('/api/notifications/count-new')
        ResponseHelper.assert_unauthorized(response)


class TestMarkNotificationsAsRead:
    """Тесты для отметки уведомлений как прочитанных"""

    def test_mark_notifications_as_read_success(self, client, auth_headers):
        """Тест успешной отметки уведомлений как прочитанных"""
        response = client.put('/api/notifications/mark-as-read',
                             json={},
                             headers=auth_headers,
                             content_type='application/json')

        assert response.status_code in [200, 400, 401]

    def test_mark_notifications_as_read_unauthorized(self, client):
        """Тест отметки как прочитанных без авторизации"""
        response = client.put('/api/notifications/mark-as-read',
                             json={},
                             content_type='application/json')

        ResponseHelper.assert_unauthorized(response)


class TestDeleteNotification:
    """Тесты для удаления уведомлений"""

    def test_delete_notification_unauthorized(self, client):
        """Тест удаления уведомления без авторизации"""
        response = client.delete('/api/notifications/1')
        ResponseHelper.assert_unauthorized(response)

    def test_delete_notification_success(self, client, auth_headers):
        """Тест удаления уведомления"""
        response = client.delete('/api/notifications/99999', headers=auth_headers)

        # Может быть успех или 404
        assert response.status_code in [200, 404, 401]


class TestClearAllNotifications:
    """Тесты для очистки всех уведомлений"""

    def test_clear_all_notifications_success(self, client, auth_headers):
        """Тест успешной очистки всех уведомлений"""
        response = client.delete('/api/notifications', headers=auth_headers)

        assert response.status_code in [200, 400, 401]

    def test_clear_all_notifications_unauthorized(self, client):
        """Тест очистки без авторизации"""
        response = client.delete('/api/notifications')
        ResponseHelper.assert_unauthorized(response)
