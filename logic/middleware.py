# middleware.py
import jwt
from flask import request, jsonify, g
from functools import wraps
from datetime import datetime
import os
from urllib.parse import unquote
from logic.utils.logger import get_logger

logger = get_logger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')

def get_token_from_request():
    """Извлекает токен из запроса (из заголовка Authorization или из cookies)"""
    token = None
    
    # Сначала пытаемся получить токен из заголовка Authorization
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_header = auth_header.strip()
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()  # Убираем 'Bearer ' и пробелы
            # Игнорируем некорректные значения (null, undefined, пустая строка)
            if not token or token.lower() in ('null', 'undefined', ''):
                token = None
    
    # Если токена нет в заголовке или он некорректный, пытаемся получить из куки
    if not token:
        token = request.cookies.get('access_token')
        if token:
            # Убираем пробелы и проверяем на некорректные значения
            if isinstance(token, str):
                token = token.strip()
                # Flask автоматически декодирует URL-кодированные значения в cookies,
                # но на всякий случай проверяем и декодируем вручную, если нужно
                # (обычно это не требуется, но для надежности)
                if token.startswith('%') or '%' in token:
                    try:
                        token = unquote(token)
                    except (ValueError, UnicodeDecodeError) as e:
                        logger.debug(f"Failed to decode token URL encoding: {e}")
            # Проверяем, что токен не пустой и не является некорректным значением
            if not token or (isinstance(token, str) and token.lower() in ('null', 'undefined', '')):
                token = None
    
    return token if token else None

def is_valid_jwt_format(token):
    """Проверяет, имеет ли токен правильный формат JWT (3 сегмента, разделенные точками)"""
    if not token:
        return False
    
    # Преобразуем в строку, если это не строка
    if not isinstance(token, str):
        try:
            token = str(token)
        except (ValueError, TypeError):
            return False
    
    # Убираем пробелы
    token = token.strip()
    
    # Проверяем, что токен не пустой и не является некорректным значением
    if not token or token.lower() in ('null', 'undefined', 'none', ''):
        return False
    
    # Проверяем формат JWT (должно быть 3 части, разделенные точками)
    parts = token.split('.')
    if len(parts) != 3:
        return False
    
    # Проверяем, что каждая часть не пустая
    for part in parts:
        if not part or not part.strip():
            return False
    
    return True

def get_user_id_from_token():
    """Извлекает user_id из токена без установки g.user_id (для опциональной проверки)"""
    token = get_token_from_request()
    
    if not token:
        return None
    
    if not is_valid_jwt_format(token):
        return None
    
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return data.get('userID')
    except jwt.InvalidTokenError:
        return None

def extract_user_from_token():
    """Извлекает информацию о пользователе из токена и устанавливает g.user_id и g.username"""
    token = get_token_from_request()
    
    if not token:
        return False
    
    # Проверяем формат токена перед декодированием
    if not is_valid_jwt_format(token):
        logger.debug("Invalid token format in extract_user_from_token")
        return False
    
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        g.user_id = data['userID']
        g.username = data['username']
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token error: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error decoding token: {e}")
        return False

def token_required(f):
    """Декоратор для проверки JWT токена"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'error': 'Токен отсутствует'}), 401
        
        # Проверяем формат токена перед декодированием
        if not is_valid_jwt_format(token):
            logger.debug("Invalid token format in token_required decorator")
            return jsonify({'error': 'Неверный формат токена'}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            g.user_id = data['userID']  # Сохраняем в контексте приложения
            g.username = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Токен истек'}), 401
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token in decorator: {e}")
            return jsonify({'error': 'Неверный токен'}), 401
        
        return f(*args, **kwargs)
    
    return decorated