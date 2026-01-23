"""Base service class for business logic"""
from logic.model import db
from logic.utils.logger import get_logger


class BaseService:
    """Базовый класс для сервисов с общей бизнес-логикой"""

    def __init__(self, model_class):
        """
        Инициализация сервиса

        Args:
            model_class: SQLAlchemy модель
        """
        self.model = model_class
        self.logger = get_logger(self.__class__.__name__)

    def get_by_id(self, entity_id):
        """
        Получение сущности по ID

        Args:
            entity_id: ID сущности

        Returns:
            Model instance or None
        """
        try:
            return self.model.query.get(entity_id)
        except Exception as e:
            self.logger.error(f"Ошибка при получении {self.model.__name__} по ID {entity_id}: {e}")
            return None

    def get_all(self, limit=None, offset=0, order_by=None):
        """
        Получение всех сущностей с пагинацией

        Args:
            limit: Лимит записей
            offset: Смещение
            order_by: Поле для сортировки

        Returns:
            List of model instances
        """
        try:
            query = self.model.query

            if order_by:
                query = query.order_by(order_by)

            if limit:
                query = query.limit(limit)

            if offset:
                query = query.offset(offset)

            return query.all()
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех {self.model.__name__}: {e}")
            return []

    def create(self, **kwargs):
        """
        Создание новой сущности

        Args:
            **kwargs: Поля для создания

        Returns:
            Created model instance or None
        """
        try:
            entity = self.model(**kwargs)
            db.session.add(entity)
            db.session.commit()
            self.logger.info(f"Создан {self.model.__name__} с ID {entity.id}")
            return entity
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Ошибка при создании {self.model.__name__}: {e}")
            return None

    def update(self, entity_id, **kwargs):
        """
        Обновление существующей сущности

        Args:
            entity_id: ID сущности
            **kwargs: Поля для обновления

        Returns:
            Updated model instance or None
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                self.logger.warning(f"{self.model.__name__} с ID {entity_id} не найден")
                return None

            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            db.session.commit()
            self.logger.info(f"Обновлен {self.model.__name__} с ID {entity_id}")
            return entity
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Ошибка при обновлении {self.model.__name__} с ID {entity_id}: {e}")
            return None

    def delete(self, entity_id):
        """
        Удаление сущности

        Args:
            entity_id: ID сущности

        Returns:
            True if deleted, False otherwise
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                self.logger.warning(f"{self.model.__name__} с ID {entity_id} не найден")
                return False

            db.session.delete(entity)
            db.session.commit()
            self.logger.info(f"Удален {self.model.__name__} с ID {entity_id}")
            return True
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Ошибка при удалении {self.model.__name__} с ID {entity_id}: {e}")
            return False

    def count(self):
        """
        Подсчет количества сущностей

        Returns:
            Count of entities
        """
        try:
            return self.model.query.count()
        except Exception as e:
            self.logger.error(f"Ошибка при подсчете {self.model.__name__}: {e}")
            return 0
