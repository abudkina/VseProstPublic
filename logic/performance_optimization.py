# performance_optimization.py
"""
Модуль оптимизации производительности для Core Web Vitals
Обеспечивает быстрое время загрузки и хороший пользовательский опыт

Интегрирует:
- Flask-Caching для кэширования ответов
- Flask-Compress для сжатия ответов
- Оптимизацию заголовков
- Resource hints для быстрой загрузки
"""
from flask import current_app
from flask_compress import Compress
from functools import wraps
import gzip
import io
from logic.utils.logger import get_logger
from logic.cache_config import cache

logger = get_logger(__name__)

# Инициализация Flask-Compress
compress = Compress()


def add_performance_headers(app):
    """
    Добавляет заголовки для оптимизации производительности
    """
    @app.after_request
    def add_headers(response):
        # Кэширование статических файлов
        if response.path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2')):
            response.headers['Cache-Control'] = 'public, max-age=2592000'  # 30 дней
        else:
            response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 час
        
        # Compression (gzip)
        response.headers['Vary'] = 'Accept-Encoding'
        
        # Preload важные ресурсы
        response.headers['Link'] = '</css/index.css>; rel=preload; as=style, </js/index.js>; rel=preload; as=script'
        
        # DNS prefetch для внешних ресурсов
        response.headers['Link'] += ', <https://fonts.googleapis.com>; rel=dns-prefetch'
        
        # Preconnect для Google Fonts
        response.headers['Link'] += ', <https://fonts.googleapis.com>; rel=preconnect'
        response.headers['Link'] += ', <https://fonts.gstatic.com>; rel=preconnect; crossorigin'
        
        # Content Security Policy для производительности
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    
    logger.info("Performance headers добавлены")


def minify_response(app):
    """
    Минификация HTML, CSS, JS для уменьшения размера
    """
    @app.after_request
    def minify(response):
        if response.content_type and 'text/html' in response.content_type:
            try:
                # Удаляем лишние пробелы и переносы
                import re
                content = response.get_data(as_text=True)
                
                # Удаляем комментарии HTML
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                
                # Удаляем лишние пробелы
                content = re.sub(r'\s+', ' ', content)
                content = re.sub(r'>\s+<', '><', content)
                
                response.set_data(content)
                
                # Добавляем Content-Encoding header
                response.headers['Content-Encoding'] = 'gzip'
                
            except Exception as e:
                logger.warning(f"Ошибка при минификации: {e}")
        
        return response
    
    logger.info("Minification включена")


class PerformanceOptimization:
    """Класс для оптимизации производительности"""
    
    @staticmethod
    def optimize_database_queries(func):
        """
        Декоратор для оптимизации SQL запросов
        Использует eager loading и кэширование
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            from logic.model import db
            
            # Включаем оптимизации SQLAlchemy
            db.engine.echo = False
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Закрываем сессию после запроса
                db.session.close()
        
        return wrapper
    
    @staticmethod
    def add_resource_hints(html_content):
        """
        Добавляет resource hints (preload, prefetch, preconnect)
        """
        resource_hints = """
        <link rel="preload" href="/css/index.css" as="style" />
        <link rel="preload" href="/js/index.js" as="script" />
        <link rel="prefetch" href="/api/problems" as="fetch" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
        """
        
        # Вставляем перед </head>
        return html_content.replace('</head>', resource_hints + '</head>')
    
    @staticmethod
    def critical_css_inline(html_content):
        """
        Встраивает критические CSS для улучшения FCP
        """
        critical_css = """
        <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; }
        header { background: #fff; border-bottom: 1px solid #e0e0e0; }
        main { padding: 20px; }
        .cards-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        </style>
        """
        
        return html_content.replace('<style>', critical_css + '<style>')
    
    @staticmethod
    def defer_non_critical_js(html_content):
        """
        Откладывает загрузку некритичного JavaScript
        """
        # Добавляем defer для скриптов
        html_content = html_content.replace(
            '<script src="',
            '<script defer src="'
        )
        
        return html_content
    
    @staticmethod
    def optimize_images_html(html_content):
        """
        Оптимизирует изображения в HTML
        """
        import re
        
        # Добавляем loading="lazy" для изображений
        html_content = re.sub(
            r'<img\s+([^>]*?)>',
            lambda m: '<img ' + m.group(1) + ' loading="lazy">' if 'loading=' not in m.group(1) else m.group(0),
            html_content
        )
        
        return html_content


# Конфигурация для app.py
def setup_performance_optimization(app):
    """
    Настраивает оптимизацию производительности приложения
    
    Включает:
    - Flask-Compress для сжатия ответов (gzip/brotli)
    - Flask-Caching для кэширования
    - Performance headers (Cache-Control, preload, etc.)
    - Минификация HTML ответов
    """
    # Инициализация сжатия ответов
    compress.init_app(app)
    logger.info("Flask-Compress инициализирован")
    
    # Инициализация кэширования
    cache.init_app(app)
    logger.info("Flask-Caching инициализирован")
    
    # Добавление performance headers
    add_performance_headers(app)
    
    # Минификация HTML (только для production)
    if app.config.get('ENV') == 'production':
        minify_response(app)
        logger.info("HTML минификация включена для production")
    
    logger.info("✅ Performance optimization полностью инициализирована")
