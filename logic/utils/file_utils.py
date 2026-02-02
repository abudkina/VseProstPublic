# file_utils.py - утилиты для работы с файлами
import os
import uuid
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from logic.utils.logger import get_logger

logger = get_logger(__name__)

# Настройка загрузки файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB (снижено с 32MB для безопасности)
MIN_FILE_SIZE = 100  # 100 bytes (защита от пустых файлов)

# MIME типы для проверки
ALLOWED_MIME_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/gif': 'gif',
    'image/webp': 'webp'
}


def allowed_file(filename: str) -> bool:
    """
    Проверка расширения файла

    Args:
        filename: Имя файла

    Returns:
        bool: True если расширение разрешено
    """
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    Проверка размера файла

    Args:
        file: Загружаемый файл

    Returns:
        Tuple[bool, Optional[str]]: (валидность, сообщение об ошибке)
    """
    if not file:
        return False, "Файл не предоставлен"

    # Получаем размер файла
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Возвращаем указатель в начало

    if file_size < MIN_FILE_SIZE:
        return False, f"Файл слишком маленький (минимум {MIN_FILE_SIZE} байт)"

    if file_size > MAX_FILE_SIZE:
        return False, f"Файл слишком большой (максимум {MAX_FILE_SIZE // (1024 * 1024)} МБ)"

    return True, None


def detect_image_type(header: bytes) -> Optional[str]:
    """
    Определение типа изображения по magic bytes (замена для imghdr)
    
    Args:
        header: Первые байты файла (минимум 12 байт для WebP)
    
    Returns:
        Optional[str]: Тип изображения ('png', 'jpg', 'gif', 'webp') или None
    """
    if not header or len(header) < 4:
        return None
    
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if header.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'png'
    
    # JPEG: FF D8 FF
    if header.startswith(b'\xFF\xD8\xFF'):
        return 'jpg'
    
    # GIF: 47 49 46 38 (GIF8)
    if header.startswith(b'GIF8'):
        return 'gif'
    
    # WebP: RIFF....WEBP (проверяем первые 12 байт)
    if len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return 'webp'
    
    return None


def validate_image_content(file: FileStorage) -> Tuple[bool, Optional[str]]:
    """
    Проверка содержимого файла (magic bytes) для подтверждения, что это изображение
    SECURITY: Защита от загрузки исполняемых файлов под видом изображений

    Args:
        file: Загружаемый файл

    Returns:
        Tuple[bool, Optional[str]]: (валидность, сообщение об ошибке)
    """
    if not file:
        return False, "Файл не предоставлен"

    # Читаем начало файла для проверки magic bytes (12 байт достаточно для всех форматов)
    header = file.read(12)
    file.seek(0)  # Возвращаем указатель в начало

    # Определяем тип изображения по magic bytes
    image_type = detect_image_type(header)

    if not image_type:
        return False, "Файл не является корректным изображением"

    if image_type not in ALLOWED_EXTENSIONS:
        return False, f"Тип изображения {image_type} не разрешен"

    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Безопасное имя файла (дополнительная защита поверх secure_filename)

    Args:
        filename: Исходное имя файла

    Returns:
        str: Безопасное имя файла
    """
    # Используем secure_filename от Werkzeug
    safe_name = secure_filename(filename)

    # Дополнительно удаляем все кроме букв, цифр, точки и дефиса
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '.-_')

    # Ограничиваем длину имени
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:250] + ext

    return safe_name or 'unnamed'


def save_file(file: FileStorage) -> Optional[str]:
    """
    Сохранение файла на сервере с полной валидацией

    Args:
        file: Загружаемый файл

    Returns:
        Optional[str]: Путь к сохраненному файлу или None при ошибке
    """
    if not file or not file.filename:
        return None

    # Проверка расширения
    if not allowed_file(file.filename):
        return None

    # Проверка размера файла
    is_valid_size, size_error = validate_file_size(file)
    if not is_valid_size:
        raise ValueError(size_error)

    # SECURITY: Проверка содержимого файла (magic bytes)
    is_valid_content, content_error = validate_image_content(file)
    if not is_valid_content:
        raise ValueError(content_error)

    # Создаем уникальное безопасное имя файла
    ext = file.filename.rsplit('.', 1)[1].lower()
    # SECURITY: Используем UUID для предотвращения конфликтов и угадывания имен
    filename = f"{uuid.uuid4().hex}.{ext}"

    # Создаем папку uploads, если её нет
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, mode=0o755)  # Безопасные права доступа

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # SECURITY: Проверка, что путь не выходит за пределы UPLOAD_FOLDER
    abs_upload_folder = os.path.abspath(UPLOAD_FOLDER)
    abs_filepath = os.path.abspath(filepath)

    if not abs_filepath.startswith(abs_upload_folder):
        raise ValueError("Недопустимый путь к файлу")

    # Сохраняем файл
    file.save(filepath)

    # SECURITY: Устанавливаем безопасные права доступа
    os.chmod(filepath, 0o644)

    return filepath


def delete_file(filepath: str) -> bool:
    """
    Безопасное удаление файла с сервера

    Args:
        filepath: Путь к файлу

    Returns:
        bool: True если файл удален успешно
    """
    if not filepath:
        return False

    # SECURITY: Проверка, что путь не выходит за пределы UPLOAD_FOLDER
    abs_upload_folder = os.path.abspath(UPLOAD_FOLDER)
    abs_filepath = os.path.abspath(filepath)

    if not abs_filepath.startswith(abs_upload_folder):
        raise ValueError("Недопустимый путь к файлу")

    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except OSError as e:
            # Логируем ошибку, но не раскрываем детали пользователю
            logger.warning(f"Ошибка удаления файла: {e}")
            return False
    return False
