# -*- coding: utf-8 -*-
"""
WSGI entry point for Beget hosting (Passenger)
"""
import os
import sys

# Путь к директории проекта - ЗАМЕНИТЕ на ваш путь!
# Формат: /home/ПЕРВАЯ_БУКВА_ЛОГИНА/ЛОГИН/ИМЯ_САЙТА
PROJECT_DIR = '/home/v/vseprost/vseprost.beget.tech'

# Путь к виртуальному окружению - ЗАМЕНИТЕ на ваш путь!
# Формат: /home/ПЕРВАЯ_БУКВА_ЛОГИНА/ЛОГИН/ИМЯ_САЙТА/venv/lib/pythonX.X/site-packages
VENV_PACKAGES = '/home/v/vseprost/vseprost.beget.tech/venv/lib/python3.10/site-packages'

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
