"""
Service layer for Solution operations

Бизнес-логика для работы с решениями (Solution).
Отделена от endpoint'ов для переиспользования и тестирования.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func
from flask import g

from logic.model import (
    db, Solution, Problem, User, Category, Hashtag,
    hashtag_solution, SolutionRating, TemporaryLinkSolution, TemporaryProblemSolution,
    UserCartSolution, UserSolutionCategories, Embedding, CommentSolution,
    comment_solution_likes, comment_solution_dislikes
)
from logic.utils.error_handler import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    DatabaseError, ConflictError, AppError
)
from logic.utils.logger import get_logger
from logic.utils.normalizers import capitalize_title, capitalize_first
from logic.utils.file_utils import delete_image
from logic.recommendations import track_user_activity, create_embedding
from logic.cache_config import cache, CACHE_TIMEOUTS

logger = get_logger(__name__)


class SolutionService:
    """Service для работы с решениями"""
    
    # Константы
    MAX_LIMIT = 100
    DEFAULT_LIMIT = 50
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 10000
    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUTS['solutions'])
    def get_all_solutions(
        problem_id: Optional[int] = None,
        search: str = '',
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Получение списка решений с фильтрацией и пагинацией.
        
        Использует кэширование для повышения производительности.
        Eager loading для избежания N+1 queries.
        
        Args:
            problem_id: ID проблемы (опционально для фильтра)
            search: Строка поиска
            limit: Максимальное количество результатов
            offset: Смещение (для пагинации)
            user_id: ID пользователя для определения избранного
            
        Returns:
            Кортеж (список решений, общее количество)
        """
        # Валидация параметров
        limit = min(limit, SolutionService.MAX_LIMIT)
        if limit <= 0:
            limit = SolutionService.DEFAULT_LIMIT
        if offset < 0:
            offset = 0
        
        # Базовый запрос с eager loading для избежания N+1 queries
        from sqlalchemy.orm import joinedload
        query = Solution.query.options(
            joinedload(Solution.creator),      # Загружаем создателя
            joinedload(Solution.hashtags),      # Загружаем хэштеги
            joinedload(Solution.problem)        # Загружаем проблему
        ).filter(Solution.show.isnot(None))
        
        # Фильтр по проблеме
        if problem_id:
            query = query.filter(Solution.problem_id == problem_id)
        
        # Поиск по названию/описанию
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(Solution.name).like(search_pattern),
                    func.lower(Solution.describe).like(search_pattern)
                )
            )
        
        # Получаем общее количество
        total_count = query.count()
        
        # Применяем сортировку и пагинацию
        solutions = query.order_by(
            Solution.modified_date.desc(),
            Solution.created_date.desc()
        ).offset(offset).limit(limit).all()
        
        # Формируем ответ
        solutions_list = [
            SolutionService._format_solution_response(s, user_id)
            for s in solutions
        ]
        
        return solutions_list, total_count
    
    @staticmethod
    @cache.memoize(timeout=CACHE_TIMEOUTS['solutions'])
    def get_solution_by_id(solution_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение решения по ID.
        
        Использует кэширование для повышения производительности.
        Eager loading для избежания N+1 queries.
        
        Args:
            solution_id: ID решения
            user_id: ID текущего пользователя (опционально)
            
        Returns:
            Словарь с информацией о решении
            
        Raises:
            ResourceNotFoundError: Если решение не найдено
        """
        # Eager loading для избежания N+1 queries
        from sqlalchemy.orm import joinedload
        solution = Solution.query.options(
            joinedload(Solution.creator),
            joinedload(Solution.hashtags),
            joinedload(Solution.problem)
        ).get(solution_id)
        
        if not solution:
            raise ResourceNotFoundError('Solution', solution_id)
        
        return SolutionService._format_solution_response(solution, user_id)
    
    @staticmethod
    def create_solution(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание нового решения.
        
        Args:
            user_id: ID создателя
            data: Данные решения (name, describe, problem_id, hashtags, etc.)
            
        Returns:
            Словарь с информацией о созданном решении
            
        Raises:
            ValidationError: При ошибках валидации
            DatabaseError: При ошибках БД
        """
        # Валидация входных данных
        name = capitalize_title(data.get('name', '').strip())
        describe = capitalize_first(data.get('describe', '').strip())
        problem_id = data.get('problem_id')
        hashtag_ids = data.get('hashtag_ids', [])
        
        # Проверка обязательных полей
        if not name:
            raise ValidationError("Название решения обязательно")

        existing = Solution.query.filter(func.lower(Solution.name) == name.lower()).first()
        if existing:
            raise ConflictError("Решение с таким названием уже существует")
        
        if len(name) > SolutionService.MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Название слишком длинное (максимум {SolutionService.MAX_TITLE_LENGTH} символов)",
                details={'max_length': SolutionService.MAX_TITLE_LENGTH}
            )
        
        if describe and len(describe) > SolutionService.MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Описание слишком длинное (максимум {SolutionService.MAX_DESCRIPTION_LENGTH} символов)",
                details={'max_length': SolutionService.MAX_DESCRIPTION_LENGTH}
            )
        
        # Проверка проблемы
        if problem_id:
            problem = Problem.query.get(problem_id)
            if not problem:
                raise ValidationError("Проблема не найдена", details={'problem_id': problem_id})
        
        try:
            # Создание решения
            solution = Solution(
                name=name,
                describe=describe,
                problem_id=problem_id,
                creator_id=user_id,
                show=True,
                created_date=datetime.utcnow()
            )
            
            # Добавление хэштегов
            if hashtag_ids:
                hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                solution.hashtags = hashtags
            
            db.session.add(solution)
            db.session.flush()
            
            # Создаем embedding для рекомендаций
            try:
                embedding = create_embedding(name, describe)
                solution.embedding = embedding
            except Exception as e:
                logger.warning(f"Ошибка при создании embedding для решения: {e}")
            
            db.session.commit()
            
            # Инвалидируем кэш списка решений
            cache.delete_memoized(SolutionService.get_all_solutions)
            
            # Трекируем активность пользователя
            try:
                track_user_activity(user_id, 'solution', 'create', solution.id)
            except Exception as e:
                logger.warning(f"Ошибка при трекировании активности: {e}")
            
            logger.info(f"Создано решение ID={solution.id} пользователем ID={user_id}")
            
            return SolutionService._format_solution_response(solution, user_id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании решения: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при создании решения: {str(e)}")
    
    @staticmethod
    def update_solution(solution_id: int, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновление решения.
        
        Args:
            solution_id: ID решения
            user_id: ID текущего пользователя (должен быть создателем)
            data: Данные для обновления
            
        Returns:
            Обновленное решение
            
        Raises:
            ResourceNotFoundError: Если решение не найдено
            AuthorizationError: Если пользователь не является создателем
            ValidationError: При ошибках валидации
        """
        solution = Solution.query.get(solution_id)
        
        if not solution:
            raise ResourceNotFoundError('Solution', solution_id)
        
        if solution.creator != user_id:
            raise AuthorizationError("Только создатель может редактировать решение")
        
        try:
            # Обновляем поля
            if 'name' in data:
                name = capitalize_title(data['name'].strip())
                if not name:
                    raise ValidationError("Название не может быть пустым")
                if len(name) > SolutionService.MAX_TITLE_LENGTH:
                    raise ValidationError(f"Название слишком длинное (максимум {SolutionService.MAX_TITLE_LENGTH} символов)")
                solution.name = name
            
            if 'describe' in data:
                describe = capitalize_first(data['describe'].strip())
                if describe and len(describe) > SolutionService.MAX_DESCRIPTION_LENGTH:
                    raise ValidationError(f"Описание слишком длинное (максимум {SolutionService.MAX_DESCRIPTION_LENGTH} символов)")
                solution.describe = describe
            
            if 'problem_id' in data:
                problem_id = data['problem_id']
                if problem_id:
                    problem = Problem.query.get(problem_id)
                    if not problem:
                        raise ValidationError("Проблема не найдена")
                solution.problem_id = problem_id
            
            if 'hashtag_ids' in data:
                hashtag_ids = data['hashtag_ids']
                if hashtag_ids:
                    hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                    solution.hashtags = hashtags
                else:
                    solution.hashtags = []
            
            solution.modified_date = datetime.utcnow()
            
            # Обновляем embedding если изменилось содержание
            if 'name' in data or 'describe' in data:
                try:
                    embedding = create_embedding(solution.name, solution.describe)
                    solution.embedding = embedding
                except Exception as e:
                    logger.warning(f"Ошибка при обновлении embedding: {e}")
            
            db.session.commit()
            
            # Инвалидируем кэш
            cache.delete_memoized(SolutionService.get_all_solutions)
            cache.delete_memoized(SolutionService.get_solution_by_id, solution_id)
            
            logger.info(f"Обновлено решение ID={solution_id}")
            
            return SolutionService._format_solution_response(solution, user_id)
            
        except (ValidationError, AppError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при обновлении решения: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при обновлении решения: {str(e)}")
    
    @staticmethod
    def delete_solution(solution_id: int, user_id: int) -> None:
        """
        Удаление решения.
        
        Args:
            solution_id: ID решения
            user_id: ID текущего пользователя (должен быть создателем)
            
        Raises:
            ResourceNotFoundError: Если решение не найдено
            AuthorizationError: Если пользователь не является создателем
        """
        solution = Solution.query.get(solution_id)
        
        if not solution:
            raise ResourceNotFoundError('Solution', solution_id)
        
        if solution.creator != user_id:
            raise AuthorizationError("Только создатель может удалить решение")
        
        if solution.image:
            try:
                delete_image(solution.image)
            except Exception as e:
                logger.warning(f"Не удалось удалить изображение: {e}")
        try:
            # Удаление из связанных таблиц (до удаления решения)
            comment_ids = [c.id for c in solution.comments]
            if comment_ids:
                db.session.execute(comment_solution_likes.delete().where(
                    comment_solution_likes.c.commentid.in_(comment_ids)))
                db.session.execute(comment_solution_dislikes.delete().where(
                    comment_solution_dislikes.c.commentid.in_(comment_ids)))
            SolutionRating.query.filter_by(solution_id=solution_id).delete()
            TemporaryLinkSolution.query.filter_by(solution=solution_id).delete()
            TemporaryProblemSolution.query.filter_by(solution=solution_id).delete()
            UserCartSolution.query.filter_by(solution=solution_id).delete()
            UserSolutionCategories.query.filter_by(solution=solution_id).delete()
            Embedding.query.filter_by(entity_type='solution', entity_id=solution_id).delete()
            db.session.delete(solution)
            db.session.commit()
            
            # Инвалидируем кэш
            cache.delete_memoized(SolutionService.get_all_solutions)
            cache.delete_memoized(SolutionService.get_solution_by_id, solution_id)
            
            logger.info(f"Удалено решение ID={solution_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при удалении решения: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при удалении решения: {str(e)}")
    
    @staticmethod
    def _format_solution_response(solution: Solution, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Форматирование ответа для решения.
        
        Args:
            solution: Объект Solution
            user_id: ID текущего пользователя (для определения избранного)
            
        Returns:
            Отформатированный словарь
        """
        is_favourite = False
        if user_id:
            user = User.query.get(user_id)
            if user and hasattr(user, 'favourite_solutions'):
                if solution in user.favourite_solutions:
                    is_favourite = True
        
        hashtags_list = [
            {'ID': h.id, 'Name': h.name}
            for h in (solution.hashtags or [])
        ]
        
        return {
            'ID': solution.id,
            'Name': solution.name,
            'Describe': solution.describe,
            'ProblemID': solution.problem_id,
            'Creator_id': solution.creator,
            'Creator_name': solution.creator.username if solution.creator else None,
            'Hashtags': hashtags_list,
            'CreatedDate': solution.created_date.isoformat() if solution.created_date else None,
            'ModifiedDate': solution.modified_date.isoformat() if solution.modified_date else None,
            'IsFavourite': is_favourite,
            'Show': solution.show is not None
        }
