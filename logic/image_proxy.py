# image_proxy.py - прокси для загрузки изображений из интернета
from flask import Blueprint, request, Response, jsonify
import requests
from urllib.parse import urlparse
from logic.utils.logger import get_logger

logger = get_logger(__name__)

image_proxy_bp = Blueprint('image_proxy', __name__, url_prefix='/api')

@image_proxy_bp.route('/image-proxy', methods=['GET'])
def proxy_image():
    """
    Прокси для загрузки изображений из интернета с правильными CORS заголовками
    Использование: /api/image-proxy?url=https://picsum.photos/seed/123/400/300
    """
    try:
        image_url = request.args.get('url')
        
        if not image_url:
            logger.warning("Ошибка: URL не указан")
            return jsonify({'error': 'URL не указан'}), 400
        
        # Декодируем URL если нужно
        from urllib.parse import unquote
        image_url = unquote(image_url)
        
        logger.debug(f"Запрос прокси для изображения: {image_url}")
        
        # Проверяем, что URL валидный
        parsed = urlparse(image_url)
        if not parsed.scheme or not parsed.netloc:
            logger.warning(f"Ошибка: Некорректный URL - {image_url}")
            return jsonify({'error': 'Некорректный URL'}), 400
        
        # Разрешаем только определенные домены для безопасности
        # Используем источники, которые работают в России
        allowed_domains = [
            'via.placeholder.com',
            'placehold.co',
            'dummyimage.com',
            'placeholder.com',
            'loremflickr.com',
            'picsum.photos'  # Оставляем на случай, если заработает
        ]
        
        # Проверяем домен
        domain_allowed = False
        for allowed_domain in allowed_domains:
            if allowed_domain in parsed.netloc:
                domain_allowed = True
                break
        
        if not domain_allowed:
            logger.warning(f"Ошибка: Домен не разрешен - {parsed.netloc}")
            return jsonify({'error': 'Домен не разрешен', 'domain': parsed.netloc}), 403
        
        # Загружаем изображение
        try:
            logger.debug(f"Загружаем изображение с {image_url}")
            response = requests.get(
                image_url,
                timeout=15,
                stream=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                allow_redirects=True
            )
            response.raise_for_status()
            
            logger.debug(f"Изображение загружено, статус: {response.status_code}, content-type: {response.headers.get('content-type')}")
            
            # Проверяем, что это изображение
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower():
                logger.warning(f"Ошибка: Не является изображением - {content_type}")
                return jsonify({'error': 'Не является изображением', 'content_type': content_type}), 400
            
            # Читаем содержимое
            image_data = response.content
            
            logger.debug(f"Изображение успешно загружено, размер: {len(image_data)} байт")
            
            # Возвращаем изображение с правильными заголовками
            return Response(
                image_data,
                mimetype=content_type,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Cache-Control': 'public, max-age=86400'  # Кешируем на 1 день
                }
            )
            
        except requests.exceptions.Timeout:
            logger.warning(f"Ошибка: Таймаут при загрузке изображения {image_url}")
            return jsonify({'error': 'Таймаут при загрузке изображения'}), 504
        except requests.exceptions.RequestException as e:
            logger.exception(f"Ошибка загрузки изображения {image_url}: {e}")
            return jsonify({'error': 'Ошибка загрузки изображения', 'details': str(e)}), 500

    except Exception as e:
        logger.exception(f"Ошибка прокси изображения: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера', 'details': str(e)}), 500

