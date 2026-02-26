# temporaryLinkProblem.py - улучшенная версия
from flask import Blueprint, jsonify, g
from logic.model import db, TemporaryLinkProblem, User, Problem, problem_link_problem
from logic.middleware import token_required
from logic.utils.logger import get_logger
from sqlalchemy import select, and_

logger = get_logger(__name__)

temporary_link_problem_bp = Blueprint('temporary_link_problem', __name__, url_prefix='/api')

def _get_tlp_query():
    user_id = getattr(g, 'user_id', None)
    if user_id is None:
        return None, None
    user_id = int(user_id)
    user = User.query.get(user_id)
    if user and getattr(user, 'type', None) == 2:
        return TemporaryLinkProblem.query, user_id
    return TemporaryLinkProblem.query.filter_by(creator=user_id), user_id

@temporary_link_problem_bp.route('/temporary-link-problems/count', methods=['GET'])
@token_required
def count_temporary_link_problem():
    """Подсчет временных ссылок на проблемы"""
    try:
        q, _ = _get_tlp_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        return jsonify({'count': q.count()}), 200
    except Exception as e:
        logger.exception(f"Ошибка подсчета временных ссылок на проблемы: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_problem_bp.route('/temporary-link-problems', methods=['GET'])
@token_required
def list_temporary_link_problem():
    """Список временных связей проблема-проблема с именами"""
    try:
        q, _ = _get_tlp_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        items = q.all()
        result = []
        for t in items:
            p1 = Problem.query.get(t.currentproblem)
            p2 = Problem.query.get(t.linkproblem)
            result.append({
                'id': t.id,
                'problem_id': t.currentproblem,
                'link_problem_id': t.linkproblem,
                'problem_name': p1.name if p1 else '',
                'link_problem_name': p2.name if p2 else ''
            })
        return jsonify({'items': result}), 200
    except Exception as e:
        logger.exception(f"Ошибка списка temporary link problem: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_problem_bp.route('/temporary-link-problems/<int:item_id>/approve', methods=['POST'])
@token_required
def approve_temporary_link_problem(item_id):
    """Сохранить связь в problem_link_problem и удалить из временных"""
    try:
        q, user_id = _get_tlp_query()
        if q is None:
            return jsonify({'error': 'userID не найден'}), 401
        t = TemporaryLinkProblem.query.get(item_id)
        if not t:
            return jsonify({'error': 'Не найдено'}), 404
        if not (user_id and User.query.get(user_id) and getattr(User.query.get(user_id), 'type', None) == 2):
            return jsonify({'error': 'Только админ'}), 403
        existing = db.session.execute(
            select(problem_link_problem).where(
                and_(
                    problem_link_problem.c.problem_id == t.currentproblem,
                    problem_link_problem.c.problem_link_id == t.linkproblem
                )
            )
        ).first()
        if existing:
            TemporaryLinkProblem.query.filter_by(id=item_id).delete()
            db.session.commit()
            return jsonify({'message': 'Связь уже существует, запись удалена'}), 200
        db.session.execute(
            problem_link_problem.insert().values(
                problem_id=t.currentproblem,
                problem_link_id=t.linkproblem
            )
        )
        TemporaryLinkProblem.query.filter_by(id=item_id).delete()
        db.session.commit()
        return jsonify({'message': 'Сохранено'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка approve temporary link problem: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@temporary_link_problem_bp.route('/temporary-link-problems/<int:item_id>', methods=['DELETE'])
@token_required
def delete_temporary_link_problem(item_id):
    """Удалить временную связь"""
    try:
        q, _ = _get_tlp_query()
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
        logger.exception(f"Ошибка удаления temporary link problem: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500