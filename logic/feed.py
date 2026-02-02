# feed.py
"""
Модуль для генерации RSS/Atom Feed
Помогает поисковикам быстро находить новый контент
"""
from flask import Blueprint, current_app, Response, request
from datetime import datetime
from logic.model import db, Problem, Solution
from logic.utils.logger import get_logger
import xml.etree.ElementTree as ET

logger = get_logger(__name__)

feed_bp = Blueprint('feed', __name__)


def generate_rss_feed(content_type='all', limit=50):
    """
    Генерирует RSS 2.0 feed
    
    Args:
        content_type: 'all', 'problems', 'solutions'
        limit: максимальное количество элементов
        
    Returns:
        XML строка RSS feed
    """
    try:
        base_url = current_app.config.get('BASE_URL', 'https://vseprost.com')
        
        # Создаем корневой элемент RSS
        rss = ET.Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
        rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
        
        channel = ET.SubElement(rss, 'channel')
        
        # Метаданные канала
        title = ET.SubElement(channel, 'title')
        title.text = 'Всё Прост - Платформа для поиска решений'
        
        link = ET.SubElement(channel, 'link')
        link.text = base_url
        
        description = ET.SubElement(channel, 'description')
        description.text = 'Новые вопросы и решения на платформе Всё Прост'
        
        language = ET.SubElement(channel, 'language')
        language.text = 'ru-RU'
        
        last_build_date = ET.SubElement(channel, 'lastBuildDate')
        last_build_date.text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        pub_date = ET.SubElement(channel, 'pubDate')
        pub_date.text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Atom self link
        atom_link = ET.SubElement(channel, 'atom:link')
        atom_link.set('href', f'{base_url}/api/feed.xml')
        atom_link.set('rel', 'self')
        atom_link.set('type', 'application/rss+xml')
        
        # Получаем контент
        items = []
        
        if content_type in ('all', 'problems'):
            problems = Problem.query.filter_by(is_deleted=False)\
                .order_by(Problem.created_date.desc())\
                .limit(limit).all()
            items.extend(problems)
        
        if content_type in ('all', 'solutions'):
            solutions = Solution.query.filter_by(is_deleted=False)\
                .order_by(Solution.created_date.desc())\
                .limit(limit).all()
            items.extend(solutions)
        
        # Сортируем по дате создания
        items.sort(key=lambda x: x.created_date if hasattr(x, 'created_date') else datetime.min, reverse=True)
        items = items[:limit]
        
        # Добавляем элементы
        for item in items:
            item_elem = ET.SubElement(channel, 'item')
            
            # Title
            item_title = ET.SubElement(item_elem, 'title')
            item_title.text = item.name if hasattr(item, 'name') else str(item.id)
            
            # Link
            item_link = ET.SubElement(item_elem, 'link')
            if isinstance(item, Problem):
                slug = getattr(item, 'slug', None) or item.id
                item_link.text = f'{base_url}/problem/{slug}'
            elif isinstance(item, Solution):
                slug = getattr(item, 'slug', None) or item.id
                item_link.text = f'{base_url}/solution/{slug}'
            else:
                item_link.text = base_url
            
            # Description
            item_description = ET.SubElement(item_elem, 'description')
            description_text = item.describe if hasattr(item, 'describe') and item.describe else ''
            # Очищаем HTML теги для RSS
            import re
            description_text = re.sub(r'<[^>]+>', '', description_text)
            description_text = description_text[:500]  # Ограничиваем длину
            item_description.text = description_text
            
            # PubDate
            item_pub_date = ET.SubElement(item_elem, 'pubDate')
            created_date = item.created_date if hasattr(item, 'created_date') else datetime.utcnow()
            item_pub_date.text = created_date.strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # GUID
            item_guid = ET.SubElement(item_elem, 'guid')
            item_guid.text = item_link.text
            item_guid.set('isPermaLink', 'true')
            
            # Category
            if isinstance(item, Problem) and hasattr(item, 'category'):
                item_category = ET.SubElement(item_elem, 'category')
                item_category.text = f'Problem Category {item.category}'
        
        # Конвертируем в строку
        tree_str = ET.tostring(rss, encoding='unicode')
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        return xml_declaration + tree_str
        
    except Exception as e:
        logger.error(f"Ошибка при генерации RSS feed: {e}")
        return None


def generate_atom_feed(content_type='all', limit=50):
    """
    Генерирует Atom 1.0 feed
    
    Args:
        content_type: 'all', 'problems', 'solutions'
        limit: максимальное количество элементов
        
    Returns:
        XML строка Atom feed
    """
    try:
        base_url = current_app.config.get('BASE_URL', 'https://vseprost.com')
        
        # Создаем корневой элемент Atom
        feed = ET.Element('feed')
        feed.set('xmlns', 'http://www.w3.org/2005/Atom')
        
        # Метаданные feed
        title = ET.SubElement(feed, 'title')
        title.text = 'Всё Прост - Платформа для поиска решений'
        
        subtitle = ET.SubElement(feed, 'subtitle')
        subtitle.text = 'Новые вопросы и решения'
        
        link = ET.SubElement(feed, 'link')
        link.set('href', f'{base_url}/api/feed.xml')
        link.set('rel', 'self')
        
        link_home = ET.SubElement(feed, 'link')
        link_home.set('href', base_url)
        
        id_elem = ET.SubElement(feed, 'id')
        id_elem.text = base_url
        
        updated = ET.SubElement(feed, 'updated')
        updated.text = datetime.utcnow().isoformat() + 'Z'
        
        author = ET.SubElement(feed, 'author')
        author_name = ET.SubElement(author, 'name')
        author_name.text = 'Всё Прост'
        
        # Получаем контент (аналогично RSS)
        items = []
        
        if content_type in ('all', 'problems'):
            problems = Problem.query.filter_by(is_deleted=False)\
                .order_by(Problem.created_date.desc())\
                .limit(limit).all()
            items.extend(problems)
        
        if content_type in ('all', 'solutions'):
            solutions = Solution.query.filter_by(is_deleted=False)\
                .order_by(Solution.created_date.desc())\
                .limit(limit).all()
            items.extend(solutions)
        
        items.sort(key=lambda x: x.created_date if hasattr(x, 'created_date') else datetime.min, reverse=True)
        items = items[:limit]
        
        # Добавляем entries
        for item in items:
            entry = ET.SubElement(feed, 'entry')
            
            entry_title = ET.SubElement(entry, 'title')
            entry_title.text = item.name if hasattr(item, 'name') else str(item.id)
            
            entry_link = ET.SubElement(entry, 'link')
            if isinstance(item, Problem):
                slug = getattr(item, 'slug', None) or item.id
                entry_link.set('href', f'{base_url}/problem/{slug}')
            elif isinstance(item, Solution):
                slug = getattr(item, 'slug', None) or item.id
                entry_link.set('href', f'{base_url}/solution/{slug}')
            else:
                entry_link.set('href', base_url)
            
            entry_id = ET.SubElement(entry, 'id')
            entry_id.text = entry_link.get('href')
            
            entry_updated = ET.SubElement(entry, 'updated')
            created_date = item.created_date if hasattr(item, 'created_date') else datetime.utcnow()
            entry_updated.text = created_date.isoformat() + 'Z'
            
            entry_summary = ET.SubElement(entry, 'summary')
            summary_text = item.describe if hasattr(item, 'describe') and item.describe else ''
            import re
            summary_text = re.sub(r'<[^>]+>', '', summary_text)
            summary_text = summary_text[:500]
            entry_summary.text = summary_text
        
        # Конвертируем в строку
        tree_str = ET.tostring(feed, encoding='unicode')
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        return xml_declaration + tree_str
        
    except Exception as e:
        logger.error(f"Ошибка при генерации Atom feed: {e}")
        return None


@feed_bp.route('/feed.xml', methods=['GET'])
@feed_bp.route('/rss.xml', methods=['GET'])
def rss_feed():
    """RSS 2.0 feed endpoint"""
    try:
        content_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 50))
        
        feed_xml = generate_rss_feed(content_type, limit)
        if feed_xml:
            return Response(feed_xml, mimetype='application/rss+xml; charset=utf-8')
        else:
            return "Ошибка при генерации RSS feed", 500
    except Exception as e:
        logger.error(f"Ошибка в маршруте RSS feed: {e}")
        return "Ошибка при генерации RSS feed", 500


@feed_bp.route('/atom.xml', methods=['GET'])
def atom_feed():
    """Atom 1.0 feed endpoint"""
    try:
        content_type = request.args.get('type', 'all')
        limit = int(request.args.get('limit', 50))
        
        feed_xml = generate_atom_feed(content_type, limit)
        if feed_xml:
            return Response(feed_xml, mimetype='application/atom+xml; charset=utf-8')
        else:
            return "Ошибка при генерации Atom feed", 500
    except Exception as e:
        logger.error(f"Ошибка в маршруте Atom feed: {e}")
        return "Ошибка при генерации Atom feed", 500
