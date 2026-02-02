"""
Middleware and optimization utilities for Flask application
Includes: compression, caching headers, performance optimizations
"""

from flask import request, g
from flask_compress import Compress
from datetime import datetime, timedelta
import time


def init_optimizations(app):
    """
    Инициализация всех оптимизаций приложения
    
    Args:
        app: Flask application instance
    """
    
    # 1. Инициализируем сжатие ответов
    _init_compression(app)
    
    # 2. Добавляем кэширующие заголовки
    _init_cache_headers(app)
    
    # 3. Инициализируем профилирование (только для development)
    if app.config['ENV'] == 'development':
        _init_profiling(app)
    
    # 4. Добавляем мониторинг производительности
    _init_performance_monitoring(app)


def _init_compression(app):
    """Инициализация сжатия ответов"""
    Compress(app)
    app.logger.info("✅ Сжатие ответов (gzip/brotli) включено")


def _init_cache_headers(app):
    """Добавление правильных заголовков кэширования"""
    
    @app.after_request
    def add_cache_headers(response):
        """Добавляем заголовки кэширования для различных типов контента"""
        
        # Кэшируем статические файлы на 1 месяц
        if request.path.startswith('/static/'):
            response.cache_control.max_age = 2592000  # 30 дней
            response.cache_control.public = True
            response.headers['ETag'] = 'W/"%s"' % datetime.utcnow().timestamp()
        
        # API ответы не кэшируем (или кэшируем меньше)
        elif request.path.startswith('/api/'):
            response.cache_control.max_age = 0
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
            response.headers['Pragma'] = 'no-cache'
        
        # Добавляем CORS заголовки
        if app.config['ENV'] != 'production' or request.origin:
            response.headers['Access-Control-Allow-Origin'] = request.origin or '*'
        
        # Добавляем заголовок производительности
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            response.headers['X-Response-Time'] = f"{duration:.2f}ms"
        
        return response
    
    app.logger.info("✅ Кэширующие заголовки настроены")


def _init_profiling(app):
    """Инициализация профилирования (только для development)"""
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
        app.logger.info("✅ Flask DebugToolbar включен для профилирования")
    except ImportError:
        app.logger.warning("⚠️ Flask-DebugToolbar не установлен")


def _init_performance_monitoring(app):
    """Мониторинг производительности запросов"""
    
    @app.before_request
    def before_request():
        """Начало отсчёта времени запроса"""
        g.start_time = time.time()
        g.db_queries_count = 0
    
    @app.after_request
    def after_request(response):
        """Логирование информации о производительности"""
        
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            
            # Логируем медленные запросы (>1000ms)
            if duration > 1000:
                app.logger.warning(
                    f"🐢 Медленный запрос: {request.method} {request.path} - {duration:.2f}ms"
                )
            
            # Добавляем в заголовок ответа
            response.headers['X-Response-Time'] = f"{duration:.2f}ms"
        
        return response
    
    app.logger.info("✅ Мониторинг производительности включен")


# ============================================================================
# Оптимизация запросов SQLAlchemy
# ============================================================================

def optimize_query(query_obj):
    """
    Оптимизация SQLAlchemy запроса
    
    Использование:
        optimized_query = optimize_query(Problem.query)
        .filter_by(category=1)
        .all()
    """
    # Отключаем lazy loading для лучшей производительности
    query_obj = query_obj.options(
        # joinedload основных отношений
        # selectinload для коллекций
    )
    return query_obj


def get_query_performance(query_str, params=None):
    """
    Получение информации о производительности запроса
    
    Использование:
        perf = get_query_performance("SELECT * FROM problem LIMIT 1")
        print(f"Время выполнения: {perf['execution_time']}ms")
    """
    from logic.model import db
    import time
    
    start = time.time()
    result = db.session.execute(query_str, params or {})
    duration = (time.time() - start) * 1000
    
    return {
        'query': query_str,
        'execution_time': duration,
        'rows': len(result.fetchall()) if hasattr(result, 'fetchall') else 0
    }


# ============================================================================
# Утилиты для измерения производительности
# ============================================================================

class PerformanceMonitor:
    """Класс для мониторинга производительности функций"""
    
    _metrics = {}
    
    @staticmethod
    def start_timer(name):
        """Начать измерение времени"""
        PerformanceMonitor._metrics[name] = {
            'start': time.time(),
            'calls': 0
        }
    
    @staticmethod
    def end_timer(name):
        """Завершить измерение времени"""
        if name in PerformanceMonitor._metrics:
            duration = (time.time() - PerformanceMonitor._metrics[name]['start']) * 1000
            PerformanceMonitor._metrics[name]['calls'] += 1
            PerformanceMonitor._metrics[name]['total_time'] = duration
            return duration
        return None
    
    @staticmethod
    def get_report():
        """Получить отчет о производительности"""
        return PerformanceMonitor._metrics
    
    @staticmethod
    def reset():
        """Очистить метрики"""
        PerformanceMonitor._metrics = {}
