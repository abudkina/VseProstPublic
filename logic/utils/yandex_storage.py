# yandex_storage.py - утилита для работы с Yandex Object Storage
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import uuid
from io import BytesIO
from PIL import Image
from logic.utils.logger import get_logger

logger = get_logger(__name__)

def compress_image(image_bytes, max_size=(1920, 1920), quality=85, convert_large_png_to_jpeg=True):
    """
    Сжимает изображение перед загрузкой
    
    Args:
        image_bytes: Байты исходного изображения
        max_size: Максимальный размер (ширина, высота) в пикселях
        quality: Качество JPEG (1-100, по умолчанию 85)
        convert_large_png_to_jpeg: Конвертировать большие PNG в JPEG для лучшего сжатия
    
    Returns:
        tuple: (сжатые байты, расширение файла) или (None, None) в случае ошибки
    """
    try:
        # Открываем изображение из байтов
        image = Image.open(BytesIO(image_bytes))
        original_format = image.format
        original_size = len(image_bytes)
        
        # Определяем исходное расширение
        format_map = {
            'PNG': 'png',
            'JPEG': 'jpg',
            'JPG': 'jpg',
            'GIF': 'gif',
            'WEBP': 'webp'
        }
        original_extension = format_map.get(original_format, 'png')
        
        # Конвертируем RGBA в RGB для JPEG (если нужно)
        # Конвертируем только если изображение большое и включена конвертация
        # Приблизительный размер в МБ (учитываем что PNG может быть сжатым)
        pixel_count = image.size[0] * image.size[1]
        # Примерная оценка: RGBA = 4 байта на пиксель, RGB = 3 байта
        estimated_size_mb = (pixel_count * 4) / (1024 * 1024)
        should_convert_to_jpeg = convert_large_png_to_jpeg and image.mode in ('RGBA', 'LA', 'P') and estimated_size_mb > 0.5
        
        if should_convert_to_jpeg:
            # Создаем белый фон для прозрачных изображений
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                rgb_image.paste(image, mask=image.split()[-1])
            else:
                rgb_image.paste(image)
            image = rgb_image
            target_format = 'JPEG'
            target_extension = 'jpg'
        else:
            # Сохраняем исходный формат, но конвертируем режим если нужно
            if image.mode == 'P':
                # Палитровые изображения конвертируем в RGBA для лучшей обработки
                image = image.convert('RGBA')
            target_format = original_format or 'PNG'
            target_extension = original_extension
        
        # Изменяем размер, если изображение слишком большое
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            logger.info(f"Изображение уменьшено до {image.size}")
        
        # Сохраняем в байты с оптимизацией
        output = BytesIO()
        
        if target_format == 'JPEG':
            # Для JPEG используем качество
            image.save(output, format='JPEG', quality=quality, optimize=True)
        elif target_format == 'PNG':
            # Для PNG используем оптимизацию
            image.save(output, format='PNG', optimize=True)
            # Пробуем дополнительное сжатие через PIL
            try:
                output.seek(0)
                png_image = Image.open(output)
                output_optimized = BytesIO()
                png_image.save(output_optimized, format='PNG', optimize=True)
                output = output_optimized
            except Exception:
                pass  # Используем исходное сохранение
        else:
            # Для других форматов сохраняем как есть
            image.save(output, format=target_format, optimize=True)
        
        output.seek(0)
        compressed_bytes = output.read()
        compressed_size = len(compressed_bytes)
        
        # Логируем результат сжатия
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        logger.info(
            f"Изображение сжато: {original_size} байт -> {compressed_size} байт "
            f"({compression_ratio:.1f}% уменьшение), формат: {target_extension}"
        )
        
        return compressed_bytes, target_extension
        
    except Exception as e:
        logger.error(f"Ошибка сжатия изображения: {e}", exc_info=True)
        # В случае ошибки возвращаем исходные данные
        return None, None

def get_yandex_storage_client():
    """
    Создает клиент для работы с Yandex Object Storage (S3-совместимый API)
    
    Returns:
        boto3 S3 client или None в случае ошибки
    """
    try:
        from config import Config as AppConfig
        
        # Получаем настройки из переменных окружения
        access_key = os.getenv('YANDEX_STORAGE_ACCESS_KEY')
        secret_key = os.getenv('YANDEX_STORAGE_SECRET_KEY')
        endpoint_url = os.getenv('YANDEX_STORAGE_ENDPOINT', 'https://storage.yandexcloud.net')
        bucket_name = os.getenv('YANDEX_STORAGE_BUCKET')
        
        if not access_key or not secret_key or not bucket_name:
            logger.warning("Yandex Storage credentials не настроены")
            return None, None
        
        # Создаем клиент S3 для Yandex Object Storage
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='ru-central1'
        )
        
        return s3_client, bucket_name
        
    except Exception as e:
        logger.error(f"Ошибка создания клиента Yandex Storage: {e}", exc_info=True)
        return None, None

def upload_file_to_yandex_storage(file_bytes, file_extension='png', folder='images', compress=True, 
                                   max_size=(1920, 1920), quality=85):
    """
    Загружает файл в Yandex Object Storage с автоматическим сжатием изображений
    
    Args:
        file_bytes: Байты файла для загрузки
        file_extension: Расширение файла (png, jpg, etc.)
        folder: Папка в бакете для хранения файлов
        compress: Сжимать ли изображение перед загрузкой (по умолчанию True)
        max_size: Максимальный размер изображения в пикселях (ширина, высота) при сжатии
        quality: Качество JPEG при сжатии (1-100, по умолчанию 85)
    
    Returns:
        Публичная ссылка на файл или None в случае ошибки
    """
    try:
        s3_client, bucket_name = get_yandex_storage_client()
        
        if not s3_client or not bucket_name:
            return None
        
        # Сжимаем изображение, если это изображение и включено сжатие
        final_bytes = file_bytes
        final_extension = file_extension
        
        if compress and file_extension.lower() in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
            compressed_bytes, new_extension = compress_image(
                file_bytes, 
                max_size=max_size, 
                quality=quality,
                convert_large_png_to_jpeg=True
            )
            
            if compressed_bytes and new_extension:
                final_bytes = compressed_bytes
                final_extension = new_extension
                logger.info(f"Изображение сжато перед загрузкой: {file_extension} -> {final_extension}")
            else:
                logger.warning("Не удалось сжать изображение, загружаем оригинал")
        
        # Создаем уникальное имя файла
        filename = f"{uuid.uuid4().hex}.{final_extension}"
        object_key = f"{folder}/{filename}" if folder else filename
        
        # Получаем endpoint URL для формирования публичной ссылки
        endpoint_url = os.getenv('YANDEX_STORAGE_ENDPOINT', 'https://storage.yandexcloud.net')
        
        # Определяем Content-Type
        content_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = content_type_map.get(final_extension.lower(), 'application/octet-stream')
        
        # Загружаем файл в хранилище
        # Примечание: для публичного доступа бакет должен быть настроен как публичный
        # или нужно использовать подписанные URL
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=final_bytes,
            ContentType=content_type
        )
        
        # Формируем публичную ссылку
        # Формат: https://storage.yandexcloud.net/bucket-name/folder/filename.ext
        # Или: https://bucket-name.storage.yandexcloud.net/folder/filename.ext (если настроен кастомный домен)
        public_url = f"{endpoint_url}/{bucket_name}/{object_key}"
        
        logger.info(f"Файл успешно загружен в Yandex Storage: {public_url}")
        return public_url
        
    except ClientError as e:
        logger.error(f"Ошибка загрузки файла в Yandex Storage: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке в Yandex Storage: {e}", exc_info=True)
        return None

def delete_file_from_yandex_storage(file_url):
    """
    Удаляет файл из Yandex Object Storage по URL
    
    Args:
        file_url: URL файла в хранилище
    
    Returns:
        True если успешно, False в случае ошибки
    """
    try:
        s3_client, bucket_name = get_yandex_storage_client()
        
        if not s3_client or not bucket_name:
            return False
        
        # Извлекаем ключ объекта из URL
        # Формат: https://storage.yandexcloud.net/bucket-name/folder/filename.ext
        if bucket_name in file_url:
            object_key = file_url.split(f"{bucket_name}/", 1)[1]
        else:
            logger.warning(f"Не удалось извлечь ключ объекта из URL: {file_url}")
            return False
        
        # Удаляем файл
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=object_key
        )
        
        logger.info(f"Файл успешно удален из Yandex Storage: {object_key}")
        return True
        
    except ClientError as e:
        logger.error(f"Ошибка удаления файла из Yandex Storage: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при удалении из Yandex Storage: {e}", exc_info=True)
        return False
