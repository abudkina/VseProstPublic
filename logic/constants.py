"""Application constants"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_INTERNAL_ERROR = 500

# Pagination
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 100
DEFAULT_OFFSET = 0

# File Upload
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 32 * 1024 * 1024  # 32 MB
DEFAULT_IMAGE_PATH = '../images/default.png'

# Token Expiry (in seconds)
ACCESS_TOKEN_EXPIRY = 15 * 60  # 15 minutes
REFRESH_TOKEN_EXPIRY = 30 * 24 * 3600  # 30 days
PASSWORD_RESET_TOKEN_EXPIRY = 3600  # 1 hour

# User Activity Types
ACTIVITY_TYPE_CREATE = 'create'
ACTIVITY_TYPE_SEARCH = 'search'
ACTIVITY_TYPE_FAVORITE = 'favorite'
ACTIVITY_TYPE_VIEW = 'view'

# Entity Types
ENTITY_TYPE_PROBLEM = 'problem'
ENTITY_TYPE_SOLUTION = 'solution'

# Rating Types
RATING_TYPE_PRICE = 'price'
RATING_TYPE_EFFICIENCY = 'efficiency'
RATING_TYPE_COMPLEXITY = 'complexity'
RATING_TYPE_TIME = 'time'

# Recommendation Settings
RECOMMENDATION_DAYS_LOOKBACK = 30
RECOMMENDATION_LIMIT = 10
RECOMMENDATION_SIMILARITY_THRESHOLD = 0.3

# Search Settings
MIN_SEARCH_QUERY_LENGTH = 2
MAX_HASHTAGS_RESULTS = 20

# ML Model Settings
DEFAULT_EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIMENSION = 384

# Error Messages
ERROR_MISSING_DATA = 'Отсутствуют данные'
ERROR_UNAUTHORIZED = 'Необходима авторизация'
ERROR_INVALID_CREDENTIALS = 'Неверное имя пользователя или пароль'
ERROR_USER_NOT_FOUND = 'Пользователь не найден'
ERROR_INTERNAL_ERROR = 'Внутренняя ошибка сервера'
ERROR_DATABASE_ERROR = 'Ошибка базы данных'
ERROR_INVALID_TOKEN = 'Недействительный токен'
ERROR_TOKEN_EXPIRED = 'Срок действия токена истек'

# Success Messages
SUCCESS_LOGIN = 'Вход выполнен успешно'
SUCCESS_LOGOUT = 'Выход выполнен успешно'
SUCCESS_CREATED = 'Создано успешно'
SUCCESS_UPDATED = 'Обновлено успешно'
SUCCESS_DELETED = 'Удалено успешно'
SUCCESS_TOKEN_REFRESHED = 'Токен обновлён'
