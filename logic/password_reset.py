# password_reset.py
"""
Модуль для восстановления пароля через email.
"""

import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash

from logic.model import User, PasswordResetToken, db
from logic.utils.validators import validate_email, validate_password_strength
from logic.utils.rate_limiter import get_rate_limit

password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/api')


def generate_reset_token():
    """Генерация безопасного токена для сброса пароля"""
    return secrets.token_urlsafe(32)


def send_reset_email(user_email, reset_token, username):
    """Отправка письма с ссылкой для сброса пароля через Yandex SMTP"""
    try:
        # Получаем настройки из конфига
        mail_server = current_app.config.get('MAIL_SERVER', 'smtp.yandex.ru')
        mail_port = current_app.config.get('MAIL_PORT', 465)
        mail_use_ssl = current_app.config.get('MAIL_USE_SSL', True)
        mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
        mail_username = current_app.config.get('MAIL_USERNAME', '')
        mail_password = current_app.config.get('MAIL_PASSWORD', '')
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER', mail_username)
        frontend_url = current_app.config.get('FRONTEND_URL', 'http://127.0.0.1:8080')
        
        if not mail_username or not mail_password:
            print("MAIL_USERNAME или MAIL_PASSWORD не настроены")
            return False
        
        # Формируем ссылку для сброса пароля
        reset_link = f"{frontend_url}/html/reset_password.html?token={reset_token}"
        
        # Создаем сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Восстановление пароля - Всё Прост'
        msg['From'] = mail_sender
        msg['To'] = user_email
        
        # Текстовая версия письма
        text_content = f"""
Здравствуйте, {username}!

Вы запросили восстановление пароля для вашего аккаунта на сайте "Всё Прост".

Для сброса пароля перейдите по ссылке:
{reset_link}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.

С уважением,
Команда "Всё Прост"
        """
        
        # HTML версия письма
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
        .button:hover {{ opacity: 0.9; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Всё Прост</h1>
            <p>Восстановление пароля</p>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{username}</strong>!</p>
            <p>Вы запросили восстановление пароля для вашего аккаунта.</p>
            <p>Для установки нового пароля нажмите на кнопку ниже:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Сбросить пароль</a>
            </p>
            <p>Или скопируйте эту ссылку в браузер:</p>
            <p style="word-break: break-all; background: #e9ecef; padding: 10px; border-radius: 5px; font-size: 12px;">
                {reset_link}
            </p>
            <div class="warning">
                <strong>⚠️ Важно:</strong> Ссылка действительна в течение <strong>1 часа</strong>.
            </div>
            <p style="margin-top: 20px;">Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.</p>
        </div>
        <div class="footer">
            <p>С уважением, команда "Всё Прост"</p>
            <p>Это автоматическое сообщение, пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Добавляем обе версии
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # Отправляем письмо
        if mail_use_ssl:
            # SSL соединение (порт 465)
            with smtplib.SMTP_SSL(mail_server, mail_port) as server:
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, user_email, msg.as_string())
        else:
            # TLS соединение (порт 587)
            with smtplib.SMTP(mail_server, mail_port) as server:
                if mail_use_tls:
                    server.starttls()
                server.login(mail_username, mail_password)
                server.sendmail(mail_sender, user_email, msg.as_string())
        
        print(f"Письмо для сброса пароля отправлено на {user_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"Ошибка аутентификации SMTP: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"Ошибка SMTP: {e}")
        return False
    except Exception as e:
        print(f"Ошибка отправки письма: {e}")
        import traceback
        traceback.print_exc()
        return False


@password_reset_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Запрос на восстановление пароля.
    Отправляет письмо с ссылкой для сброса пароля.
    Rate limit: 3 попытки в час с одного IP
    """
    # Применяем rate limiting
    limiter = current_app.limiter if hasattr(current_app, 'limiter') else None
    if limiter:
        limiter.limit(get_rate_limit('password_reset'))(lambda: None)()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Данные не предоставлены'}), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'error': 'Email обязателен'}), 400
        
        if not validate_email(email):
            return jsonify({'error': 'Неверный формат email'}), 400
        
        # Ищем пользователя по email
        user = User.query.filter_by(email=email).first()
        
        # Для безопасности всегда возвращаем успех, даже если email не найден
        # Это предотвращает перечисление пользователей
        if not user:
            print(f"Попытка восстановления пароля для несуществующего email: {email}")
            return jsonify({
                'message': 'Если указанный email зарегистрирован, на него будет отправлена ссылка для восстановления пароля.'
            }), 200
        
        # Деактивируем все предыдущие токены для этого пользователя
        PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
        db.session.commit()
        
        # Генерируем новый токен
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(
            seconds=current_app.config.get('PASSWORD_RESET_TOKEN_EXPIRES', 3600)
        )
        
        # Сохраняем токен в БД
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        try:
            db.session.add(reset_token)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения токена: {e}")
            return jsonify({'error': 'Ошибка при создании токена сброса'}), 500
        
        # Отправляем письмо
        if send_reset_email(user.email, token, user.username):
            return jsonify({
                'message': 'Если указанный email зарегистрирован, на него будет отправлена ссылка для восстановления пароля.'
            }), 200
        else:
            # Если письмо не отправлено, удаляем токен
            db.session.delete(reset_token)
            db.session.commit()
            return jsonify({'error': 'Ошибка при отправке письма. Попробуйте позже.'}), 500
            
    except Exception as e:
        print(f"Ошибка восстановления пароля: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500


@password_reset_bp.route('/verify-reset-token', methods=['POST'])
def verify_reset_token():
    """
    Проверка валидности токена сброса пароля.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Данные не предоставлены'}), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Токен обязателен'}), 400
        
        # Ищем токен в БД
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return jsonify({'error': 'Недействительный токен'}), 400
        
        if not reset_token.is_valid():
            return jsonify({'error': 'Токен истек или уже использован'}), 400
        
        return jsonify({
            'message': 'Токен валиден',
            'valid': True
        }), 200
        
    except Exception as e:
        print(f"Ошибка проверки токена: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500


@password_reset_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Сброс пароля по токену.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Данные не предоставлены'}), 400
        
        token = data.get('token', '').strip()
        new_password = data.get('password', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        
        if not token:
            return jsonify({'error': 'Токен обязателен'}), 400
        
        if not new_password:
            return jsonify({'error': 'Новый пароль обязателен'}), 400

        if new_password != confirm_password:
            return jsonify({'error': 'Пароли не совпадают'}), 400

        # Валидация сложности пароля
        is_valid_password, password_error = validate_password_strength(new_password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400
        
        # Ищем токен в БД
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token:
            return jsonify({'error': 'Недействительный токен'}), 400
        
        if not reset_token.is_valid():
            return jsonify({'error': 'Токен истек или уже использован'}), 400
        
        # Получаем пользователя
        user = User.query.get(reset_token.user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 400
        
        # Обновляем пароль
        user.password_hash = generate_password_hash(new_password)
        user.modified_date = datetime.utcnow()
        
        # Помечаем токен как использованный
        reset_token.used = True
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка обновления пароля: {e}")
            return jsonify({'error': 'Ошибка при обновлении пароля'}), 500
        
        print(f"Пароль успешно сброшен для пользователя {user.username}")
        
        return jsonify({
            'message': 'Пароль успешно изменен! Теперь вы можете войти с новым паролем.'
        }), 200
        
    except Exception as e:
        print(f"Ошибка сброса пароля: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
