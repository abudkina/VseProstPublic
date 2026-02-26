# normalizers.py - функции нормализации имен

def capitalize_title(text):
    """Первая буква заглавная, остальные строчные (названия, заголовки)."""
    if not text or not str(text).strip():
        return "" if text is None else str(text)
    s = str(text).strip()
    return s[0].upper() + s[1:].lower() if s else s


def capitalize_first(text):
    """Только первая буква строки заглавная (описания)."""
    if not text or not str(text).strip():
        return "" if text is None else str(text)
    s = str(text).strip()
    return s[0].upper() + s[1:] if len(s) > 1 else s.upper()


def normalize_category_name(name):
    """
    Нормализует имя категории:
    - Убирает пробелы по краям
    - Приводит к нижнему регистру
    - Заменяет букву "ё" на "е" (и строчную, и заглавную)
    """
    if not name:
        return ""
    
    # Убираем пробелы по краям
    name = name.strip()
    
    # Приводим к нижнему регистру
    name = name.lower()
    
    # Заменяем ё/Ё на е
    name = name.replace('ё', 'е')
    
    return name

def normalize_hashtag_name(name):
    """
    Нормализует имя хэштега:
    - Убирает символ # в начале, если есть
    - Убирает пробелы по краям
    - Приводит к нижнему регистру
    - Заменяет букву "ё" на "е" (и строчную, и заглавную)
    """
    if not name:
        return ""
    
    # Убираем символ # в начале
    if name.startswith('#'):
        name = name[1:]
    
    # Убираем пробелы по краям
    name = name.strip()
    
    # Приводим к нижнему регистру
    name = name.lower()
    
    # Заменяем ё/Ё на е
    name = name.replace('ё', 'е')
    
    return name


def normalize_category_display_name(name):
    """Имя категории для сохранения: с большой буквы."""
    return capitalize_title(name) if name else ""


def normalize_topic_name(name):
    """
    Нормализация имени темы:
    - Убирает пробелы по краям
    - Делает первую букву заглавной, остальные строчные
    """
    if not name:
        return ""
    
    # Убираем пробелы по краям
    name = name.strip()
    
    # Первая буква заглавная, остальные строчные
    if name:
        name = name[0].upper() + name[1:].lower()
    
    return name
