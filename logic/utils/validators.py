# validators.py - функции валидации
import re
from typing import Tuple, Optional

def validate_email(email: str) -> bool:
    """
    Проверяет корректность email-адреса

    Args:
        email: Email адрес для проверки

    Returns:
        True если email корректен, иначе False
    """
    if not email:
        return False
    # RFC 5322 compliant email regex (упрощенная версия)
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет сложность пароля согласно современным стандартам безопасности

    Требования:
    - Минимум 12 символов (рекомендация NIST 2023)
    - Хотя бы одна заглавная буква
    - Хотя бы одна строчная буква
    - Хотя бы одна цифра
    - Хотя бы один специальный символ
    - Не должен содержать очевидных паттернов

    Args:
        password: Пароль для проверки

    Returns:
        Tuple[bool, Optional[str]]: (валидность, сообщение об ошибке)
    """
    if not password:
        return False, "Пароль не может быть пустым"

    # Минимальная длина согласно NIST SP 800-63B
    if len(password) < 12:
        return False, "Пароль должен содержать минимум 12 символов"

    # Максимальная длина для предотвращения DoS
    if len(password) > 128:
        return False, "Пароль не может быть длиннее 128 символов"

    # Проверка на наличие заглавных букв
    if not re.search(r'[A-Z]', password):
        return False, "Пароль должен содержать хотя бы одну заглавную букву"

    # Проверка на наличие строчных букв
    if not re.search(r'[a-z]', password):
        return False, "Пароль должен содержать хотя бы одну строчную букву"

    # Проверка на наличие цифр
    if not re.search(r'[0-9]', password):
        return False, "Пароль должен содержать хотя бы одну цифру"

    # Проверка на наличие специальных символов
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        return False, "Пароль должен содержать хотя бы один специальный символ (!@#$%^&* и т.д.)"

    # Проверка на очевидные паттерны (последовательности)
    common_patterns = [
        r'(012|123|234|345|456|567|678|789|890)',  # Числовые последовательности
        r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',
        r'(qwer|wert|erty|rtyu|tyui|yuio|uiop|asdf|sdfg|dfgh|fghj|ghjk|hjkl|zxcv|xcvb|cvbn|vbnm)',  # Клавиатура
    ]

    password_lower = password.lower()
    for pattern in common_patterns:
        if re.search(pattern, password_lower):
            return False, "Пароль содержит очевидные последовательности символов"

    # Проверка на повторяющиеся символы (более 3 подряд)
    if re.search(r'(.)\1{3,}', password):
        return False, "Пароль не должен содержать более 3 одинаковых символов подряд"

    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность имени пользователя

    Args:
        username: Имя пользователя для проверки

    Returns:
        Tuple[bool, Optional[str]]: (валидность, сообщение об ошибке)
    """
    if not username:
        return False, "Имя пользователя не может быть пустым"

    if len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"

    if len(username) > 32:
        return False, "Имя пользователя не может быть длиннее 32 символов"

    # Только буквы, цифры, подчеркивание и дефис
    if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
        return False, "Имя пользователя может содержать только буквы, цифры, _ и -"

    # Не должно начинаться с цифры
    if username[0].isdigit():
        return False, "Имя пользователя не может начинаться с цифры"

    return True, None

def parse_int_list(value, separator=','):
    """Парсит строку с разделителями в список целых чисел"""
    if not value:
        return []
    
    result = []
    for item in value.split(separator):
        item = item.strip()
        if item:
            try:
                result.append(int(item))
            except ValueError:
                pass
    return result

def parse_bool(value):
    """Парсит строковое значение в boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', 'on', '1', 'yes']
    return bool(value)


def validate_string(value: str, min_length: int = 1, max_length: int = 1000, field_name: str = 'строка') -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность строки
    
    Args:
        value: Строка для проверки
        min_length: Минимальная длина
        max_length: Максимальная длина
        field_name: Имя поля для сообщения об ошибке
    
    Returns:
        Tuple[bool, Optional[str]]: (валидность, сообщение об ошибке)
    """
    if not value:
        return False, f"{field_name} не может быть пустым"
    
    if not isinstance(value, str):
        return False, f"{field_name} должно быть строкой"
    
    if len(value) < min_length:
        return False, f"{field_name} должно содержать минимум {min_length} символов"
    
    if len(value) > max_length:
        return False, f"{field_name} не может быть длиннее {max_length} символов"
    
    return True, None
