# ssr_renderer.py
"""
Модуль для Server-Side Rendering (SSR) мета-тегов и контента
Обеспечивает правильную индексацию поисковыми роботами
"""
from flask import render_template_string, current_app, jsonify
from logic.seo_manager import SEOManager
from logic.utils.logger import get_logger
import json

logger = get_logger(__name__)


class SSRRenderer:
    """Класс для рендеринга контента на стороне сервера"""
    
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    
    <!-- SEO Meta Tags -->
    <title>{{ meta.title }}</title>
    <meta name="description" content="{{ meta.description }}" />
    <meta name="keywords" content="{{ meta.keywords }}" />
    <meta name="robots" content="{{ meta.robots }}" />
    <link rel="canonical" href="{{ meta.canonical }}" />
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="{{ meta['og:type'] }}" />
    <meta property="og:url" content="{{ meta['og:url'] }}" />
    <meta property="og:title" content="{{ meta['og:title'] }}" />
    <meta property="og:description" content="{{ meta['og:description'] }}" />
    <meta property="og:image" content="{{ meta['og:image'] }}" />
    <meta property="og:locale" content="ru_RU" />
    <meta property="og:site_name" content="Всё Прост" />
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{{ meta['twitter:title'] }}" />
    <meta name="twitter:description" content="{{ meta['twitter:description'] }}" />
    <meta name="twitter:image" content="{{ meta['twitter:image'] }}" />
    
    <!-- Article Meta -->
    {% if meta['article:published_time'] %}
    <meta property="article:published_time" content="{{ meta['article:published_time'] }}" />
    {% endif %}
    {% if meta['article:modified_time'] %}
    <meta property="article:modified_time" content="{{ meta['article:modified_time'] }}" />
    {% endif %}
    {% if meta['article:author'] %}
    <meta property="article:author" content="{{ meta['article:author'] }}" />
    {% endif %}
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/favicon.ico" />
    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
    
    <!-- Structured Data (JSON-LD) -->
    {% if structured_data %}
    <script type="application/ld+json">
    {{ structured_data|safe }}
    </script>
    {% endif %}
    
    <!-- Breadcrumb Structured Data -->
    {% if breadcrumb_schema %}
    <script type="application/ld+json">
    {{ breadcrumb_schema|safe }}
    </script>
    {% endif %}
    
    <!-- Content -->
</head>
<body>
    <main>
        {{ content|safe }}
    </main>
    <script>window.dataLayer = {{ data_layer|safe }};</script>
</body>
</html>
"""
    
    @staticmethod
    def render_problem(problem_data, solutions_data=None):
        """
        Рендерит проблему (вопрос) с SEO-оптимизацией
        
        Args:
            problem_data: словарь с данными проблемы
            solutions_data: список решений
            
        Returns:
            HTML контент с мета-тегами
        """
        try:
            # Генерируем meta-теги
            meta_tags = SEOManager.generate_meta_tags('problem', problem_data)
            
            # Генерируем Structured Data
            structured_data = SEOManager.generate_structured_data('problem', problem_data)
            
            # Генерируем breadcrumb схему
            breadcrumbs = [
                ('Главная', '/'),
                ('Вопросы', '/?category=all'),
                (problem_data.get('title', 'Вопрос'), '')
            ]
            breadcrumb_schema = SEOManager.generate_breadcrumb_schema(breadcrumbs)
            
            # Подготавливаем контент
            content_html = _generate_problem_html(problem_data, solutions_data)
            
            # Подготавливаем dataLayer для Google Analytics
            data_layer = _prepare_data_layer('problem', problem_data)
            
            # Рендерим шаблон
            return render_template_string(
                SSRRenderer.HTML_TEMPLATE,
                meta=meta_tags,
                structured_data=json.dumps(structured_data) if structured_data else None,
                breadcrumb_schema=json.dumps(breadcrumb_schema) if breadcrumb_schema else None,
                content=content_html,
                data_layer=json.dumps(data_layer)
            )
        except Exception as e:
            logger.error(f"Ошибка при рендеринге проблемы: {e}")
            return None
    
    @staticmethod
    def render_solution(solution_data, problem_data=None):
        """
        Рендерит решение с SEO-оптимизацией
        
        Args:
            solution_data: словарь с данными решения
            problem_data: данные связанной проблемы (опционально)
            
        Returns:
            HTML контент с мета-тегами
        """
        try:
            # Генерируем meta-теги
            meta_tags = SEOManager.generate_meta_tags('solution', solution_data)
            
            # Добавляем данные проблемы в solution_data для Structured Data
            if problem_data:
                solution_data['question_title'] = problem_data.get('title', '')
            
            # Генерируем Structured Data
            structured_data = SEOManager.generate_structured_data('solution', solution_data)
            
            # Генерируем breadcrumb схему
            breadcrumbs = [
                ('Главная', '/'),
                ('Решения', '/html/solutions.html'),
                (solution_data.get('title', 'Решение'), '')
            ]
            breadcrumb_schema = SEOManager.generate_breadcrumb_schema(breadcrumbs)
            
            # Подготавливаем контент
            content_html = _generate_solution_html(solution_data, problem_data)
            
            # Подготавливаем dataLayer для Google Analytics
            data_layer = _prepare_data_layer('solution', solution_data)
            
            # Рендерим шаблон
            return render_template_string(
                SSRRenderer.HTML_TEMPLATE,
                meta=meta_tags,
                structured_data=json.dumps(structured_data) if structured_data else None,
                breadcrumb_schema=json.dumps(breadcrumb_schema) if breadcrumb_schema else None,
                content=content_html,
                data_layer=json.dumps(data_layer)
            )
        except Exception as e:
            logger.error(f"Ошибка при рендеринге решения: {e}")
            return None


def _generate_problem_html(problem_data, solutions_data=None):
    """Генерирует HTML для проблемы"""
    html = f"""
    <article>
        <h1>{problem_data.get('title', 'Вопрос')}</h1>
        <time datetime="{problem_data.get('created_date', '')}">
            Создано: {problem_data.get('created_date', '')}
        </time>
        <div class="description">
            {problem_data.get('description', '')}
        </div>
    """
    
    if problem_data.get('image'):
        html += f"""
        <figure>
            <img src="{problem_data.get('image')}" alt="{problem_data.get('title', '')}" />
        </figure>
        """
    
    html += """
    </article>
    """
    
    return html


def _generate_solution_html(solution_data, problem_data=None):
    """Генерирует HTML для решения"""
    html = f"""
    <article>
        <h1>{solution_data.get('title', 'Решение')}</h1>
        <time datetime="{solution_data.get('created_date', '')}">
            Создано: {solution_data.get('created_date', '')}
        </time>
    """
    
    if problem_data:
        html += f"""
        <section>
            <h2>Связанный вопрос</h2>
            <p>{problem_data.get('title', '')}</p>
        </section>
        """
    
    html += f"""
        <div class="description">
            {solution_data.get('description', '')}
        </div>
    """
    
    if solution_data.get('rating'):
        html += f"""
        <div class="rating">
            <span class="rating-label">Рейтинг:</span>
            <span class="rating-value">{solution_data.get('rating', 0)}</span>
        </div>
        """
    
    if solution_data.get('image'):
        html += f"""
        <figure>
            <img src="{solution_data.get('image')}" alt="{solution_data.get('title', '')}" />
        </figure>
        """
    
    html += """
    </article>
    """
    
    return html


def _prepare_data_layer(content_type, content_data):
    """Подготавливает dataLayer для Google Analytics"""
    return {
        'event': 'pageview',
        'pageType': content_type,
        'contentId': content_data.get('id', ''),
        'contentTitle': content_data.get('title', ''),
        'author': content_data.get('author_name', 'anonymous'),
        'timestamp': content_data.get('created_date', '')
    }
