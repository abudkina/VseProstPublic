"""
Rate Limiting Configuration
Защита от брутфорс атак и DoS
"""
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _exempt_static():
    """Исключить статику и GET списков из лимита — иначе 429 на .js/.css или при загрузке страниц."""
    from flask import request
    path = (request.path or "").rstrip("/")
    if (
        path.startswith("/js/")
        or path.startswith("/css/")
        or path.startswith("/assets/")
        or path.startswith("/fonts/")
        or path.startswith("/uploads/")
        or path == "/favicon.ico"
        or path.startswith("/favicon")
        or path.startswith("/apple-touch-icon")
    ):
        return True
    # GET запросы к спискам — не лимитируем, иначе страницы решений/проблем дают 429
    if request.method == "GET":
        if path == "/solutions" or path == "/problems" or path == "/categories" or path == "/topics" or path == "/hashtags":
            return True
    # validate-token вызывается часто (корзина, уведомления, checkAuth) — лимит задаём отдельно в view
    if "/validate-token" in path:
        return True
    return False


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
            os.getenv('RATELIMIT_PER_MINUTE', '100 per minute')
        ],
        strategy="fixed-window",
        headers_enabled=True,
        swallow_errors=True,
        default_limits_exempt_when=_exempt_static,  # /js/, /css/, /assets/ не лимитируем
    )

    app.logger.info(f"Rate limiter инициализирован с хранилищем: {get_limiter_storage()}")

    return limiter


# Предопределенные лимиты для различных эндпоинтов
RATE_LIMITS = {
    'login': os.getenv('RATELIMIT_LOGIN', '5 per minute'),
    'register': os.getenv('RATELIMIT_REGISTER', '3 per hour'),
    'password_reset': os.getenv('RATELIMIT_PASSWORD_RESET', '3 per hour'),
    'validate_token': os.getenv('RATELIMIT_VALIDATE_TOKEN', '120 per minute'),
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
