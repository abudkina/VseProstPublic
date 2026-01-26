"""
Service layer for Problem operations

Бизнес-логика для работы с проблемами (Problem).
Отделена от endpoint'ов для переиспользования и тестирования.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func, exists
from flask import g

from logic.model import (
    db, Problem, Category, Hashtag, User, Solution,
    favourite_problem, hashtag_problem, Topic
)
from logic.utils.error_handler import (
    ValidationError, AuthorizationError, ResourceNotFoundError,
    DatabaseError, ConflictError, AppError
)
from logic.utils.logger import get_logger
from logic.utils.validators import parse_int_list, parse_bool
from logic.recommendations import track_user_activity, create_embedding

logger = get_logger(__name__)


class ProblemService:
    """Service для работы с проблемами"""
    
    # Константы
    MAX_LIMIT = 100
    DEFAULT_LIMIT = 50
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 10000
    
    @staticmethod
    def get_all_problems(
        search: str = '',
        category_id: Optional[int] = None,
        hashtag_ids: Optional[List[int]] = None,
        topic_id: Optional[int] = None,
        exclude_ids: Optional[List[int]] = None,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Получение списка проблем с фильтрацией и пагинацией.
        
        Args:
            search: Строка поиска по названию/описанию
            category_id: ID категории для фильтра
            hashtag_ids: Список ID хэштегов для фильтра
            topic_id: ID топика для фильтра
            exclude_ids: Список ID для исключения
            limit: Максимальное количество результатов
            offset: Смещение (для пагинации)
            user_id: ID пользователя для определения избранного
            
        Returns:
            Кортеж (список проблем, общее количество)
        """
        # Валидация параметров
        limit = min(limit, ProblemService.MAX_LIMIT)
        if limit <= 0:
            limit = ProblemService.DEFAULT_LIMIT
        if offset < 0:
            offset = 0
        
        # Базовый запрос
        query = Problem.query.filter(Problem.show.isnot(None))
        
        # Поиск по названию/описанию
        if search:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(Problem.name).like(search_pattern),
                    func.lower(Problem.describe).like(search_pattern)
                )
            )
        
        # Фильтр по категории
        if category_id:
            query = query.filter(Problem.category == category_id)
        
        # Фильтр по хэштегам
        if hashtag_ids:
            for hashtag_id in hashtag_ids:
                subquery = db.session.query(hashtag_problem).filter(
                    hashtag_problem.c.problem_id == Problem.id,
                    hashtag_problem.c.hashtag_id == hashtag_id
                ).exists()
                query = query.filter(subquery)
        
        # Фильтр по топику
        if topic_id:
            query = query.filter(Problem.topic == topic_id)
        
        # Исключение проблем
        if exclude_ids:
            query = query.filter(~Problem.id.in_(exclude_ids))
        
        # Получаем общее количество
        total_count = query.count()
        
        # Применяем сортировку и пагинацию
        problems = query.order_by(
            Problem.modified_date.desc().nulls_last(),
            Problem.created_date.desc()
        ).offset(offset).limit(limit).all()
        
        # Формируем ответ
        problems_list = []
        for problem in problems:
            problems_list.append(
                ProblemService._format_problem_response(problem, user_id)
            )
        
        return problems_list, total_count
    
    @staticmethod
    def get_problem_by_id(problem_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение проблемы по ID.
        
        Args:
            problem_id: ID проблемы
            user_id: ID текущего пользователя (опционально)
            
        Returns:
            Словарь с информацией о проблеме
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        return ProblemService._format_problem_response(problem, user_id)
    
    @staticmethod
    def create_problem(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создание новой проблемы.
        
        Args:
            user_id: ID создателя
            data: Данные проблемы (name, describe, category, hashtags, topic, etc.)
            
        Returns:
            Словарь с информацией о созданной проблеме
            
        Raises:
            ValidationError: При ошибках валидации
            DatabaseError: При ошибках БД
        """
        # Валидация входных данных
        name = data.get('name', '').strip()
        describe = data.get('describe', '').strip()
        category_id = data.get('category')
        hashtag_ids = data.get('hashtag_ids', [])
        topic_id = data.get('topic')
        
        # Проверка обязательных полей
        if not name:
            raise ValidationError("Название проблемы обязательно")
        
        if len(name) > ProblemService.MAX_TITLE_LENGTH:
            raise ValidationError(
                f"Название слишком длинное (максимум {ProblemService.MAX_TITLE_LENGTH} символов)",
                details={'max_length': ProblemService.MAX_TITLE_LENGTH}
            )
        
        if describe and len(describe) > ProblemService.MAX_DESCRIPTION_LENGTH:
            raise ValidationError(
                f"Описание слишком длинное (максимум {ProblemService.MAX_DESCRIPTION_LENGTH} символов)",
                details={'max_length': ProblemService.MAX_DESCRIPTION_LENGTH}
            )
        
        # Проверка категории
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                raise ValidationError("Категория не найдена", details={'category_id': category_id})
        
        # Проверка топика
        if topic_id:
            topic = Topic.query.get(topic_id)
            if not topic:
                raise ValidationError("Топик не найден", details={'topic_id': topic_id})
        
        try:
            # Создание проблемы
            problem = Problem(
                name=name,
                describe=describe,
                category=category_id,
                creator_id=user_id,
                topic=topic_id,
                show=True,
                created_date=datetime.utcnow()
            )
            
            # Добавление хэштегов
            if hashtag_ids:
                hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                problem.hashtags = hashtags
            
            db.session.add(problem)
            db.session.flush()  # Получаем ID проблемы
            
            # Создаем embedding для рекомендаций
            try:
                embedding = create_embedding(name, describe)
                problem.embedding = embedding
            except Exception as e:
                logger.warning(f"Ошибка при создании embedding для проблемы: {e}")
            
            db.session.commit()
            
            # Трекируем активность пользователя
            try:
                track_user_activity(user_id, 'problem', 'create', problem.id)
            except Exception as e:
                logger.warning(f"Ошибка при трекировании активности: {e}")
            
            logger.info(f"Создана проблема ID={problem.id} пользователем ID={user_id}")
            
            return ProblemService._format_problem_response(problem, user_id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании проблемы: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при создании проблемы: {str(e)}")
    
    @staticmethod
    def update_problem(problem_id: int, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновление проблемы.
        
        Args:
            problem_id: ID проблемы
            user_id: ID текущего пользователя (должен быть создателем)
            data: Данные для обновления
            
        Returns:
            Обновленная проблема
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
            AuthorizationError: Если пользователь не является создателем
            ValidationError: При ошибках валидации
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        if problem.creator_id != user_id:
            raise AuthorizationError("Только создатель может редактировать проблему")
        
        try:
            # Обновляем поля
            if 'name' in data:
                name = data['name'].strip()
                if not name:
                    raise ValidationError("Название не может быть пустым")
                if len(name) > ProblemService.MAX_TITLE_LENGTH:
                    raise ValidationError(f"Название слишком длинное (максимум {ProblemService.MAX_TITLE_LENGTH} символов)")
                problem.name = name
            
            if 'describe' in data:
                describe = data['describe'].strip()
                if describe and len(describe) > ProblemService.MAX_DESCRIPTION_LENGTH:
                    raise ValidationError(f"Описание слишком длинное (максимум {ProblemService.MAX_DESCRIPTION_LENGTH} символов)")
                problem.describe = describe
            
            if 'category' in data:
                category_id = data['category']
                if category_id:
                    category = Category.query.get(category_id)
                    if not category:
                        raise ValidationError("Категория не найдена")
                problem.category = category_id
            
            if 'topic' in data:
                topic_id = data['topic']
                if topic_id:
                    topic = Topic.query.get(topic_id)
                    if not topic:
                        raise ValidationError("Топик не найдена")
                problem.topic = topic_id
            
            if 'hashtag_ids' in data:
                hashtag_ids = data['hashtag_ids']
                if hashtag_ids:
                    hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
                    problem.hashtags = hashtags
                else:
                    problem.hashtags = []
            
            problem.modified_date = datetime.utcnow()
            
            # Обновляем embedding если изменилось содержание
            if 'name' in data or 'describe' in data:
                try:
                    embedding = create_embedding(problem.name, problem.describe)
                    problem.embedding = embedding
                except Exception as e:
                    logger.warning(f"Ошибка при обновлении embedding: {e}")
            
            db.session.commit()
            logger.info(f"Обновлена проблема ID={problem_id}")
            
            return ProblemService._format_problem_response(problem, user_id)
            
        except (ValidationError, AppError):
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при обновлении проблемы: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при обновлении проблемы: {str(e)}")
    
    @staticmethod
    def delete_problem(problem_id: int, user_id: int) -> None:
        """
        Удаление проблемы.
        
        Args:
            problem_id: ID проблемы
            user_id: ID текущего пользователя (должен быть создателем)
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
            AuthorizationError: Если пользователь не является создателем
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        if problem.creator_id != user_id:
            raise AuthorizationError("Только создатель может удалить проблему")
        
        try:
            db.session.delete(problem)
            db.session.commit()
            logger.info(f"Удалена проблема ID={problem_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при удалении проблемы: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при удалении проблемы: {str(e)}")
    
    @staticmethod
    def toggle_favourite(problem_id: int, user_id: int) -> Dict[str, Any]:
        """
        Переключение статуса избранного.
        
        Args:
            problem_id: ID проблемы
            user_id: ID пользователя
            
        Returns:
            Словарь с новым статусом избранного
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        try:
            user = User.query.get(user_id)
            
            if user and problem in user.favourite_problems:
                user.favourite_problems.remove(problem)
                is_favourite = False
            else:
                if user:
                    user.favourite_problems.append(problem)
                is_favourite = True
            
            db.session.commit()
            logger.info(f"Статус избранного переключен для проблемы ID={problem_id}")
            
            return {
                'problem_id': problem_id,
                'is_favourite': is_favourite
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при переключении избранного: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при переключении избранного: {str(e)}")
    
    @staticmethod
    def toggle_show(problem_id: int, user_id: int) -> Dict[str, bool]:
        """
        Переключение видимости проблемы.
        
        Args:
            problem_id: ID проблемы
            user_id: ID пользователя (должен быть создателем)
            
        Returns:
            Словарь с новым статусом show
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
            AuthorizationError: Если пользователь не является создателем
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        if problem.creator_id != user_id:
            raise AuthorizationError("Только создатель может менять видимость проблемы")
        
        try:
            problem.show = None if problem.show else True
            problem.modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'problem_id': problem_id, 'show': problem.show is not None}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при переключении видимости: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при переключении видимости: {str(e)}")
    
    @staticmethod
    def mark_as_read(problem_id: int, user_id: int) -> Dict[str, Any]:
        """
        Отметить проблему как прочитанную.
        
        Args:
            problem_id: ID проблемы
            user_id: ID пользователя
            
        Returns:
            Информация о статусе
            
        Raises:
            ResourceNotFoundError: Если проблема не найдена
        """
        problem = Problem.query.get(problem_id)
        
        if not problem:
            raise ResourceNotFoundError('Problem', problem_id)
        
        try:
            # Трекируем активность
            track_user_activity(user_id, 'problem', 'view', problem_id)
            
            return {
                'problem_id': problem_id,
                'marked_as_read': True
            }
        except Exception as e:
            logger.error(f"Ошибка при отметке как прочитанной: {e}", exc_info=True)
            raise DatabaseError(f"Ошибка при отметке: {str(e)}")
    
    @staticmethod
    def _format_problem_response(problem: Problem, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Форматирование ответа для проблемы.
        
        Args:
            problem: Объект Problem
            user_id: ID текущего пользователя (для определения избранного)
            
        Returns:
            Отформатированный словарь
        """
        is_favourite = False
        if user_id:
            user = User.query.get(user_id)
            if user and problem in user.favourite_problems:
                is_favourite = True
        
        hashtags_list = [
            {'ID': h.id, 'Name': h.name}
            for h in (problem.hashtags or [])
        ]
        
        return {
            'ID': problem.id,
            'Name': problem.name,
            'Describe': problem.describe,
            'Category': problem.category,
            'Creator_id': problem.creator_id,
            'Creator_name': problem.creator.username if problem.creator else None,
            'Hashtags': hashtags_list,
            'CreatedDate': problem.created_date.isoformat() if problem.created_date else None,
            'ModifiedDate': problem.modified_date.isoformat() if problem.modified_date else None,
            'IsFavourite': is_favourite,
            'Show': problem.show is not None,
            'Topic': problem.topic
        }
