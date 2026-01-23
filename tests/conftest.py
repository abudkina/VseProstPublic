"""
Конфигурация для pytest тестов
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash

# ВАЖНО: Устанавливаем переменные окружения ДО импорта любых модулей
os.environ['FLASK_ENV'] = 'testing'
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing-only'

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.model import db, User, Category, Problem, Solution, Hashtag, Topic, RefreshToken
from config import TestingConfig

# Константы для тестов
TEST_JWT_SECRET = 'test-secret-key-for-testing-only'
TEST_PASSWORD = 'testpassword123'
TEST_USERNAME = 'testuser'
TEST_EMAIL = 'test@example.com'
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'adminpassword123'

@pytest.fixture(scope='function')
def test_app():
    """Создает тестовое приложение Flask"""
    # Устанавливаем переменную окружения перед импортом
    os.environ['FLASK_ENV'] = 'testing'
    
    # Пересоздаем приложение с тестовой конфигурацией
    from flask import Flask
    from flask_cors import CORS
    from logic.model import db
    
    test_app = Flask(__name__)
    test_app.config.from_object(TestingConfig)
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    # Настройка CORS
    CORS(test_app,
         origins=test_app.config.get('CORS_ORIGINS', ['http://127.0.0.1:8080']),
         methods=test_app.config.get('CORS_METHODS', ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH']),
         allow_headers=test_app.config.get('CORS_ALLOW_HEADERS', ['Content-Type', 'Authorization']),
         supports_credentials=test_app.config.get('CORS_SUPPORTS_CREDENTIALS', True))
    
    # Инициализация базы данных
    db.init_app(test_app)
    
    # Регистрация blueprint'ов
    from logic.authorization import auth_bp
    from logic.category import category_bp
    from logic.solution import solution_bp
    from logic.commentSolution import comment_solution_bp
    from logic.hashtag import hashtag_bp
    from logic.notification import notification_bp
    from logic.problem import problem_bp
    from logic.topic import topic_bp
    from logic.user import user_bp
    from logic.registration import registration_bp
    from logic.temporaryLinkProblem import temporary_link_problem_bp
    from logic.temporaryLinkSolution import temporary_link_solution_bp
    from logic.temporaryProblemSolution import temporary_problem_solution_bp
    from logic.cart import cart_bp
    
    test_app.register_blueprint(auth_bp)
    test_app.register_blueprint(category_bp)
    test_app.register_blueprint(solution_bp)
    test_app.register_blueprint(comment_solution_bp)
    test_app.register_blueprint(hashtag_bp)
    test_app.register_blueprint(problem_bp)
    test_app.register_blueprint(topic_bp)
    test_app.register_blueprint(notification_bp)
    test_app.register_blueprint(user_bp)
    test_app.register_blueprint(registration_bp)
    test_app.register_blueprint(temporary_link_problem_bp)
    test_app.register_blueprint(temporary_link_solution_bp)
    test_app.register_blueprint(temporary_problem_solution_bp)
    test_app.register_blueprint(cart_bp)
    
    with test_app.app_context():
        # Создаем все таблицы
        db.create_all()
        yield test_app
        # Очищаем после тестов
        db.session.remove()
        # Для SQLite просто удаляем все таблицы
        # Для MySQL нужно отключить проверку внешних ключей
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
                conn.commit()
        except:
            pass
        db.drop_all()
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
                conn.commit()
        except:
            pass

@pytest.fixture(scope='function')
def client(test_app):
    """Создает тестовый клиент Flask"""
    return test_app.test_client()

@pytest.fixture(scope='function')
def db_session(test_app):
    """Создает сессию базы данных для тестов"""
    with test_app.app_context():
        yield db.session
        db.session.rollback()

@pytest.fixture
def test_user(db_session):
    """Создает тестового пользователя"""
    user = User(
        username=TEST_USERNAME,
        email=TEST_EMAIL,
        password_hash=generate_password_hash(TEST_PASSWORD),
        isactive=True,
        type=1,  # Обычный пользователь
        isnew=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_user(db_session):
    """Создает тестового администратора"""
    user = User(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password_hash=generate_password_hash(ADMIN_PASSWORD),
        isactive=True,
        type=2,  # Администратор
        isnew=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def _create_jwt_token(user: User) -> str:
    """Вспомогательная функция для создания JWT токена"""
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {
        'username': user.username,
        'userID': user.id,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm='HS256')

@pytest.fixture
def auth_token(test_user):
    """Создает JWT токен для тестового пользователя"""
    return _create_jwt_token(test_user)

@pytest.fixture
def admin_token(admin_user):
    """Создает JWT токен для администратора"""
    return _create_jwt_token(admin_user)

@pytest.fixture
def test_category(db_session, test_user):
    """Создает тестовую категорию"""
    category = Category(
        name='Test Category',
        creator=test_user.id,
        isnew=False
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category

@pytest.fixture
def test_topic(db_session, test_user):
    """Создает тестовую тему"""
    topic = Topic(
        name='Test Topic',
        creator=test_user.id,
        is_new=False
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)
    return topic

@pytest.fixture
def test_problem(db_session, test_user, test_category):
    """Создает тестовую проблему"""
    problem = Problem(
        name='Test Problem',
        describe='Test problem description',
        category=test_category.id,
        creator=test_user.id,
        image='test_image.png',
        isnew=False,
        show=0,
        favourite=0
    )
    db_session.add(problem)
    db_session.commit()
    db_session.refresh(problem)
    return problem

@pytest.fixture
def test_solution(db_session, test_user):
    """Создает тестовое решение"""
    solution = Solution(
        name='Test Solution',
        describe='Test solution description',
        creator=test_user.id,
        image='test_image.png',
        isnew=False,
        show=0,
        favourite=0,
        like=0,
        notlike=0,
        price=100.00
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    return solution

@pytest.fixture
def auth_headers(auth_token):
    """Возвращает заголовки с токеном авторизации"""
    return {'Authorization': f'Bearer {auth_token}'}

@pytest.fixture
def admin_headers(admin_token):
    """Возвращает заголовки с токеном администратора"""
    return {'Authorization': f'Bearer {admin_token}'}

