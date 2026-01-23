"""
Rate Limiting Configuration
Защита от брутфорс атак и DoS
"""
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_limiter_storage():
    """
    Получает URL хранилища для rate limiter из переменных окружения

    Returns:
        str: URL хранилища (redis:// или memory://)
    """
    storage_url = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    return storage_url


def init_limiter(app):
    """
    Инициализирует Flask-Limiter для приложения

    Args:
        app: Flask application instance

    Returns:
        Limiter: Configured limiter instance
    """
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=get_limiter_storage(),
        default_limits=[
            os.getenv('RATELIMIT_DEFAULT', '200 per hour'),
            os.getenv('RATELIMIT_PER_MINUTE', '100 per minute')  # Увеличено с 50 до 100
        ],
        # Настройки для production
        strategy="fixed-window",  # или "moving-window" для более точного контроля
        headers_enabled=True,  # Добавляет заголовки X-RateLimit-*
        swallow_errors=True,  # Не ломает приложение при ошибках rate limiter
    )

    app.logger.info(f"Rate limiter инициализирован с хранилищем: {get_limiter_storage()}")

    return limiter


# Предопределенные лимиты для различных эндпоинтов
RATE_LIMITS = {
    'login': os.getenv('RATELIMIT_LOGIN', '5 per minute'),
    'register': os.getenv('RATELIMIT_REGISTER', '3 per hour'),
    'password_reset': os.getenv('RATELIMIT_PASSWORD_RESET', '3 per hour'),
    'api_general': '100 per hour',
    'api_read': '200 per hour',
    'api_write': '50 per hour',
}


def get_rate_limit(limit_type: str) -> str:
    """
    Получает rate limit для указанного типа

    Args:
        limit_type: Тип лимита (login, register, etc.)

    Returns:
        str: Строка лимита в формате Flask-Limiter
    """
    return RATE_LIMITS.get(limit_type, '100 per hour')
