"""
Database optimization - Index creation script
Run this script to create optimized indexes for better query performance
"""

from logic.model import db
from sqlalchemy import text
from logic.utils.logger import get_logger

logger = get_logger(__name__)

def create_performance_indexes():
    """Создание индексов для оптимизации производительности БД"""
    
    with db.engine.connect() as connection:
        # Отключаем проверку внешних ключей временно
        connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        connection.commit()
        
        logger.info("Создание индексов БД...")
        
        indexes = [
            # Problem table indexes
            ("CREATE INDEX IF NOT EXISTS idx_problem_name ON problem(name);", 
             "Индекс на название проблемы"),
            ("CREATE INDEX IF NOT EXISTS idx_problem_category ON problem(category);", 
             "Индекс на категорию"),
            ("CREATE INDEX IF NOT EXISTS idx_problem_topic ON problem(topic);", 
             "Индекс на тему"),
            ("CREATE INDEX IF NOT EXISTS idx_problem_created_date ON problem(created_date DESC);", 
             "Индекс на дату создания (сортировка)"),
            
            # Solution table indexes
            ("CREATE INDEX IF NOT EXISTS idx_solution_problem_id ON solution(problem_id);", 
             "Индекс на problem_id в решениях"),
            ("CREATE INDEX IF NOT EXISTS idx_solution_user_id ON solution(user_id);", 
             "Индекс на user_id в решениях"),
            ("CREATE INDEX IF NOT EXISTS idx_solution_created_date ON solution(created_date DESC);", 
             "Индекс на дату создания решений"),
            
            # Hashtag-Problem junction
            ("CREATE INDEX IF NOT EXISTS idx_hashtag_problem_hashtag ON hashtag_problem(hashtag_id);", 
             "Индекс на hashtag_id в junction"),
            ("CREATE INDEX IF NOT EXISTS idx_hashtag_problem_problem ON hashtag_problem(problem_id);", 
             "Индекс на problem_id в junction"),
            ("CREATE INDEX IF NOT EXISTS idx_hashtag_problem_both ON hashtag_problem(hashtag_id, problem_id);", 
             "Составной индекс для поиска по тегам"),
            
            # User activity tracking
            ("CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity(user_id);", 
             "Индекс на user_id в активности"),
            ("CREATE INDEX IF NOT EXISTS idx_user_activity_date ON user_activity(created_date DESC);", 
             "Индекс на дату активности"),
            ("CREATE INDEX IF NOT EXISTS idx_user_activity_user_date ON user_activity(user_id, created_date DESC);", 
             "Составной индекс для истории пользователя"),
            
            # Favourites
            ("CREATE INDEX IF NOT EXISTS idx_favourite_problem_user ON favourite_problem(user_id);", 
             "Индекс на пользователя в избранных проблемах"),
            ("CREATE INDEX IF NOT EXISTS idx_favourite_solution_user ON favourite_solution(user_id);", 
             "Индекс на пользователя в избранных решениях"),
            
            # Comments
            ("CREATE INDEX IF NOT EXISTS idx_comment_solution_solution ON comment_solution(solution_id);", 
             "Индекс на solution_id в комментариях"),
            ("CREATE INDEX IF NOT EXISTS idx_comment_solution_user ON comment_solution(user_id);", 
             "Индекс на user_id в комментариях"),
            
            # User table
            ("CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);", 
             "Индекс на email для быстрого поиска пользователя"),
            
            # Embedding table (для рекомендаций)
            ("CREATE INDEX IF NOT EXISTS idx_embedding_user_object ON embedding(user_id, object_type, object_id);", 
             "Индекс для поиска эмбеддингов пользователя"),
        ]
        
        for sql, description in indexes:
            try:
                connection.execute(text(sql))
                connection.commit()
                logger.info(f"{description}")
            except Exception as e:
                logger.warning(f"{description} - {e}")
        
        # Включаем проверку внешних ключей обратно
        connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        connection.commit()
        
        logger.info("Индексы успешно созданы!")


def optimize_tables():
    """Оптимизация таблиц"""
    
    with db.engine.connect() as connection:
        logger.info("Оптимизация таблиц...")
        
        tables = [
            'problem', 'solution', 'user', 'hashtag', 'hashtag_problem',
            'user_activity', 'favourite_problem', 'favourite_solution',
            'comment_solution', 'embedding'
        ]
        
        for table in tables:
            try:
                connection.execute(text(f"OPTIMIZE TABLE {table}"))
                connection.commit()
                logger.info(f"Таблица {table} оптимизирована")
            except Exception as e:
                logger.warning(f"Таблица {table} - {e}")
        
        logger.info("Оптимизация завершена!")


def analyze_tables():
    """Анализ таблиц для обновления статистики"""
    
    with db.engine.connect() as connection:
        logger.info("Анализ таблиц...")
        
        tables = [
            'problem', 'solution', 'user', 'hashtag', 'hashtag_problem',
            'user_activity', 'favourite_problem', 'favourite_solution',
            'comment_solution', 'embedding'
        ]
        
        for table in tables:
            try:
                connection.execute(text(f"ANALYZE TABLE {table}"))
                connection.commit()
                logger.info(f"Таблица {table} проанализирована")
            except Exception as e:
                logger.warning(f"Таблица {table} - {e}")
        
        logger.info("Анализ завершен!")


if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        create_performance_indexes()
        optimize_tables()
        analyze_tables()
        
        logger.info("Все оптимизации БД завершены!")
