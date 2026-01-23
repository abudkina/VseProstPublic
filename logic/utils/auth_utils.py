# auth_utils.py - утилиты для авторизации и работы с токенами
import os
import jwt
from datetime import datetime, timedelta
from flask import make_response

# Конфигурация
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
ENV = os.getenv('ENV', 'development')

def is_production():
    """Проверяет, является ли среда продакшеном"""
    return ENV == 'production'

def set_cookie(response, name, value, max_age, secure=None, http_only=True):
    """Устанавливает куку с параметрами безопасности"""
    if secure is None:
        secure = is_production()
    
    response.set_cookie(
        name,
        value=value,
        max_age=max_age,
        path='/',
        domain=None if not is_production() else None,
        secure=secure,
        httponly=http_only,
        samesite='Strict'
    )

def generate_access_token(user_id, username):
    """Генерирует access token"""
    expiration = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        'userID': user_id,
        'username': username,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    # Убеждаемся, что токен - это строка (в некоторых версиях PyJWT может возвращать bytes)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def generate_refresh_token(user_id):
    """Генерирует refresh token (JWT)"""
    token = jwt.encode({
        'userID': user_id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    # Убеждаемся, что токен - это строка (в некоторых версиях PyJWT может возвращать bytes)
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def get_access_token_expiry():
    """Возвращает время истечения access token в ISO формате"""
    return (datetime.utcnow() + timedelta(minutes=15)).isoformat() + 'Z'
