# category.py
from flask import Blueprint, jsonify, request, g
from datetime import datetime
from logic.model import Category, User
from logic.middleware import token_required
from logic.model import db
from logic.utils.normalizers import normalize_category_name, normalize_category_display_name
from logic.utils.logger import get_logger

logger = get_logger(__name__)

category_bp = Blueprint('category', __name__, url_prefix='/api')

@category_bp.route('/categories', methods=['POST'])
@token_required
def add_category():
    """Обработчик для добавления категории"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        # Проверяем наличие имени категории
        category_name = data.get('name')
        if not category_name or not str(category_name).strip():
            return jsonify({'error': 'Неверный запрос: имя категории обязательно и не должно быть пустым'}), 400
        
        # Убираем лишние пробелы
        category_name = str(category_name).strip()
        
        # Получаем userID из контекста (установлено middleware)
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, что пользователь существует
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Нормализуем имя запроса
        normalized_req_name = normalize_category_name(category_name)
        
        # Проверяем, существует ли уже категория с таким нормализованным именем для этого пользователя
        try:
            # Сначала получаем все категории пользователя
            user_categories = Category.query.filter_by(creator=user_id).all()
            
            # Проверяем каждую категорию на нормализованное имя
            for category in user_categories:
                normalized_existing_name = normalize_category_name(category.name)
                if normalized_existing_name == normalized_req_name:
                    return jsonify({'error': 'Категория с таким именем уже существует'}), 400
        
        except Exception as e:
            logger.error(f"Ошибка проверки уникальности: {e}")
            return jsonify({'error': 'Ошибка проверки уникальности'}), 500
        
        # Создаем новую категорию (название с большой буквы)
        new_category = Category(
            name=normalize_category_display_name(category_name),
            creator=user_id,  # Используем creator, а не creator_id
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            isnew=True  # В модели это поле называется isnew (все маленькими буквами)
        )
        
        try:
            db.session.add(new_category)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания категории: {e}")
            return jsonify({'error': 'Ошибка создания категории'}), 500
        
        # Возвращаем созданную категорию
        return jsonify({
            'ID': new_category.id,  # Для фронтенда используем 'ID'
            'Name': new_category.name,
            'creator': new_category.creator,
            'created_date': new_category.created_date.isoformat(),
            'modified_date': new_category.modified_date.isoformat(),
            'isnew': new_category.isnew
        }), 201
        
    except Exception as e:
        logger.exception(f"Общая ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@category_bp.route('/categories/count', methods=['GET'])
@token_required
def count_category():
    """Обработчик для подсчета новых категорий"""
    try:
        # Получаем userID из контекста
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчитываем количество новых категорий для текущего пользователя
        count = Category.query.filter_by(
            creator=user_id,  # Используем creator, а не creator_id
            isnew=True
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка подсчета категорий: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@category_bp.route('/categories', methods=['GET'])
def get_categories():
    """Получение всех категорий (без авторизации для фронтенда)"""
    try:
        # Если есть авторизация, показываем категории текущего пользователя
        user_id = getattr(g, 'user_id', None)
        
        if user_id:
            # Авторизованный пользователь - показываем только его категории
            categories = Category.query.filter_by(creator=user_id).all()
        else:
            # Неавторизованный пользователь - показываем все категории
            categories = Category.query.all()
        
        categories_list = []
        for category in categories:
            categories_list.append({
                'ID': category.id,
                'Name': category.name,
                'creator': category.creator,
                'created_date': category.created_date.isoformat() if category.created_date else None,
                'modified_date': category.modified_date.isoformat() if category.modified_date else None,
                'isnew': category.isnew
            })
        
        return jsonify(categories_list), 200
        
    except Exception as e:
        logger.exception(f"Ошибка получения категорий: {e}")
        return jsonify({'error': 'Ошибка получения категорий'}), 500

@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
@token_required
def update_category(category_id):
    """Обновление категории"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        category_name = data.get('name')
        if not category_name or not str(category_name).strip():
            return jsonify({'error': 'Имя категории обязательно'}), 400
        
        # Находим категорию
        category = Category.query.filter_by(id=category_id, creator=user_id).first()
        if not category:
            return jsonify({'error': 'Категория не найдена'}), 404
        
        # Проверяем уникальность нового имени
        new_name = str(category_name).strip()
        normalized_new_name = normalize_category_name(new_name)
        
        # Проверяем другие категории пользователя (кроме текущего)
        other_categories = Category.query.filter(
            Category.creator == user_id,
            Category.id != category_id
        ).all()
        
        for other_category in other_categories:
            normalized_existing_name = normalize_category_name(other_category.name)
            if normalized_existing_name == normalized_new_name:
                return jsonify({'error': 'Категория с таким именем уже существует'}), 400
        
        # Обновляем категорию (название с большой буквы)
        category.name = normalize_category_display_name(new_name)
        category.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления категории'}), 500
        
        return jsonify({
            'ID': category.id,
            'Name': category.name,
            'modified_date': category.modified_date.isoformat()
        }), 200
        
    except Exception as e:
        logger.exception(f"Ошибка обновления категории: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@token_required
def delete_category(category_id):
    """Удаление категории"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Находим категорию
        category = Category.query.filter_by(id=category_id, creator=user_id).first()
        if not category:
            return jsonify({'error': 'Категория не найдена'}), 404
        
        try:
            db.session.delete(category)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка удаления категории'}), 500
        
        return jsonify({'message': 'Категория успешно удалена'}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка удаления категории: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@category_bp.route('/categories/<int:category_id>/mark-as-read', methods=['PUT'])
@token_required
def mark_category_as_read(category_id):
    """Отметить категорию как прочитанную (снять флаг is_new)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Находим категорию
        category = Category.query.filter_by(id=category_id, creator=user_id).first()
        if not category:
            return jsonify({'error': 'Категория не найдена'}), 404
        
        # Снимаем флаг is_new
        category.isnew = False
        category.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления категории'}), 500
        
        return jsonify({'message': 'Категория отмечена как прочитанная'}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка обновления категории: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500