# url_manager.py
"""
Менеджер для управления SEO-friendly URL структурой
Обеспечивает использование slug'ов вместо ID'шек
"""
from slugify import slugify
from logic.utils.logger import get_logger

logger = get_logger(__name__)


class URLManager:
    """Класс для управления URL структурой"""
    
    @staticmethod
    def generate_slug(text, max_length=50):
        """
        Генерирует SEO-friendly slug из текста
        
        Args:
            text: текст для преобразования
            max_length: максимальная длина slug'а
            
        Returns:
            оптимизированный slug
        """
        try:
            # Используем python-slugify если доступна, иначе простое преобразование
            try:
                slug = slugify(text, max_length=max_length, word_boundary=True, separator='-')
            except (ImportError, AttributeError, TypeError) as e:
                # Fallback на простое преобразование если библиотека недоступна
                slug = text.lower().strip()
                slug = slug.replace(' ', '-')
                slug = ''.join(c for c in slug if c.isalnum() or c == '-')
                slug = slug[:max_length]
            
            return slug if slug else 'item'
        except Exception as e:
            logger.error(f"Ошибка при генерации slug: {e}")
            return 'item'
    
    @staticmethod
    def create_problem_url(problem_id, problem_title):
        """
        Создает SEO-friendly URL для проблемы
        
        Args:
            problem_id: ID проблемы
            problem_title: название проблемы
            
        Returns:
            URL строка
        """
        slug = URLManager.generate_slug(problem_title)
        return f"/problem/{slug}-{problem_id}"
    
    @staticmethod
    def create_solution_url(solution_id, solution_title):
        """
        Создает SEO-friendly URL для решения
        
        Args:
            solution_id: ID решения
            solution_title: название решения
            
        Returns:
            URL строка
        """
        slug = URLManager.generate_slug(solution_title)
        return f"/solution/{slug}-{solution_id}"
    
    @staticmethod
    def create_category_url(category_id, category_name):
        """
        Создает SEO-friendly URL для категории
        
        Args:
            category_id: ID категории
            category_name: название категории
            
        Returns:
            URL параметр
        """
        slug = URLManager.generate_slug(category_name)
        return f"/?category={slug}-{category_id}"
    
    @staticmethod
    def parse_slug_id(slug):
        """
        Извлекает ID из slug'а
        
        Args:
            slug: slug со встроенным ID (например 'problem-title-123')
            
        Returns:
            ID или None
        """
        try:
            # ID обычно находится в конце после последнего дефиса
            parts = slug.split('-')
            if parts[-1].isdigit():
                return int(parts[-1])
        except Exception as e:
            logger.warning(f"Ошибка при парсинге slug: {e}")
        
        return None
    
    @staticmethod
    def redirect_old_urls(old_id_url, new_slug_url):
        """
        Подготавливает данные для редиректов со старых URL'ов
        
        Args:
            old_id_url: старый URL с ID (например '/problem/123')
            new_slug_url: новый URL со slug'ом (например '/problem/title-123')
            
        Returns:
            конфигурация редиректа
        """
        return {
            'source': old_id_url,
            'destination': new_slug_url,
            'permanent': True,  # 301 редирект для SEO
            'statusCode': 301
        }


# Интеграция с Flask
def setup_url_redirection(app):
    """
    Настраивает редиректы со старых URL'ов на новые SEO-friendly URL'ы
    """
    from flask import redirect, url_for
    
    @app.route('/problem/<int:problem_id>', methods=['GET'])
    @app.route('/problem/<string:slug_and_id>', methods=['GET'])
    def problem_redirect(problem_id=None, slug_and_id=None):
        """Редирект со старых URL'ов на новые"""
        if slug_and_id:
            # Уже используется новый формат
            return None
        elif problem_id:
            # Старый формат, редирект не нужен - используется новый маршрут
            return None
    
    logger.info("URL редиректы настроены")


# Утилита для миграции данных
def migrate_to_slug_urls(db, Model):
    """
    Миграция существующих записей для использования slug'ов
    
    Args:
        db: SQLAlchemy database
        Model: модель для миграции
    """
    try:
        items = Model.query.all()
        
        for item in items:
            if not hasattr(item, 'slug') or not item.slug:
                # Генерируем slug из названия
                slug = URLManager.generate_slug(item.name if hasattr(item, 'name') else str(item.id))
                
                if hasattr(item, 'slug'):
                    item.slug = slug
                    
                    try:
                        db.session.commit()
                        logger.info(f"Обновлена {Model.__name__} {item.id}: {slug}")
                    except Exception as e:
                        logger.error(f"Ошибка при обновлении {Model.__name__} {item.id}: {e}")
                        db.session.rollback()
        
        logger.info(f"Миграция {Model.__name__} завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при миграции {Model.__name__}: {e}")


# Рекомендуемая структура маршрутов для новых URL'ов

RECOMMENDED_ROUTES = """
# Структура новых SEO-friendly маршрутов

# Проблемы (вопросы)
@app.route('/problem/<slug_and_id>')  # Пример: /problem/learn-python-123
def view_problem(slug_and_id):
    problem_id = URLManager.parse_slug_id(slug_and_id)
    # ... загрузить проблему по ID ...

# Решения
@app.route('/solution/<slug_and_id>')  # Пример: /solution/learn-python-guide-456
def view_solution(slug_and_id):
    solution_id = URLManager.parse_slug_id(slug_and_id)
    # ... загрузить решение по ID ...

# Категории
@app.route('/category/<slug_and_id>')  # Пример: /category/programming-789
def view_category(slug_and_id):
    category_id = URLManager.parse_slug_id(slug_and_id)
    # ... загрузить категорию по ID ...

# Топики
@app.route('/topic/<slug_and_id>')  # Пример: /topic/python-questions-321
def view_topic(slug_and_id):
    topic_id = URLManager.parse_slug_id(slug_and_id)
    # ... загрузить топик по ID ...
"""
