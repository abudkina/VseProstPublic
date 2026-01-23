# image_generation.py - API для генерации изображений через OpenAI DALL-E
from flask import Blueprint, jsonify, request, g
from logic.middleware import token_required
from logic.utils.image_search import generate_image_with_openai
from logic.utils.logger import get_logger
from logic.utils.validators import validate_string

logger = get_logger(__name__)

image_generation_bp = Blueprint('image_generation', __name__, url_prefix='/api')


@image_generation_bp.route('/generate-image', methods=['POST'])
@token_required
def generate_image():
    """
    Генерация изображения через OpenAI DALL-E API
    
    Тело запроса (JSON):
    {
        "prompt": "описание изображения",  # обязательное
        "description": "дополнительное описание",  # опционально
        "model": "dall-e-2" или "dall-e-3",  # опционально, по умолчанию "dall-e-2"
        "size": "256x256" или "512x512" или "1024x1024",  # опционально, по умолчанию "256x256"
        "response_format": "b64_json" или "url"  # опционально, по умолчанию "b64_json"
    }
    
    Returns:
        JSON с публичной ссылкой на изображение в Yandex Storage
    """
    try:
        # Получаем данные из запроса
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Тело запроса должно быть в формате JSON'}), 400
        
        # Валидация промпта
        prompt = data.get('prompt') or data.get('name')  # Поддержка обоих полей для совместимости
        if not prompt:
            return jsonify({'error': 'Поле "prompt" или "name" обязательно'}), 400
        
        # Валидация строки
        is_valid, error_msg = validate_string(prompt, min_length=1, max_length=4000, field_name='prompt')
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Получаем опциональные параметры
        description = data.get('description')
        model = data.get('model', 'dall-e-2')  # По умолчанию DALL-E 2 (дешевле)
        size = data.get('size', '256x256')  # По умолчанию минимальный размер
        response_format = data.get('response_format', 'b64_json')
        
        # Валидация модели
        if model not in ['dall-e-2', 'dall-e-3']:
            return jsonify({'error': 'Модель должна быть "dall-e-2" или "dall-e-3"'}), 400
        
        # Валидация размера для DALL-E 2
        if model == 'dall-e-2':
            valid_sizes = ['256x256', '512x512', '1024x1024']
            if size not in valid_sizes:
                return jsonify({
                    'error': f'Для DALL-E 2 размер должен быть одним из: {", ".join(valid_sizes)}'
                }), 400
        # Валидация размера для DALL-E 3
        elif model == 'dall-e-3':
            valid_sizes = ['1024x1024', '1792x1024', '1024x1792']
            if size not in valid_sizes:
                size = '1024x1024'  # Используем размер по умолчанию для DALL-E 3
                logger.info(f"Неверный размер для DALL-E 3, используется размер по умолчанию: {size}")
        
        # Валидация формата ответа
        if response_format not in ['b64_json', 'url']:
            return jsonify({'error': 'response_format должен быть "b64_json" или "url"'}), 400
        
        # Валидация описания, если указано
        if description:
            is_valid, error_msg = validate_string(description, min_length=1, max_length=4000, field_name='description')
            if not is_valid:
                return jsonify({'error': error_msg}), 400
        
        # Получаем user_id из контекста (для логирования)
        user_id = getattr(g, 'user_id', None)
        logger.info(f"Пользователь {user_id} запросил генерацию изображения: {prompt[:100]}...")
        
        # Генерируем изображение
        image_url = generate_image_with_openai(
            name=prompt,
            description=description,
            model=model,
            size=size,
            response_format=response_format
        )
        
        if not image_url:
            logger.error(f"Не удалось сгенерировать изображение для промпта: {prompt[:100]}...")
            return jsonify({
                'error': 'Не удалось сгенерировать изображение. Проверьте настройки OpenAI API и Yandex Storage.'
            }), 500
        
        logger.info(f"Изображение успешно сгенерировано для пользователя {user_id}: {image_url}")
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'prompt': prompt,
            'model': model,
            'size': size
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}", exc_info=True)
        return jsonify({
            'error': 'Внутренняя ошибка сервера при генерации изображения'
        }), 500


@image_generation_bp.route('/generate-image/info', methods=['GET'])
def get_generation_info():
    """
    Получение информации о доступных моделях и параметрах генерации изображений
    
    Returns:
        JSON с информацией о моделях и параметрах
    """
    return jsonify({
        'models': {
            'dall-e-2': {
                'name': 'DALL-E 2',
                'description': 'Более экономичная модель, быстрая генерация',
                'sizes': ['256x256', '512x512', '1024x1024'],
                'max_prompt_length': 1000,
                'response_formats': ['b64_json', 'url']
            },
            'dall-e-3': {
                'name': 'DALL-E 3',
                'description': 'Более качественная модель, лучшая детализация',
                'sizes': ['1024x1024', '1792x1024', '1024x1792'],
                'max_prompt_length': 4000,
                'response_formats': ['b64_json', 'url'],
                'quality_options': ['standard', 'hd']
            }
        },
        'defaults': {
            'model': 'dall-e-2',
            'size': '256x256',
            'response_format': 'b64_json'
        }
    }), 200
