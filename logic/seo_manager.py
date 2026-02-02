# seo_manager.py
"""
Менеджер для управления SEO параметрами и meta-тегами
Поддерживает динамическую генерацию метаданных для различных типов контента
"""
from datetime import datetime
from logic.utils.logger import get_logger

logger = get_logger(__name__)


class SEOManager:
    """Класс для управления SEO параметрами"""
    
    BASE_URL = "https://vseprost.com"
    
    # Стандартные метаданные
    DEFAULT_SITE_NAME = "Всё Прост"
    DEFAULT_SITE_DESCRIPTION = "Платформа для поиска решений и обсуждения проблем"
    DEFAULT_SITE_IMAGE = "/assets/images/Screenshot_4-ww78noDj9-transformed.png"
    
    @staticmethod
    def generate_meta_tags(content_type, content_data):
        """
        Генерирует meta-теги для контента
        
        Args:
            content_type: тип контента ('problem', 'solution', 'category', 'topic', 'home')
            content_data: словарь с данными контента
            
        Returns:
            словарь с meta-тегами
        """
        if content_type == 'problem':
            return SEOManager._generate_problem_tags(content_data)
        elif content_type == 'solution':
            return SEOManager._generate_solution_tags(content_data)
        elif content_type == 'category':
            return SEOManager._generate_category_tags(content_data)
        elif content_type == 'topic':
            return SEOManager._generate_topic_tags(content_data)
        else:
            return SEOManager._generate_default_tags()
    
    @staticmethod
    def _generate_problem_tags(data):
        """Генерирует meta-теги для проблемы (вопроса)"""
        title = data.get('title', 'Проблема') or 'Проблема'
        # Обрезаем title до 60 символов для оптимальности
        if len(title) > 60:
            title = title[:57] + '...'
        
        description = data.get('description', '')[:160] or ''
        if not description:
            description = f"{title} - найти решение на платформе Всё Прост"
        
        # Обрезаем description до 160 символов
        if len(description) > 160:
            description = description[:157] + '...'
        
        problem_id = data.get('id', '')
        slug = data.get('slug', problem_id)
        canonical_url = f"{SEOManager.BASE_URL}/problem/{slug}"
        
        image = data.get('image') or SEOManager.DEFAULT_SITE_IMAGE
        if not image.startswith('http'):
            image = f"{SEOManager.BASE_URL}{image}"
        
        category = data.get('category', '')
        keywords = [
            'вопрос',
            'ответ',
            'помощь',
            'проблема',
            'решение',
            category,
            title
        ]
        keywords = [k for k in keywords if k]
        
        return {
            'title': title,
            'description': description,
            'keywords': ', '.join(keywords[:8]),
            'canonical': canonical_url,
            'og:title': title,
            'og:description': description,
            'og:url': canonical_url,
            'og:image': image,
            'og:type': 'article',
            'twitter:title': title,
            'twitter:description': description,
            'twitter:image': image,
            'robots': 'index, follow',
            'article:published_time': data.get('created_date', ''),
            'article:modified_time': data.get('modified_date', ''),
            'article:author': data.get('author_name', ''),
        }
    
    @staticmethod
    def _generate_solution_tags(data):
        """Генерирует meta-теги для решения"""
        title = data.get('title', 'Решение') or 'Решение'
        if len(title) > 60:
            title = title[:57] + '...'
        
        description = data.get('description', '')[:160] or ''
        if not description:
            description = f"{title} - решение на платформе Всё Прост"
        
        if len(description) > 160:
            description = description[:157] + '...'
        
        solution_id = data.get('id', '')
        slug = data.get('slug', solution_id)
        canonical_url = f"{SEOManager.BASE_URL}/solution/{slug}"
        
        image = data.get('image') or SEOManager.DEFAULT_SITE_IMAGE
        if not image.startswith('http'):
            image = f"{SEOManager.BASE_URL}{image}"
        
        rating = data.get('rating', 0)
        efficiency = data.get('efficiency', 0)
        
        keywords = [
            'решение',
            'ответ',
            'помощь',
            'совет',
            f'рейтинг: {rating}' if rating > 0 else '',
            title
        ]
        keywords = [k for k in keywords if k]
        
        return {
            'title': title,
            'description': description,
            'keywords': ', '.join(keywords[:8]),
            'canonical': canonical_url,
            'og:title': title,
            'og:description': description,
            'og:url': canonical_url,
            'og:image': image,
            'og:type': 'article',
            'twitter:title': title,
            'twitter:description': description,
            'twitter:image': image,
            'robots': 'index, follow',
            'article:published_time': data.get('created_date', ''),
            'article:modified_time': data.get('modified_date', ''),
            'article:author': data.get('author_name', ''),
        }
    
    @staticmethod
    def _generate_category_tags(data):
        """Генерирует meta-теги для категории"""
        category_name = data.get('name', 'Категория')
        title = f"{category_name} - Всё Прост"
        if len(title) > 60:
            title = title[:57] + '...'
        
        description = data.get('description', '')[:160] or f"Категория {category_name} на платформе Всё Прост"
        if len(description) > 160:
            description = description[:157] + '...'
        
        category_id = data.get('id', '')
        canonical_url = f"{SEOManager.BASE_URL}/?category={category_id}"
        
        return {
            'title': title,
            'description': description,
            'keywords': f"{category_name}, вопросы, ответы, помощь",
            'canonical': canonical_url,
            'og:title': title,
            'og:description': description,
            'og:url': canonical_url,
            'og:image': SEOManager.DEFAULT_SITE_IMAGE,
            'og:type': 'website',
            'robots': 'index, follow',
        }
    
    @staticmethod
    def _generate_topic_tags(data):
        """Генерирует meta-теги для топика"""
        topic_name = data.get('name', 'Топик')
        title = f"{topic_name} - Всё Прост"
        if len(title) > 60:
            title = title[:57] + '...'
        
        description = data.get('description', '')[:160] or f"Обсуждение {topic_name} на платформе Всё Прост"
        if len(description) > 160:
            description = description[:157] + '...'
        
        topic_id = data.get('id', '')
        canonical_url = f"{SEOManager.BASE_URL}/?topic={topic_id}"
        
        return {
            'title': title,
            'description': description,
            'keywords': f"{topic_name}, обсуждение, вопросы, ответы",
            'canonical': canonical_url,
            'og:title': title,
            'og:description': description,
            'og:url': canonical_url,
            'og:image': SEOManager.DEFAULT_SITE_IMAGE,
            'og:type': 'website',
            'robots': 'index, follow',
        }
    
    @staticmethod
    def _generate_default_tags():
        """Генерирует стандартные meta-теги"""
        return {
            'title': SEOManager.DEFAULT_SITE_NAME,
            'description': SEOManager.DEFAULT_SITE_DESCRIPTION,
            'keywords': 'VseProst, ВсеПрост, Все Просто, ВсёПрост, Всё Прост, решения проблем, вопросы и ответы, помощь, сообщество',
            'canonical': SEOManager.BASE_URL,
            'og:title': SEOManager.DEFAULT_SITE_NAME,
            'og:description': SEOManager.DEFAULT_SITE_DESCRIPTION,
            'og:url': SEOManager.BASE_URL,
            'og:image': SEOManager.DEFAULT_SITE_IMAGE,
            'og:type': 'website',
            'robots': 'index, follow',
        }
    
    @staticmethod
    def generate_structured_data(content_type, content_data):
        """
        Генерирует JSON-LD Structured Data для контента
        
        Args:
            content_type: тип контента ('problem', 'solution', 'faq')
            content_data: словарь с данными контента
            
        Returns:
            словарь для JSON-LD или None
        """
        if content_type == 'problem':
            return SEOManager._generate_problem_structured_data(content_data)
        elif content_type == 'solution':
            return SEOManager._generate_solution_structured_data(content_data)
        elif content_type == 'faq':
            return SEOManager._generate_faq_structured_data(content_data)
        return None
    
    @staticmethod
    def _generate_problem_structured_data(data):
        """Генерирует JSON-LD для вопроса"""
        return {
            '@context': 'https://schema.org',
            '@type': 'Question',
            'name': data.get('title', ''),
            'text': data.get('description', ''),
            'dateCreated': data.get('created_date', ''),
            'dateModified': data.get('modified_date', ''),
            'author': {
                '@type': 'Person',
                'name': data.get('author_name', 'Аноним')
            },
            'keywords': data.get('keywords', ''),
            'image': data.get('image', ''),
        }
    
    @staticmethod
    def _generate_solution_structured_data(data):
        """Генерирует JSON-LD для решения"""
        answer_data = {
            '@type': 'Answer',
            'text': data.get('description', ''),
            'author': {
                '@type': 'Person',
                'name': data.get('author_name', 'Аноним')
            },
            'dateCreated': data.get('created_date', ''),
        }
        
        if data.get('rating'):
            answer_data['upvoteCount'] = data.get('rating', 0)
        
        return {
            '@context': 'https://schema.org',
            '@type': 'QAPage',
            'mainEntity': {
                '@type': 'Question',
                'name': data.get('question_title', ''),
                'acceptedAnswer': answer_data
            }
        }
    
    @staticmethod
    def _generate_faq_structured_data(faqs):
        """Генерирует JSON-LD для FAQ"""
        faq_items = []
        for item in faqs:
            faq_items.append({
                '@type': 'Question',
                'name': item.get('question', ''),
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': item.get('answer', '')
                }
            })
        
        return {
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            'mainEntity': faq_items
        }
    
    @staticmethod
    def generate_breadcrumb_schema(breadcrumbs):
        """
        Генерирует JSON-LD для хлебных крошек
        
        Args:
            breadcrumbs: список кортежей (название, URL)
            
        Returns:
            JSON-LD структура
        """
        items = []
        for idx, (name, url) in enumerate(breadcrumbs, 1):
            items.append({
                '@type': 'ListItem',
                'position': idx,
                'name': name,
                'item': url
            })
        
        return {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': items
        }
    
    @staticmethod
    def generate_organization_schema():
        """Генерирует JSON-LD для организации"""
        return {
            '@context': 'https://schema.org',
            '@type': 'Organization',
            'name': 'Всё Прост (VseProst)',
            'url': SEOManager.BASE_URL,
            'logo': f"{SEOManager.BASE_URL}/assets/images/logo1-Photoroom1.png",
            'description': SEOManager.DEFAULT_SITE_DESCRIPTION,
            'sameAs': [
                'https://www.facebook.com/vseprost',
                'https://www.twitter.com/vseprost',
                'https://www.instagram.com/vseprost',
            ]
        }
