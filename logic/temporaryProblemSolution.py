# temporaryProblemSolution.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import db, TemporaryProblemSolution, User, Problem, Solution, solution_problems
from logic.middleware import token_required
from logic.utils.logger import get_logger
from sqlalchemy import select, and_

logger = get_logger(__name__)

temporary_problem_solution_bp = Blueprint('temporary_problem_solution', __name__, url_prefix='/api')

def _get_tps_query():
    user_id = getattr(g, 'user_id', None)
    if user_id is None:
        return None, None
    user_id = int(user_id)
    user = User.query.get(user_id)
    if user and getattr(user, 'type', None) == 2:
        return TemporaryProblemSolution.query, user_id
    return TemporaryProblemSolution.query.filter_by(creator=user_id), user_id

@temporary_problem_solution_bp.route('/temporary-problem-solutions/count', methods=['GET'])
@token_required
def count_temporary_problem_solution():
    """Подсчет временных связей проблем и решений"""
    try:
        q, _ = _get_tps_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        return jsonify({'count': q.count()}), 200
    except Exception as e:
        logger.exception(f"Ошибка подсчета временных связей проблем и решений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_problem_solution_bp.route('/temporary-problem-solutions', methods=['GET'])
@token_required
def list_temporary_problem_solution():
    """Список временных связей проблема-решение с именами"""
    try:
        q, _ = _get_tps_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        items = q.all()
        result = []
        for t in items:
            problem = Problem.query.get(t.problem)
            solution = Solution.query.get(t.solution)
            result.append({
                'id': t.id,
                'problem_id': t.problem,
                'solution_id': t.solution,
                'problem_name': problem.name if problem else '',
                'solution_name': solution.name if solution else ''
            })
        return jsonify({'items': result}), 200
    except Exception as e:
        logger.exception(f"Ошибка списка temporary problem solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_problem_solution_bp.route('/temporary-problem-solutions/<int:item_id>/approve', methods=['POST'])
@token_required
def approve_temporary_problem_solution(item_id):
    """Сохранить связь в solution_problems и удалить из временных"""
    try:
        q, user_id = _get_tps_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        t = TemporaryProblemSolution.query.get(item_id)
        if not t:
            return jsonify({'error': 'Не найдено'}), 404
        if not (user_id and User.query.get(user_id) and getattr(User.query.get(user_id), 'type', None) == 2):
            return jsonify({'error': 'Только админ'}), 403
        existing = db.session.execute(
            select(solution_problems).where(
                and_(
                    solution_problems.c.problem_id == t.problem,
                    solution_problems.c.solution_id == t.solution
                )
            )
        ).first()
        if existing:
            TemporaryProblemSolution.query.filter_by(id=item_id).delete()
            db.session.commit()
            return jsonify({'message': 'Связь уже существует, запись удалена'}), 200
        db.session.execute(
            solution_problems.insert().values(problem_id=t.problem, solution_id=t.solution)
        )
        TemporaryProblemSolution.query.filter_by(id=item_id).delete()
        db.session.commit()
        return jsonify({'message': 'Сохранено'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка approve temporary problem solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_problem_solution_bp.route('/temporary-problem-solutions/<int:item_id>', methods=['DELETE'])
@token_required
def delete_temporary_problem_solution(item_id):
    """Удалить временную связь"""
    try:
        q, _ = _get_tps_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        t = q.filter_by(id=item_id).first()
        if not t:
            return jsonify({'error': 'Не найдено'}), 404
        db.session.delete(t)
        db.session.commit()
        return jsonify({'message': 'Удалено'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка удаления temporary problem solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500