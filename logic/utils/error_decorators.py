"""
Декораторы для единообразной обработки ошибок в endpoints
"""
from functools import wraps
from flask import current_app
from logic.utils.error_handler import ErrorResponse, AppError


def handle_errors(include_details: bool = False):
    """
    Декоратор для автоматической обработки ошибок в endpoints.
    
    Args:
        include_details: Включать ли детали ошибки в ответе
    
    Пример использования:
        @app.route('/api/endpoint', methods=['GET'])
        @handle_errors(include_details=False)
        def my_endpoint():
            # Ваш код здесь
            return {"data": "value"}, 200
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except AppError as e:
                # Логируем ошибку приложения
                current_app.logger.warning(f"AppError в {f.__name__}: {e.message}")
                # Проверяем окружение для include_details
                should_include_details = include_details or current_app.config.get('ENV') == 'development'
                return ErrorResponse.jsonify(e, include_details=should_include_details)
            except Exception as e:
                # Логируем неожиданные ошибки
                current_app.logger.error(f"Необработанная ошибка в {f.__name__}: {e}", exc_info=True)
                return ErrorResponse.jsonify(e, include_details=False)
        
        return decorated_function
    return decorator
