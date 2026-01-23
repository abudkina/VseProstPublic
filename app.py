"""Main Flask application entry point"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_talisman import Talisman
import os

from config import get_config
from logic.model import db
from logic.utils.logger import setup_logger
from logic.utils.rate_limiter import init_limiter
from logic.database import init_database, create_directories

# Импорт blueprint'ов
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
from logic.image_proxy import image_proxy_bp
from logic.password_reset import password_reset_bp
from logic.image_generation import image_generation_bp


def create_app(config=None):
    """
    Application factory pattern

    Args:
        config: Configuration object (optional)

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Загружаем конфигурацию
    if config is None:
        config = get_config()
    app.config.from_object(config)

    # Настраиваем логгирование
    setup_logger(app)
    app.logger.info("Запуск приложения VseProst")

    # Настройка CORS
    CORS(app,
         origins=app.config['CORS_ORIGINS'],
         methods=app.config['CORS_METHODS'],
         allow_headers=app.config['CORS_ALLOW_HEADERS'],
         supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'])

    # Инициализация безопасности
    _init_security(app)

    # Инициализация базы данных
    db.init_app(app)

    # Регистрация blueprint'ов
    _register_blueprints(app)

    # Регистрация маршрутов для статических файлов
    _register_static_routes(app)

    # Регистрация обработчиков ошибок
    _register_error_handlers(app)

    return app


def _init_security(app):
    """Инициализация модулей безопасности"""

    # Rate Limiting
    limiter = init_limiter(app)
    app.limiter = limiter

    # Security Headers (только для production)
    if app.config['ENV'] == 'production':
        # Content Security Policy
        csp = {
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'"],  # Временно unsafe-inline, потом убрать
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ['*', 'data:', 'blob:'],
            'font-src': ["'self'", 'data:'],
            'connect-src': ["'self'"],
        }

        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,  # 1 год
            content_security_policy=csp,
            content_security_policy_nonce_in=['script-src'],
            referrer_policy='strict-origin-when-cross-origin',
            feature_policy={
                'geolocation': "'none'",
                'microphone': "'none'",
                'camera': "'none'",
            }
        )
        app.logger.info("Security headers (Talisman) активированы для production")
    else:
        app.logger.info("Security headers отключены для development (включите для production)")

    app.logger.info("Модули безопасности инициализированы")


def _register_blueprints(app):
    """Регистрация всех blueprint'ов приложения"""
    blueprints = [
        auth_bp,
        category_bp,
        solution_bp,
        comment_solution_bp,
        hashtag_bp,
        problem_bp,
        topic_bp,
        notification_bp,
        user_bp,
        registration_bp,
        temporary_link_problem_bp,
        temporary_link_solution_bp,
        temporary_problem_solution_bp,
        cart_bp,
        image_proxy_bp,
        password_reset_bp,
        image_generation_bp
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    app.logger.info(f"Зарегистрировано {len(blueprints)} blueprints")


def _register_static_routes(app):
    """Регистрация маршрутов для статических файлов"""

    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        """Обработка OPTIONS запросов для CORS"""
        return '', 200

    @app.route('/')
    def index():
        """Отображение главной страницы"""
        if os.path.exists('html/index.html'):
            return send_from_directory('html', 'index.html')
        elif os.path.exists('static/index.html'):
            return send_from_directory('static', 'index.html')
        else:
            return "Файл index.html не найден. Создайте папку html/ или static/ с файлом index.html", 404

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Обслуживание CSS файлов"""
        return send_from_directory('css', filename)

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Обслуживание JS файлов"""
        return send_from_directory('js', filename)

    @app.route('/assets/<path:filename>')
    def serve_assets(filename):
        """Обслуживание файлов из assets"""
        try:
            # Определяем корневую директорию проекта
            # app.py находится в корне проекта
            project_root = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(project_root, 'assets')
            
            # Проверяем существование директории
            if not os.path.exists(assets_dir):
                app.logger.warning(f"Assets directory not found at {assets_dir}, trying relative path")
                assets_dir = 'assets'
            
            # Проверяем существование файла
            file_path = os.path.join(assets_dir, filename)
            if not os.path.exists(file_path):
                app.logger.warning(f"Asset file not found: {file_path}")
                return f"Файл {filename} не найден", 404
            
            return send_from_directory(assets_dir, filename)
        except FileNotFoundError:
            app.logger.warning(f"Asset file not found: {filename}")
            return f"Файл {filename} не найден в папке assets", 404
        except Exception as e:
            app.logger.error(f"Ошибка при обслуживании файла {filename}: {e}", exc_info=True)
            return f"Ошибка при загрузке файла {filename}", 500

    @app.route('/fonts/<path:filename>')
    def serve_fonts(filename):
        """Обслуживание шрифтов"""
        return send_from_directory('fonts', filename)

    @app.route('/html/<path:filename>')
    def serve_html(filename):
        """Обслуживание HTML страниц из папки html"""
        try:
            return send_from_directory('html', filename)
        except FileNotFoundError:
            return f"Файл {filename} не найден в папке html", 404

    @app.route('/html/')
    def html_index():
        """Перенаправление на главную страницу"""
        return send_from_directory('html', 'index.html')

    @app.route('/robots.txt')
    def robots_txt():
        """Обслуживание robots.txt"""
        return send_from_directory('.', 'robots.txt', mimetype='text/plain')

    @app.route('/sitemap.xml')
    def sitemap_xml():
        """Генерация sitemap.xml"""
        from flask import Response, request
        from datetime import datetime
        from logic.model import Problem, Solution
        
        try:
            # Используем request.url_root для более точного определения базового URL
            base_url = request.url_root.rstrip('/')
            # Если не удалось получить из request, используем конфигурацию
            if not base_url or base_url == '/':
                base_url = app.config.get('FRONTEND_URL', 'http://127.0.0.1:8080').rstrip('/')
            
            # Получаем только опубликованные проблемы и решения (show=True или show не None)
            problems = Problem.query.filter(
                Problem.id.isnot(None),
                Problem.show.isnot(None)
            ).order_by(Problem.modified_date.desc().nulls_last(), Problem.created_date.desc()).limit(50000).all()
            
            solutions = Solution.query.filter(
                Solution.id.isnot(None),
                Solution.show.isnot(None)
            ).order_by(Solution.modified_date.desc().nulls_last(), Solution.created_date.desc()).limit(50000).all()
            
            sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
            sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
            
            # Текущая дата для статических страниц
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Главная страница
            sitemap.append('  <url>')
            sitemap.append(f'    <loc>{base_url}/</loc>')
            sitemap.append(f'    <lastmod>{today}</lastmod>')
            sitemap.append('    <changefreq>daily</changefreq>')
            sitemap.append('    <priority>1.0</priority>')
            sitemap.append('  </url>')
            
            # Статические страницы (исключаем favourites, cart, notifications, profile - они личные)
            static_pages = [
                ('/html/solutions.html', 'daily', '0.9'),
            ]
            
            for path, changefreq, priority in static_pages:
                sitemap.append('  <url>')
                sitemap.append(f'    <loc>{base_url}{path}</loc>')
                sitemap.append(f'    <lastmod>{today}</lastmod>')
                sitemap.append(f'    <changefreq>{changefreq}</changefreq>')
                sitemap.append(f'    <priority>{priority}</priority>')
                sitemap.append('  </url>')
            
            # Проблемы (используем id или problemId в зависимости от того, что поддерживается)
            for problem in problems:
                sitemap.append('  <url>')
                # Поддерживаем оба варианта параметров для совместимости
                sitemap.append(f'    <loc>{base_url}/html/problem.html?id={problem.id}</loc>')
                if problem.modified_date:
                    sitemap.append(f'    <lastmod>{problem.modified_date.strftime("%Y-%m-%d")}</lastmod>')
                elif problem.created_date:
                    sitemap.append(f'    <lastmod>{problem.created_date.strftime("%Y-%m-%d")}</lastmod>')
                else:
                    sitemap.append(f'    <lastmod>{today}</lastmod>')
                sitemap.append('    <changefreq>weekly</changefreq>')
                sitemap.append('    <priority>0.8</priority>')
                sitemap.append('  </url>')
            
            # Решения (используем solutionId согласно коду в solution.js)
            for solution in solutions:
                sitemap.append('  <url>')
                sitemap.append(f'    <loc>{base_url}/html/solution.html?solutionId={solution.id}</loc>')
                if solution.modified_date:
                    sitemap.append(f'    <lastmod>{solution.modified_date.strftime("%Y-%m-%d")}</lastmod>')
                elif solution.created_date:
                    sitemap.append(f'    <lastmod>{solution.created_date.strftime("%Y-%m-%d")}</lastmod>')
                else:
                    sitemap.append(f'    <lastmod>{today}</lastmod>')
                sitemap.append('    <changefreq>weekly</changefreq>')
                sitemap.append('    <priority>0.8</priority>')
                sitemap.append('  </url>')
            
            sitemap.append('</urlset>')
            
            return Response('\n'.join(sitemap), mimetype='application/xml; charset=utf-8')
        except Exception as e:
            app.logger.error(f"Ошибка при генерации sitemap: {e}", exc_info=True)
            # Возвращаем минимальный sitemap в случае ошибки
            try:
                from flask import request
                base_url = request.url_root.rstrip('/')
                if not base_url or base_url == '/':
                    base_url = app.config.get('FRONTEND_URL', 'http://127.0.0.1:8080').rstrip('/')
            except:
                base_url = app.config.get('FRONTEND_URL', 'http://127.0.0.1:8080').rstrip('/')
            
            today = datetime.now().strftime('%Y-%m-%d')
            minimal_sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''
            return Response(minimal_sitemap, mimetype='application/xml; charset=utf-8')


def _register_error_handlers(app):
    """Регистрация обработчиков ошибок"""

    @app.errorhandler(404)
    def not_found_error(error):
        """Обработка ошибки 404"""
        from flask import request
        # Игнорируем стандартные запросы браузеров и инструментов разработчика
        ignored_paths = [
            '/.well-known/',
            '/favicon.ico',
            '/robots.txt',
            '/apple-touch-icon',
            '/sitemap.xml'
        ]
        
        # Логируем только реальные ошибки, не служебные запросы
        if not any(request.path.startswith(path) for path in ignored_paths):
            app.logger.warning(f"404 ошибка: {request.method} {request.path} - {error}")
        
        return {"error": "Ресурс не найден"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Обработка ошибки 500"""
        app.logger.error(f"500 ошибка: {error}", exc_info=True)
        db.session.rollback()
        return {"error": "Внутренняя ошибка сервера"}, 500

    @app.errorhandler(429)
    def rate_limit_error(error):
        """Обработка ошибки 429 (Rate Limit Exceeded)"""
        from flask import request
        from flask_limiter.errors import RateLimitExceeded
        if isinstance(error, RateLimitExceeded):
            message = error.description or "Слишком много запросов. Пожалуйста, попробуйте позже."
        else:
            message = "Слишком много запросов. Пожалуйста, попробуйте позже."
        
        app.logger.warning(f"429 Rate Limit: {request.method} {request.path} - {message}")
        return {"error": message}, 429

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Обработка всех необработанных исключений"""
        # Пропускаем RateLimitExceeded, так как у него есть отдельный обработчик
        from flask_limiter.errors import RateLimitExceeded
        if isinstance(error, RateLimitExceeded):
            raise  # Позволяем Flask-Limiter обработать это через errorhandler(429)
        
        app.logger.error(f"Необработанное исключение: {error}", exc_info=True)
        db.session.rollback()
        return {"error": "Внутренняя ошибка сервера"}, 500


# Создаем приложение
app = create_app()


if __name__ == '__main__':
    with app.app_context():
        # Создаем необходимые директории
        create_directories()

        # Инициализируем базу данных
        init_database(db, app)

    # Запуск сервера
    port = int(os.getenv('PORT', 8080))
    app.logger.info(f"🚀 Сервер запущен в режиме {app.config['ENV']} на порту {port}")
    app.logger.info(f"🌐 CORS разрешено для: {app.config['CORS_ORIGINS']}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
