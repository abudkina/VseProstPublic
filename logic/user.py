# user.py - исправленная версия
from flask import Blueprint, jsonify, g, request
from logic.model import User, Problem, Solution
from logic.middleware import token_required
from logic.model import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from logic.utils.file_utils import allowed_file, save_file, delete_file
from logic.utils.validators import validate_email

user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/users/count-new', methods=['GET'])
@token_required
def count_user():
    """Подсчет новых пользователей"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, является ли пользователь админом
        user = User.query.get(user_id)
        if not user or user.type != 2:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        # Подсчет пользователей с флагом isnew=True
        count = User.query.filter_by(isnew=True).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"Ошибка подсчета пользователей: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@user_bp.route('/users', methods=['GET'])
@token_required
def get_users():
    """Получение списка всех пользователей (только для админов)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, является ли пользователь админом
        user = User.query.get(user_id)
        if not user or user.type != 2:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        users = User.query.order_by(User.created_date.desc()).all()
        users_list = [u.to_dict() for u in users]
        
        return jsonify(users_list), 200
        
    except Exception as e:
        print(f"Ошибка получения пользователей: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user_by_id(user_id):
    """Получение пользователя по ID (только для админов)"""
    try:
        current_user_id = getattr(g, 'user_id', None)
        if not current_user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, является ли пользователь админом
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.type != 2:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"Ошибка получения пользователя: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """Обновление пользователя (только для админов)"""
    try:
        current_user_id = getattr(g, 'user_id', None)
        if not current_user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, является ли пользователь админом
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.type != 2:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        if 'username' in data:
            username = str(data['username']).strip()
            if username:
                existing = User.query.filter(
                    User.username == username,
                    User.id != user_id
                ).first()
                if existing:
                    return jsonify({'error': 'Пользователь с таким username уже существует'}), 400
                user.username = username
        
        if 'email' in data:
            email = str(data['email']).strip().lower()
            if email:
                existing = User.query.filter(
                    User.email == email,
                    User.id != user_id
                ).first()
                if existing:
                    return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
                user.email = email
        
        if 'type' in data:
            user.type = int(data['type']) if data['type'] else None
        
        if 'isnew' in data:
            user.isnew = bool(data['isnew'])
        
        if 'isactive' in data:
            user.isactive = bool(data['isactive'])
        
        user.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления пользователя'}), 500
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"Ошибка обновления пользователя: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    """Удаление пользователя (только для админов)"""
    try:
        current_user_id = getattr(g, 'user_id', None)
        if not current_user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, является ли пользователь админом
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.type != 2:
            return jsonify({'error': 'Нет прав доступа'}), 403
        
        # Нельзя удалить самого себя
        if user_id == current_user_id:
            return jsonify({'error': 'Нельзя удалить самого себя'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка удаления пользователя'}), 500
        
        return jsonify({'message': 'Пользователь успешно удален'}), 200
        
    except Exception as e:
        print(f"Ошибка удаления пользователя: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# ============ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ============

@user_bp.route('/user/profile', methods=['GET'])
@token_required
def get_profile():
    """Получение профиля текущего пользователя со статистикой"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Подсчитываем статистику
        problems_count = Problem.query.filter_by(creator=user_id, show=True).count()
        solutions_count = Solution.query.filter_by(creator=user_id, show=True).count()
        favourite_problems_count = len(user.favourite_problems) if user.favourite_problems else 0
        favourite_solutions_count = len(user.favourite_solutions) if user.favourite_solutions else 0
        
        profile_data = user.to_dict()
        profile_data['stats'] = {
            'problems_created': problems_count,
            'solutions_created': solutions_count,
            'favourite_problems': favourite_problems_count,
            'favourite_solutions': favourite_solutions_count
        }
        
        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Ошибка получения профиля: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@user_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_profile():
    """Обновление профиля текущего пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных для обновления'}), 400
        
        updated = False
        
        if 'username' in data:
            new_username = str(data['username']).strip()
            if new_username and new_username != user.username:
                # Проверяем уникальность username
                existing = User.query.filter(
                    User.username == new_username,
                    User.id != user_id
                ).first()
                if existing:
                    return jsonify({'error': 'Пользователь с таким username уже существует'}), 409
                user.username = new_username
                updated = True
        
        if 'email' in data:
            new_email = str(data['email']).strip().lower()
            if new_email and new_email != user.email:
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
                updated = True
        
        if updated:
            user.modified_date = datetime.utcnow()
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Ошибка обновления профиля: {e}")
                return jsonify({'error': 'Ошибка обновления профиля'}), 500
        
        return jsonify({
            'message': 'Профиль успешно обновлен',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Ошибка обновления профиля: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@user_bp.route('/user/profile/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """Загрузка аватара пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        if 'avatar' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Недопустимый формат файла. Разрешены: png, jpg, jpeg, gif'}), 400
        
        # Удаляем старый аватар, если он есть
        if user.image:
            delete_file(user.image)
        
        # Сохраняем новый аватар
        image_path = save_file(file)
        if not image_path:
            return jsonify({'error': 'Ошибка сохранения файла'}), 500
        
        user.image = image_path
        user.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            delete_file(image_path)
            print(f"Ошибка сохранения аватара: {e}")
            return jsonify({'error': 'Ошибка сохранения аватара'}), 500
        
        return jsonify({
            'message': 'Аватар успешно загружен',
            'image': image_path,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Ошибка загрузки аватара: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@user_bp.route('/user/profile/password', methods=['PUT'])
@token_required
def change_password():
    """Смена пароля пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
        
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not old_password or not new_password:
            return jsonify({'error': 'Старый и новый пароль обязательны'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Новый пароль должен содержать минимум 6 символов'}), 400
        
        # Проверяем старый пароль
        if not check_password_hash(user.password_hash, old_password):
            return jsonify({'error': 'Неверный старый пароль'}), 401
        
        # Устанавливаем новый пароль
        user.password_hash = generate_password_hash(new_password)
        user.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка смены пароля: {e}")
            return jsonify({'error': 'Ошибка смены пароля'}), 500
        
        return jsonify({'message': 'Пароль успешно изменен'}), 200
        
    except Exception as e:
        print(f"Ошибка смены пароля: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500