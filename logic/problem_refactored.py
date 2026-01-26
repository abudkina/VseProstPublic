"""
Problem Blueprint - HTTP endpoints для работы с проблемами

Использует ProblemService для бизнес-логики.
"""
from flask import Blueprint, jsonify, request, g
from logic.middleware import token_required, extract_user_from_token
from logic.utils.error_decorators import handle_errors
from logic.utils.error_handler import ValidationError, ResourceNotFoundError
from logic.utils.validators import parse_int_list
from logic.utils.logger import get_logger
from logic.services import ProblemService
from logic.model import Hashtag, db

logger = get_logger(__name__)

problem_bp = Blueprint('problem', __name__, url_prefix='/api')


@problem_bp.route('/hashtags', methods=['GET'])
@handle_errors()
def get_hashtags():
    """Получение хэштегов с фильтрацией LIKE (длина запроса минимум 2 символа)"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([]), 200
    
    # Получаем userID из контекста для фильтрации по пользователю
    user_id = getattr(g, 'user_id', None)
    
    if not user_id:
        raise ValidationError("Требуется аутентификация для получения хэштегов")
    
    # Ищем хэштеги пользователя, начинающиеся с запроса (без учета регистра)
    search_pattern = f"{query.lower()}%"
    
    hashtags = Hashtag.query.filter(
        Hashtag.creator == user_id,
        Hashtag.name.ilike(search_pattern)
    ).order_by(
        Hashtag.show.desc(),
        Hashtag.modified_date.desc()
    ).limit(20).all()
    
    hashtags_list = [
        {
            'id': hashtag.id,
            'name': hashtag.name,
            'creator_id': hashtag.creator,
            'created_date': hashtag.created_date.isoformat() if hashtag.created_date else None,
            'modified_date': hashtag.modified_date.isoformat() if hashtag.modified_date else None,
            'is_new': hashtag.isnew,
            'show': hashtag.show
        }
        for hashtag in hashtags
    ]
    
    return jsonify(hashtags_list), 200


@problem_bp.route('/problems', methods=['GET'])
@handle_errors()
def get_problems():
    """Получение списка проблем с фильтрацией и пагинацией"""
    # Извлекаем информацию о пользователе из токена (если есть)
    extract_user_from_token()
    
    # Получаем параметры фильтрации
    search = request.args.get('search', '').strip()
    category_param = request.args.get('category', '')
    hashtags_param = request.args.get('hashtags', '')
    topic_param = request.args.get('topic', '')
    exclude_param = request.args.get('exclude', '')
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    logger.debug(f"Параметры запроса: search={search}, category={category_param}, hashtags={hashtags_param}, limit={limit}, offset={offset}")
    
    # Получаем user_id для рекомендаций и проверки избранного
    user_id = getattr(g, 'user_id', None)
    
    # Парсим фильтры
    category_id = int(category_param) if category_param else None
    hashtag_ids = parse_int_list(hashtags_param)
    topic_id = int(topic_param) if topic_param else None
    exclude_ids = parse_int_list(exclude_param)
    
    # Получаем проблемы
    problems_list, total_count = ProblemService.get_all_problems(
        search=search,
        category_id=category_id,
        hashtag_ids=hashtag_ids,
        topic_id=topic_id,
        exclude_ids=exclude_ids,
        limit=limit,
        offset=offset,
        user_id=user_id
    )
    
    return {
        'data': problems_list,
        'total': total_count,
        'limit': limit,
        'offset': offset
    }, 200


@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
@handle_errors()
def get_problem_by_id(problem_id):
    """Получение проблемы по ID"""
    extract_user_from_token()
    user_id = getattr(g, 'user_id', None)
    
    problem = ProblemService.get_problem_by_id(problem_id, user_id=user_id)
    return problem, 200


@problem_bp.route('/problems', methods=['POST'])
@handle_errors()
@token_required
def create_problem():
    """Создание новой проблемы"""
    data = request.get_json() or {}
    
    problem = ProblemService.create_problem(g.user_id, data)
    return problem, 201


@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
@handle_errors()
@token_required
def update_problem(problem_id):
    """Обновление проблемы"""
    data = request.get_json() or {}
    
    problem = ProblemService.update_problem(problem_id, g.user_id, data)
    return problem, 200


@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
@handle_errors()
@token_required
def delete_problem(problem_id):
    """Удаление проблемы"""
    ProblemService.delete_problem(problem_id, g.user_id)
    return {'message': 'Проблема успешно удалена'}, 204


@problem_bp.route('/problems/<int:problem_id>/toggle-favourite', methods=['POST'])
@handle_errors()
@token_required
def toggle_favourite(problem_id):
    """Переключение статуса избранного"""
    result = ProblemService.toggle_favourite(problem_id, g.user_id)
    return result, 200


@problem_bp.route('/problems/<int:problem_id>/toggle-show', methods=['POST'])
@handle_errors()
@token_required
def toggle_show(problem_id):
    """Переключение видимости проблемы"""
    result = ProblemService.toggle_show(problem_id, g.user_id)
    return result, 200


@problem_bp.route('/problems/<int:problem_id>/mark-as-read', methods=['POST'])
@handle_errors()
@token_required
def mark_problem_as_read(problem_id):
    """Отметить проблему как прочитанную"""
    result = ProblemService.mark_as_read(problem_id, g.user_id)
    return result, 200


@problem_bp.route('/problems/favorites', methods=['GET'])
@handle_errors()
@token_required
def get_favourite_problems():
    """Получение избранных проблем пользователя"""
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    # Получаем избранные проблемы
    from logic.model import User, favourite_problem, Problem
    user = User.query.get(g.user_id)
    
    if not user:
        raise ResourceNotFoundError('User', g.user_id)
    
    # Получаем count
    total_count = len(user.favourite_problems)
    
    # Получаем с пагинацией
    favourite_ids = [p.id for p in user.favourite_problems]
    problems = Problem.query.filter(Problem.id.in_(favourite_ids)).offset(offset).limit(limit).all()
    
    problems_list = [
        ProblemService._format_problem_response(p, g.user_id)
        for p in problems
    ]
    
    return {
        'data': problems_list,
        'total': total_count,
        'limit': limit,
        'offset': offset
    }, 200


@problem_bp.route('/problems/user/<int:user_id>', methods=['GET'])
@handle_errors()
def get_user_problems(user_id):
    """Получение проблем конкретного пользователя"""
    extract_user_from_token()
    current_user_id = getattr(g, 'user_id', None)
    
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    from logic.model import User, Problem
    user = User.query.get(user_id)
    
    if not user:
        raise ResourceNotFoundError('User', user_id)
    
    # Получаем проблемы пользователя
    problems = Problem.query.filter_by(creator_id=user_id, show=True).order_by(
        Problem.created_date.desc()
    ).offset(offset).limit(limit).all()
    
    total_count = Problem.query.filter_by(creator_id=user_id, show=True).count()
    
    problems_list = [
        ProblemService._format_problem_response(p, current_user_id)
        for p in problems
    ]
    
    return {
        'data': problems_list,
        'total': total_count,
        'limit': limit,
        'offset': offset
    }, 200


@problem_bp.route('/problems/count-new', methods=['GET'])
@handle_errors()
def count_problem():
    """Получение количества новых проблем"""
    from logic.model import Problem
    count = Problem.query.filter(Problem.show.isnot(None)).count()
    return {'count': count}, 200


@problem_bp.route('/problems/<int:problem_id>/link', methods=['POST'])
@handle_errors()
@token_required
def link_problem(problem_id):
    """Создание временной ссылки для проблемы (устаревший endpoint, для совместимости)"""
    from logic.model import Problem
    
    problem = Problem.query.get(problem_id)
    if not problem:
        raise ResourceNotFoundError('Problem', problem_id)
    
    # Для совместимости - просто возвращаем ID
    return {
        'problem_id': problem_id,
        'link': f'/html/problem.html?id={problem_id}'
    }, 200


@problem_bp.route('/problems/<int:problem_id>/add-solution', methods=['POST'])
@handle_errors()
@token_required
def add_solution_to_problem(problem_id):
    """Добавить решение к проблеме (перенаправляется на solution endpoint)"""
    from logic.model import Problem
    
    problem = Problem.query.get(problem_id)
    if not problem:
        raise ResourceNotFoundError('Problem', problem_id)
    
    # Добавляем problem_id к данным и передаем в solution service
    data = request.get_json() or {}
    data['problem_id'] = problem_id
    
    # Это будет использовать SolutionService (когда будет готов)
    from logic.services import SolutionService
    solution = SolutionService.create_solution(g.user_id, data)
    
    return solution, 201
