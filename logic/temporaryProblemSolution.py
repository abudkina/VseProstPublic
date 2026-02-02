# temporaryProblemSolution.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import TemporaryProblemSolution
from logic.middleware import token_required
from logic.utils.logger import get_logger

logger = get_logger(__name__)

temporary_problem_solution_bp = Blueprint('temporary_problem_solution', __name__, url_prefix='/api')

@temporary_problem_solution_bp.route('/temporary-problem-solutions/count', methods=['GET'])
@token_required
def count_temporary_problem_solution():
    """Подсчет временных связей проблем и решений"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчет всех связей пользователя (модель не имеет полей is_used и expires_at)
        count = TemporaryProblemSolution.query.filter_by(
            creator=user_id
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.error(f"Ошибка подсчета временных связей проблем и решений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500