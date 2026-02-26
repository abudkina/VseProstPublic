import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


def get_env_variable(name, default=''):
    """Получение строковой переменной окружения"""
    return os.getenv(name, default)


def get_env_int(name, default=0):
    """Получение целочисленной переменной окружения"""
    try:
        return int(os.getenv(name, default))
    except (ValueError, TypeError):
        return default


def get_env_bool(name, default=False):
    """Получение булевой переменной окружения"""
    value = os.getenv(name, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


class Config:
    """Базовый класс конфигурации"""
    # SECURITY: JWT_SECRET обязателен для production
    SECRET_KEY = os.getenv('JWT_SECRET')
    if not SECRET_KEY:
        raise ValueError("CRITICAL: JWT_SECRET environment variable must be set")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB

    # Настройки CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://127.0.0.1:8080').split(',')
    CORS_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-CSRF-Token']
    CORS_SUPPORTS_CREDENTIALS = True

    # Настройки JWT (в секундах)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 часа
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 дней

    # Настройки OpenAI API для генерации изображений
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_API_URL = os.getenv('OPENAI_API_URL', 'https://api.proxyapi.ru/openai/v1')
    OPENAI_API_URL2 = os.getenv('OPENAI_API_URL2', 'https://api.proxyapi.ru/openrouter/v1')  # DeepSeek

    # Настройки Yandex Object Storage
    YANDEX_STORAGE_ACCESS_KEY = os.getenv('YANDEX_STORAGE_ACCESS_KEY')
    YANDEX_STORAGE_SECRET_KEY = os.getenv('YANDEX_STORAGE_SECRET_KEY')
    YANDEX_STORAGE_ENDPOINT = os.getenv('YANDEX_STORAGE_ENDPOINT', 'https://storage.yandexcloud.net')
    YANDEX_STORAGE_BUCKET = os.getenv('YANDEX_STORAGE_BUCKET')
    
    # Mail Configuration (Yandex SMTP)
    MAIL_SERVER = get_env_variable('MAIL_SERVER', 'smtp.yandex.ru')
    MAIL_PORT = get_env_int('MAIL_PORT', 465)
    MAIL_USE_TLS = get_env_bool('MAIL_USE_TLS', False)
    MAIL_USE_SSL = get_env_bool('MAIL_USE_SSL', True)
    MAIL_USERNAME = get_env_variable('MAIL_USERNAME', '')
    MAIL_PASSWORD = get_env_variable('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = get_env_variable('MAIL_DEFAULT_SENDER', '')
    MAIL_DEBUG = get_env_bool('MAIL_DEBUG', False)
    
    # Password Reset Settings
    PASSWORD_RESET_TOKEN_EXPIRES = get_env_int('PASSWORD_RESET_TOKEN_EXPIRES', 3600)  # 1 час
    FRONTEND_URL = get_env_variable('FRONTEND_URL', 'http://127.0.0.1:8080')
    
    # SEO Settings
    BASE_URL = get_env_variable('BASE_URL', 'https://vseprost.com')  # Основной URL сайта для SEO
    
    # Google Settings
    GOOGLE_ANALYTICS_ID = get_env_variable('GOOGLE_ANALYTICS_ID', '')  # Google Analytics 4 ID (G-XXXXXXXXXX)
    GOOGLE_TAG_MANAGER_ID = get_env_variable('GOOGLE_TAG_MANAGER_ID', '')  # Google Tag Manager ID (GTM-XXXXXXX)
    GOOGLE_VERIFICATION_CODE = get_env_variable('GOOGLE_VERIFICATION_CODE', '')  # Код верификации Search Console
    
    # Yandex Settings
    YANDEX_METRIKA_ID = get_env_variable('YANDEX_METRIKA_ID', '106548955')  # Яндекс.Метрика ID
    YANDEX_VERIFICATION = get_env_variable('YANDEX_VERIFICATION', '')  # Код верификации Яндекс.Вебмастер
    YANDEX_VERIFICATION_CODE = get_env_variable('YANDEX_VERIFICATION_CODE', '')  # Код для файла верификации

    # YooKassa (ЮKassa) payment
    YOOKASSA_SHOP_ID = get_env_variable('YOOKASSA_SHOP_ID', '')
    YOOKASSA_SECRET_KEY = get_env_variable('YOOKASSA_SECRET_KEY', '')
    YOOKASSA_RETURN_URL = get_env_variable('YOOKASSA_RETURN_URL', '')

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    ENV = 'development'

    # SECURITY: Для разработки можно использовать дефолты, но в .env они должны быть установлены
    SECRET_KEY = os.getenv('JWT_SECRET', 'dev-secret-key-CHANGE-IN-PRODUCTION')

    # MySQL конфигурация для разработки
    DB_HOST = os.getenv('DEV_DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DEV_DB_PORT', 3306))
    DB_USER = os.getenv('DEV_DB_USER', 'root')
    DB_PASSWORD = os.getenv('DEV_DB_PASSWORD')
    # Проверяем только если не в режиме тестирования
    if not DB_PASSWORD and os.getenv('FLASK_ENV') != 'testing':
        raise ValueError("DEV_DB_PASSWORD must be set in .env file")
    DB_NAME = os.getenv('DEV_DB_NAME', 'vseprost')
    USE_SSL = os.getenv('DB_USE_SSL', 'false').lower() == 'false'
    
    # SQLAlchemy URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    
    # Правильные ENGINE_OPTIONS для SSL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # Добавляем SSL параметры только если нужно
    if USE_SSL:
        # Собираем SSL параметры в словарь, только если они указаны
        ssl_args = {}
        
        ssl_ca = os.getenv('DB_SSL_CA')
        ssl_cert = os.getenv('DB_SSL_CERT')
        ssl_key = os.getenv('DB_SSL_KEY')
        
        if ssl_ca:
            ssl_args['ca'] = ssl_ca
        if ssl_cert:
            ssl_args['cert'] = ssl_cert
        if ssl_key:
            ssl_args['key'] = ssl_key
        
        # Если указаны какие-либо SSL параметры, добавляем их
        if ssl_args:
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'ssl': ssl_args}
    else:
        # Для отключения SSL явно
        SQLALCHEMY_DATABASE_URI += "&ssl_disabled=true"
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'ssl_disabled': True}

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    ENV = 'production'

    # MySQL конфигурация для продакшена
    DB_HOST = os.getenv('DB_HOST')
    # Проверяем только если не в режиме тестирования
    if not DB_HOST and os.getenv('FLASK_ENV') != 'testing':
        raise ValueError("DB_HOST must be set in production")
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER')
    if not DB_USER and os.getenv('FLASK_ENV') != 'testing':
        raise ValueError("DB_USER must be set in production")
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    if not DB_PASSWORD and os.getenv('FLASK_ENV') != 'testing':
        raise ValueError("DB_PASSWORD must be set in production")
    DB_NAME = os.getenv('DB_NAME', 'vseprost')
    USE_SSL = os.getenv('DB_USE_SSL', 'true').lower() == 'true'
    
    # SQLAlchemy URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )
    
    # ENGINE_OPTIONS
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'connect_timeout': 30
    }
    
    # Обработка SSL для продакшена
    if USE_SSL:
        ssl_args = {}
        
        ssl_ca = os.getenv('DB_SSL_CA')
        ssl_cert = os.getenv('DB_SSL_CERT')
        ssl_key = os.getenv('DB_SSL_KEY')
        
        if ssl_ca:
            ssl_args['ca'] = ssl_ca
        if ssl_cert:
            ssl_args['cert'] = ssl_cert
        if ssl_key:
            ssl_args['key'] = ssl_key
        
        if ssl_args:
            SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'ssl': ssl_args}
    else:
        SQLALCHEMY_DATABASE_URI += "&ssl_disabled=true"
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'ssl_disabled': True}

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DEBUG = True
    
    # SQLite для тестов (или тестовая MySQL БД)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    SQLALCHEMY_ENGINE_OPTIONS = {}


# Словарь конфигураций для удобного доступа
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Функция для получения текущей конфигурации"""
    env = os.getenv('FLASK_ENV', 'development')
    return config_dict.get(env, DevelopmentConfig)