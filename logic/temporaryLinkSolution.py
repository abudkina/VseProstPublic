# temporaryLinkSolution.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import TemporaryLinkSolution
from logic.middleware import token_required
from logic.utils.logger import get_logger

logger = get_logger(__name__)

temporary_link_solution_bp = Blueprint('temporary_link_solution', __name__, url_prefix='/api')

@temporary_link_solution_bp.route('/temporary-link-solutions/count', methods=['GET'])
@token_required
def count_temporary_link_solution():
    """Подсчет временных ссылок на решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчет всех ссылок пользователя (модель не имеет полей is_used и expires_at)
        count = TemporaryLinkSolution.query.filter_by(
            creator=user_id
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.error(f"Ошибка подсчета временных ссылок на решения: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500