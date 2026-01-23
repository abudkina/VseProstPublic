# temporaryLinkProblem.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import TemporaryLinkProblem
from logic.middleware import token_required

temporary_link_problem_bp = Blueprint('temporary_link_problem', __name__, url_prefix='/api')

@temporary_link_problem_bp.route('/temporary-link-problems/count', methods=['GET'])
@token_required
def count_temporary_link_problem():
    """Подсчет временных ссылок на проблемы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
    
        # Подсчет всех ссылок пользователя (модель не имеет полей is_used и expires_at)
        count = TemporaryLinkProblem.query.filter_by(
            creator=user_id
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"Ошибка подсчета временных ссылок на проблемы: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500