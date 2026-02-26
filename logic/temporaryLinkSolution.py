# temporaryLinkSolution.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import db, TemporaryLinkSolution, User, Problem, Solution, solution_problems
from logic.middleware import token_required
from logic.utils.logger import get_logger
from sqlalchemy import select, and_

logger = get_logger(__name__)

temporary_link_solution_bp = Blueprint('temporary_link_solution', __name__, url_prefix='/api')

def _get_tls_query():
    user_id = getattr(g, 'user_id', None)
    if user_id is None:
        return None, None
    user_id = int(user_id)
    user = User.query.get(user_id)
    if user and getattr(user, 'type', None) == 2:
        return TemporaryLinkSolution.query, user_id
    return TemporaryLinkSolution.query.filter_by(creator=user_id), user_id

@temporary_link_solution_bp.route('/temporary-link-solutions/count', methods=['GET'])
@token_required
def count_temporary_link_solution():
    """Подсчет временных ссылок на решения"""
    try:
        q, _ = _get_tls_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        return jsonify({'count': q.count()}), 200
    except Exception as e:
        logger.exception(f"Ошибка подсчета временных ссылок на решения: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_solution_bp.route('/temporary-link-solutions', methods=['GET'])
@token_required
def list_temporary_link_solution():
    """Список временных связей решение-проблема с именами"""
    try:
        q, _ = _get_tls_query()
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
        logger.exception(f"Ошибка списка temporary link solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_solution_bp.route('/temporary-link-solutions/<int:item_id>/approve', methods=['POST'])
@token_required
def approve_temporary_link_solution(item_id):
    """Сохранить связь в solution_problems и удалить из временных"""
    try:
        q, user_id = _get_tls_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        t = TemporaryLinkSolution.query.get(item_id)
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
            TemporaryLinkSolution.query.filter_by(id=item_id).delete()
            db.session.commit()
            return jsonify({'message': 'Связь уже существует, запись удалена'}), 200
        db.session.execute(
            solution_problems.insert().values(problem_id=t.problem, solution_id=t.solution)
        )
        TemporaryLinkSolution.query.filter_by(id=item_id).delete()
        db.session.commit()
        return jsonify({'message': 'Сохранено'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка approve temporary link solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_solution_bp.route('/temporary-link-solutions/<int:item_id>', methods=['DELETE'])
@token_required
def delete_temporary_link_solution(item_id):
    """Удалить временную связь"""
    try:
        q, _ = _get_tls_query()
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
        logger.exception(f"Ошибка удаления temporary link solution: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500