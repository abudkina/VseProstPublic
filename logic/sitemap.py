# sitemap.py
"""
Модуль для генерации динамического Sitemap
Поддерживает XML Sitemap для всех типов контента
"""
from flask import Blueprint, current_app
from datetime import datetime
from logic.model import db, Problem, Solution, Category, Topic, User
from logic.utils.logger import get_logger
import xml.etree.ElementTree as ET

logger = get_logger(__name__)

sitemap_bp = Blueprint('sitemap', __name__)

# Константы для приоритета и частоты обновления
PRIORITY_HOME = 1.0
PRIORITY_CATEGORY = 0.9
PRIORITY_TOPIC = 0.8
PRIORITY_PROBLEM = 0.7
PRIORITY_SOLUTION = 0.6

CHANGE_FREQ_HOME = 'daily'
CHANGE_FREQ_CATEGORY = 'daily'
CHANGE_FREQ_TOPIC = 'weekly'
CHANGE_FREQ_PROBLEM = 'weekly'
CHANGE_FREQ_SOLUTION = 'monthly'


def generate_sitemap_xml():
    """
    Генерирует XML Sitemap со всеми страницами сайта
    Соответствует стандарту https://www.sitemaps.org/protocol.html
    """
    try:
        # Создаем корневой элемент
        urlset = ET.Element('urlset')
        urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        urlset.set('xmlns:mobile', 'http://www.google.com/schemas/sitemap-mobile/1.0')

        base_url = current_app.config.get('BASE_URL', 'https://vseprost.com')

        # 1. Главная страница
        add_url_entry(urlset, f'{base_url}/', 
                     datetime.utcnow(), PRIORITY_HOME, CHANGE_FREQ_HOME)

        # 2. Статические страницы
        static_pages = [
            '/html/solutions.html',
        ]
        for page in static_pages:
            add_url_entry(urlset, f'{base_url}{page}', 
                         datetime.utcnow(), 0.8, 'daily')

        # 3. Категории
        categories = Category.query.all()
        for category in categories:
            url = f'{base_url}/?category={category.id}'
            add_url_entry(urlset, url, 
                         category.modified_date or datetime.utcnow(),
                         PRIORITY_CATEGORY, CHANGE_FREQ_CATEGORY)

        # 4. Топики
        topics = Topic.query.all()
        for topic in topics:
            url = f'{base_url}/?topic={topic.id}'
            add_url_entry(urlset, url,
                         topic.modified_date or datetime.utcnow(),
                         PRIORITY_TOPIC, CHANGE_FREQ_TOPIC)

        # 5. Проблемы (вопросы)
        problems = Problem.query.filter_by(is_deleted=False).all()
        for problem in problems:
            # Используем slug для SEO-friendly URL
            slug = problem.slug or problem.id
            url = f'{base_url}/problem/{slug}'
            add_url_entry(urlset, url,
                         problem.modified_date or problem.created_date or datetime.utcnow(),
                         PRIORITY_PROBLEM, CHANGE_FREQ_PROBLEM,
                         image_url=problem.image)

        # 6. Решения
        solutions = Solution.query.filter_by(is_deleted=False).all()
        for solution in solutions:
            slug = solution.slug or solution.id
            url = f'{base_url}/solution/{slug}'
            add_url_entry(urlset, url,
                         solution.modified_date or solution.created_date or datetime.utcnow(),
                         PRIORITY_SOLUTION, CHANGE_FREQ_SOLUTION,
                         image_url=solution.image)

        # Конвертируем в строку
        tree_str = ET.tostring(urlset, encoding='unicode')
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        return xml_declaration + tree_str

    except Exception as e:
        logger.error(f"Ошибка при генерации sitemap: {e}")
        return None


def add_url_entry(urlset, loc, lastmod, priority, changefreq, image_url=None):
    """
    Добавляет запись URL в Sitemap
    
    Args:
        urlset: Корневой элемент XML
        loc: URL страницы
        lastmod: Дата последнего изменения
        priority: Приоритет (0.0-1.0)
        changefreq: Частота изменения
        image_url: URL изображения (опционально)
    """
    url_elem = ET.SubElement(urlset, 'url')
    
    loc_elem = ET.SubElement(url_elem, 'loc')
    loc_elem.text = loc
    
    lastmod_elem = ET.SubElement(url_elem, 'lastmod')
    lastmod_elem.text = lastmod.isoformat() if lastmod else datetime.utcnow().isoformat()
    
    changefreq_elem = ET.SubElement(url_elem, 'changefreq')
    changefreq_elem.text = changefreq
    
    priority_elem = ET.SubElement(url_elem, 'priority')
    priority_elem.text = str(priority)
    
    # Добавляем информацию об изображении если есть
    if image_url:
        image_elem = ET.SubElement(url_elem, 'image:image')
        image_loc = ET.SubElement(image_elem, 'image:loc')
        image_loc.text = image_url if image_url.startswith('http') else f'https://vseprost.com{image_url}'
        
        image_title = ET.SubElement(image_elem, 'image:title')
        image_title.text = 'Изображение контента'


def generate_sitemap_index():
    """
    Генерирует индекс Sitemap для больших сайтов
    (когда количество ссылок превышает 50,000)
    """
    try:
        sitemapindex = ET.Element('sitemapindex')
        sitemapindex.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        base_url = current_app.config.get('BASE_URL', 'https://vseprost.com')
        
        sitemaps = [
            '/api/sitemap.xml',
            '/api/sitemap_problems.xml',
            '/api/sitemap_solutions.xml',
        ]
        
        for sitemap in sitemaps:
            sitemap_elem = ET.SubElement(sitemapindex, 'sitemap')
            loc_elem = ET.SubElement(sitemap_elem, 'loc')
            loc_elem.text = f'{base_url}{sitemap}'
            
            lastmod_elem = ET.SubElement(sitemap_elem, 'lastmod')
            lastmod_elem.text = datetime.utcnow().isoformat()
        
        tree_str = ET.tostring(sitemapindex, encoding='unicode')
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        return xml_declaration + tree_str
        
    except Exception as e:
        logger.error(f"Ошибка при генерации индекса sitemap: {e}")
        return None


@sitemap_bp.route('/sitemap.xml', methods=['GET'])
def sitemap():
    """Точка входа для основного Sitemap"""
    try:
        sitemap_xml = generate_sitemap_xml()
        if sitemap_xml:
            return sitemap_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
        else:
            return "Ошибка при генерации sitemap", 500
    except Exception as e:
        logger.error(f"Ошибка в маршруте sitemap: {e}")
        return "Ошибка при генерации sitemap", 500


@sitemap_bp.route('/sitemap-index.xml', methods=['GET'])
def sitemap_index():
    """Точка входа для индекса Sitemap"""
    try:
        sitemap_index_xml = generate_sitemap_index()
        if sitemap_index_xml:
            return sitemap_index_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}
        else:
            return "Ошибка при генерации индекса sitemap", 500
    except Exception as e:
        logger.error(f"Ошибка в маршруте индекса sitemap: {e}")
        return "Ошибка при генерации индекса sitemap", 500
