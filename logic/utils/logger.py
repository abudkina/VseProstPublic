"""Centralized logging configuration"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import os


def setup_logger(app=None):
    """
    Настройка централизованного логгирования для приложения

    Args:
        app: Flask application instance (optional)

    Returns:
        Logger instance
    """
    # Определяем уровень логгирования
    log_level = logging.DEBUG if (app and app.config.get('DEBUG')) else logging.INFO

    # Создаем директорию для логов
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # Формат логов
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Удаляем существующие обработчики
    root_logger.handlers.clear()

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Файловый обработчик с ротацией
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Отдельный файл для ошибок
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Настраиваем логгеры сторонних библиотек
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    if app:
        app.logger.setLevel(log_level)
        app.logger.info(f"Логгирование настроено. Уровень: {logging.getLevelName(log_level)}")

    return root_logger


def get_logger(name):
    """
    Получить логгер для конкретного модуля

    Args:
        name: Имя модуля

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
