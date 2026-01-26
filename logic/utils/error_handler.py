"""
Единая система обработки ошибок для всего приложения.

Обеспечивает консистентные ответы об ошибках во всех endpoints.
"""
from flask import jsonify
from typing import Dict, Optional, Any, Tuple, Union
from enum import Enum


class ErrorCode(Enum):
    """Коды ошибок приложения"""
    # Ошибки валидации (400)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Ошибки аутентификации (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # Ошибки авторизации (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Ошибки ресурсов (404)
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    
    # Ошибки конфликта (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    
    # Ошибки ограничений (429)
    RATE_LIMITED = "RATE_LIMITED"
    TOO_MANY_REQUESTS = "TOO_MANY_REQUESTS"
    
    # Ошибки сервера (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_ERROR = "SERVICE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class AppError(Exception):
    """Базовый класс для ошибок приложения"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            message: Сообщение об ошибке
            error_code: Код ошибки из ErrorCode
            status_code: HTTP статус код
            details: Дополнительные детали ошибки
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Ошибка валидации входных данных"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            status_code=400,
            details=details
        )


class AuthenticationError(AppError):
    """Ошибка аутентификации"""
    def __init__(self, message: str = "Требуется аутентификация", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            details=details
        )


class AuthorizationError(AppError):
    """Ошибка авторизации"""
    def __init__(self, message: str = "Недостаточно прав", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details
        )


class ResourceNotFoundError(AppError):
    """Ошибка когда ресурс не найден"""
    def __init__(self, resource_type: str, resource_id: Any = None):
        message = f"{resource_type} не найден"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404
        )


class ConflictError(AppError):
    """Ошибка конфликта (например, дубликат записи)"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            details=details
        )


class RateLimitError(AppError):
    """Ошибка превышения лимита запросов"""
    def __init__(self, message: str = "Слишком много запросов"):
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMITED,
            status_code=429
        )


class DatabaseError(AppError):
    """Ошибка базы данных"""
    def __init__(self, message: str = "Ошибка базы данных", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details
        )


class ErrorResponse:
    """Класс для формирования единых ответов об ошибках"""
    
    @staticmethod
    def create_response(
        error: Union[AppError, Exception],
        include_details: bool = False
    ) -> Tuple[Dict[str, Any], int]:
        """
        Создает единый ответ об ошибке.
        
        Args:
            error: Исключение AppError или обычное Exception
            include_details: Включать ли детали ошибки (для разработки)
            
        Returns:
            Кортеж (response_dict, status_code)
        """
        if isinstance(error, AppError):
            response = {
                "success": False,
                "error": {
                    "code": error.error_code.value,
                    "message": error.message
                }
            }
            
            if include_details and error.details:
                response["error"]["details"] = error.details
            
            return response, error.status_code
        else:
            # Для неожиданных ошибок
            response = {
                "success": False,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "Внутренняя ошибка сервера"
                }
            }
            return response, 500
    
    @staticmethod
    def jsonify(
        error: Union[AppError, Exception],
        include_details: bool = False
    ) -> Tuple[Any, int]:
        """
        Преобразует ошибку в JSON ответ Flask.
        
        Args:
            error: Исключение
            include_details: Включать ли детали ошибки
            
        Returns:
            Кортеж (response_dict, status_code) для Flask
        """
        response, status_code = ErrorResponse.create_response(error, include_details)
        return jsonify(response), status_code


class SuccessResponse:
    """Класс для формирования единых успешных ответов"""
    
    @staticmethod
    def create_response(
        data: Any = None,
        message: str = "Успешно",
        status_code: int = 200
    ) -> Dict[str, Any]:
        """
        Создает единый успешный ответ.
        
        Args:
            data: Данные ответа
            message: Сообщение
            status_code: HTTP статус код
            
        Returns:
            Словарь ответа
        """
        return {
            "success": True,
            "message": message,
            "data": data,
            "status": status_code
        }
    
    @staticmethod
    def jsonify(
        data: Any = None,
        message: str = "Успешно",
        status_code: int = 200
    ) -> Tuple[Any, int]:
        """
        Преобразует успешный ответ в JSON для Flask.
        
        Args:
            data: Данные
            message: Сообщение
            status_code: HTTP статус код
            
        Returns:
            Кортеж (response_dict, status_code) для Flask
        """
        response = SuccessResponse.create_response(data, message, status_code)
        return jsonify(response), status_code
