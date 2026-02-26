# topic.py
from flask import Blueprint, jsonify, request, g
from datetime import datetime
import re
from flask_sqlalchemy import SQLAlchemy
from logic.model import Topic
from logic.middleware import token_required, extract_user_from_token

from logic.model import db
from logic.utils.normalizers import normalize_topic_name
from logic.utils.logger import get_logger

logger = get_logger(__name__)

topic_bp = Blueprint('topic', __name__,url_prefix='/api')

@topic_bp.route('/topics', methods=['POST'])
@token_required
def add_topic():
    """Добавление новой темы"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        # Получаем userID из контекста
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Пользователь не авторизован'}), 401
        
        # Получаем и валидируем имя темы
        topic_name = data.get('name')
        if not topic_name or not str(topic_name).strip():
            return jsonify({'error': 'Имя темы не может быть пустым'}), 400
        
        # Нормализуем имя темы
        topic_name = normalize_topic_name(str(topic_name).strip())
        
        # Проверка уникальности по имени
        existing_topic = Topic.query.filter_by(name=topic_name).first()
        if existing_topic:
            return jsonify({'error': 'Тема с таким именем уже существует'}), 409
        
        # Создаем новую тему
        topic = Topic(
            name=topic_name,
            creator=user_id,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            is_new=True
        )
        
        try:
            db.session.add(topic)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания темы: {e}")
            return jsonify({'error': 'Ошибка создания темы'}), 500
        
        # Возвращаем созданную тему
        return jsonify({
            'ID': topic.id,  # Используем ID
            'Name': topic.name,  # Используем Name
            'creator_id': topic.creator,
            'created_date': topic.created_date.isoformat(),
            'modified_date': topic.modified_date.isoformat(),
            'is_new': topic.is_new
        }), 201
        
    except Exception as e:
        logger.error(f"Общая ошибка создания темы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@topic_bp.route('/topics', methods=['GET'])
def get_topics():
    """Получение списка тем с поиском"""
    try:
        search = request.args.get('search', '').strip()
        all_topics = request.args.get('all', '').lower() == 'true'
        
        # Всегда пытаемся извлечь информацию о пользователе (если токен есть)
        extract_user_from_token()  # Не критично, если не получится
        user_id = getattr(g, 'user_id', None)
        
        # Если запрос на все темы (для админки) - требуется авторизация
        if all_topics:
            if not user_id:
                return jsonify({'error': 'Требуется авторизация для получения всех тем'}), 401
            # Проверяем, является ли пользователь админом (опционально)
            from logic.model import User
            user = User.query.get(user_id)
            if user and user.type == 2:
                # Админ - все темы
                topics = Topic.query.order_by(Topic.name).all()
            else:
                # Обычный пользователь - только свои темы
                topics = Topic.query.filter_by(creator=user_id).order_by(Topic.name).all()
        elif len(search) >= 2:
            search_pattern = f"%{search}%"
            topics = Topic.query.filter(
                Topic.name.ilike(search_pattern)
            ).order_by(Topic.name).limit(50).all()
        else:
            # Пустой поиск — подсказки: первые темы по алфавиту
            topics = Topic.query.order_by(Topic.name).limit(30).all()
        
        topics_list = []
        for topic in topics:
            topics_list.append({
                'ID': topic.id,  # Используем ID для фронтенда
                'Name': topic.name,  # Используем Name для фронтенда
                'creator_id': topic.creator,  # В модели поле называется creator
                'created_date': topic.created_date.isoformat() if topic.created_date else None,
                'modified_date': topic.modified_date.isoformat() if topic.modified_date else None,
                'is_new': topic.is_new
            })
        
        return jsonify(topics_list), 200
        
    except Exception as e:
        logger.error(f"Ошибка поиска тем: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
    
@topic_bp.route('/topics/count-new', methods=['GET'])
@token_required
def count_topic():
    """Подсчет новых тем"""
    try:
        # Получаем userID из контекста
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчитываем количество новых тем для текущего пользователя
        count = Topic.query.filter_by(
            creator=user_id,
            is_new=True
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.error(f"Ошибка подсчета тем: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@topic_bp.route('/topics/<int:topic_id>', methods=['GET'])
def get_topic_by_id(topic_id):
    """Получение темы по ID"""
    try:
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Тема не найдена'}), 404
        
        return jsonify({
            'ID': topic.id,
            'Name': topic.name,
            'creator_id': topic.creator,
            'created_date': topic.created_date.isoformat() if topic.created_date else None,
            'modified_date': topic.modified_date.isoformat() if topic.modified_date else None,
            'is_new': topic.is_new
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения темы: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@topic_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@token_required
def update_topic(topic_id):
    """Обновление темы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Тема не найдена'}), 404
        
        # Проверяем права (только создатель или админ)
        if topic.creator != user_id:
            # Проверяем, является ли пользователь админом
            from logic.model import User
            user = User.query.get(user_id)
            if not user or user.type != 2:
                return jsonify({'error': 'Нет прав на обновление'}), 403
        
        topic_name = data.get('name')
        if topic_name:
            topic_name = normalize_topic_name(str(topic_name).strip())
            # Проверка уникальности
            existing = Topic.query.filter(
                Topic.name == topic_name,
                Topic.id != topic_id
            ).first()
            if existing:
                return jsonify({'error': 'Тема с таким именем уже существует'}), 400
            topic.name = topic_name
        
        if 'is_new' in data:
            topic.is_new = bool(data['is_new'])
        
        topic.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления темы'}), 500
        
        return jsonify({
            'ID': topic.id,
            'Name': topic.name,
            'is_new': topic.is_new,
            'modified_date': topic.modified_date.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка обновления темы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@topic_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@token_required
def delete_topic(topic_id):
    """Удаление темы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        topic = Topic.query.get(topic_id)
        if not topic:
            return jsonify({'error': 'Тема не найдена'}), 404
        
        # Проверяем права (только создатель или админ)
        if topic.creator != user_id:
            from logic.model import User
            user = User.query.get(user_id)
            if not user or user.type != 2:
                return jsonify({'error': 'Нет прав на удаление'}), 403
        
        try:
            db.session.delete(topic)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка удаления темы'}), 500
        
        return jsonify({'message': 'Тема успешно удалена'}), 200
        
    except Exception as e:
        logger.error(f"Ошибка удаления темы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500