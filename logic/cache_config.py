# Caching configuration for Flask application
from flask_caching import Cache
from functools import wraps
import os

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple'),  # 'redis' for production
    'CACHE_REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'vseprost_',
}

# Initialize cache
cache = Cache(config=CACHE_CONFIG)

def cache_route(timeout=300, key_prefix=None):
    """
    Декоратор для кэширования результатов API маршрутов
    
    Args:
        timeout: Время кэширования в секундах (по умолчанию 5 минут)
        key_prefix: Префикс ключа кэша (если не указан, используется путь)
    
    Example:
        @app.route('/api/problems')
        @cache_route(timeout=600)
        def get_problems():
            return jsonify(problems)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Генерируем ключ кэша
            cache_key = key_prefix or f"route_{f.__name__}"
            
            # Добавляем параметры запроса в ключ
            from flask import request
            if request.args:
                args_str = '_'.join(f"{k}={v}" for k, v in sorted(request.args.items()))
                cache_key = f"{cache_key}_{args_str}"
            
            # Пытаемся получить из кэша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Вычисляем результат
            result = f(*args, **kwargs)
            
            # Сохраняем в кэш
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator


def invalidate_cache(pattern=None):
    """
    Инвалидировать кэш по паттерну
    
    Example:
        invalidate_cache('route_get_problems_*')
    """
    if pattern:
        # Для Redis нужна специальная обработка
        if CACHE_CONFIG['CACHE_TYPE'] == 'redis':
            from redis import Redis
            redis_client = Redis.from_url(CACHE_CONFIG['CACHE_REDIS_URL'])
            keys = redis_client.keys(pattern)
            for key in keys:
                redis_client.delete(key)
    else:
        cache.clear()


# Специализированные кэши для разных типов данных
CACHE_TIMEOUTS = {
    'problems_list': 600,          # 10 минут
    'problem_detail': 1800,        # 30 минут
    'recommendations': 900,        # 15 минут
    'hashtags': 3600,              # 1 час
    'categories': 3600,            # 1 час
    'user_profile': 300,           # 5 минут
    'solutions': 600,              # 10 минут
}
