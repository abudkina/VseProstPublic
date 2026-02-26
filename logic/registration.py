# registration.py
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, jsonify, request, make_response, g, current_app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

from logic.model import RefreshToken, User
from logic.model import db
from logic.utils.auth_utils import (
    is_production, set_cookie, generate_access_token, generate_refresh_token, get_access_token_expiry, JWT_SECRET
)
from logic.utils.validators import validate_email, validate_password_strength, validate_username
from logic.utils.rate_limiter import get_rate_limit
from logic.utils.logger import get_logger

logger = get_logger(__name__)

registration_bp = Blueprint('registration', __name__, url_prefix='/api')

# Используем JWT_SECRET из auth_utils для консистентности
SECRET_KEY = JWT_SECRET

class AuthResponse:
    """Представляет ответ авторизации"""
    def __init__(self, message, access_expiry=None):
        self.message = message
        self.access_expiry = access_expiry
    
    def to_dict(self):
        result = {'message': self.message}
        if self.access_expiry:
            result['accessExpiry'] = self.access_expiry
        return result

def is_valid_jwt_format(token):
    """Проверяет, имеет ли токен правильный формат JWT (3 сегмента, разделенные точками)"""
    if not token or not isinstance(token, str):
        return False
    token = token.strip()
    if not token:
        return False
    parts = token.split('.')
    return len(parts) == 3

def auth_middleware(f):
    """Middleware для проверки JWT токена (поддерживает cookies и Authorization header)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Пытаемся получить токен из cookies
        access_token = request.cookies.get('access_token')
        
        # Если токена нет в cookies, проверяем заголовок Authorization
        if not access_token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
        
        if not access_token:
            return jsonify({'error': 'Access token отсутствует'}), 401
        
        # Проверяем формат токена перед декодированием
        if not is_valid_jwt_format(access_token):
            logger.warning("Ошибка проверки токена: Неверный формат токена (ожидается формат JWT: header.payload.signature)")
            return jsonify({'error': 'Неверный формат токена'}), 401
        
        try:
            # Декодируем токен
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
            g.user_id = int(payload['userID'])
            g.username = payload['username']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Токен истек'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Ошибка проверки токена: {e}")
            return jsonify({'error': 'Неверный токен'}), 401
        except Exception as e:
            logger.warning(f"Ошибка проверки токена: {e}")
            return jsonify({'error': 'Некорректные данные токена'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@registration_bp.route('/register', methods=['POST'])
def register_handler():
    """
    Обработчик регистрации пользователя
    Rate limit: 3 регистрации в час с одного IP
    """
    # Применяем rate limiting
    limiter = current_app.limiter if hasattr(current_app, 'limiter') else None
    if limiter:
        limiter.limit(get_rate_limit('register'))(lambda: None)()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Все поля должны быть заполнены в формате JSON'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip().lower()

        # Валидация обязательных полей
        if not username or not password or not email:
            return jsonify({'error': 'Все поля должны быть заполнены'}), 400

        # Валидация username
        is_valid_username, username_error = validate_username(username)
        if not is_valid_username:
            return jsonify({'error': username_error}), 400

        # Валидация пароля (усиленная проверка)
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400

        # Валидация email
        if not validate_email(email):
            return jsonify({'error': 'Неверный формат email'}), 400

        # SECURITY: Проверка существования - общее сообщение для предотвращения user enumeration
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user or existing_email:
            # Не раскрываем, что именно уже существует
            current_app.logger.warning(f"Попытка регистрации с существующими данными: username={username}, email={email}")
            return jsonify({'error': 'Пользователь с такими данными уже существует'}), 409
        
        # Хеширование пароля
        hashed_password = generate_password_hash(password)
        
        # Создаем пользователя
        user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow()
        )
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания пользователя: {e}")
            return jsonify({'error': 'Ошибка при создании пользователя'}), 500
        
        # Генерация токенов
        access_token = generate_access_token(user.id, username)
        refresh_token = generate_refresh_token(user.id)
        
        # Сохраняем refresh token в БД
        rt = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        try:
            db.session.add(rt)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Удаляем пользователя, если не удалось сохранить refresh token
            db.session.delete(user)
            db.session.commit()
            logger.error(f"Ошибка сохранения refresh token: {e}")
            return jsonify({'error': 'Ошибка при сохранении refresh token'}), 500
        
        # Создаем ответ
        response = make_response(jsonify(AuthResponse(
            message="Регистрация успешна!"
        ).to_dict()), 200)
        
        # Устанавливаем токены в HttpOnly cookies
        access_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
        set_cookie(response, 'access_token', access_token, access_expires, http_only=True)
        set_cookie(response, 'refresh_token', refresh_token, 30*24*3600, http_only=True)
        
        return response
        
    except Exception as e:
        logger.error(f"Общая ошибка регистрации: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@registration_bp.route('/validate-token', methods=['GET'])
def validate_token():
    """Проверка валидности токена. Возвращает 200 с valid: false при отсутствии/невалидном токене (без 401)."""
    from logic.middleware import get_token_from_request, is_valid_jwt_format
    access_token = get_token_from_request()
    if not access_token or not is_valid_jwt_format(access_token):
        return jsonify({'valid': False, 'userID': None, 'username': None, 'userType': None, 'isAdmin': False}), 200
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
        g.user_id = int(payload['userID'])
        g.username = payload.get('username', '')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        return jsonify({'valid': False, 'userID': None, 'username': None, 'userType': None, 'isAdmin': False}), 200
    try:
        user = User.query.get(g.user_id)
        user_type = user.type if user else None
        is_admin = user_type == 2
        return jsonify({
            'valid': True,
            'userID': g.user_id,
            'username': g.username,
            'userType': user_type,
            'isAdmin': is_admin
        }), 200
    except Exception as e:
        logger.error(f"Ошибка получения типа пользователя: {e}")
        return jsonify({
            'valid': True,
            'userID': g.user_id,
            'username': g.username,
            'userType': None,
            'isAdmin': False
        }), 200

# Дополнительные функции для работы с паролями

def hash_password(password):
    """Хеширует пароль (аналогично bcrypt.GenerateFromPassword)"""
    return generate_password_hash(password)

def check_password(hashed_password, password):
    """Проверяет пароль (аналогично bcrypt.CompareHashAndPassword)"""
    return check_password_hash(hashed_password, password)

# Декоратор для использования в других модулях
def token_required(f):
    """Декоратор для проверки JWT токена (альтернатива auth_middleware)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        access_token = request.cookies.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Access token отсутствует'}), 401
        
        # Проверяем формат токена перед декодированием
        if not is_valid_jwt_format(access_token):
            logger.warning("Ошибка проверки токена: Неверный формат токена (ожидается формат JWT: header.payload.signature)")
            return jsonify({'error': 'Неверный формат токена'}), 401
        
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
            g.user_id = int(payload['userID'])
            g.username = payload['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Токен истек'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Ошибка проверки токена: {e}")
            return jsonify({'error': 'Неверный токен'}), 401
        except Exception as e:
            logger.warning(f"Ошибка проверки токена: {e}")
            return jsonify({'error': 'Некорректные данные токена'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Утилитарные функции для других модулей

def get_current_user_id():
    """Получение ID текущего пользователя из контекста"""
    return getattr(g, 'user_id', None)

def get_current_username():
    """Получение имени текущего пользователя из контекста"""
    return getattr(g, 'username', None)

# Обработчики для управления пользователями

@registration_bp.route('/users/<int:user_id>', methods=['GET'])
@auth_middleware
def get_user(user_id):
    """Получение информации о пользователе"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Проверяем права доступа
        current_user_id = get_current_user_id()
        if user_id != current_user_id:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@registration_bp.route('/users/me', methods=['GET'])
@auth_middleware
def get_current_user():
    """Получение информации о текущем пользователе"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения текущего пользователя: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@registration_bp.route('/users/me', methods=['PUT'])
@auth_middleware
def update_current_user():
    """Обновление информации о текущем пользователе"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных для обновления'}), 400
        
        # Обновляем поля, если они предоставлены
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username:
                # Проверяем уникальность username
                existing = User.query.filter(
                    User.username == new_username,
                    User.id != user_id
                ).first()
                if existing:
                    return jsonify({'error': 'Пользователь с таким username уже существует'}), 409
                user.username = new_username
        
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email:
                # Валидация email
                if not validate_email(new_email):
                    return jsonify({'error': 'Неверный формат email'}), 400
                
                # Проверяем уникальность email
                existing = User.query.filter(
                    User.email == new_email,
                    User.id != user_id
                ).first()
                if existing:
                    return jsonify({'error': 'Пользователь с таким email уже существует'}), 409
                user.email = new_email
        
        if 'password' in data:
            new_password = data['password'].strip()
            if new_password:
                user.password_hash = generate_password_hash(new_password)
        
        user.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка обновления пользователя: {e}")
            return jsonify({'error': 'Ошибка обновления пользователя'}), 500
        
        return jsonify({'message': 'Пользователь успешно обновлен'}), 200
        
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500