from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
import os
from logic.model import Hashtag, Problem, Solution, User, SolutionRating, Topic, solution_problems, hashtag_problem, favourite_solution, solution_link_solution
from logic.middleware import token_required
from sqlalchemy import or_, func, and_

from logic.model import db
from logic.utils.file_utils import allowed_file, save_file, delete_file
from logic.utils.validators import parse_int_list, parse_bool
from logic.utils.image_search import generate_image_with_openai
from logic.recommendations import track_user_activity, get_user_recommendations, create_embedding

solution_bp = Blueprint('solution', __name__, url_prefix='/api')

@solution_bp.route('/solutions/<int:solution_id>', methods=['GET'])
def get_solution_by_id(solution_id):
    """Получение решения по ID через путь"""
    try:
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Увеличиваем счетчик просмотров
        solution.show = (solution.show or 0) + 1
        db.session.commit()
        
        # Отслеживаем просмотр решения
        try:
            from logic.middleware import get_user_id_from_token
            user_id = get_user_id_from_token()
            if user_id:
                track_user_activity(user_id, 'view', 'solution', solution_id)
        except:
            pass  # Не критично, если не удалось отследить
        
        # Проверяем, добавлено ли в избранное текущим пользователем
        is_favourite = False
        try:
            from logic.middleware import get_user_id_from_token
            user_id = get_user_id_from_token()
            if user_id:
                from logic.model import User
                user = User.query.get(user_id)
                if user and solution in user.favourite_solutions:
                    is_favourite = True
        except:
            pass  # Если токена нет или ошибка, is_favourite останется False
        
        # Формат, ожидаемый фронтендом из solution.js
        solution_data = {
            'ID': solution.id,
            'Name': solution.name,
            'Describe': solution.describe or '',
            'Image': solution.image or '../images/default.png',
            'Show': solution.show or 0,
            'Favourite': solution.favourite or 0,
            'IsFavourite': is_favourite,
            'Reply': solution.reply or 0,
            'Price': float(solution.price) if solution.price else 0,
            'Efficiency': solution.efficiency or 0,
            'Complexity': solution.complexity or 0,
            'Time': solution.time or 0,
            'Rating': solution.rating or 0,
            'Comments': []
        }
        
        # Добавляем комментарии, если они есть
        if hasattr(solution, 'comments') and solution.comments:
            solution_data['Comments'] = [
                {
                    'ID': comment.id,
                    'Text': comment.text,
                    'CreatedDate': comment.created_date.isoformat() if comment.created_date else '',
                    'Creator': {
                        'User': comment.creator_user.username if comment.creator_user else 'Аноним'
                    },
                    'LikeCount': comment.likecount or 0,
                    'NotLikeCount': comment.notlikecount or 0
                }
                for comment in solution.comments
            ]
        
        # Добавляем связанные решения (похожие решения) с полными данными
        linked_solutions = []
        try:
            # Используем passive='raise' чтобы предотвратить ленивую загрузку, если таблица не существует
            from sqlalchemy.orm import object_session
            from sqlalchemy import inspect as sql_inspect
            session = object_session(solution)
            if session and hasattr(solution, 'linked_solutions'):
                insp = sql_inspect(solution)
                if 'linked_solutions' in insp.attrs:
                    # Пытаемся получить значение без ленивой загрузки
                    try:
                        # Используем getattr с обработкой ошибки
                        linked_solutions_list = getattr(solution, 'linked_solutions', None)
                        if linked_solutions_list:
                            # Получаем user_id из токена, если он есть (опционально)
                            user_id = None
                            try:
                                from logic.middleware import get_user_id_from_token
                                user_id = get_user_id_from_token()
                            except:
                                pass  # Если токена нет, user_id останется None
                            
                            for linked_solution in linked_solutions_list:
                                # Получаем комментарии
                                comments = []
                                if hasattr(linked_solution, 'comments') and linked_solution.comments:
                                    comments = [
                                        {
                                            'ID': comment.id,
                                            'Text': comment.text,
                                            'CreatedDate': comment.created_date.isoformat() if comment.created_date else '',
                                            'Creator': comment.creator_user.username if comment.creator_user else 'Неизвестно',
                                            'LikeCount': comment.likecount or 0,
                                            'NotLikeCount': comment.notlikecount or 0
                                        }
                                        for comment in linked_solution.comments[:10]
                                    ]
                                
                                # Получаем связанные проблемы
                                problems_data = []
                                if hasattr(linked_solution, 'problems') and linked_solution.problems:
                                    for problem in linked_solution.problems[:5]:
                                        problem_dict = {
                                            'ID': problem.id,
                                            'Name': problem.name,
                                            'Hashtags': []
                                        }
                                        
                                        # Получаем хэштеги проблемы
                                        if hasattr(problem, 'hashtags') and problem.hashtags:
                                            problem_dict['Hashtags'] = [
                                                {
                                                    'ID': hashtag.id,
                                                    'Name': hashtag.name
                                                }
                                                for hashtag in problem.hashtags[:3]
                                            ]
                                        
                                        # Получаем информацию о теме проблемы
                                        if problem.topic:
                                            from logic.model import Topic
                                            topic = Topic.query.get(problem.topic)
                                            if topic:
                                                problem_dict['TopicInfo'] = {
                                                    'ID': topic.id,
                                                    'Name': topic.name
                                                }
                                        
                                        problems_data.append(problem_dict)
                                
                                # Проверяем, добавлено ли в избранное текущим пользователем
                                is_favourite = False
                                if user_id:
                                    from logic.model import User
                                    user = User.query.get(user_id)
                                    if user and linked_solution in user.favourite_solutions:
                                        is_favourite = True
                                
                                linked_solution_data = {
                                    'ID': linked_solution.id,
                                    'Name': linked_solution.name,
                                    'Image': linked_solution.image or '../images/default.png',
                                    'Describe': linked_solution.describe or '',
                                    'Favourite': linked_solution.favourite or 0,
                                    'IsFavourite': is_favourite,
                                    'Show': linked_solution.show or 0,
                                    'Reply': linked_solution.reply or 0,
                                    'Rating': linked_solution.rating or 0,
                                    'CommentSolutions': comments,
                                    'Comments': comments,
                                    'Problems': problems_data
                                }
                                linked_solutions.append(linked_solution_data)
                    except Exception as load_error:
                        # Если таблица не существует, просто пропускаем связанные решения
                        error_msg = str(load_error)
                        if 'doesn\'t exist' in error_msg or 'Table' in error_msg:
                            print(f"Таблица solution_link_solution не существует, пропускаем связанные решения")
                        else:
                            print(f"Ошибка загрузки связанных решений: {load_error}")
                        linked_solutions = []
        except Exception as e:
            # Если таблица solution_link_solution не существует, просто пропускаем связанные решения
            error_msg = str(e)
            if 'doesn\'t exist' in error_msg or 'Table' in error_msg:
                print(f"Таблица solution_link_solution не существует, пропускаем связанные решения")
            else:
                print(f"Ошибка загрузки связанных решений: {e}")
            linked_solutions = []
        solution_data['LinkedSolutions'] = linked_solutions
        
        return jsonify(solution_data), 200
        
    except Exception as e:
        print(f"Ошибка получения решения: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
    
@solution_bp.route('/solutions', methods=['GET'])
def get_solutions():
    """Получение списка решений с фильтрацией"""
    try:
        # Получаем параметры запроса
        search = request.args.get('search', '').strip()
        category_param = request.args.get('category', '')
        hashtags_param = request.args.get('hashtags', '')
        exclude_param = request.args.get('exclude', '')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        print(f"Параметры запроса solutions: search={search}, category={category_param}, hashtags={hashtags_param}, exclude={exclude_param}, limit={limit}, offset={offset}")
        
        # Ограничиваем лимит
        if limit > 100:
            limit = 100
        
        # Начинаем формировать запрос
        query = Solution.query
        
        # Фильтр по поиску
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Solution.name).like(search_lower),
                    func.lower(Solution.describe).like(search_lower)
                )
            )
        
        # Фильтр по категории
        if category_param:
            try:
                category_id = int(category_param)
                # Получаем ID решений через связанные проблемы
                solution_ids = db.session.query(
                    solution_problems.c.solution_id
                ).join(
                    Problem, Problem.id == solution_problems.c.problem_id
                ).filter(
                    Problem.category == category_id
                ).distinct().all()
                
                if solution_ids:
                    solution_id_list = [row[0] for row in solution_ids]
                    query = query.filter(Solution.id.in_(solution_id_list))
                else:
                    # Если нет решений для этой категории, возвращаем пустой результат
                    query = query.filter(Solution.id == -1)  # Невозможное условие
            except (ValueError, Exception) as e:
                print(f"Ошибка преобразования категории: {e}")
                import traceback
                traceback.print_exc()
        
        # Фильтр по хэштегам
        if hashtags_param:
            hashtag_ids = parse_int_list(hashtags_param)
            
            print(f"Хэштеги для фильтрации решений: {hashtag_ids}")
            
            if hashtag_ids:
                try:
                    # Получаем проблемы с указанными хэштегами
                    problem_ids = db.session.query(
                        hashtag_problem.c.problem_id
                    ).filter(
                        hashtag_problem.c.hashtag_id.in_(hashtag_ids)
                    ).group_by(
                        hashtag_problem.c.problem_id
                    ).having(
                        func.count(hashtag_problem.c.hashtag_id.distinct()) == len(hashtag_ids)
                    ).all()
                    
                    if problem_ids:
                        problem_id_list = [row[0] for row in problem_ids]
                        # Получаем решения через эти проблемы
                        solution_ids = db.session.query(
                            solution_problems.c.solution_id
                        ).filter(
                            solution_problems.c.problem_id.in_(problem_id_list)
                        ).distinct().all()
                        
                        if solution_ids:
                            solution_id_list = [row[0] for row in solution_ids]
                            query = query.filter(Solution.id.in_(solution_id_list))
                        else:
                            # Если нет решений для этих проблем, возвращаем пустой результат
                            query = query.filter(Solution.id == -1)  # Невозможное условие
                    else:
                        # Если нет проблем с этими хэштегами, возвращаем пустой результат
                        query = query.filter(Solution.id == -1)  # Невозможное условие
                except Exception as e:
                    print(f"Ошибка фильтрации по хэштегам: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Фильтр исключения решения (для поиска похожих решений)
        if exclude_param:
            try:
                exclude_id = int(exclude_param)
                query = query.filter(Solution.id != exclude_id)
            except ValueError:
                pass
        
        # Сортировка и пагинация
        solutions = query.order_by(Solution.created_date.desc()).offset(offset).limit(limit).all()
        
        print(f"Найдено решений: {len(solutions)}")
        
        # Получаем user_id из токена, если он есть (опционально)
        user_id = None
        try:
            from logic.middleware import get_user_id_from_token
            user_id = get_user_id_from_token()
        except:
            pass  # Если токена нет, user_id останется None
        
        # Отслеживаем поиск, если есть поисковый запрос
        if user_id and search:
            try:
                track_user_activity(user_id, 'search', 'solution', None, search)
            except:
                pass
        
        # Получаем рекомендации для пользователя (если авторизован)
        recommended_ids = set()
        if user_id:
            try:
                recommended_list = get_user_recommendations(user_id, 'solution', limit=20)
                recommended_ids = set(recommended_list)
            except Exception as e:
                print(f"⚠️ Ошибка получения рекомендаций: {e}")
        
        # Формируем ответ в формате, ожидаемом фронтендом
        solutions_list = []
        for solution in solutions:
            # Получаем комментарии
            comments = []
            if hasattr(solution, 'comments') and solution.comments:
                comments = [
                    {
                        'ID': comment.id,
                        'Text': comment.text,
                        'CreatedDate': comment.created_date.isoformat() if comment.created_date else '',
                        'Creator': comment.creator_user.username if comment.creator_user else 'Неизвестно',
                        'LikeCount': comment.likecount or 0,
                        'NotLikeCount': comment.notlikecount or 0
                    }
                    for comment in solution.comments[:10]  # Ограничиваем количество
                ]
            
            # Получаем связанные проблемы
            problems_data = []
            if hasattr(solution, 'problems') and solution.problems:
                for problem in solution.problems[:5]:  # Ограничиваем количество
                    problem_dict = {
                        'ID': problem.id,
                        'Name': problem.name,
                        'Hashtags': []
                    }
                    
                    # Получаем хэштеги проблемы
                    if hasattr(problem, 'hashtags') and problem.hashtags:
                        problem_dict['Hashtags'] = [
                            {
                                'ID': hashtag.id,
                                'Name': hashtag.name
                            }
                            for hashtag in problem.hashtags[:3]  # Ограничиваем количество
                        ]
                    
                    # Получаем информацию о теме проблемы
                    if problem.topic:
                        topic = Topic.query.get(problem.topic)
                        if topic:
                            problem_dict['TopicInfo'] = {
                                'ID': topic.id,
                                'Name': topic.name
                            }
                    
                    problems_data.append(problem_dict)
            
            # Проверяем, добавлено ли в избранное текущим пользователем
            is_favourite = False
            if user_id:
                user = User.query.get(user_id)
                if user and solution in user.favourite_solutions:
                    is_favourite = True
            
            # Отмечаем, является ли решение рекомендованным
            is_recommended = solution.id in recommended_ids if recommended_ids else False
            
            # Получаем количество связанных решений
            linked_solutions_count = 0
            try:
                if hasattr(solution, 'linked_solutions') and solution.linked_solutions:
                    linked_solutions_count = len(solution.linked_solutions)
            except:
                pass  # Если таблица не существует, просто пропускаем
            
            solution_data = {
                'ID': solution.id,
                'Name': solution.name,
                'Describe': solution.describe or '',
                'Image': solution.image or '../images/default.png',
                'Favourite': solution.favourite or 0,
                'IsFavourite': is_favourite,
                'IsRecommended': is_recommended,
                'Show': solution.show or 0,
                'Reply': solution.reply or 0,
                'Price': float(solution.price) if solution.price else 0,
                'Efficiency': solution.efficiency or 0,
                'Complexity': solution.complexity or 0,
                'Time': solution.time or 0,
                'Rating': solution.rating or 0,
                'IsBought': bool(solution.isbought),
                'IsRating': bool(solution.israting),
                'IsNew': bool(solution.isnew),
                'FromAuthor': bool(solution.fromauthor),
                'Creator': solution.creator,
                'CreatedDate': solution.created_date.isoformat() if solution.created_date else '',
                'ModifiedDate': solution.modified_date.isoformat() if solution.modified_date else '',
                'CommentSolutions': comments,  # Для совместимости с фронтендом
                'Comments': comments,  # Дублируем для разных названий
                'Problems': problems_data,  # Связанные проблемы
                'LinkedSolutionsCount': linked_solutions_count  # Количество связанных решений
            }
            
            solutions_list.append(solution_data)
        
        return jsonify(solutions_list), 200
        
    except Exception as e:
        print(f"Ошибка получения решений: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500
    
@solution_bp.route('/solutions/count-new', methods=['GET'])
@token_required
def count_solution():
    """Подсчет новых решений"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Подсчитываем новые решения пользователя
        count = Solution.query.filter_by(
            creator=user_id,
            isnew=True
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        print(f"Ошибка подсчета решений: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@solution_bp.route('/solutions', methods=['POST'])
@token_required
def create_solution():
    """Создание нового решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем multipart/form-data (фронтенд отправляет так)
        if not request.form:
            return jsonify({'error': 'Неверный формат данных'}), 400
        
        # Получаем данные из формы
        name = request.form.get('solution', '').strip() or request.form.get('name', '').strip()
        describe = request.form.get('details', '').strip() or request.form.get('describe', '').strip()
        related_problems_str = request.form.get('relatedProblems', '')
        can_buy = request.form.get('canBuy') == 'on'
        can_evaluate = request.form.get('canEvaluate') == 'on'
        
        # Валидация
        if not name:
            return jsonify({'error': 'Название решения обязательно'}), 400
        
        if not describe:
            return jsonify({'error': 'Описание решения обязательно'}), 400
        
        if not related_problems_str:
            return jsonify({'error': 'Необходимо выбрать хотя бы одну связанную проблему'}), 400
        
        # Обработка файла изображения
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '' and allowed_file(file.filename):
                image_path = save_file(file)
        
        # Если изображение не загружено, генерируем через OpenAI API
        if not image_path:
            try:
                image_path = generate_image_with_openai(name, describe)
                if image_path:
                    print(f"Автоматически сгенерировано изображение для решения '{name}': {image_path}")
            except Exception as e:
                print(f"Ошибка автоматической генерации изображения: {e}")
                # Продолжаем без изображения
        
        # Если всё ещё нет изображения, используем дефолтное
        if not image_path:
            image_path = '../images/default.png'
        
        # Парсим связанные проблемы
        problem_ids = parse_int_list(related_problems_str) if related_problems_str else []
        if not problem_ids:
            return jsonify({'error': 'Необходимо выбрать хотя бы одну связанную проблему'}), 400
        
        # Создаём решение
        solution = Solution(
            name=name,
            describe=describe,
            image=image_path,
            creator=user_id,
            isnew=True,
            show=1,
            favourite=0,
            fromauthor=False,
            reply=0,
            isbought=can_buy,
            israting=can_evaluate
        )
        
        try:
            db.session.add(solution)
            db.session.flush()  # Получаем ID решения
            
            # Связываем проблемы ПОСЛЕ сохранения решения
            if problem_ids:
                problems = Problem.query.filter(Problem.id.in_(problem_ids)).all()
                if problems:
                    solution.problems.extend(problems)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения решения: {e}")
            # Удаляем скачанное изображение, если оно было автоматически найдено
            if image_path and image_path != '../images/default.png' and os.path.exists(image_path):
                try:
                    delete_file(image_path)
                except:
                    pass
            return jsonify({'error': 'Ошибка сохранения решения'}), 500
        
        # Возвращаем в формате, ожидаемом фронтендом
        return jsonify({
            'message': 'Решение сохранено',
            'id': solution.id,
            'solution': {
                'ID': solution.id,
                'Name': solution.name,
                'Describe': solution.describe,
                'Image': solution.image
            }
        }), 201
        
    except Exception as e:
        print(f"Ошибка создания решения: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

# Дополнительные обработчики

@solution_bp.route('/solutions/user/<int:user_id>', methods=['GET'])
def get_user_solutions(user_id):
    """Получение решений конкретного пользователя"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        if limit > 100:
            limit = 100
        
        # Проверяем, существует ли пользователь
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Получаем решения пользователя
        solutions = Solution.query.filter_by(
            creator=user_id,
            show=True
        ).order_by(
            Solution.created_date.desc()
        ).offset(offset).limit(limit).all()
        
        solutions_list = []
        for solution in solutions:
            solution_dict = solution.to_dict()
            
            # Добавляем связанные проблемы
            solution_dict['problems'] = [
                problem.to_dict() for problem in solution.problems
            ]
            
            solutions_list.append(solution_dict)
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username
            },
            'solutions': solutions_list,
            'total': Solution.query.filter_by(creator=user_id, show=True).count()
        }), 200
        
    except Exception as e:
        print(f"Ошибка получения решений пользователя: {e}")
        return jsonify({'error': 'Ошибка базы данных'}), 500

@solution_bp.route('/solutions/<int:solution_id>', methods=['PUT'])
@token_required
def update_solution(solution_id):
    """Обновление решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли решение и принадлежит ли пользователю
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        if solution.creator != user_id:
            return jsonify({'error': 'Нет прав на обновление'}), 403
        
        # Получаем данные из формы
        name = request.form.get('name', solution.name).strip()
        describe = request.form.get('describe', solution.describe).strip()
        related_problems_str = request.form.get('relatedProblems', '')
        can_buy = request.form.get('canBuy') == 'on'
        can_evaluate = request.form.get('canEvaluate') == 'on'
        
        # Валидация
        if not name:
            return jsonify({'error': 'Название решения обязательно'}), 400
        
        # Обработка файла изображения
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # Удаляем старое изображение, если есть
                if solution.image:
                    delete_file(solution.image)
                
                # Сохраняем новое
                solution.image = save_file(file)
        
        # Обновляем решение
        solution.name = name
        solution.describe = describe
        solution.is_bought = can_buy
        solution.is_rating = can_evaluate
        solution.modified_date = datetime.utcnow()
        
        # Обработка связанных проблем
        if related_problems_str is not None:
            # Очищаем старые связи
            solution.problems.clear()
            
            # Добавляем новые проблемы
            if related_problems_str:
                problem_ids = parse_int_list(related_problems_str)
                
                if problem_ids:
                    problems = Problem.query.filter(Problem.id.in_(problem_ids)).all()
                    solution.problems.extend(problems)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка обновления решения: {e}")
            return jsonify({'error': 'Ошибка обновления решения'}), 500
        
        return jsonify({
            'message': 'Решение обновлено',
            'solution': solution.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Ошибка обновления решения: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/<int:solution_id>', methods=['DELETE'])
@token_required
def delete_solution(solution_id):
    """Удаление решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли решение и принадлежит ли пользователю
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        if solution.creator != user_id:
            return jsonify({'error': 'Нет прав на удаление'}), 403
        
        # Удаляем связанные файлы
        if solution.image:
            delete_file(solution.image)
        
        # Удаляем решение (каскадное удаление настроено в моделях)
        try:
            db.session.delete(solution)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка удаления решения: {e}")
            return jsonify({'error': 'Ошибка удаления решения'}), 500
        
        return jsonify({'message': 'Решение удалено'}), 200
        
    except Exception as e:
        print(f"Ошибка удаления решения: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/<int:solution_id>/toggle-favourite', methods=['POST'])
@token_required
def toggle_solution_favourite(solution_id):
    """Добавление/удаление решения в избранное"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Получаем пользователя
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Проверяем, есть ли уже в избранном через many-to-many
        is_favourite = solution in user.favourite_solutions
        
        if is_favourite:
            # Удаляем из избранного
            user.favourite_solutions.remove(solution)
            # Обновляем счетчик избранного
            solution.favourite = max(0, (solution.favourite or 0) - 1)
            is_favourite = False
        else:
            # Добавляем в избранное
            user.favourite_solutions.append(solution)
            # Обновляем счетчик избранного
            solution.favourite = (solution.favourite or 0) + 1
            is_favourite = True
            # Отслеживаем добавление в избранное
            try:
                track_user_activity(user_id, 'favorite', 'solution', solution_id)
            except:
                pass
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления избранного'}), 500
        
        return jsonify({
            'message': 'Избранное обновлено',
            'is_favourite': is_favourite
        }), 200
        
    except Exception as e:
        print(f"Ошибка обновления избранного: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/favorites', methods=['GET'])
@token_required
def get_favourite_solutions():
    """Получение избранных решений пользователя"""
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
        
        # Получаем избранные решения пользователя через relationship
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Начинаем с решений из избранного пользователя
        query = Solution.query.filter(
            Solution.id.in_([s.id for s in user.favourite_solutions])
        )
        
        # Фильтр по поиску
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(Solution.name).like(search_lower),
                    func.lower(Solution.describe).like(search_lower)
                )
            )
        
        # Фильтр по категории
        if category_param:
            try:
                category_id = int(category_param)
                # Подзапрос для поиска решений через связанные проблемы
                problem_subquery = db.session.query(
                    solution_problems.c.solution_id
                ).join(
                    Problem, Problem.id == solution_problems.c.problem_id
                ).filter(
                    Problem.category == category_id
                ).subquery()
                
                query = query.filter(Solution.id.in_(db.session.query(problem_subquery.c.solution_id)))
            except ValueError as e:
                print(f"Ошибка преобразования категории: {e}")
        
        # Фильтр по хэштегам
        if hashtags_param:
            hashtag_ids = parse_int_list(hashtags_param)
            
            if hashtag_ids:
                # Подзапрос для поиска проблем с указанными хэштегами
                problem_subquery = db.session.query(
                    hashtag_problem.c.problem_id
                ).filter(
                    hashtag_problem.c.hashtag_id.in_(hashtag_ids)
                ).group_by(
                    hashtag_problem.c.problem_id
                ).having(
                    func.count(hashtag_problem.c.hashtag_id.distinct()) == len(hashtag_ids)
                ).subquery()
                
                # Подзапрос для поиска решений через эти проблемы
                solution_subquery = db.session.query(
                    solution_problems.c.solution_id
                ).filter(
                    solution_problems.c.problem_id.in_(db.session.query(problem_subquery.c.problem_id))
                ).subquery()
                
                query = query.filter(Solution.id.in_(db.session.query(solution_subquery.c.solution_id)))
        
        # Сортировка и пагинация
        solutions = query.order_by(Solution.created_date.desc()).offset(offset).limit(limit).all()
        
        solutions_list = []
        for solution in solutions:
            # Получаем связанные проблемы
            problems_data = []
            if hasattr(solution, 'problems') and solution.problems:
                for problem in solution.problems:
                    problem_dict = {
                        'ID': problem.id,
                        'Name': problem.name,
                        'Image': problem.image or '../images/default.png',
                        'Hashtags': []
                    }
                    
                    # Получаем хэштеги проблемы
                    if hasattr(problem, 'hashtags') and problem.hashtags:
                        problem_dict['Hashtags'] = [
                            {
                                'ID': hashtag.id,
                                'Name': hashtag.name
                            }
                            for hashtag in problem.hashtags
                        ]
                    
                    # Получаем информацию о теме проблемы
                    if problem.topic:
                        topic = Topic.query.get(problem.topic)
                        if topic:
                            problem_dict['TopicInfo'] = {
                                'ID': topic.id,
                                'Name': topic.name
                            }
                    
                    problems_data.append(problem_dict)
            
            # Получаем комментарии
            comments = []
            if hasattr(solution, 'comments') and solution.comments:
                for comment in solution.comments:
                    comment_dict = {
                        'ID': comment.id,
                        'Text': comment.text,
                        'CreatedDate': comment.created_date.isoformat() if comment.created_date else '',
                        'Creator': {
                            'User': comment.creator_user.username if comment.creator_user else 'Аноним'
                        },
                        'LikeCount': comment.likecount or 0,
                        'NotLikeCount': comment.notlikecount or 0
                    }
                    comments.append(comment_dict)
            
            solution_data = {
                'ID': solution.id,
                'Name': solution.name,
                'Describe': solution.describe or '',
                'Image': solution.image or '../images/default.png',
                'Favourite': 1,  # Так как это решение в избранном
                'Show': solution.show or 0,
                'Reply': solution.reply or 0,
                'Price': float(solution.price) if solution.price else 0,
                'Efficiency': solution.efficiency or 0,
                'Complexity': solution.complexity or 0,
                'Time': solution.time or 0,
                'Rating': solution.rating or 0,
                'IsBought': bool(solution.isbought),
                'IsRating': bool(solution.israting),
                'IsNew': bool(solution.isnew),
                'FromAuthor': bool(solution.fromauthor),
                'Creator': solution.creator,
                'CreatedDate': solution.created_date.isoformat() if solution.created_date else '',
                'ModifiedDate': solution.modified_date.isoformat() if solution.modified_date else '',
                'Comments': comments,
                'Problems': problems_data
            }
            
            solutions_list.append(solution_data)
        
        return jsonify(solutions_list), 200
        
    except Exception as e:
        print(f"Ошибка получения избранных решений: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500

@solution_bp.route('/solutions/<int:solution_id>/toggle-show', methods=['POST'])
@token_required
def toggle_solution_show(solution_id):
    """Переключение видимости решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        solution = Solution.query.get(solution_id)
        if not solution or solution.creator != user_id:
            return jsonify({'error': 'Решение не найдено или нет прав'}), 404
        
        # Переключаем видимость
        solution.show = not solution.show
        solution.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления видимости'}), 500
        
        return jsonify({
            'message': 'Видимость обновлена',
            'show': solution.show
        }), 200
        
    except Exception as e:
        print(f"Ошибка обновления видимости: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/<int:solution_id>/mark-as-read', methods=['POST'])
@token_required
def mark_solution_as_read(solution_id):
    """Отметить решение как прочитанное"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        solution = Solution.query.get(solution_id)
        if not solution or solution.creator != user_id:
            return jsonify({'error': 'Решение не найдено или нет прав'}), 404
        
        # Снимаем флаг is_new
        solution.isnew = False
        solution.modified_date = datetime.utcnow()
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Ошибка обновления решения'}), 500
        
        return jsonify({'message': 'Решение отмечено как прочитанное'}), 200
        
    except Exception as e:
        print(f"Ошибка обновления решения: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/<int:solution_id>/link', methods=['POST'])
@token_required
def add_solution_link(solution_id):
    """Добавление связи между решениями"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли решение
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Получаем данные из запроса
        data = request.get_json()
        if not data or 'linked_solution_id' not in data:
            return jsonify({'error': 'Не указан ID связанного решения'}), 400
        
        linked_solution_id = int(data['linked_solution_id'])
        
        # Проверяем, что не пытаемся связать решение само с собой
        if solution_id == linked_solution_id:
            return jsonify({'error': 'Нельзя связать решение само с собой'}), 400
        
        # Проверяем, существует ли связанное решение
        linked_solution = Solution.query.get(linked_solution_id)
        if not linked_solution:
            return jsonify({'error': 'Связанное решение не найдено'}), 404
        
        # Проверяем, не существует ли уже такая связь
        existing_link = db.session.query(solution_link_solution).filter(
            and_(
                solution_link_solution.c.solution_id == solution_id,
                solution_link_solution.c.solution_link_id == linked_solution_id
            )
        ).first()
        
        if existing_link:
            return jsonify({'error': 'Связь уже существует'}), 400
        
        # Добавляем связь (двустороннюю)
        try:
            # Добавляем связь в обе стороны для симметричности
            db.session.execute(
                solution_link_solution.insert().values(
                    solution_id=solution_id,
                    solution_link_id=linked_solution_id
                )
            )
            db.session.execute(
                solution_link_solution.insert().values(
                    solution_id=linked_solution_id,
                    solution_link_id=solution_id
                )
            )
            
            # Увеличиваем счетчик связей
            solution.reply = (solution.reply or 0) + 1
            linked_solution.reply = (linked_solution.reply or 0) + 1
            
            db.session.commit()
            
            return jsonify({
                'message': 'Связь между решениями добавлена',
                'solution_id': solution_id,
                'linked_solution_id': linked_solution_id
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка добавления связи: {e}")
            # Проверяем, не была ли связь добавлена частично
            return jsonify({'error': 'Ошибка добавления связи'}), 500
        
    except Exception as e:
        print(f"Ошибка добавления связи между решениями: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

def recalculate_solution_rating(solution_id):
    """Пересчитывает общий рейтинг решения как среднее арифметическое всех категорий оценки"""
    try:
        # Получаем все оценки для данного решения
        ratings = SolutionRating.query.filter_by(solution_id=solution_id).all()
        
        if not ratings:
            # Если оценок нет, общий рейтинг = 0
            return 0
        
        # Группируем оценки по типам и вычисляем среднее для каждого типа
        rating_types = {}
        for rating in ratings:
            rating_type = rating.rating_type
            if rating_type not in rating_types:
                rating_types[rating_type] = []
            rating_types[rating_type].append(rating.rating_value)
        
        # Вычисляем среднее для каждого типа
        type_averages = {}
        for rating_type, values in rating_types.items():
            type_averages[rating_type] = sum(values) / len(values)
        
        # Вычисляем общее среднее арифметическое всех категорий
        if type_averages:
            overall_rating = sum(type_averages.values()) / len(type_averages)
            # Округляем до целого числа
            return round(overall_rating)
        else:
            return 0
    except Exception as e:
        print(f"Ошибка пересчета рейтинга: {e}")
        import traceback
        traceback.print_exc()
        return 0

@solution_bp.route('/solutions/<int:solution_id>/rating', methods=['POST'])
@token_required
def save_solution_rating(solution_id):
    """Сохранение оценки решения пользователем"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли решение
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Получаем данные из запроса
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Не указаны данные для оценки'}), 400
        
        rating_type = data.get('rating_type')
        rating_value = data.get('rating_value')
        
        # Валидация
        if not rating_type or rating_type not in ['price', 'efficiency', 'complexity', 'time']:
            return jsonify({'error': 'Неверный тип оценки. Допустимые значения: price, efficiency, complexity, time'}), 400
        
        if not rating_value or not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return jsonify({'error': 'Оценка должна быть целым числом от 1 до 5'}), 400
        
        # Проверяем, есть ли уже оценка от этого пользователя для этого типа
        existing_rating = SolutionRating.query.filter_by(
            solution_id=solution_id,
            user_id=user_id,
            rating_type=rating_type
        ).first()
        
        if existing_rating:
            # Обновляем существующую оценку
            existing_rating.rating_value = rating_value
            existing_rating.modified_date = datetime.utcnow()
        else:
            # Создаем новую оценку
            new_rating = SolutionRating(
                solution_id=solution_id,
                user_id=user_id,
                rating_type=rating_type,
                rating_value=rating_value
            )
            db.session.add(new_rating)
        
        # Пересчитываем общий рейтинг решения
        overall_rating = recalculate_solution_rating(solution_id)
        solution.rating = overall_rating
        
        # Также обновляем средние значения для каждого типа рейтинга в таблице Solution
        # Для efficiency, complexity, time вычисляем средние
        for rt in ['efficiency', 'complexity', 'time']:
            ratings_for_type = SolutionRating.query.filter_by(
                solution_id=solution_id,
                rating_type=rt
            ).all()
            
            if ratings_for_type:
                avg_value = sum(r.rating_value for r in ratings_for_type) / len(ratings_for_type)
                avg_value = round(avg_value)
                
                # Обновляем соответствующее поле в Solution
                if rt == 'efficiency':
                    solution.efficiency = avg_value
                elif rt == 'complexity':
                    solution.complexity = avg_value
                elif rt == 'time':
                    solution.time = avg_value
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка сохранения оценки: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Ошибка сохранения оценки'}), 500
        
        return jsonify({
            'message': 'Оценка сохранена',
            'rating': overall_rating,
            'rating_type': rating_type,
            'rating_value': rating_value
        }), 200
        
    except Exception as e:
        print(f"Ошибка сохранения оценки решения: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@solution_bp.route('/solutions/<int:solution_id>/rating', methods=['GET'])
@token_required
def get_user_solution_ratings(solution_id):
    """Получение оценок текущего пользователя для решения"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Получаем все оценки пользователя для данного решения
        ratings = SolutionRating.query.filter_by(
            solution_id=solution_id,
            user_id=user_id
        ).all()
        
        # Формируем словарь с оценками по типам
        ratings_dict = {}
        for rating in ratings:
            ratings_dict[rating.rating_type] = rating.rating_value
        
        return jsonify({
            'ratings': ratings_dict,
            'solution_id': solution_id,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        print(f"Ошибка получения оценок: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500