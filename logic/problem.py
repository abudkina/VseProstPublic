# problem.py
from flask import Blueprint, jsonify, request, g, current_app
from datetime import datetime, timedelta
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from logic.model import Category, Hashtag, Problem, Solution, User, Topic, favourite_problem
from logic.middleware import token_required, extract_user_from_token
import re

from logic.model import db
from logic.utils.file_utils import allowed_file, save_file_to_yandex_storage, delete_image, normalize_image_url, image_url_for_display
from logic.utils.validators import parse_int_list, parse_bool
from logic.utils.image_search import generate_image_with_openai
from logic.recommendations import track_user_activity, get_user_recommendations, create_embedding
from logic.rag_search import search_with_rag, hybrid_search, semantic_search
from logic.utils.logger import get_logger
from logic.utils.normalizers import capitalize_title, capitalize_first
from logic.services.problem_service import ProblemService
from logic.utils.error_handler import (
    ValidationError, AuthorizationError, ResourceNotFoundError, DatabaseError
)

logger = get_logger(__name__)

problem_bp = Blueprint('problem', __name__, url_prefix='/api')

@problem_bp.route('/hashtags', methods=['GET'])
def get_hashtags():
    """Получение хэштегов с фильтрацией LIKE (длина запроса минимум 2 символа)"""
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([]), 200
        
        # Получаем userID из контекста для фильтрации по пользователю
        user_id = getattr(g, 'user_id', None)
        
        # Ищем хэштеги пользователя, начинающиеся с запроса (без учета регистра)
        search_pattern = f"{query.lower()}%"
        
        hashtags = Hashtag.query.filter(
            Hashtag.creator == user_id,
            Hashtag.name.ilike(search_pattern)
        ).order_by(
            Hashtag.show.desc(),
            Hashtag.modified_date.desc()
        ).limit(20).all()
        
        hashtags_list = []
        for hashtag in hashtags:
            hashtags_list.append({
                'id': hashtag.id,
                'name': hashtag.name,
                'creator_id': hashtag.creator,
                'created_date': hashtag.created_date.isoformat() if hashtag.created_date else None,
                'modified_date': hashtag.modified_date.isoformat() if hashtag.modified_date else None,
                'is_new': hashtag.isnew,
                'show': hashtag.show
            })
        
        return jsonify(hashtags_list), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения хэштегов: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@problem_bp.route('/problems', methods=['GET'])
def get_problems():
    """Получение списка проблем с фильтрацией и пагинацией"""
    try:
        # Извлекаем информацию о пользователе из токена (если есть)
        # Это нужно для определения IsFavourite, даже если авторизация не обязательна
        extract_user_from_token()
        
        # Получаем параметры фильтрации
        search = request.args.get('search', '').strip()
        category_param = request.args.get('category', '')
        hashtags_param = request.args.get('hashtags', '')
        topic_param = request.args.get('topic', '')
        exclude_param = request.args.get('exclude', '')
        isnew_param = request.args.get('isnew', '').strip().lower()
        sort_param = (request.args.get('sort', '') or 'default').strip().lower()
        try:
            limit = int(request.args.get('limit', 50))
        except (TypeError, ValueError):
            limit = 50
        try:
            offset = int(request.args.get('offset', 0))
        except (TypeError, ValueError):
            offset = 0
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 50
        if offset < 0:
            offset = 0
        
        logger.debug(f"Параметры запроса: search={search}, category={category_param}, hashtags={hashtags_param}, limit={limit}, offset={offset}")
        
        # Получаем user_id для рекомендаций и проверки избранного
        user_id = getattr(g, 'user_id', None)
        
        # Отслеживаем поисковый запрос (если пользователь авторизован и есть поиск)
        if user_id and search:
            try:
                track_user_activity(user_id, 'search', 'problem', search_query=search)
            except Exception as e:
                logger.debug(f"Не удалось отследить поисковый запрос: {e}")
        
        # Рекомендации в отдельном потоке с таймаутом, чтобы не блокировать ответ
        recommended_ids = []
        if user_id:
            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(get_user_recommendations, user_id, 'problem', 20)
                    recommended_ids = fut.result(timeout=2)
            except (FuturesTimeoutError, Exception) as e:
                logger.debug(f"Рекомендации не получены (таймаут/ошибка): {e}")
                recommended_ids = []
        
        # Начинаем базовый запрос
        # Используем joinedload для eager loading связанных объектов (исправление N+1)
        query = Problem.query.options(
            joinedload(Problem.hashtags),
            joinedload(Problem.solutions),
            joinedload(Problem.linked_problems),
            joinedload(Problem.favourite_users)
        )

        # Фильтр по поиску (название или описание)
        # Используем гибридный поиск (RAG + текстовый) для лучших результатов
        rag_search_results = []
        if search:
            try:
                # Пробуем использовать RAG поиск для семантического поиска
                search_mode = request.args.get('search_mode', 'hybrid')  # 'text', 'semantic', 'hybrid', 'multimodal'
                rag_search_results = search_with_rag(
                    query=search,
                    entity_type='problem',
                    search_mode=search_mode,
                    limit=limit * 2,  # Берем больше для фильтрации
                    exclude_ids=[int(exclude_param)] if exclude_param else None
                )
                
                # Если есть результаты RAG поиска, используем их
                if rag_search_results:
                    rag_ids = [entity_id for entity_id, score in rag_search_results]
                    query = query.filter(Problem.id.in_(rag_ids))
                else:
                    # Fallback на обычный текстовый поиск
                    search_lower = f"%{search.lower()}%"
                    from sqlalchemy import func
                    query = query.filter(
                        db.or_(
                            func.lower(Problem.name).like(search_lower),
                            func.lower(Problem.describe).like(search_lower)
                        )
                    )
            except Exception as e:
                logger.warning(f"Ошибка RAG поиска, используем текстовый поиск: {e}")
                # Fallback на обычный текстовый поиск
                search_lower = f"%{search.lower()}%"
                from sqlalchemy import func
                query = query.filter(
                    db.or_(
                        func.lower(Problem.name).like(search_lower),
                        func.lower(Problem.describe).like(search_lower)
                    )
                )
        
        # Фильтр по категории
        if category_param:
            try:
                category_id = int(category_param)
                query = query.filter_by(category=category_id)
            except ValueError:
                logger.warning(f"Ошибка преобразования category: {category_param}")
        
        # Фильтр по хэштегам
        if hashtags_param:
            hashtag_ids = parse_int_list(hashtags_param)
            
            logger.debug(f"Хэштеги для фильтрации: {hashtag_ids}")
            
            if hashtag_ids:
                from sqlalchemy import and_, func
                from logic.model import hashtag_problem
                
                # Подзапрос для фильтрации по всем указанным хэштегам
                subquery = db.session.query(
                    hashtag_problem.c.problem_id
                ).filter(
                    hashtag_problem.c.hashtag_id.in_(hashtag_ids)
                ).group_by(
                    hashtag_problem.c.problem_id
                ).having(
                    func.count(hashtag_problem.c.hashtag_id.distinct()) == len(hashtag_ids)
                ).subquery()
                
                query = query.filter(Problem.id.in_(db.session.query(subquery.c.problem_id)))
        
        # Фильтр по теме
        if topic_param:
            try:
                topic_id = int(topic_param)
                query = query.filter_by(topic=topic_id)
            except ValueError:
                logger.warning(f"Ошибка преобразования topic: {topic_param}")
        
        # Исключаем проблему по ID
        if exclude_param:
            try:
                exclude_id = int(exclude_param)
                query = query.filter(Problem.id != exclude_id)
            except ValueError:
                logger.warning(f"Ошибка преобразования exclude: {exclude_param}")
        
        # По умолчанию показываем все (is_new true и false). Фильтр только при явном isnew=true
        if isnew_param in ('true', '1'):
            query = query.filter(Problem.isnew == True)
        
        # Применяем сортировку и пагинацию
        # Если использовался RAG поиск, сортируем по релевантности
        if rag_search_results and search:
            # Создаем словарь с оценками релевантности
            relevance_scores = {entity_id: score for entity_id, score in rag_search_results}
            
            # Получаем все проблемы
            all_problems = query.all()
            
            # Сортируем по релевантности (если есть), затем по дате
            problems = sorted(
                all_problems,
                key=lambda p: (
                    -relevance_scores.get(p.id, 0.0),  # Сначала по релевантности (убывание)
                    -(p.created_date or datetime.min).timestamp()  # Затем по дате (убывание)
                )
            )
            
            # Применяем пагинацию
            problems = problems[offset:offset + limit]
        else:
            # Сортировка по параметру sort
            if sort_param == 'show':
                query = query.order_by(Problem.show.desc(), Problem.created_date.desc())
            elif sort_param == 'popularity':
                query = query.order_by(Problem.favourite.desc(), Problem.created_date.desc())
            else:
                # default, date или любое другое — по дате
                query = query.order_by(Problem.created_date.desc())
            problems = query.offset(offset).limit(limit).all()
        
        logger.debug(f"Найдено проблем через SQLAlchemy: {len(problems)}")
        
        # Если есть рекомендации и нет активных фильтров и сортировка по умолчанию — добавляем рекомендованные в начало
        if (recommended_ids and not search and not category_param and not hashtags_param and not topic_param
                and sort_param in ('', 'default')):
            # Получаем рекомендованные проблемы
            recommended_problems = Problem.query.filter(Problem.id.in_(recommended_ids)).all()
            
            # Разделяем на рекомендованные и не рекомендованные
            recommended_dict = {p.id: p for p in recommended_problems}
            regular_problems = [p for p in problems if p.id not in recommended_ids]
            
            # Сортируем рекомендованные по релевантности (можно улучшить)
            recommended_sorted = sorted(
                [p for p in recommended_problems if p.id in recommended_ids],
                key=lambda x: (x.created_date or datetime.min),
                reverse=True
            )
            
            # Объединяем: сначала рекомендованные, потом обычные
            problems = recommended_sorted + regular_problems
            
            # Ограничиваем общее количество
            problems = problems[:limit]
        
        # Если не найдено через SQLAlchemy, пробуем прямой SQL запрос
        # SECURITY: Используем whitelist для имен таблиц
        if len(problems) == 0:
            try:
                from sqlalchemy import text
                ALLOWED_TABLE_NAMES = ['Problem', 'problem', 'PROBLEM']
                direct_result = None
                working_table_name = None
                for table_name in ALLOWED_TABLE_NAMES:
                    try:
                        direct_sql = text(f"""
                            SELECT id FROM `{table_name}`
                            ORDER BY created_date DESC
                            LIMIT :limit OFFSET :offset
                        """)
                        direct_result = db.session.execute(
                            direct_sql,
                            {'limit': limit, 'offset': offset}
                        ).fetchall()
                        if direct_result:
                            working_table_name = table_name
                            current_app.logger.info(
                                f"Найдено {len(direct_result)} записей через SQL из таблицы '{table_name}'"
                            )
                            break
                    except Exception as sql_error:
                        current_app.logger.warning(
                            f"Ошибка при запросе к таблице '{table_name}': {sql_error}"
                        )
                        direct_result = None
                        continue
                if direct_result and working_table_name:
                    problem_ids = [row[0] for row in direct_result]
                    old_name = Problem.__table__.name
                    try:
                        Problem.__table__.name = working_table_name
                        problems = Problem.query.options(
                            joinedload(Problem.hashtags),
                            joinedload(Problem.solutions),
                            joinedload(Problem.linked_problems),
                            joinedload(Problem.favourite_users)
                        ).filter(Problem.id.in_(problem_ids)).all()
                        id_order = {pid: i for i, pid in enumerate(problem_ids)}
                        problems = sorted(problems, key=lambda p: id_order.get(p.id, 999))
                    finally:
                        Problem.__table__.name = old_name
            except Exception as fallback_error:
                current_app.logger.error(f"Ошибка при прямом SQL запросе: {fallback_error}")
        
        # Формируем ответ в формате, ожидаемом фронтендом
        problems_list = []

        # Предзагрузка данных для избежания N+1 queries
        # Загружаем user один раз (вместо загрузки в каждой итерации цикла)
        current_user = None
        user_favourite_problem_ids = set()
        if user_id:
            current_user = User.query.options(joinedload(User.favourite_problems)).get(user_id)
            if current_user:
                user_favourite_problem_ids = {p.id for p in current_user.favourite_problems}

        # Предзагружаем все темы одним запросом (вместо N запросов)
        topic_ids = {p.topic for p in problems if p.topic}
        # Темы для связанных проблем (linked_problems)
        for p in problems:
            if getattr(p, 'linked_problems', None):
                for lp in p.linked_problems:
                    if lp.topic:
                        topic_ids.add(lp.topic)
        topics_dict = {}
        if topic_ids:
            topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()
            topics_dict = {t.id: {'ID': t.id, 'Name': t.name} for t in topics}

        base_url = request.url_root.rstrip('/')
        def _abs_image_url(raw):
            if not raw:
                return f'{base_url}/assets/images/Screenshot_4-ww78noDj9-transformed.png'
            from urllib.parse import quote
            from logic.utils.file_utils import _is_yandex_storage_url
            if raw.startswith('http') and _is_yandex_storage_url(raw):
                return f'{base_url}/api/storage-image?url={quote(raw)}'
            if raw.startswith('http'):
                return raw
            if raw.startswith('/'):
                return f'{base_url}{raw}'
            if raw.startswith('../'):
                return f'{base_url}/{raw.lstrip("./")}'  # ../images/ -> /images/
            return f'{base_url}/{raw}'

        for problem in problems:
            # Получаем количество избранных для этой проблемы
            favourite_count = 0
            try:
                if hasattr(problem, 'favourite_users'):
                    favourite_count = len(problem.favourite_users)
            except Exception as fav_error:
                # Если таблица favourite_problem не существует, используем значение из поля favourite
                logger.warning(f"Ошибка при получении избранных пользователей: {fav_error}")
                favourite_count = problem.favourite or 0

            # Проверяем, добавлено ли в избранное текущим пользователем (O(1) вместо N+1)
            is_favourite = problem.id in user_favourite_problem_ids

            # Отмечаем, является ли проблема рекомендованной
            is_recommended = problem.id in recommended_ids if recommended_ids else False

            # Получаем информацию о теме из предзагруженного словаря (O(1) вместо N+1)
            topic_info = topics_dict.get(problem.topic)
            
            problem_data = {
                'ID': problem.id,
                'Name': problem.name,
                'Describe': problem.describe or '',
                'Image': _abs_image_url(normalize_image_url(problem.image) or '../images/default.png'),
                'Favourite': favourite_count,
                'IsFavourite': is_favourite,
                'IsRecommended': is_recommended,
                'Show': problem.show or 0,
                'Reply': problem.reply or 0,
                'Category': problem.category,
                'Creator': problem.creator,
                'CreatedDate': problem.created_date.isoformat() if problem.created_date else None,
                'ModifiedDate': problem.modified_date.isoformat() if problem.modified_date else None,
                'IsNew': problem.isnew,
                'FromAuthor': problem.fromauthor,
                'Topic': problem.topic,
                'TopicInfo': topic_info,
                'Hashtags': [],
                'Solutions': [],
                'LinkedProblems': []
            }
            
            # Добавляем хэштеги
            if hasattr(problem, 'hashtags') and problem.hashtags:
                problem_data['Hashtags'] = [{
                    'ID': hashtag.id,
                    'Name': hashtag.name
                } for hashtag in problem.hashtags]
            
            # Добавляем решения
            if hasattr(problem, 'solutions') and problem.solutions:
                problem_data['Solutions'] = [{
                    'ID': solution.id,
                    'Name': solution.name,
                    'Describe': (solution.describe[:100] + '...') if (solution.describe and len(solution.describe) > 100) else (solution.describe or ''),
                    'Image': _abs_image_url(normalize_image_url(solution.image) or '../images/default.png')
                } for solution in problem.solutions]
            
            # Добавляем связанные проблемы
            if hasattr(problem, 'linked_problems') and problem.linked_problems:
                linked_problems_list = []
                for linked_problem in problem.linked_problems:
                    linked_problem_data = {
                        'ID': linked_problem.id,
                        'Name': linked_problem.name,
                        'Image': _abs_image_url(normalize_image_url(linked_problem.image) or '../images/default.png')
                    }
                    if linked_problem.topic:
                        linked_problem_data['TopicInfo'] = topics_dict.get(linked_problem.topic)
                    linked_problems_list.append(linked_problem_data)
                problem_data['LinkedProblems'] = linked_problems_list
            
            problems_list.append(problem_data)
        
        has_filters = bool(search or category_param or hashtags_param or topic_param)
        if len(problems_list) == 0 and has_filters:
            return jsonify({
                "problems": problems_list,
                "suggest_ai": True,
                "ai_plan_price_rub": 999,
            }), 200
        if has_filters:
            return jsonify({"problems": problems_list}), 200
        return jsonify(problems_list), 200
        
    except Exception as e:
        logger.exception(f"Ошибка получения списка проблем: {str(e)}")
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
    
@problem_bp.route('/problems/<int:problem_id>', methods=['GET'])
def get_problem_by_id(problem_id):
    """Получение проблемы по ID с связанными хэштегами и решениями"""
    try:
        # Получаем основную информацию о проблеме с eager loading связей
        # Используем joinedload для избежания N+1 queries
        problem = Problem.query.options(
            joinedload(Problem.hashtags),
            joinedload(Problem.solutions).joinedload(Solution.comments),
            joinedload(Problem.solutions).joinedload(Solution.problems).joinedload(Problem.hashtags),
            joinedload(Problem.linked_problems),
            joinedload(Problem.favourite_users)
        ).get(problem_id)
        
        if not problem:
            return jsonify({'error': 'Проблема не найдена'}), 404

        # Увеличиваем счетчик просмотров
        if problem.show is None:
            problem.show = 1
        else:
            problem.show += 1
        db.session.commit()
        db.session.refresh(problem)  # актуальные данные из БД (в т.ч. image после только что созданной проблемы)

        base_url = request.url_root.rstrip('/')

        # Отслеживаем просмотр проблемы
        try:
            from logic.middleware import get_user_id_from_token
            user_id = get_user_id_from_token()
            if user_id:
                track_user_activity(user_id, 'view', 'problem', problem_id)
        except Exception as e:
            current_app.logger.debug(f"Не удалось отследить просмотр проблемы: {e}")  # Не критично
        
        # Получаем хэштеги
        hashtags = []
        if hasattr(problem, 'hashtags') and problem.hashtags:
            hashtags = [{
                'ID': hashtag.id,
                'Name': hashtag.name
            } for hashtag in problem.hashtags]
        
        # Получаем решения с комментариями
        solutions = []
        
        # Получаем решения через relationship (уже загружены с joinedload)
        if hasattr(problem, 'solutions'):
            for solution in problem.solutions:
                
                # Формируем данные о решении
                solution_data = {
                    'ID': solution.id,
                    'Name': solution.name,
                    'Describe': solution.describe[:100] + '...' if solution.describe and len(solution.describe) > 100 else solution.describe or '',
                    'Image': image_url_for_display(solution.image, base_url, '/assets/images/default.png'),
                    'Favourite': solution.favourite or 0,
                    'Rating': solution.rating or 0,
                    'Show': solution.show or 0,
                    'Reply': solution.reply or 0,
                    'Creator': solution.creator,
                    'CreatedDate': solution.created_date.isoformat() if solution.created_date else '',
                    'ModifiedDate': solution.modified_date.isoformat() if solution.modified_date else '',
                    'Price': float(solution.price) if solution.price else 0,
                    'Efficiency': solution.efficiency or 0,
                    'Complexity': solution.complexity or 0,
                    'Time': solution.time or 0,
                    'IsBought': solution.isbought,
                    'IsRating': solution.israting,
                    'Comments': []
                }
                
                # Добавляем комментарии
                if hasattr(solution, 'comments') and solution.comments:
                    for comment in solution.comments:
                        comment_data = {
                            'ID': comment.id,
                            'Text': comment.text,
                            'CreatedDate': comment.created_date.isoformat() if comment.created_date else '',
                            'Creator': comment.creator,
                            'LikeCount': comment.likecount,
                            'NotLikeCount': comment.notlikecount,
                            'IsNew': comment.isnew
                        }
                        solution_data['Comments'].append(comment_data)
                
                # Добавляем количество связанных решений
                linked_solutions_count = 0
                try:
                    if hasattr(solution, 'linked_solutions') and solution.linked_solutions:
                        linked_solutions_count = len(solution.linked_solutions)
                except (AttributeError, TypeError) as e:
                    current_app.logger.debug(f"Не удалось получить количество связанных решений: {e}")
                solution_data['LinkedSolutionsCount'] = linked_solutions_count
                
                # Добавляем связанные проблемы с хэштегами для отображения тегов
                problems_data = []
                if hasattr(solution, 'problems') and solution.problems:
                    for prob in solution.problems:
                        problem_dict = {
                            'ID': prob.id,
                            'Name': prob.name,
                            'Hashtags': []
                        }
                        # Получаем хэштеги проблемы
                        if hasattr(prob, 'hashtags') and prob.hashtags:
                            problem_dict['Hashtags'] = [
                                {
                                    'ID': hashtag.id,
                                    'Name': hashtag.name
                                }
                                for hashtag in prob.hashtags
                            ]
                        # Получаем информацию о теме проблемы
                        if prob.topic:
                            topic = Topic.query.get(prob.topic)
                            if topic:
                                problem_dict['TopicInfo'] = {
                                    'ID': topic.id,
                                    'Name': topic.name
                                }
                        problems_data.append(problem_dict)
                solution_data['Problems'] = problems_data
                
                solutions.append(solution_data)
        else:
            # Запасной вариант: прямой SQL запрос
            from sqlalchemy import text
            
            sql = text("""
                SELECT s.id, s.name, s.describe, s.image, 
                       s.favourite, s.rating,
                       s.show, s.reply, s.creator, s.created_date, s.modified_date,
                       s.price, s.efficiency, s.complexity, s.time, s.isbought, s.israting
                FROM solution s
                JOIN solution_problems sp ON s.id = sp.solution_id
                WHERE sp.problem_id = :problem_id
                ORDER BY s.created_date DESC
            """)
            
            result = db.session.execute(sql, {'problem_id': problem_id}).fetchall()
            
            for row in result:
                solution_data = {
                    'ID': row[0],
                    'Name': row[1],
                    'Describe': row[2][:100] + '...' if row[2] and len(row[2]) > 100 else row[2] or '',
                    'Image': image_url_for_display(row[3], base_url, '/assets/images/default.png'),
                    'Favourite': row[4] or 0,
                    'Rating': row[5] or 0,
                    'Show': row[6] or 0,
                    'Reply': row[7] or 0,
                    'Creator': row[8],
                    'CreatedDate': row[9].isoformat() if row[9] else '',
                    'ModifiedDate': row[10].isoformat() if row[10] else '',
                    'Price': float(row[11]) if row[11] else 0,
                    'Efficiency': row[12] or 0,
                    'Complexity': row[13] or 0,
                    'Time': row[14] or 0,
                    'IsBought': bool(row[15]),
                    'IsRating': bool(row[16]),
                    'Comments': []
                }
                
                # Получаем комментарии для этого решения
                try:
                    # Пробуем разные варианты имени таблицы
                    comment_table_name = None
                    for table_name in ['CommentSolution', 'comment_solution']:
                        try:
                            test_sql = text(f"SELECT 1 FROM `{table_name}` LIMIT 1")
                            db.session.execute(test_sql)
                            comment_table_name = table_name
                            break
                        except Exception as e:
                            current_app.logger.debug(f"Таблица {table_name} не найдена: {e}")
                            continue
                    
                    if comment_table_name:
                        comments_sql = text(f"""
                            SELECT id, text, created_date, creator,
                                   likecount, notlikecount, isnew
                            FROM `{comment_table_name}`
                            WHERE solution_id = :solution_id
                            ORDER BY created_date DESC
                        """)

                        comments_result = db.session.execute(
                            comments_sql,
                            {'solution_id': row[0]}
                        ).fetchall()
                    else:
                        # Если таблица не найдена, используем пустой список
                        comments_result = []
                        current_app.logger.warning(f"Таблица комментариев не найдена для решения {row[0]}")
                except Exception as comment_error:
                    logger.warning(f"Ошибка при получении комментариев: {comment_error}")
                    comments_result = []
                
                for comment_row in comments_result:
                    comment_data = {
                        'ID': comment_row[0],
                        'Text': comment_row[1],
                        'CreatedDate': comment_row[2].isoformat() if comment_row[2] else '',
                        'Creator': comment_row[3],
                        'LikeCount': comment_row[4],
                        'NotLikeCount': comment_row[5],
                        'IsNew': bool(comment_row[6])
                    }
                    solution_data['Comments'].append(comment_data)
                
                # Добавляем количество связанных решений
                linked_solutions_count = 0
                try:
                    solution_obj = Solution.query.get(row[0])
                    if solution_obj and hasattr(solution_obj, 'linked_solutions') and solution_obj.linked_solutions:
                        linked_solutions_count = len(solution_obj.linked_solutions)
                except (AttributeError, TypeError) as e:
                    current_app.logger.debug(f"Не удалось получить связанные решения: {e}")
                solution_data['LinkedSolutionsCount'] = linked_solutions_count

                # Добавляем связанные проблемы с хэштегами для отображения тегов
                problems_data = []
                try:
                    solution_obj = Solution.query.get(row[0])
                    if solution_obj and hasattr(solution_obj, 'problems') and solution_obj.problems:
                        for prob in solution_obj.problems:
                            problem_dict = {
                                'ID': prob.id,
                                'Name': prob.name,
                                'Hashtags': []
                            }
                            # Получаем хэштеги проблемы
                            if hasattr(prob, 'hashtags') and prob.hashtags:
                                problem_dict['Hashtags'] = [
                                    {
                                        'ID': hashtag.id,
                                        'Name': hashtag.name
                                    }
                                    for hashtag in prob.hashtags
                                ]
                            # Получаем информацию о теме проблемы
                            if prob.topic:
                                topic = Topic.query.get(prob.topic)
                                if topic:
                                    problem_dict['TopicInfo'] = {
                                        'ID': topic.id,
                                        'Name': topic.name
                                    }
                            problems_data.append(problem_dict)
                except (AttributeError, TypeError) as e:
                    current_app.logger.debug(f"Не удалось получить связанные проблемы: {e}")
                solution_data['Problems'] = problems_data
                
                solutions.append(solution_data)
        
        # Получаем связанные проблемы
        linked_problems = []
        linked_problems_count = 0
        if hasattr(problem, 'linked_problems') and problem.linked_problems:
            for linked_problem in problem.linked_problems:
                linked_problem_data = {
                    'ID': linked_problem.id,
                    'Name': linked_problem.name,
                    'Image': image_url_for_display(linked_problem.image, base_url, '/assets/images/default.png')
                }
                # Добавляем информацию о теме
                if linked_problem.topic:
                    topic = Topic.query.get(linked_problem.topic)
                    if topic:
                        linked_problem_data['TopicInfo'] = {
                            'ID': topic.id,
                            'Name': topic.name
                        }
                linked_problems.append(linked_problem_data)
            linked_problems_count = len(linked_problems)
        
        # Получаем информацию о теме
        topic_info = None
        if problem.topic:
            topic = Topic.query.get(problem.topic)
            if topic:
                topic_info = {
                    'ID': topic.id,
                    'Name': topic.name
                }
        
        # Проверяем, добавлено ли в избранное текущим пользователем
        is_favourite = False
        try:
            from logic.middleware import get_user_id_from_token
            user_id = get_user_id_from_token()
            if user_id:
                user = User.query.get(user_id)
                if user and problem in user.favourite_problems:
                    is_favourite = True
        except Exception as e:
            current_app.logger.debug(f"Не удалось проверить избранное: {e}")  # Если токена нет или ошибка, is_favourite останется False
        
        # Формируем ответ: URL картинки (через прокси для Yandex Storage при приватном бакете)
        problem_dict = {
            'ID': problem.id,
            'Name': problem.name,
            'Describe': problem.describe or '',
            'Image': image_url_for_display(problem.image, base_url, '/assets/images/default.png'),
            'Favourite': problem.favourite or 0,
            'IsFavourite': is_favourite,
            'Show': problem.show or 0,
            'Reply': problem.reply or 0,
            'Category': problem.category,
            'Creator': problem.creator,
            'CreatedDate': problem.created_date.isoformat() if problem.created_date else None,
            'ModifiedDate': problem.modified_date.isoformat() if problem.modified_date else None,
            'IsNew': problem.isnew,
            'FromAuthor': problem.fromauthor,
            'Topic': problem.topic,
            'TopicInfo': topic_info,
            'Hashtags': hashtags,
            'Solutions': solutions,
            'LinkedProblems': linked_problems,
            'LinkedProblemsCount': linked_problems_count
        }
        
        return jsonify(problem_dict), 200
        
    except Exception as e:
        logger.exception(f"Ошибка получения проблемы: {e}")
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
       
@problem_bp.route('/problems/favorites', methods=['GET'])
@token_required
def get_favourite_problems():
    """Получение избранных проблем пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Получаем параметры запроса
        search = request.args.get('search', '').strip()
        category_param = request.args.get('category', '')
        hashtags_param = request.args.get('hashtags', '')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Ограничиваем лимит
        if limit > 100:
            limit = 100
        
        # Получаем избранные проблемы пользователя через relationship
        # У пользователя уже есть favourite_problems через many-to-many
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Начинаем с проблем из избранного пользователя
        query = Problem.query.filter(
            Problem.id.in_([p.id for p in user.favourite_problems])
        )
        
        # Фильтр по поиску
        if search:
            search_lower = f"%{search.lower()}%"
            
            from sqlalchemy import func
            query = query.filter(
                db.or_(
                    func.lower(Problem.name).like(search_lower),
                    func.lower(Problem.describe).like(search_lower)
                )
            )
        
        # Фильтр по категории
        if category_param:
            try:
                category_id = int(category_param)
                query = query.filter(Problem.category == category_id)
            except ValueError:
                pass
        
        # Фильтр по хэштегам
        if hashtags_param:
            hashtag_ids = parse_int_list(hashtags_param)
            
            if hashtag_ids:
                # Используем подзапрос для фильтрации по хэштегам
                from sqlalchemy import exists
                from logic.model import hashtag_problem
                
                # Создаем подзапрос для проверки наличия всех указанных хэштегов
                for hashtag_id in hashtag_ids:
                    subquery = db.session.query(hashtag_problem).filter(
                        hashtag_problem.c.problem_id == Problem.id,
                        hashtag_problem.c.hashtag_id == hashtag_id
                    ).exists()
                    query = query.filter(subquery)
        
        # Применяем сортировку и пагинацию
        problems = query.order_by(Problem.created_date.desc()).offset(offset).limit(limit).all()
        
        # Формируем ответ в формате, ожидаемом фронтендом
        base_url = request.url_root.rstrip('/')
        problems_list = []
        for problem in problems:
            # Получаем хэштеги проблемы
            hashtags_list = []
            if hasattr(problem, 'hashtags') and problem.hashtags:
                hashtags_list = [{
                    'ID': hashtag.id,
                    'Name': hashtag.name
                } for hashtag in problem.hashtags]
            
            # Получаем количество решений
            solutions_count = 0
            if hasattr(problem, 'solutions'):
                solutions_count = len(problem.solutions)
            
            # Получаем количество связанных проблем
            linked_problems_count = 0
            if hasattr(problem, 'linked_problems'):
                linked_problems_count = len(problem.linked_problems)
            
            problem_data = {
                'ID': problem.id,
                'Name': problem.name,
                'Describe': problem.describe or '',
                'Image': image_url_for_display(problem.image, base_url, '/assets/images/default.png'),
                'Favourite': 1,  # Так как эта проблема в избранном
                'Show': problem.show or 0,
                'Reply': problem.reply or 0,
                'Category': problem.category,
                'Creator': problem.creator,
                'CreatedDate': problem.created_date.isoformat() if problem.created_date else None,
                'ModifiedDate': problem.modified_date.isoformat() if problem.modified_date else None,
                'IsNew': problem.isnew,
                'FromAuthor': problem.fromauthor,
                'Topic': problem.topic,
                'Hashtags': hashtags_list,
                'Solutions': solutions_count,  # Количество решений
                'LinkedProblems': linked_problems_count  # Количество связанных проблем
            }
            
            problems_list.append(problem_data)
        
        return jsonify(problems_list), 200
        
    except Exception as e:
        logger.exception(f"Ошибка получения избранных проблем: {e}")
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
    
@problem_bp.route('/problems', methods=['POST'])
@token_required
def create_problem():
    """Создание новой проблемы (совместимо с фронтендом)"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем multipart/form-data (фронтенд отправляет так)
        if not request.form:
            # Также поддерживаем JSON для других клиентов
            if request.is_json:
                data = request.get_json()
                return create_problem_from_json(user_id, data)
            return jsonify({'error': 'Неверный формат данных'}), 400
        
        # Получаем данные из формы (поддержка разных имён полей от фронта)
        name = capitalize_title(request.form.get('name', '').strip())
        describe = capitalize_first(request.form.get('describe', '').strip())
        category_str = request.form.get('category') or request.form.get('category_id', '')
        topic_str = request.form.get('topicID') or request.form.get('topic_id', '')
        hashtags_str = request.form.get('hashtagsIDs') or request.form.get('hashtags', '')
        
        # Валидация
        if not name:
            return jsonify({'error': 'Название проблемы обязательно'}), 400

        if Problem.query.filter(func.lower(Problem.name) == name.lower()).first():
            return jsonify({'error': 'Проблема с таким названием уже существует'}), 409
        
        if not category_str:
            return jsonify({'error': 'Категория обязательна'}), 400
        
        try:
            category_id = int(category_str)
        except ValueError:
            return jsonify({'error': 'Неверная категория'}), 400
        
        # Обработка topic (опционально)
        topic_id = None
        if topic_str:
            try:
                topic_id = int(topic_str)
            except ValueError:
                pass
        
        # Обработка хэштегов
        hashtag_ids = parse_int_list(hashtags_str) if hashtags_str else []
        
        # Обработка файла изображения (Yandex Storage). Генерация ИИ только если пользователь не прикладывал файл.
        image_path = None
        user_sent_image = bool(
            request.files.get('image') and (request.files['image'].filename or '').strip() != ''
        )
        if user_sent_image:
            file = request.files['image']
            if not allowed_file(file.filename):
                return jsonify({
                    'error': 'Недопустимый формат файла. Разрешены: PNG, JPG, JPEG, GIF, WEBP'
                }), 400
            try:
                image_path = save_file_to_yandex_storage(file, 'problems')
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            if not image_path:
                return jsonify({'error': 'Не удалось загрузить изображение. Попробуйте другой файл или позже.'}), 400

        # Создаём проблему сразу (генерация изображения только если пользователь НЕ загружал своё)
        problem = Problem(
            name=name,
            describe=describe,
            category=category_id,
            topic=topic_id,
            image=image_path or '../images/default.png',
            creator=user_id,
            isnew=True,
            show=1,
            favourite=0,
            fromauthor=False,
            reply=0
        )
        
        try:
            db.session.add(problem)
            db.session.commit()
            
            # Связываем хэштеги ПОСЛЕ сохранения проблемы
            if hashtag_ids:
                hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                if hashtags:
                    problem.hashtags.extend(hashtags)
                    db.session.commit()
            
            # Отслеживаем создание проблемы
            try:
                track_user_activity(user_id, 'create', 'problem', problem.id)
            except Exception as e:
                current_app.logger.debug(f"Не удалось отследить создание проблемы: {e}")
            
            # Эмбеддинг и автогенерация картинки только если пользователь не загружал своё изображение
            app = current_app._get_current_object()
            problem_id = problem.id
            need_bg_image = not image_path and not user_sent_image

            def _background_tasks():
                with app.app_context():
                    try:
                        create_embedding('problem', problem_id)
                    except Exception as e:
                        logger.warning(f"Ошибка создания вектора для проблемы {problem_id}: {e}")
                    if need_bg_image:
                        try:
                            bg_path = generate_image_with_openai(name, describe)
                            if bg_path:
                                p = Problem.query.get(problem_id)
                                if p:
                                    p.image = bg_path
                                    db.session.commit()
                                    logger.info(f"Авто-изображение для проблемы {problem_id}: {bg_path}")
                        except Exception as e:
                            logger.warning(f"Ошибка авто-генерации изображения для проблемы {problem_id}: {e}")

            threading.Thread(target=_background_tasks, daemon=True).start()
                    
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка сохранения проблемы: {e}")
            if image_path and image_path != '../images/default.png':
                try:
                    delete_image(image_path)
                except Exception as del_err:
                    logger.warning(f"Не удалось удалить изображение: {del_err}")
            return jsonify({'error': 'Ошибка сохранения проблемы'}), 500
        
        # Абсолютный URL картинки для фронта
        base_url = request.url_root.rstrip('/')
        raw_img = normalize_image_url(problem.image)
        if raw_img and raw_img.startswith('http'):
            img_url = raw_img
        elif raw_img:
            img_url = f'{base_url}{raw_img}' if raw_img.startswith('/') else f'{base_url}/{raw_img}'
        else:
            img_url = f'{base_url}/assets/images/Screenshot_4-ww78noDj9-transformed.png'
        # Возвращаем в формате, ожидаемом фронтендом
        return jsonify({
            'message': 'Проблема сохранена',
            'id': problem.id,
            'problem': {
                'ID': problem.id,
                'Name': problem.name,
                'Describe': problem.describe,
                'Image': img_url,
                'Category': {
                    'ID': problem.category
                }
            }
        }), 201
        
    except ValueError as e:
        logger.warning(f"Ошибка валидации при создании проблемы: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Ошибка создания проблемы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

def create_problem_from_json(user_id, data):
    """Создание проблемы из JSON (для API)"""
    try:
        name = capitalize_title((data.get('name') or data.get('Name', '')).strip())
        describe = capitalize_first((data.get('describe') or data.get('Describe', '')).strip())
        category_id = data.get('category_id') or data.get('CategoryID')
        topic_id = data.get('topic_id') or data.get('TopicID')
        
        if not name:
            return jsonify({'error': 'Название проблемы обязательно'}), 400

        if Problem.query.filter(func.lower(Problem.name) == name.lower()).first():
            return jsonify({'error': 'Проблема с таким названием уже существует'}), 409
        
        if not category_id:
            return jsonify({'error': 'Категория обязательна'}), 400
        
        # Если изображение не загружено, генерируем через OpenAI API
        image_path = None
        try:
            image_path = generate_image_with_openai(name, describe)
            if image_path:
                logger.info(f"Автоматически сгенерировано изображение для проблемы '{name}': {image_path}")
        except Exception as e:
            logger.warning(f"Ошибка автоматической генерации изображения: {e}")
            # Продолжаем без изображения
        
        # Создаём проблему
        problem = Problem(
            name=name,
            describe=describe,
            category=category_id,
            topic=topic_id,
            image=image_path or '../images/default.png',
            creator=user_id,
            isnew=True,
            show=1,
            favourite=0,
            fromauthor=False,
            reply=0
        )
        
        # Обработка хэштегов из JSON
        hashtag_ids = data.get('hashtag_ids') or data.get('HashtagIDs', [])
        if hashtag_ids:
            hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
            problem.hashtags.extend(hashtags)
        
        db.session.add(problem)
        db.session.commit()
        
        return jsonify({
            'message': 'Проблема успешно создана',
            'id': problem.id,
            'problem': {
                'ID': problem.id,
                'Name': problem.name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка создания проблемы из JSON: {e}")
        return jsonify({'error': 'Ошибка создания проблемы'}), 500

@problem_bp.route('/problems/count-new', methods=['GET'])
@token_required
def count_problem():
    """Подсчет новых проблем"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401

        count = ProblemService.count_new_problems(user_id)
        return jsonify({'count': count}), 200

    except DatabaseError as e:
        logger.error(f"Ошибка подсчета проблем: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f"Ошибка подсчета проблем: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['PUT'])
@token_required
def update_problem(problem_id):
    """Обновление проблемы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли проблема и принадлежит ли пользователю
        problem = Problem.query.get(problem_id)
        if not problem:
            return jsonify({'error': 'Проблема не найдена'}), 404
        
        if problem.creator != user_id:
            return jsonify({'error': 'Нет прав на обновление'}), 403
        
        # Получаем данные из формы
        name = capitalize_title(request.form.get('name', problem.name).strip())
        describe = capitalize_first(request.form.get('describe', problem.describe).strip())
        category_str = request.form.get('category', str(problem.category))
        is_new_str = request.form.get('isNew', '')
        from_author_str = request.form.get('fromAuthor', '')
        topic_str = request.form.get('topic', '')
        
        # Валидация
        if not name:
            return jsonify({'error': 'Название проблемы обязательно'}), 400
        
        try:
            category_id = int(category_str)
        except ValueError:
            return jsonify({'error': 'Неверная категория'}), 400
        
        # Обработка boolean значений
        is_new = parse_bool(is_new_str) if is_new_str else problem.isnew
        from_author = parse_bool(from_author_str) if from_author_str else problem.fromauthor
        
        # Обработка topic
        topic_id = None
        if topic_str:
            try:
                topic_id = int(topic_str)
            except ValueError:
                pass
        
        # Обработка файла изображения (Yandex Storage)
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                if problem.image:
                    delete_image(problem.image)
                problem.image = save_file_to_yandex_storage(file, 'problems')
        
        # Обновляем проблему
        problem.name = name
        problem.describe = describe
        problem.category = category_id
        problem.isnew = is_new
        problem.fromauthor = from_author
        problem.topic = topic_id
        problem.modified_date = datetime.utcnow()
        
        # Обработка хэштегов — только если поле явно передано в форме
        if 'hashtagsIDs' in request.form or 'hashtags' in request.form:
            hashtags_str = request.form.get('hashtagsIDs') or request.form.get('hashtags', '')
            problem.hashtags.clear()
            if hashtags_str:
                hashtag_ids = parse_int_list(hashtags_str)
                if hashtag_ids:
                    hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                    problem.hashtags.extend(hashtags)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка обновления проблемы: {e}")
            return jsonify({'error': 'Ошибка обновления проблемы'}), 500

        return jsonify({
            'message': 'Проблема обновлена',
            'problem': problem.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Ошибка обновления проблемы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/<int:problem_id>', methods=['DELETE'])
@token_required
def delete_problem(problem_id):
    """Удаление проблемы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401

        ProblemService.delete_problem(problem_id, user_id)
        return jsonify({'message': 'Проблема удалена'}), 200

    except ResourceNotFoundError:
        return jsonify({'error': 'Проблема не найдена'}), 404
    except AuthorizationError:
        return jsonify({'error': 'Нет прав на удаление'}), 403
    except DatabaseError as e:
        logger.error(f"Ошибка удаления проблемы: {e}")
        return jsonify({'error': 'Ошибка удаления проблемы'}), 500
    except Exception as e:
        logger.error(f"Ошибка удаления проблемы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Дополнительные обработчики

@problem_bp.route('/problems/<int:problem_id>/toggle-favourite', methods=['POST'])
@token_required
def toggle_favourite(problem_id):
    """Добавление/удаление проблемы в избранное"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401

        result = ProblemService.toggle_favourite(problem_id, user_id)
        return jsonify({'message': 'Избранное обновлено', **result}), 200

    except ResourceNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except DatabaseError as e:
        logger.error(f"Ошибка БД: {e}")
        return jsonify({'error': 'Ошибка обновления избранного'}), 500
    except Exception as e:
        logger.exception(f"Ошибка обновления избранного: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/<int:problem_id>/toggle-show', methods=['POST'])
@token_required
def toggle_show(problem_id):
    """Переключение видимости проблемы"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401

        result = ProblemService.toggle_show(problem_id, user_id)
        return jsonify({'message': 'Видимость обновлена', **result}), 200

    except ResourceNotFoundError:
        return jsonify({'error': 'Проблема не найдена'}), 404
    except AuthorizationError:
        return jsonify({'error': 'Нет прав для этой операции'}), 403
    except DatabaseError as e:
        logger.error(f"Ошибка БД: {e}")
        return jsonify({'error': 'Ошибка обновления видимости'}), 500
    except Exception as e:
        logger.exception(f"Ошибка обновления видимости: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/<int:problem_id>/mark-as-read', methods=['POST'])
@token_required
def mark_problem_as_read(problem_id):
    """Отметить проблему как прочитанную"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401

        result = ProblemService.mark_as_read(problem_id, user_id)
        return jsonify({'message': 'Проблема отмечена как прочитанная', **result}), 200

    except ResourceNotFoundError:
        return jsonify({'error': 'Проблема не найдена'}), 404
    except AuthorizationError:
        return jsonify({'error': 'Нет прав для этой операции'}), 403
    except DatabaseError as e:
        logger.error(f"Ошибка БД: {e}")
        return jsonify({'error': 'Ошибка обновления проблемы'}), 500
    except Exception as e:
        logger.exception(f"Ошибка обновления проблемы: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/user/<int:user_id>', methods=['GET'])
def get_user_problems(user_id):
    """Получение проблем конкретного пользователя"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

        result = ProblemService.get_user_problems(user_id, limit, offset)
        return jsonify(result), 200

    except ResourceNotFoundError:
        return jsonify({'error': 'Пользователь не найден'}), 404
    except DatabaseError as e:
        logger.error(f"Ошибка получения проблем пользователя: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500
    except Exception as e:
        logger.error(f"Ошибка получения проблем пользователя: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@problem_bp.route('/problems/<int:problem_id>/link', methods=['POST'])
@token_required
def link_problem(problem_id):
    """Добавление связи между проблемами"""
    try:
        from logic.model import problem_link_problem
        from sqlalchemy import select, and_
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Требуется авторизация'}), 401
        
        data = request.get_json()
        linked_problem_id = data.get('linked_problem_id') or data.get('problem_link_id')
        
        if not linked_problem_id:
            return jsonify({'error': 'Не указан ID связанной проблемы'}), 400
        
        if problem_id == linked_problem_id:
            return jsonify({'error': 'Нельзя связать проблему с самой собой'}), 400
        
        # Проверяем, что обе проблемы существуют
        problem = Problem.query.get(problem_id)
        linked_problem = Problem.query.get(linked_problem_id)
        
        if not problem:
            return jsonify({'error': 'Проблема не найдена'}), 404
        
        if not linked_problem:
            return jsonify({'error': 'Связанная проблема не найдена'}), 404
        
        # Проверяем, не существует ли уже такая связь
        existing_link = db.session.execute(
            select(problem_link_problem).where(
                and_(
                    problem_link_problem.c.problem_id == problem_id,
                    problem_link_problem.c.problem_link_id == linked_problem_id
                )
            )
        ).first()
        
        if existing_link:
            return jsonify({'error': 'Связь уже существует'}), 400
        
        # Добавляем связь
        db.session.execute(
            problem_link_problem.insert().values(
                problem_id=problem_id,
                problem_link_id=linked_problem_id
            )
        )
        db.session.commit()
        
        return jsonify({
            'message': 'Связь успешно добавлена',
            'problem_id': problem_id,
            'linked_problem_id': linked_problem_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка добавления связи между проблемами: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@problem_bp.route('/problems/<int:problem_id>/add-solution', methods=['POST'])
@token_required
def add_solution_to_problem(problem_id):
    """Добавление существующего решения к проблеме"""
    try:
        from logic.model import solution_problems
        from sqlalchemy import select, and_
        
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'Требуется авторизация'}), 401
        
        data = request.get_json()
        solution_id = data.get('solution_id')
        
        if not solution_id:
            return jsonify({'error': 'Не указан ID решения'}), 400
        
        # Проверяем, что проблема и решение существуют
        problem = Problem.query.get(problem_id)
        solution = Solution.query.get(solution_id)
        
        if not problem:
            return jsonify({'error': 'Проблема не найдена'}), 404
        
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Проверяем, не существует ли уже такая связь
        existing_link = db.session.execute(
            select(solution_problems).where(
                and_(
                    solution_problems.c.problem_id == problem_id,
                    solution_problems.c.solution_id == solution_id
                )
            )
        ).first()
        
        if existing_link:
            return jsonify({'error': 'Решение уже связано с этой проблемой'}), 400
        
        # Добавляем связь
        db.session.execute(
            solution_problems.insert().values(
                problem_id=problem_id,
                solution_id=solution_id
            )
        )
        db.session.commit()
        
        return jsonify({
            'message': 'Решение успешно добавлено к проблеме',
            'problem_id': problem_id,
            'solution_id': solution_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Ошибка добавления решения к проблеме: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500