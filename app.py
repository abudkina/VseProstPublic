"""Main Flask application entry point"""
from flask import Flask, send_from_directory, request, Response
from flask_cors import CORS
from flask_talisman import Talisman
import os
import re
import json
import html as html_module

from config import get_config
from logic.model import db
from logic.utils.logger import setup_logger
from logic.utils.file_utils import image_url_for_display
from logic.utils.rate_limiter import init_limiter
from logic.database import init_database, create_directories
from logic.performance_optimization import setup_performance_optimization

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
from logic.sitemap import sitemap_bp
from logic.feed import feed_bp
from logic.search_engines_optimization import search_engines_bp
# from logic.payment import payment_bp
# from logic.ai_routes import ai_bp
from logic.cache_config import invalidate_cache


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

    # Оптимизация производительности для SEO
    setup_performance_optimization(app)

    _register_cache_routes(app)

    # Предзагрузка модели рекомендаций в фоне (чтобы первый запрос не ждал ~7 сек)
    def _preload_recommendations_model():
        with app.app_context():
            try:
                from logic.recommendations import get_model
                get_model()
            except Exception:
                pass
    import threading
    t = threading.Thread(target=_preload_recommendations_model, daemon=True)
    t.start()

    return app


def _init_security(app):
    """Инициализация модулей безопасности"""

    # Rate Limiting
    limiter = init_limiter(app)
    app.limiter = limiter

    # Security Headers (только для production)
    if app.config['ENV'] == 'production':
        # Content Security Policy - исключаем unsafe-inline для безопасности
        csp = {
            'default-src': "'self'",
            'script-src': ["'self'"],  # Нет unsafe-inline - используем отдельные файлы
            'style-src': ["'self'"],   # Нет unsafe-inline - используем внешние CSS
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
        image_generation_bp,
        sitemap_bp,
        feed_bp,
        search_engines_bp,
        # payment_bp,
        # ai_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    app.logger.info(f"Зарегистрировано {len(blueprints)} blueprints")


def _register_cache_routes(app):
    """Маршрут для сброса кэша (после ручной очистки БД)."""
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        invalidate_cache()
        return json.dumps({'ok': True}), 200, {'Content-Type': 'application/json'}


def _register_static_routes(app):
    """Регистрация маршрутов для статических файлов"""
    def _resolve_favicon_path():
        """Возвращает путь к favicon (ICO или PNG) если найден"""
        project_root = os.path.dirname(os.path.abspath(__file__))
        favicon_ico = os.path.join(project_root, 'favicon.ico')
        if os.path.exists(favicon_ico):
            return favicon_ico
        candidates = [
            os.path.join(project_root, 'assets', 'images', 'Screenshot_4-ww78noDj9-transformed.png'),
            os.path.join(project_root, 'assets', 'images', 'logo1-Photoroom11.png'),
            os.path.join(project_root, 'assets', 'images', 'logo1-Photoroom1.png'),
            os.path.join(project_root, 'assets', 'images', 'logo1.jpg'),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return None

    def _resolve_icon_png(name):
        """Путь к PNG-иконке в корне (favicon-48x48.png, apple-touch-icon.png)"""
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        return path if os.path.exists(path) else None

    @app.route('/api/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        """Обработка OPTIONS запросов для CORS"""
        return '', 200

    @app.route('/')
    def index():
        """Отображение главной страницы с SEO-ссылками на проблемы"""
        try:
            index_path = os.path.join(project_root, 'html', 'index.html')
            if not os.path.exists(index_path):
                index_path = os.path.join(project_root, 'static', 'index.html')
                if not os.path.exists(index_path):
                    return "Файл index.html не найден. Создайте папку html/ или static/ с файлом index.html", 404

            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Inject SEO links block for all problems and solutions (visible and for crawlers)
            try:
                from logic.model import Problem, Solution

                problems = Problem.query.order_by(Problem.modified_date.desc()).limit(500).all()
                solutions = Solution.query.order_by(Solution.modified_date.desc()).limit(500).all()

                if problems or solutions:
                    # Генерируем блок с ссылками (будет виден для поисковиков)
                    seo_links_html = '''
                    <nav aria-label="Все проблемы и решения" style="position: absolute; left: -9999px; top: auto; width: 1px; height: 1px; overflow: hidden;">
                    '''

                    if problems:
                        seo_links_html += '<h2>Популярные проблемы</h2><ul>'
                        for p in problems:
                            # Генерируем slug
                            import re
                            slug = re.sub(r'[^\w\s-]', '', p.name.lower())
                            slug = re.sub(r'[-\s]+', '-', slug).strip('-')[:50]
                            url = f'/problem/{p.id}'
                            if slug:
                                url = f'/problem/{p.id}-{slug}'
                            seo_links_html += f'<li><a href="{url}">{html_module.escape(p.name)}</a></li>'
                        seo_links_html += '</ul>'

                    if solutions:
                        seo_links_html += '<h2>Популярные решения</h2><ul>'
                        for s in solutions:
                            # Генерируем slug
                            import re
                            slug = re.sub(r'[^\w\s-]', '', s.name.lower())
                            slug = re.sub(r'[-\s]+', '-', slug).strip('-')[:50]
                            url = f'/solution/{s.id}'
                            if slug:
                                url = f'/solution/{s.id}-{slug}'
                            seo_links_html += f'<li><a href="{url}">{html_module.escape(s.name)}</a></li>'
                        seo_links_html += '</ul>'

                    seo_links_html += '</nav>'

                    # Вставляем перед закрытием body
                    content = content.replace('</body>', seo_links_html + '\n</body>', 1)
            except Exception as e:
                app.logger.warning(f"Не удалось добавить SEO-ссылки на главную: {e}")

            return Response(content, mimetype='text/html; charset=utf-8')
        except Exception as e:
            app.logger.exception(f"Ошибка при отдаче index: {e}")
            return f"Ошибка загрузки страницы: {e}", 500

    project_root = os.path.dirname(os.path.abspath(__file__))

    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Обслуживание CSS файлов"""
        css_dir = os.path.join(project_root, 'css')
        return send_from_directory(css_dir, filename, mimetype='text/css')

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        """Обслуживание JS файлов"""
        js_dir = os.path.join(project_root, 'js')
        return send_from_directory(js_dir, filename)

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

    @app.route('/favicon.ico')
    def favicon():
        """Favicon для поисковых систем и браузеров"""
        icon_path = _resolve_favicon_path()
        if not icon_path:
            return "Favicon не найден", 404
        # Определяем MIME тип в зависимости от расширения файла
        if icon_path.endswith('.ico'):
            mimetype = 'image/x-icon'
        elif icon_path.endswith('.png'):
            mimetype = 'image/png'
        elif icon_path.endswith('.jpg') or icon_path.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        else:
            mimetype = 'image/png'
        return send_from_directory(
            os.path.dirname(icon_path),
            os.path.basename(icon_path),
            mimetype=mimetype
        )

    @app.route('/favicon-48x48.png')
    def favicon_png_48():
        """PNG 48x48 для поисковиков (Google/Yandex)"""
        icon_path = _resolve_icon_png('favicon-48x48.png')
        if not icon_path:
            return "Favicon 48x48 не найден. Запустите create_favicon.py", 404
        return send_from_directory(
            os.path.dirname(icon_path),
            os.path.basename(icon_path),
            mimetype='image/png'
        )

    @app.route('/apple-touch-icon.png')
    @app.route('/apple-touch-icon')
    def apple_touch_icon():
        """Иконка для iOS и соцсетей"""
        icon_path = _resolve_icon_png('apple-touch-icon.png')
        if not icon_path:
            icon_path = _resolve_favicon_path()
            if not icon_path:
                return "Favicon не найден", 404
        mimetype = 'image/png' if icon_path.endswith('.png') else 'image/x-icon'
        return send_from_directory(
            os.path.dirname(icon_path),
            os.path.basename(icon_path),
            mimetype=mimetype
        )

    @app.route('/fonts/<path:filename>')
    def serve_fonts(filename):
        """Обслуживание шрифтов"""
        return send_from_directory('fonts', filename)

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Обслуживание загруженных файлов (изображения проблем/решений)"""
        return send_from_directory('uploads', filename)

    def _render_page_with_seo(template_file, replacements):
        """
        Читает HTML-шаблон и подставляет SEO мета-теги из БД.
        replacements — dict с ключами: title, description, image, url, jsonld
        """
        template_path = os.path.join(project_root, 'html', template_file)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return None

        title = html_module.escape(replacements.get('title', ''))
        description = html_module.escape(replacements.get('description', ''))
        image = html_module.escape(replacements.get('image', ''))
        url = html_module.escape(replacements.get('url', ''))
        noscript_html = replacements.get('noscript_html', '')
        jsonld = replacements.get('jsonld', None)

        # Replace title
        content = re.sub(
            r'<title[^>]*>.*?</title>',
            f'<title id="page-title">{title}</title>',
            content, count=1
        )

        # Replace meta description
        content = re.sub(
            r'<meta\s+name="description"[^>]*/>',
            f'<meta name="description" id="page-description" content="{description}" />',
            content, count=1
        )

        # Replace canonical
        content = re.sub(
            r'<link\s+rel="canonical"[^>]*/>',
            f'<link rel="canonical" id="canonical-url" href="{url}" />',
            content, count=1
        )

        # Replace OG tags
        content = re.sub(r'<meta\s+property="og:title"[^>]*/>', f'<meta property="og:title" id="og-title" content="{title}" />', content, count=1)
        content = re.sub(r'<meta\s+property="og:description"[^>]*/>', f'<meta property="og:description" id="og-description" content="{description}" />', content, count=1)
        content = re.sub(r'<meta\s+property="og:image"[^>]*/>', f'<meta property="og:image" id="og-image" content="{image}" />', content, count=1)
        content = re.sub(r'<meta\s+property="og:url"[^>]*/>', f'<meta property="og:url" id="og-url" content="{url}" />', content, count=1)

        # Replace Twitter tags
        content = re.sub(r'<meta\s+name="twitter:title"[^>]*/>', f'<meta name="twitter:title" id="twitter-title" content="{title}" />', content, count=1)
        content = re.sub(r'<meta\s+name="twitter:description"[^>]*/>', f'<meta name="twitter:description" id="twitter-description" content="{description}" />', content, count=1)
        content = re.sub(r'<meta\s+name="twitter:image"[^>]*/>', f'<meta name="twitter:image" id="twitter-image" content="{image}" />', content, count=1)
        content = re.sub(r'<meta\s+name="twitter:url"[^>]*/>', f'<meta name="twitter:url" id="twitter-url" content="{url}" />', content, count=1)

        # Insert JSON-LD before </head>
        if jsonld:
            jsonld_script = f'<script type="application/ld+json">\n{json.dumps(jsonld, ensure_ascii=False, indent=2)}\n</script>\n'
            content = content.replace('</head>', jsonld_script + '</head>', 1)

        # Insert SSR content directly into solutionContainer (visible to crawlers!)
        # JS will replace this on load, but crawlers see full content
        ssr_content = replacements.get('ssr_content', '')
        if ssr_content:
            # Match both <div id="solutionContainer"></div> and <main ... id="solutionContainer">...</main>
            content = re.sub(
                r'(<(?:div|main)[^>]*id="solutionContainer"[^>]*>)(.*?)(</(?:div|main)>)',
                rf'\1{ssr_content}\3',
                content, count=1, flags=re.DOTALL
            )

        return Response(content, mimetype='text/html; charset=utf-8')

    # Новые красивые URL для проблем и решений (ЧПУ)
    @app.route('/problem/<int:problem_id>')
    @app.route('/problem/<int:problem_id>-<slug>')
    def problem_by_id(problem_id, slug=None):
        """Красивый URL для проблемы: /problem/123 или /problem/123-название"""
        from logic.model import Problem

        try:
            problem = Problem.query.get(int(problem_id))
        except (ValueError, TypeError):
            return "Проблема не найдена", 404

        if not problem:
            return "Проблема не найдена", 404

        base_url = app.config.get('BASE_URL', request.url_root.rstrip('/'))

        # Генерируем правильный slug из названия
        import re
        actual_slug = re.sub(r'[^\w\s-]', '', problem.name.lower())
        actual_slug = re.sub(r'[-\s]+', '-', actual_slug).strip('-')[:50]

        # Если slug в URL не совпадает с реальным, делаем 301 редирект
        if slug and slug != actual_slug:
            return app.redirect(f'/problem/{problem_id}-{actual_slug}', code=301)

        # Формируем canonical URL с правильным slug
        canonical_url = f'{base_url}/problem/{problem_id}'
        if actual_slug:
            canonical_url = f'{base_url}/problem/{problem_id}-{actual_slug}'

        # Оптимизируем title для поисковых запросов
        # Если название не начинается с вопросительного слова, добавляем контекст
        question_words = ['как', 'что', 'где', 'когда', 'почему', 'зачем', 'какой', 'какая', 'какие', 'чем', 'кто']
        title_for_seo = problem.name
        name_lower = problem.name.lower()

        # Проверяем начинается ли с вопросительного слова
        starts_with_question = any(name_lower.startswith(word) for word in question_words)

        if not starts_with_question:
            # Добавляем контекст для лучшего поиска
            if '?' in problem.name:
                title_for_seo = problem.name  # Уже вопрос с знаком
            else:
                # Добавляем "Как решить:" для проблем без вопросительного слова
                title_for_seo = f"{problem.name} - как решить?"

        desc_text = problem.describe or problem.name or ''
        # Улучшаем description для поиска
        if desc_text and len(desc_text) > 10:
            desc_text = desc_text[:200]
        else:
            # Создаем привлекательное description
            desc_text = f"{title_for_seo} ✓ Найдите лучшие решения и советы на Всё Прост. Реальные ответы от людей."[:160]

        image_url = image_url_for_display(problem.image, base_url, '/assets/images/Screenshot_4-ww78noDj9-transformed.png')

        solutions_count = len(problem.solutions) if problem.solutions else 0

        jsonld = {
            "@context": "https://schema.org",
            "@type": "Question",
            "name": title_for_seo,
            "text": desc_text,
            "headline": title_for_seo,
            "dateCreated": problem.created_date.isoformat() if problem.created_date else None,
            "dateModified": problem.modified_date.isoformat() if problem.modified_date else None,
            "answerCount": solutions_count,
            "upvoteCount": problem.favourite or 0,
            "image": image_url,
            "url": canonical_url
        }

        if problem.solutions:
            jsonld["suggestedAnswer"] = []
            for sol in problem.solutions[:5]:
                sol_slug = re.sub(r'[^\w\s-]', '', sol.name.lower())
                sol_slug = re.sub(r'[-\s]+', '-', sol_slug).strip('-')[:50]
                sol_url = f'{base_url}/solution/{sol.id}'
                if sol_slug:
                    sol_url = f'{base_url}/solution/{sol.id}-{sol_slug}'
                jsonld["suggestedAnswer"].append({
                    "@type": "Answer",
                    "text": sol.name,
                    "url": sol_url,
                    "upvoteCount": sol.favourite or 0
                })

        # Добавляем Breadcrumbs для SEO
        breadcrumb_jsonld = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Главная",
                    "item": base_url
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": problem.name,
                    "item": canonical_url
                }
            ]
        }

        # Комбинируем оба JSON-LD
        combined_jsonld = [jsonld, breadcrumb_jsonld]

        # Создаем полноценный HTML-контент для поисковиков
        # Вставляется прямо в solutionContainer — роботы видят весь текст
        # JS при загрузке заменит на динамический контент
        ssr_content = f'''
        <article class="ssr-content" itemscope itemtype="https://schema.org/Question">
            <h1 itemprop="name">{html_module.escape(problem.name)}</h1>
        '''

        if problem.describe:
            ssr_content += f'<div itemprop="text"><p>{html_module.escape(problem.describe)}</p></div>'

        if problem.solutions and len(problem.solutions) > 0:
            ssr_content += f'<section><h2>Решения ({len(problem.solutions)})</h2>'
            for sol in problem.solutions:
                sol_slug = re.sub(r'[^\w\s-]', '', sol.name.lower())
                sol_slug = re.sub(r'[-\s]+', '-', sol_slug).strip('-')[:50]
                sol_url = f'/solution/{sol.id}'
                if sol_slug:
                    sol_url = f'/solution/{sol.id}-{sol_slug}'

                ssr_content += f'<article><h3><a href="{sol_url}" itemprop="suggestedAnswer">{html_module.escape(sol.name)}</a></h3>'
                if sol.describe:
                    ssr_content += f'<p>{html_module.escape(sol.describe[:300])}</p>'
                ssr_content += '</article>'
            ssr_content += '</section>'

        ssr_content += '</article>'

        result = _render_page_with_seo('problem.html', {
            'title': f'{problem.name} - Всё Прост',
            'description': desc_text,
            'image': image_url,
            'url': canonical_url,
            'jsonld': combined_jsonld,
            'ssr_content': ssr_content
        })
        return result if result else send_from_directory('html', 'problem.html')

    @app.route('/solution/<int:solution_id>')
    @app.route('/solution/<int:solution_id>-<slug>')
    def solution_by_id(solution_id, slug=None):
        """Красивый URL для решения: /solution/123 или /solution/123-название"""
        from logic.model import Solution

        try:
            solution = db.session.get(Solution, int(solution_id))
        except (ValueError, TypeError):
            return "Решение не найдено", 404

        if not solution:
            return "Решение не найдено", 404

        base_url = app.config.get('BASE_URL', request.url_root.rstrip('/'))

        # Генерируем правильный slug из названия
        import re
        actual_slug = re.sub(r'[^\w\s-]', '', solution.name.lower())
        actual_slug = re.sub(r'[-\s]+', '-', actual_slug).strip('-')[:50]

        # Если slug в URL не совпадает с реальным, делаем 301 редирект
        if slug and slug != actual_slug:
            return app.redirect(f'/solution/{solution_id}-{actual_slug}', code=301)

        # Формируем canonical URL с правильным slug
        canonical_url = f'{base_url}/solution/{solution_id}'
        if actual_slug:
            canonical_url = f'{base_url}/solution/{solution_id}-{actual_slug}'

        desc_text = (solution.describe or solution.name or '')[:200]
        image_url = image_url_for_display(solution.image, base_url, '/assets/images/Screenshot_4-ww78noDj9-transformed.png')

        jsonld = {
            "@context": "https://schema.org",
            "@type": "Answer",
            "name": solution.name,
            "text": solution.describe or solution.name,
            "dateCreated": solution.created_date.isoformat() if solution.created_date else None,
            "dateModified": solution.modified_date.isoformat() if solution.modified_date else None,
            "upvoteCount": solution.favourite or 0,
            "image": image_url,
            "url": canonical_url
        }

        if solution.rating:
            jsonld["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": solution.rating,
                "ratingCount": max(solution.like + solution.notlike, 1)
            }

        # Добавляем Breadcrumbs для SEO
        breadcrumb_jsonld = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Главная",
                    "item": base_url
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Решения",
                    "item": f"{base_url}/html/solutions.html"
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": solution.name,
                    "item": canonical_url
                }
            ]
        }

        # Комбинируем оба JSON-LD
        combined_jsonld = [jsonld, breadcrumb_jsonld]

        # Создаем полноценный HTML-контент для поисковиков
        # Вставляется прямо в solutionContainer — роботы видят весь текст
        ssr_content = f'''
        <article class="ssr-content" itemscope itemtype="https://schema.org/Answer">
            <h1 itemprop="name">{html_module.escape(solution.name)}</h1>
        '''

        if solution.describe:
            ssr_content += f'<div itemprop="text"><p>{html_module.escape(solution.describe)}</p></div>'

        if solution.problems and len(solution.problems) > 0:
            ssr_content += f'<section><h2>Связанные проблемы ({len(solution.problems)})</h2>'
            for prob in solution.problems:
                prob_slug = re.sub(r'[^\w\s-]', '', prob.name.lower())
                prob_slug = re.sub(r'[-\s]+', '-', prob_slug).strip('-')[:50]
                prob_url = f'/problem/{prob.id}'
                if prob_slug:
                    prob_url = f'/problem/{prob.id}-{prob_slug}'

                ssr_content += f'<article><h3><a href="{prob_url}">{html_module.escape(prob.name)}</a></h3>'
                if prob.describe:
                    ssr_content += f'<p>{html_module.escape(prob.describe[:300])}</p>'
                ssr_content += '</article>'
            ssr_content += '</section>'

        ssr_content += '</article>'

        result = _render_page_with_seo('solution.html', {
            'title': f'{solution.name} - Всё Прост',
            'description': desc_text,
            'image': image_url,
            'url': canonical_url,
            'jsonld': combined_jsonld,
            'ssr_content': ssr_content
        })
        return result if result else send_from_directory('html', 'solution.html')

    @app.route('/html/problem.html')
    def serve_problem_page():
        """Старый URL - делаем 301 редирект на новый красивый URL"""
        from logic.model import Problem
        from flask import redirect
        problem_id = request.args.get('id') or request.args.get('problemId')

        if not problem_id:
            return send_from_directory('html', 'problem.html')

        try:
            problem = Problem.query.get(int(problem_id))
        except (ValueError, TypeError):
            return send_from_directory('html', 'problem.html')

        if not problem:
            return send_from_directory('html', 'problem.html')

        # Генерируем slug и делаем редирект на новый URL
        import re
        slug = re.sub(r'[^\w\s-]', '', problem.name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')[:50]

        new_url = f'/problem/{problem.id}'
        if slug:
            new_url = f'/problem/{problem.id}-{slug}'

        return redirect(new_url, code=301)

    @app.route('/html/solution.html')
    def serve_solution_page():
        """Старый URL - делаем 301 редирект на новый красивый URL"""
        from logic.model import Solution
        from flask import redirect
        solution_id = request.args.get('solutionId') or request.args.get('id')

        if not solution_id:
            return send_from_directory('html', 'solution.html')

        try:
            solution = db.session.get(Solution, int(solution_id))
        except (ValueError, TypeError):
            return send_from_directory('html', 'solution.html')

        if not solution:
            return send_from_directory('html', 'solution.html')

        # Генерируем slug и делаем редирект на новый URL
        import re
        slug = re.sub(r'[^\w\s-]', '', solution.name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')[:50]

        new_url = f'/solution/{solution.id}'
        if slug:
            new_url = f'/solution/{solution.id}-{slug}'

        return redirect(new_url, code=301)

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


def _register_error_handlers(app):
    """Регистрация обработчиков ошибок"""
    from logic.utils.error_handler import ErrorResponse, AppError

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
            '/sitemap.xml',
            '/api/'
        ]
        
        # Для HTML запросов возвращаем SEO-оптимизированную страницу 404
        if request.path.startswith('/html/') or request.path == '/' or not request.path.startswith('/api/'):
            if os.path.exists('html/404.html'):
                return send_from_directory('html', '404.html'), 404
        
        # Логируем только реальные ошибки, не служебные запросы
        if not any(request.path.startswith(path) for path in ignored_paths):
            app.logger.warning(f"404 ошибка: {request.method} {request.path} - {error}")
        
        response, status_code = ErrorResponse.create_response(
            error,
            include_details=app.config.get('ENV') == 'development'
        )
        return response, status_code

    @app.errorhandler(500)
    def internal_error(error):
        """Обработка ошибки 500"""
        from flask import request
        app.logger.error(f"500 ошибка: {request.method} {request.path} — {error}", exc_info=True)
        db.session.rollback()
        response, status_code = ErrorResponse.create_response(
            error,
            include_details=app.config.get('ENV') == 'development'
        )
        return response, status_code

    @app.errorhandler(429)
    def rate_limit_error(error):
        """Обработка ошибки 429 (Rate Limit Exceeded)"""
        from flask import request
        from flask_limiter.errors import RateLimitExceeded
        from logic.utils.error_handler import RateLimitError
        
        if isinstance(error, RateLimitExceeded):
            app_error = RateLimitError(error.description or "Слишком много запросов")
        else:
            app_error = RateLimitError("Слишком много запросов")
        
        app.logger.warning(f"429 Rate Limit: {request.method} {request.path}")
        response, status_code = ErrorResponse.create_response(app_error)
        return response, status_code

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Обработка всех необработанных исключений"""
        from flask_limiter.errors import RateLimitExceeded
        # Пропускаем RateLimitExceeded, так как у него есть отдельный обработчик
        if isinstance(error, RateLimitExceeded):
            raise  # Позволяем Flask-Limiter обработать это через errorhandler(429)
        
        # Проверяем, это ли AppError
        if isinstance(error, AppError):
            app.logger.warning(f"AppError: {error.message}")
            response, status_code = ErrorResponse.create_response(
                error,
                include_details=app.config.get('ENV') == 'development'
            )
            return response, status_code
        
        # Для неожиданных ошибок
        from flask import request
        app.logger.error(f"Необработанное исключение: {request.method} {request.path} — {error}", exc_info=True)
        db.session.rollback()
        response, status_code = ErrorResponse.create_response(
            error,
            include_details=app.config.get('ENV') == 'development'
        )
        return response, status_code


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
        debug=app.config['DEBUG'],
        use_reloader=(os.name != 'nt'),  # avoid WinError 10038 on Ctrl+C on Windows
    )
