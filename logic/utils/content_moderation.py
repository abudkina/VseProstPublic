# content_moderation.py - проверка изображений на нежелательный контент (NudeNet)
from typing import Tuple, Optional
from logic.utils.logger import get_logger

logger = get_logger(__name__)

# Классы NudeNet, считающиеся нежелательным контентом (блокируем загрузку)
UNSAFE_CLASSES = frozenset({
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "MALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
})

# Порог уверенности (0.0–1.0): выше — считаем детекцию достоверной
CONFIDENCE_THRESHOLD = 0.5

_detector = None


def _get_detector():
    global _detector
    if _detector is None:
        try:
            from nudenet import NudeDetector
            _detector = NudeDetector()
        except Exception as e:
            logger.warning(f"NudeNet не загружен, модерация отключена: {e}")
    return _detector


def is_image_safe(image_bytes: bytes) -> Tuple[bool, Optional[str]]:
    """
    Проверка изображения на нежелательный контент (NudeNet).

    Args:
        image_bytes: байты изображения (PNG, JPEG, etc.)

    Returns:
        (True, None) если контент допустим,
        (False, "сообщение") если контент недопустим или ошибка проверки.
    """
    detector = _get_detector()
    if detector is None:
        return True, None  # при недоступности NudeNet пропускаем

    try:
        detections = detector.detect(image_bytes)
    except Exception as e:
        logger.warning(f"Ошибка NudeNet при проверке изображения: {e}")
        return False, "Не удалось проверить изображение. Попробуйте другой файл."

    for d in detections:
        cls_name = d.get("class", "")
        score = float(d.get("score", 0))
        if cls_name in UNSAFE_CLASSES and score >= CONFIDENCE_THRESHOLD:
            logger.info(f"Модерация: отклонено, класс={cls_name}, score={score:.2f}")
            return False, "Загрузка отклонена: изображение содержит недопустимый контент."

    return True, None
