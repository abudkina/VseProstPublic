# image_search.py - утилита для генерации изображений
import os
import uuid
import base64
import requests
from typing import Optional
from openai import OpenAI
from logic.utils.logger import get_logger

logger = get_logger(__name__)

def generate_image_with_openai(name: str, description: Optional[str] = None, save_folder: str = 'uploads', 
                                model: str = 'dall-e-2', size: str = '256x256', response_format: str = 'b64_json') -> Optional[str]:
    """
    Генерация изображения через OpenAI API (DALL-E 2 или DALL-E 3)
    Изображение загружается в Yandex Object Storage, возвращается публичная ссылка
    
    Args:
        name: Название проблемы/решения (обязательно)
        description: Описание (опционально)
        save_folder: Папка для локального сохранения (fallback, если Yandex Storage недоступен)
        model: Модель для генерации ('dall-e-2' или 'dall-e-3', по умолчанию 'dall-e-2')
        size: Размер изображения ('256x256', '512x512', '1024x1024' для DALL-E 2; 
              '1024x1024', '1792x1024', '1024x1792' для DALL-E 3)
        response_format: Формат ответа ('url' или 'b64_json', по умолчанию 'b64_json')
    
    Returns:
        Публичная ссылка на изображение в Yandex Storage или локальный путь (fallback), или None в случае ошибки
    """
    if not name:
        logger.warning("generate_image_with_openai: name не указан")
        return None
    
    try:
        from config import Config
        
        # Получаем настройки API
        api_key = Config.OPENAI_API_KEY
        base_url = Config.OPENAI_API_URL
        
        if not api_key:
            logger.error("OpenAI API ключ не настроен")
            return None
        
        if not base_url:
            logger.warning("OpenAI API URL не настроен, используется стандартный")
            base_url = 'https://api.openai.com/v1'
        
        # Создаем клиент OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Формируем промпт для генерации изображения
        prompt = name
        if description:
            # Добавляем ключевые слова из описания (первые 15 слов)
            desc_words = description.split()[:15]
            if desc_words:
                prompt = f"{name}, {', '.join(desc_words)}"
        
        # Ограничиваем длину промпта (DALL-E 2: до 1000 символов, DALL-E 3: до 4000)
        max_length = 4000 if model == 'dall-e-3' else 1000
        prompt = prompt[:max_length]
        
        logger.info(f"Генерация изображения через {model} для: {prompt[:100]}...")
        
        # Определяем параметры генерации в зависимости от модели
        generate_params = {
            'model': model,
            'prompt': prompt,
            'n': 1,
            'response_format': response_format
        }
        
        # Добавляем размер только для DALL-E 2 (DALL-E 3 всегда 1024x1024)
        if model == 'dall-e-2':
            generate_params['size'] = size
        elif model == 'dall-e-3':
            # DALL-E 3 поддерживает только определенные размеры
            if size not in ['1024x1024', '1792x1024', '1024x1792']:
                size = '1024x1024'
            generate_params['size'] = size
            generate_params['quality'] = 'standard'  # или 'hd' для более высокого качества
        elif model == 'gpt-image-1':
            generate_params['size'] = size if size else '1024x1024'
            if 'quality' not in generate_params:
                generate_params['quality'] = 'low'

        # Генерируем изображение
        result = client.images.generate(**generate_params)
        
        # Получаем данные изображения
        if response_format == 'b64_json':
            image_base64 = result.data[0].b64_json
            if not image_base64:
                logger.error("Не удалось получить base64 данные изображения")
                return None
            
            # Декодируем base64
            try:
                image_bytes = base64.b64decode(image_base64)
            except Exception as e:
                logger.error(f"Ошибка декодирования base64: {e}")
                return None
        else:
            # Если формат URL, скачиваем изображение
            image_url = result.data[0].url
            if not image_url:
                logger.error("Не удалось получить URL изображения")
                return None
            
            try:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_bytes = response.content
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения по URL: {e}")
                return None
        
        # Загружаем в Yandex Storage
        try:
            from logic.utils.yandex_storage import upload_file_to_yandex_storage
            
            # Определяем расширение файла
            file_extension = 'png'  # DALL-E генерирует PNG
            
            # Загружаем изображение в Yandex Object Storage
            public_url = upload_file_to_yandex_storage(
                file_bytes=image_bytes,
                file_extension=file_extension,
                folder='generated-images'  # Папка для сгенерированных изображений
            )
            
            if public_url:
                logger.info(f"Изображение успешно сгенерировано и загружено в Yandex Storage: {public_url}")
                return public_url
            else:
                logger.warning("Не удалось загрузить изображение в Yandex Storage, используем fallback")
                # Fallback: сохраняем локально, если Yandex Storage недоступен
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                filename = f"{uuid.uuid4().hex}.png"
                filepath = os.path.join(save_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                logger.info(f"Изображение сохранено локально (fallback): {filepath}")
                return filepath
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}", exc_info=True)
            # Fallback: сохраняем локально
            try:
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                filename = f"{uuid.uuid4().hex}.png"
                filepath = os.path.join(save_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                logger.info(f"Изображение сохранено локально (fallback после ошибки): {filepath}")
                return filepath
            except Exception as fallback_error:
                logger.error(f"Ошибка fallback сохранения: {fallback_error}")
                return None
            
    except Exception as e:
        logger.error(f"Ошибка генерации изображения через OpenAI API: {e}", exc_info=True)
        return None
