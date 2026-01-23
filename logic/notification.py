# notofication.py
from flask import Blueprint, jsonify, request, g
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from logic.model import Notification
from logic.middleware import token_required
from logic.model import db

notification_bp = Blueprint('notification', __name__,url_prefix='/api')

@notification_bp.route('/notifications/count-unread', methods=['GET'])
@token_required
def count_unread_notifications():
    """Подсчет непрочитанных уведомлений"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        try:
            # Пробуем использовать прямой SQL запрос для большей надежности
            from sqlalchemy import text
            # Используем правильное имя таблицы для MySQL
            result = db.session.execute(
                text("SELECT COUNT(*) FROM `Notification` WHERE `user` = :user_id AND `read` = 0"),
                {'user_id': user_id}
            )
            count = result.scalar() or 0
        except Exception as db_error:
            # Если таблица не существует, просто возвращаем 0 вместо ошибки
            error_str = str(db_error)
            if "doesn't exist" in error_str or "Table" in error_str:
                # Таблица не существует - это нормально, возвращаем 0 без вывода ошибки
                count = 0
            else:
                print(f"Ошибка запроса к базе данных: {db_error}")
                import traceback
                traceback.print_exc()
                # Пробуем через ORM как fallback
                try:
                    count = Notification.query.filter_by(
                        user=user_id,
                        read=False
                    ).count()
                except Exception as orm_error:
                    # Если и ORM не работает (таблица не существует), возвращаем 0
                    if "doesn't exist" in str(orm_error) or "Table" in str(orm_error):
                        # Таблица не существует - это нормально, возвращаем 0 без вывода ошибки
                        count = 0
                    else:
                        print(f"ORM запрос также не сработал: {orm_error}")
                        return jsonify({'error': 'Ошибка базы данных', 'details': str(orm_error)}), 500
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"Ошибка подсчета уведомлений: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500

@notification_bp.route('/notifications/<int:notification_id>', methods=['GET'])
@token_required
def get_notification(notification_id):
    """Получение конкретного уведомления"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                user=user_id
            ).first()
        except Exception as e:
            error_str = str(e)
            if "doesn't exist" in error_str or "Table" in error_str:
                return jsonify({'error': 'Уведомление не найдено'}), 404
            raise
        
        if not notification:
            return jsonify({'error': 'Уведомление не найдено'}), 404
        
        return jsonify(notification.to_dict()), 200
        
    except Exception as e:
        print(f"Ошибка получения уведомления: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@notification_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@token_required
def delete_notification(notification_id):
    """Удаление уведомления"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user=user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Уведомление не найдено'}), 404
        
        try:
            db.session.delete(notification)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка удаления уведомления'}), 500
        
        return jsonify({'message': 'Уведомление успешно удалено'}), 200
        
    except Exception as e:
        print(f"Ошибка удаления уведомления: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@notification_bp.route('/notifications/mark-all-read', methods=['PATCH'])
@token_required
def mark_all_as_read():
    """Отметить все уведомления как прочитанные"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        try:
            # Обновляем все непрочитанные уведомления пользователя
            updated_count = Notification.query.filter_by(
                user=user_id,
                read=False
            ).update({
                'read': True,
                'modified_date': datetime.utcnow()
            })
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error_str = str(e)
            if "doesn't exist" in error_str or "Table" in error_str:
                # Таблица не существует - возвращаем успешный ответ с 0 обновлений
                return jsonify({
                    'message': 'Все уведомления отмечены как прочитанные',
                    'updated_count': 0
                }), 200
            print(f"Ошибка обновления уведомлений: {e}")
            return jsonify({'error': 'Ошибка обновления уведомлений'}), 500
        
        return jsonify({
            'message': 'Все уведомления отмечены как прочитанные',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@notification_bp.route('/notifications', methods=['POST'])
@token_required
def create_notification():
    """Создание нового уведомления"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        name = data.get('name')
        if not name or not str(name).strip():
            return jsonify({'error': 'Имя уведомления обязательно'}), 400
        
        description = data.get('description', '')
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Создаем новое уведомление
        notification = Notification(
            user=user_id,
            creator=user_id,  # По умолчанию создатель = получатель
            name=str(name).strip(),
            describe=str(description).strip() if description else '',
            read=False
        )
        
        try:
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка создания уведомления: {e}")
            return jsonify({'error': 'Ошибка создания уведомления'}), 500
        
        return jsonify(notification.to_dict()), 201
        
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@notification_bp.route('/notifications', methods=['GET'])
@token_required
def get_all_notifications():
    """Получение всех уведомлений пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        try:
            # Получаем все уведомления пользователя, отсортированные по дате (новые первыми)
            notifications = Notification.query.filter_by(
                user=user_id
            ).order_by(Notification.created_date.desc()).all()
        except Exception as e:
            error_str = str(e)
            if "doesn't exist" in error_str or "Table" in error_str:
                # Таблица не существует - возвращаем пустой список
                return jsonify([]), 200
            raise
        
        response = [notification.to_dict() for notification in notifications]
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Ошибка получения уведомлений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@notification_bp.route('/notifications/toggle-read', methods=['PATCH'])
@token_required
def toggle_read_notification():
    """Переключение статуса прочтения уведомления"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        notification_id = request.args.get('id', type=int)
        if not notification_id:
            return jsonify({'error': 'ID уведомления не указан'}), 400
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user=user_id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Уведомление не найдено'}), 404
        
        try:
            # Переключаем статус прочтения
            notification.read = not notification.read
            notification.modified_date = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка обновления уведомления: {e}")
            return jsonify({'error': 'Ошибка обновления уведомления'}), 500
        
        return jsonify({
            'message': 'Статус уведомления обновлен',
            'read': notification.read
        }), 200
        
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@notification_bp.route('/notifications/recent', methods=['GET'])
@token_required
def get_recent_notifications():
    """Получение последних уведомлений (с пагинацией)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Получаем параметры пагинации
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Ограничиваем максимальный лимит
        if limit > 100:
            limit = 100
        
        try:
            # Получаем уведомления с пагинацией
            notifications = Notification.query.filter_by(
                user=user_id
            ).order_by(Notification.modified_date.desc()).offset(offset).limit(limit).all()
            
            # Получаем общее количество
            total_count = Notification.query.filter_by(user=user_id).count()
        except Exception as e:
            error_str = str(e)
            if "doesn't exist" in error_str or "Table" in error_str:
                # Таблица не существует - возвращаем пустой список
                return jsonify({
                    'notifications': [],
                    'total_count': 0,
                    'limit': limit,
                    'offset': offset
                }), 200
            raise
        
        response = [notification.to_dict() for notification in notifications]
        
        return jsonify({
            'notifications': response,
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f"Ошибка получения уведомлений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500 