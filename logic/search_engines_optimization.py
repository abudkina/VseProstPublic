# search_engines_optimization.py
"""
Специфичные оптимизации для Google и Яндекс
Обеспечивает максимальную видимость в этих поисковых системах
"""
from flask import Blueprint, current_app, request
from logic.seo_manager import SEOManager
from logic.utils.logger import get_logger
import json

logger = get_logger(__name__)

search_engines_bp = Blueprint('search_engines', __name__)


class GoogleOptimization:
    """Класс для оптимизации под Google"""
    
    @staticmethod
    def generate_google_schema(content_type, content_data):
        """
        Генерирует расширенные Structured Data для Google
        
        Поддерживает:
        - FAQPage
        - HowTo
        - Article
        - VideoObject
        - BreadcrumbList
        """
        base_schema = SEOManager.generate_structured_data(content_type, content_data)
        
        if not base_schema:
            return None
        
        # Дополнительные оптимизации для Google
        if content_type == 'problem':
            # Добавляем FAQPage если есть ответы
            if content_data.get('solutions'):
                faq_items = []
                for solution in content_data.get('solutions', [])[:5]:  # Максимум 5 FAQ
                    faq_items.append({
                        '@type': 'Question',
                        'name': content_data.get('title', ''),
                        'acceptedAnswer': {
                            '@type': 'Answer',
                            'text': solution.get('description', '')[:500]
                        }
                    })
                
                if faq_items:
                    return {
                        '@context': 'https://schema.org',
                        '@type': 'FAQPage',
                        'mainEntity': faq_items
                    }
        
        return base_schema
    
    @staticmethod
    def generate_google_rich_snippets(content_type, content_data):
        """
        Генерирует Rich Snippets для Google
        
        Поддерживает:
        - Rating (звездочки)
        - Review (отзывы)
        - Price (цена)
        - Availability (доступность)
        """
        snippets = {}
        
        if content_type == 'solution':
            # Rating snippet
            if content_data.get('rating', 0) > 0:
                snippets['aggregateRating'] = {
                    '@type': 'AggregateRating',
                    'ratingValue': content_data.get('rating', 0),
                    'bestRating': 5,
                    'worstRating': 1,
                    'ratingCount': content_data.get('reply', 0) or 1
                }
            
            # Price snippet
            if content_data.get('price', 0) > 0:
                snippets['offers'] = {
                    '@type': 'Offer',
                    'price': str(content_data.get('price', 0)),
                    'priceCurrency': 'RUB',
                    'availability': 'https://schema.org/InStock' if content_data.get('isbought', False) else 'https://schema.org/OnlineOnly'
                }
        
        return snippets
    
    @staticmethod
    def generate_google_meta_tags(content_data):
        """
        Генерирует специфичные мета-теги для Google
        """
        meta_tags = {}
        
        # Google-specific meta tags
        if content_data.get('author_name'):
            meta_tags['author'] = content_data.get('author_name')
        
        # Article meta для Google News
        if content_data.get('created_date'):
            meta_tags['article:published_time'] = content_data.get('created_date')
        if content_data.get('modified_date'):
            meta_tags['article:modified_time'] = content_data.get('modified_date')
        
        # Geo targeting (если нужно)
        meta_tags['geo.region'] = 'RU'
        meta_tags['geo.placename'] = 'Russia'
        
        return meta_tags


class YandexOptimization:
    """Класс для оптимизации под Яндекс"""
    
    @staticmethod
    def generate_yandex_schema(content_type, content_data):
        """
        Генерирует Structured Data для Яндекс
        
        Яндекс поддерживает:
        - Organization
        - BreadcrumbList
        - Article
        - FAQPage
        """
        # Яндекс использует те же схемы что и Google, но с некоторыми отличиями
        base_schema = SEOManager.generate_structured_data(content_type, content_data)
        
        if not base_schema:
            return None
        
        # Яндекс-специфичные дополнения
        if '@type' in base_schema and base_schema['@type'] == 'Article':
            # Добавляем больше метаданных для Яндекса
            base_schema['publisher'] = {
                '@type': 'Organization',
                'name': 'Всё Прост',
                'logo': {
                    '@type': 'ImageObject',
                    'url': 'https://vseprost.com/assets/images/logo1-Photoroom1.png'
                }
            }
        
        return base_schema
    
    @staticmethod
    def generate_yandex_meta_tags(content_data):
        """
        Генерирует специфичные мета-теги для Яндекс
        """
        meta_tags = {}
        
        # Яндекс-специфичные теги
        base_url = current_app.config.get('BASE_URL', 'https://vseprost.com')
        
        # Яндекс.Каталог (если зарегистрирован)
        meta_tags['yandex-verification'] = current_app.config.get('YANDEX_VERIFICATION', '')
        
        # Географическая привязка для Яндекса
        meta_tags['geo.position'] = '55.7558;37.6173'  # Москва (можно настроить)
        meta_tags['geo.region'] = 'RU-MOW'  # Москва
        
        # Язык контента
        meta_tags['language'] = 'ru'
        
        # Дата публикации для Яндекса
        if content_data.get('created_date'):
            meta_tags['document-date'] = content_data.get('created_date')
        
        return meta_tags
    
    @staticmethod
    def generate_yandex_turbo_content(html_content):
        """
        Генерирует контент для Яндекс.Турбо страниц
        
        Яндекс.Турбо - аналог AMP для Яндекса
        """
        # Базовая структура Turbo страницы
        turbo_content = {
            'header': {
                'title': 'Всё Прост',
                'h1': 'Платформа для поиска решений'
            },
            'content': html_content,
            'footer': {
                'text': '© Всё Прост. Все права защищены.'
            }
        }
        
        return turbo_content


class SearchEnginesHelper:
    """Универсальный помощник для оптимизации под поисковики"""
    
    @staticmethod
    def generate_combined_meta_tags(content_type, content_data):
        """
        Генерирует комбинированные мета-теги для Google и Яндекс
        """
        # Базовые мета-теги
        base_meta = SEOManager.generate_meta_tags(content_type, content_data)
        
        # Google-специфичные
        google_meta = GoogleOptimization.generate_google_meta_tags(content_data)
        
        # Яндекс-специфичные
        yandex_meta = YandexOptimization.generate_yandex_meta_tags(content_data)
        
        # Объединяем
        combined_meta = {**base_meta, **google_meta, **yandex_meta}
        
        return combined_meta
    
    @staticmethod
    def generate_combined_structured_data(content_type, content_data):
        """
        Генерирует комбинированные Structured Data для Google и Яндекс
        """
        # Базовые схемы
        base_schema = SEOManager.generate_structured_data(content_type, content_data)
        
        # Google-оптимизированные схемы
        google_schema = GoogleOptimization.generate_google_schema(content_type, content_data)
        
        # Яндекс-оптимизированные схемы
        yandex_schema = YandexOptimization.generate_yandex_schema(content_type, content_data)
        
        # Используем Google схему как основную (Яндекс её тоже понимает)
        return google_schema or base_schema
    
    @staticmethod
    def add_search_engines_scripts(html_content):
        """
        Добавляет скрипты для Google и Яндекс в HTML
        """
        scripts = []
        
        # Google Analytics 4 (если настроен)
        ga_id = current_app.config.get('GOOGLE_ANALYTICS_ID')
        if ga_id:
            scripts.append("""
            <!-- Google tag (gtag.js) -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=""" + str(ga_id) + """"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '""" + str(ga_id) + """');
            </script>
            """)
        
        # Яндекс.Метрика (уже есть, но можно улучшить)
        yandex_id = current_app.config.get('YANDEX_METRIKA_ID', '106548955')
        scripts.append("""
        <!-- Yandex.Metrika counter -->
        <script type="text/javascript">
           (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
           m[i].l=1*new Date();
           for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
           k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}
           })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
        
           ym(""" + str(yandex_id) + """, "init", {
                clickmap:true,
                trackLinks:true,
                accurateTrackBounce:true,
                webvisor:true,
                ecommerce:"dataLayer"
           });
        </script>
        <noscript><div><img src="https://mc.yandex.ru/watch/""" + str(yandex_id) + """" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
        <!-- /Yandex.Metrika counter -->
        """)
        
        return '\n'.join(scripts)


# API endpoints для поисковиков
@search_engines_bp.route('/api/google/verify', methods=['GET'])
def google_verification():
    """
    Endpoint для верификации Google Search Console
    """
    verification_code = current_app.config.get('GOOGLE_VERIFICATION_CODE', '')
    if verification_code:
        return verification_code, 200, {'Content-Type': 'text/plain'}
    return "Verification code not configured", 404


@search_engines_bp.route('/api/yandex/verify', methods=['GET'])
def yandex_verification():
    """
    Endpoint для верификации Яндекс.Вебмастер
    """
    verification_code = current_app.config.get('YANDEX_VERIFICATION_CODE', '')
    if verification_code:
        return verification_code, 200, {'Content-Type': 'text/plain'}
    return "Verification code not configured", 404


@search_engines_bp.route('/api/yandex/turbo/<path:path>', methods=['GET'])
def yandex_turbo_page(path):
    """
    Endpoint для Яндекс.Турбо страниц
    """
    try:
        # Генерируем Turbo-контент
        # В реальности здесь нужно загрузить контент и преобразовать в Turbo формат
        turbo_content = {
            'header': {'title': 'Всё Прост'},
            'content': '<p>Контент для Яндекс.Турбо</p>',
            'footer': {'text': '© Всё Прост'}
        }
        
        return jsonify(turbo_content), 200
    except Exception as e:
        logger.error(f"Ошибка при генерации Turbo страницы: {e}")
        return "Ошибка", 500
