# yandex_storage.py - утилита для работы с Yandex Object Storage
import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import uuid
from logic.utils.logger import get_logger

logger = get_logger(__name__)

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

def upload_file_to_yandex_storage(file_bytes, file_extension='png', folder='images'):
    """
    Загружает файл в Yandex Object Storage
    
    Args:
        file_bytes: Байты файла для загрузки
        file_extension: Расширение файла (png, jpg, etc.)
        folder: Папка в бакете для хранения файлов
    
    Returns:
        Публичная ссылка на файл или None в случае ошибки
    """
    try:
        s3_client, bucket_name = get_yandex_storage_client()
        
        if not s3_client or not bucket_name:
            return None
        
        # Создаем уникальное имя файла
        filename = f"{uuid.uuid4().hex}.{file_extension}"
        object_key = f"{folder}/{filename}" if folder else filename
        
        # Получаем endpoint URL для формирования публичной ссылки
        endpoint_url = os.getenv('YANDEX_STORAGE_ENDPOINT', 'https://storage.yandexcloud.net')
        
        # Загружаем файл в хранилище
        # Примечание: для публичного доступа бакет должен быть настроен как публичный
        # или нужно использовать подписанные URL
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=file_bytes,
            ContentType=f'image/{file_extension}' if file_extension in ['png', 'jpg', 'jpeg', 'gif'] else 'application/octet-stream'
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
