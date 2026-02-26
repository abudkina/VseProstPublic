# hashtag.py
from flask import Blueprint, jsonify, request, g
from datetime import datetime
import re

from flask_sqlalchemy import SQLAlchemy
from logic.model import Hashtag, User
from logic.middleware import token_required
from logic.model import db
from logic.utils.normalizers import normalize_hashtag_name
from logic.utils.logger import get_logger

logger = get_logger(__name__)

hashtag_bp = Blueprint('hashtag', __name__,url_prefix='/api')

@hashtag_bp.route('/hashtags', methods=['POST'])
@token_required
def add_hashtag():
    """Обработчик для добавления хэштега"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        # Проверяем наличие имени хэштега
        hashtag_name = data.get('name')
        if not hashtag_name or not str(hashtag_name).strip():
            return jsonify({'error': 'Неверный запрос: имя хэштега обязательно и не должно быть пустым'}), 400
        
        # Убираем лишние пробелы
        hashtag_name = str(hashtag_name).strip()
        
        # Получаем userID из контекста (установлено middleware)
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Проверяем, что пользователь существует
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Нормализуем имя запроса
        normalized_req_name = normalize_hashtag_name(hashtag_name)
        
        # Проверяем, существует ли уже хэштег с таким нормализованным именем для этого пользователя
        try:
            # Сначала получаем все хэштеги пользователя
            user_hashtags = Hashtag.query.filter_by(creator=user_id).all()
            
            # Проверяем каждый хэштег на нормализованное имя
            for hashtag in user_hashtags:
                normalized_existing_name = normalize_hashtag_name(hashtag.name)
                if normalized_existing_name == normalized_req_name:
                    return jsonify({'error': 'Хэштег с таким именем уже существует'}), 400
        
        except Exception as e:
            logger.error(f"Ошибка проверки уникальности: {e}")
            return jsonify({'error': 'Ошибка проверки уникальности'}), 500
        
        # Создаем новый хэштег (сохраняем без #, с маленькой буквы)
        new_hashtag = Hashtag(
            name=normalized_req_name,
            creator=user_id,  # Используем creator, а не creator_id
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow(),
            isnew=True,  # В модели это поле называется isnew
            show=0  # Добавляем обязательное поле show
        )
        
        try:
            db.session.add(new_hashtag)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка создания хэштега: {e}")
            return jsonify({'error': 'Ошибка создания хэштега'}), 500
        
        # Возвращаем созданный хэштег
        return jsonify({
            'ID': new_hashtag.id,
            'Name': new_hashtag.name,
            'creator': new_hashtag.creator,
            'created_date': new_hashtag.created_date.isoformat(),
            'modified_date': new_hashtag.modified_date.isoformat(),
            'isnew': new_hashtag.isnew,
            'show': new_hashtag.show
        }), 201
        
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@hashtag_bp.route('/hashtags/count', methods=['GET'])
@token_required
def count_hashtag():
    """Обработчик для подсчета новых хэштегов"""
    try:
        # Получаем userID из контекста
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчитываем количество новых хэштегов для текущего пользователя
        count = Hashtag.query.filter_by(
            creator=user_id,
            isnew=True
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.error(f"Ошибка подсчета хэштегов: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500
    
@hashtag_bp.route('/hashtags', methods=['GET'])
@token_required
def get_hashtags():
    """Получение всех хэштегов пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        hashtags = Hashtag.query.filter_by(creator=user_id).order_by(Hashtag.created_date.desc()).all()
        
        hashtags_list = [hashtag.to_dict() for hashtag in hashtags]
        
        return jsonify({'hashtags': hashtags_list}), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения хэштегов: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных'}), 500

@hashtag_bp.route('/hashtags/<int:hashtag_id>', methods=['PUT'])
@token_required
def update_hashtag(hashtag_id):
    """Обновление хэштега"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        hashtag_name = data.get('name')
        if not hashtag_name or not str(hashtag_name).strip():
            return jsonify({'error': 'Имя хэштега обязательно'}), 400
        
        # Находим хэштег
        hashtag = Hashtag.query.filter_by(id=hashtag_id, creator=user_id).first()
        if not hashtag:
            return jsonify({'error': 'Хэштег не найден'}), 404
        
        # Проверяем уникальность нового имени
        new_name = str(hashtag_name).strip()
        normalized_new_name = normalize_hashtag_name(new_name)
        
        # Проверяем другие хэштеги пользователя (кроме текущего)
        other_hashtags = Hashtag.query.filter(
            Hashtag.creator == user_id,
            Hashtag.id != hashtag_id
        ).all()
        
        for other_hashtag in other_hashtags:
            normalized_existing_name = normalize_hashtag_name(other_hashtag.name)
            if normalized_existing_name == normalized_new_name:
                return jsonify({'error': 'Хэштег с таким именем уже существует'}), 400
        
        # Обновляем хэштег (без #, с маленькой буквы)
        hashtag.name = normalized_new_name
        hashtag.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления хэштега'}), 500
        
        return jsonify({
            'id': hashtag.id,
            'name': hashtag.name,
            'modified_date': hashtag.modified_date.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка обновления хэштега: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@hashtag_bp.route('/hashtags/<int:hashtag_id>', methods=['DELETE'])
@token_required
def delete_hashtag(hashtag_id):
    """Удаление хэштега"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Находим хэштег
        hashtag = Hashtag.query.filter_by(id=hashtag_id, creator=user_id).first()
        if not hashtag:
            return jsonify({'error': 'Хэштег не найден'}), 404
        
        try:
            db.session.delete(hashtag)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка удаления хэштега'}), 500
        
        return jsonify({'message': 'Хэштег успешно удален'}), 200
        
    except Exception as e:
        logger.error(f"Ошибка удаления хэштега: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@hashtag_bp.route('/hashtags/<int:hashtag_id>/mark-as-read', methods=['PUT'])
@token_required
def mark_hashtag_as_read(hashtag_id):
    """Отметить хэштег как прочитанный (снять флаг is_new)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Находим хэштег
        hashtag = Hashtag.query.filter_by(id=hashtag_id, creator=user_id).first()
        if not hashtag:
            return jsonify({'error': 'Хэштег не найден'}), 404
        
        # Снимаем флаг is_new
        hashtag.isnew = False
        hashtag.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления хэштега'}), 500
        
        return jsonify({'message': 'Хэштег отмечен как прочитанный'}), 200
        
    except Exception as e:
        logger.error(f"Ошибка обновления хэштега: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@hashtag_bp.route('/hashtags/search', methods=['GET'])
@token_required
def search_hashtags():
    """Поиск хэштегов по имени"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        search_query = request.args.get('q', '').strip()
        if not search_query:
            return jsonify({'hashtags': []}), 200
        
        # Ищем хэштеги пользователя, содержащие поисковый запрос
        # Поиск без учета регистра
        hashtags = Hashtag.query.filter(
            Hashtag.creator == user_id,
            Hashtag.name.ilike(f'%{search_query}%')
        ).order_by(Hashtag.name).limit(10).all()
        
        hashtags_list = [hashtag.to_dict() for hashtag in hashtags]
        
        return jsonify({'hashtags': hashtags_list}), 200
        
    except Exception as e:
        logger.error(f"Ошибка поиска хэштегов: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500