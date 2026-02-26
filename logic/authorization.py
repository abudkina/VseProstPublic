# authorization.py

from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, make_response, current_app
import bcrypt
import jwt
from logic.model import User, RefreshToken, db
from logic.registration import check_password
from logic.utils.auth_utils import (
    is_production, set_cookie, generate_access_token,
    generate_refresh_token, get_access_token_expiry, JWT_SECRET
)
from logic.utils.rate_limiter import get_rate_limit
from logic.utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

def is_valid_jwt_format(token):
    """Проверяет, имеет ли токен правильный формат JWT (3 сегмента, разделенные точками)"""
    if not token or not isinstance(token, str):
        return False
    token = token.strip()
    if not token:
        return False
    parts = token.split('.')
    return len(parts) == 3

class AuthResponse:
    """Представляет ответ авторизации"""
    def __init__(self, message, access_expiry):
        self.message = message
        self.access_expiry = access_expiry
    
    def to_dict(self):
        return {
            'message': self.message,
            'accessExpiry': self.access_expiry
        }

import traceback


def get_limiter():
    """Получает limiter из app context"""
    return current_app.limiter if hasattr(current_app, 'limiter') else None


@auth_bp.route('/login', methods=['POST'])
def login_handler():
    """
    Обработчик входа пользователя
    Rate limit: 5 попыток в минуту с одного IP
    """
    # Применяем rate limiting
    limiter = get_limiter()
    if limiter:
        limiter.limit(get_rate_limit('login'))(lambda: None)()

    try:
        current_app.logger.info("LOGIN REQUEST")
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400
        
        username = data.get('login')
        password = data.get('password')

        logger.info(f"Login attempt for user: {username}")

        if not username or not password:
            return jsonify({'error': 'Имя пользователя и пароль обязательны'}), 400

        logger.debug("Querying database for user")
        user = User.query.filter_by(username=username).first()

        if not user:
            logger.warning(f"Login failed: user '{username}' not found")
            return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401

        logger.debug(f"User found: ID={user.id}, Username={user.username}")
        # SECURITY: Never log password hashes

        # Проверка пароля
        logger.debug("Verifying password")
        test_result = check_password(user.password_hash, password)

        if not test_result:
            logger.warning(f"Login failed: invalid password for user '{username}'")
            return jsonify({'error': 'Неверное имя пользователя или пароль'}), 401

        logger.debug("Password verified successfully")
        
        # Генерация токенов
        access_token = generate_access_token(user.id, username)
        access_expiry = get_access_token_expiry()
        refresh_token = generate_refresh_token(user.id)

        logger.debug(f"Access token generated for user_id={user.id}, expiry: {access_expiry}")
        
        # Сохраняем refresh token в БД
        rt = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        try:
            db.session.add(rt)
            db.session.commit()
            logger.debug(f"Refresh token saved to database for user_id={user.id}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error saving refresh token for user_id={user.id}: {db_error}")
            return jsonify({'error': 'Ошибка при сохранении refresh token'}), 500
        
        # Создаем ответ
        response_data = {
            'message': "Вход выполнен успешно!",
            'accessExpiry': access_expiry,
            'userID': user.id,
            'username': username
        }

        logger.debug(f"Login response prepared for user_id={user.id}")
        
        response = make_response(jsonify(response_data), 200)
        
        # Устанавливаем токены в HttpOnly cookies
        access_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
        set_cookie(response, 'access_token', access_token, access_expires, secure=False, http_only=True)
        set_cookie(response, 'refresh_token', refresh_token, 30*24*3600, secure=False, http_only=True)

        logger.info(f"Login successful for user: {username} (user_id={user.id})")
        return response

    except Exception as e:
        logger.exception(f"Login error: {str(e)}")
        return jsonify({'error': 'Внутренняя ошибка сервера', 'details': str(e)}), 500
    
@auth_bp.route('/logout', methods=['POST'])
def logout_handler():
    """Обработчик выхода пользователя"""
    try:
        # Получить refresh_token из куки
        refresh_token = request.cookies.get('refresh_token')
        
        if refresh_token:
            # Удалить из БД
            rt = RefreshToken.query.filter_by(token=refresh_token).first()
            if rt:
                try:
                    db.session.delete(rt)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
        
        # Создаем ответ
        response = make_response(jsonify({'message': 'Выход выполнен успешно'}), 200)
        
        # Очищаем куки
        expired_time = datetime.utcnow() - timedelta(days=1)
        secure = is_production()
        
        response.set_cookie(
            'access_token',
            value='',
            expires=expired_time,
            path='/',
            secure=secure,
            httponly=True,
            samesite='Lax'
        )
        
        response.set_cookie(
            'refresh_token',
            value='',
            expires=expired_time,
            path='/',
            secure=secure,
            httponly=True,
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@auth_bp.route('/refreshToken', methods=['POST'])
def refresh_token_handler():
    """
    Обновление access token
    Rate limit: 10 попыток в минуту
    """
    # Применяем rate limiting
    limiter = get_limiter()
    if limiter:
        limiter.limit("10 per minute")(lambda: None)()

    try:
        refresh_token = request.cookies.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token отсутствует'}), 401
        
        # Проверяем формат токена перед декодированием
        if not is_valid_jwt_format(refresh_token):
            logger.warning("Invalid refresh token format")
            return jsonify({'error': 'Неверный формат refresh token'}), 401
        
        # Проверяем refresh token в БД
        rt = RefreshToken.query.filter_by(token=refresh_token).first()
        if not rt or rt.is_expired():
            return jsonify({'error': 'Недействительный refresh token'}), 401
        
        # Декодируем refresh token
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=['HS256'])
            user_id = payload.get('userID')
            
            if not user_id:
                return jsonify({'error': 'Неверный refresh token'}), 401
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return jsonify({'error': 'Неверный refresh token'}), 401
        
        # Получаем пользователя
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 401
        
        # Генерация нового access token
        access_token = generate_access_token(user.id, user.username)
        access_expiry = get_access_token_expiry()
        
        # Создаем ответ
        response = make_response(jsonify({
            'message': 'Токен обновлён',
            'accessExpiry': access_expiry,
            'userID': user.id,
            'username': user.username
        }), 200)
        
        # Устанавливаем новый access token в cookie
        access_expires = current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 86400)
        set_cookie(response, 'access_token', access_token, access_expires, http_only=True)
        
        return response
        
    except Exception as e:
        logger.exception(f"Token refresh error: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500    