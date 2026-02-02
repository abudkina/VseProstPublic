# commentSolution.py
from datetime import datetime
from flask import Blueprint, jsonify, g, request
from logic.model import CommentSolution, Solution, User
from logic.middleware import token_required
from logic.model import db
from logic.utils.logger import get_logger

logger = get_logger(__name__)

comment_solution_bp = Blueprint('comment_solution', __name__, url_prefix='/api')

@comment_solution_bp.route('/comment-solutions/count', methods=['GET'])
@token_required
def count_comment_solution():
    """Подсчет новых комментариев решений (для админа - все новые)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, является ли пользователь админом
        from logic.model import User
        user = User.query.get(user_id)
        if user and user.type == 2:
            # Для админа - все новые комментарии
            count = CommentSolution.query.filter_by(isnew=True).count()
        else:
            # Для обычного пользователя - его новые комментарии
            count = CommentSolution.query.filter_by(
                creator=user_id,
                isnew=True
            ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка подсчета комментариев решений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@comment_solution_bp.route('/comment-solutions', methods=['GET'])
@token_required
def get_comment_solutions():
    """Получение комментариев решений для текущего пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Получаем комментарии пользователя
        comments = CommentSolution.query.filter_by(
            creator=user_id
        ).order_by(CommentSolution.created_date.desc()).all()
        
        # Форматируем для фронтенда
        comments_list = []
        for comment in comments:
            comment_data = comment.to_dict()
            # Добавляем информацию о решении
            solution = Solution.query.get(comment.solution_id)
            if solution:
                comment_data['Solution'] = {
                    'ID': solution.id,
                    'Name': solution.name
                }
            comments_list.append(comment_data)
        
        return jsonify({'comments': comments_list}), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения комментариев: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@comment_solution_bp.route('/comment-solutions/<int:comment_id>/mark-as-read', methods=['PUT'])
@token_required
def mark_comment_as_read(comment_id):
    """Отметить комментарий как прочитанный"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        comment = CommentSolution.query.filter_by(
            id=comment_id,
            creator=user_id
        ).first()
        
        if not comment:
            return jsonify({'error': 'Комментарий не найден'}), 404
        
        comment.is_new = False
        comment.modified_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Комментарий отмечен как прочитанный'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка обновления комментария: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@comment_solution_bp.route('/comment-solutions', methods=['POST'])
@token_required
def add_comment_solution():
    """Добавление нового комментария к решению"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        solution_id = data.get('solution_id')
        content = data.get('content') or data.get('text')
        
        if not solution_id or not content or not str(content).strip():
            return jsonify({'error': 'ID решения и содержание комментария обязательны'}), 400
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        # Получаем решение
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Создаем комментарий
        new_comment = CommentSolution(
            solution_id=solution_id,
            creator=user_id,
            text=str(content).strip(),
            isnew=True
        )
        
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify(new_comment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка создания комментария: {e}")
        return jsonify({'error': 'Ошибка создания комментария'}), 500

@comment_solution_bp.route('/comment-solutions/<int:comment_id>', methods=['PUT'])
@token_required
def update_comment_solution(comment_id):
    """Обновление комментария"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Неверный запрос'}), 400
        
        comment = CommentSolution.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Комментарий не найден'}), 404
        
        # Проверяем права (только создатель или админ)
        if comment.creator != user_id:
            from logic.model import User
            user = User.query.get(user_id)
            if not user or user.type != 2:
                return jsonify({'error': 'Нет прав на обновление'}), 403
        
        if 'text' in data:
            comment.text = str(data['text']).strip()
        
        if 'isnew' in data:
            comment.isnew = bool(data['isnew'])
        
        comment.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления комментария'}), 500
        
        return jsonify(comment.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка обновления комментария: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@comment_solution_bp.route('/comment-solutions/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment_solution(comment_id):
    """Удаление комментария"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        comment = CommentSolution.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Комментарий не найден'}), 404
        
        # Проверяем права (только создатель или админ)
        if comment.creator != user_id:
            from logic.model import User
            user = User.query.get(user_id)
            if not user or user.type != 2:
                return jsonify({'error': 'Нет прав на удаление'}), 403
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({'message': 'Комментарий успешно удален'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка удаления комментария: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@comment_solution_bp.route('/comment-solutions/<int:comment_id>/like', methods=['POST'])
@token_required
def like_comment(comment_id):
    """Лайк комментария"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        comment = CommentSolution.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Комментарий не найден'}), 404
        
        comment.like_count += 1
        db.session.commit()
        
        return jsonify({'like_count': comment.like_count}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка лайка комментария: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@comment_solution_bp.route('/comment-solutions/<int:comment_id>/not-like', methods=['POST'])
@token_required
def not_like_comment(comment_id):
    """Дизлайк комментария"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Не авторизован'}), 401
        
        comment = CommentSolution.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Комментарий не найден'}), 404
        
        comment.not_like_count += 1
        db.session.commit()
        
        return jsonify({'not_like_count': comment.not_like_count}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка дизлайка комментария: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500