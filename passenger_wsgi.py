# -*- coding: utf-8 -*-
"""
WSGI entry point for Beget hosting (Passenger)

Конфигурация через переменные окружения:
- PROJECT_DIR: путь к директории проекта (формат: /home/ПЕРВАЯ_БУКВА_ЛОГИНА/ЛОГИН/ИМЯ_САЙТА)
- VENV_PACKAGES: путь к виртуальному окружению (формат: /home/ПЕРВАЯ_БУКВА_ЛОГИНА/ЛОГИН/ИМЯ_САЙТА/venv/lib/pythonX.X/site-packages)

Если переменные не установлены, используются значения по умолчанию.
"""
import os
import sys

# Используем переменные окружения с fallback на значения по умолчанию
PROJECT_DIR = os.environ.get(
    'PROJECT_DIR',
    '/home/v/vseprost/vseprost.beget.tech'
)

# Путь к виртуальному окружению
VENV_PACKAGES = os.environ.get(
    'VENV_PACKAGES',
    '/home/v/vseprost/vseprost.beget.tech/venv/lib/python3.10/site-packages'
)

# Добавляем пути в sys.path
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

if VENV_PACKAGES not in sys.path:
    sys.path.insert(1, VENV_PACKAGES)

# Устанавливаем переменные окружения
os.environ['FLASK_ENV'] = 'production'

# Загружаем .env файл если он существует
env_path = os.path.join(PROJECT_DIR, '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Импортируем приложение Flask
from app import app as application

# Опционально: включение режима отладки (ТОЛЬКО ДЛЯ РАЗРАБОТКИ!)
# from werkzeug.debug import DebuggedApplication
# application.wsgi_app = DebuggedApplication(application.wsgi_app, True)
# application.debug = True
