# VseProst - Платформа для решения проблем

Веб-приложение для публикации проблем и предложения решений с системой рекомендаций на базе Machine Learning.

## Возможности

- 🔐 Система авторизации и регистрации с JWT
- 📝 Создание и управление проблемами и решениями
- 🏷️ Система хештегов и категорий
- ⭐ Избранное и корзина
- 💬 Комментарии и рейтинги
- 🤖 ML-рекомендации на основе активности пользователя
- 📧 Восстановление пароля по email
- 🔔 Система уведомлений
- 🛒 Платные решения с корзиной

## Технологический стек

### Backend
- Python 3.8+
- Flask 2.3.3
- SQLAlchemy (MySQL/MariaDB)
- JWT для аутентификации
- sentence-transformers для ML рекомендаций
- bcrypt для хеширования паролей

### Frontend
- Vanilla JavaScript (ES6+)
- HTML5 / CSS3
- Модульная архитектура

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd VseProst
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env и заполните все значения
```

**Важно**: Сгенерируйте сильный JWT_SECRET:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Настройка базы данных

```bash
# Создайте базу данных MySQL
mysql -u root -p
CREATE DATABASE vseprost CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 5. Запуск приложения

```bash
python app.py
```

Приложение будет доступно по адресу: `http://127.0.0.1:8080`

## Структура проекта

```
VseProst/
├── app.py                      # Точка входа приложения
├── config.py                   # Конфигурация
├── .env.example                # Пример переменных окружения
├── requirements.txt            # Python зависимости
│
├── logic/                      # Backend логика
│   ├── constants.py            # Константы приложения
│   ├── model.py                # SQLAlchemy модели
│   │
│   ├── database/               # Инициализация БД
│   │   ├── __init__.py
│   │   └── init_db.py
│   │
│   ├── services/               # Бизнес-логика
│   │   ├── __init__.py
│   │   └── base_service.py
│   │
│   ├── utils/                  # Утилиты
│   │   ├── logger.py           # Логгирование
│   │   ├── auth_utils.py       # JWT утилиты
│   │   ├── validators.py       # Валидация
│   │   └── file_utils.py       # Работа с файлами
│   │
│   └── *.py                    # Blueprints (endpoints)
│
├── js/                         # Frontend JavaScript
│   ├── utils/                  # JS утилиты
│   │   ├── api.js              # API клиент
│   │   ├── dom.js              # DOM утилиты
│   │   ├── validation.js       # Валидация форм
│   │   └── helpers.js          # Вспомогательные функции
│   │
│   └── *.js                    # Страничные скрипты
│
├── html/                       # HTML страницы
├── css/                        # CSS стили
├── assets/                     # Статические файлы
├── logs/                       # Логи приложения
└── uploads/                    # Загруженные файлы
```

## Использование

### Backend (Python)

#### Использование логгера

```python
from logic.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Информационное сообщение")
logger.warning("Предупреждение")
logger.error("Ошибка", exc_info=True)
```

#### Использование констант

```python
from logic.constants import HTTP_OK, ERROR_UNAUTHORIZED

return jsonify({'error': ERROR_UNAUTHORIZED}), HTTP_UNAUTHORIZED
```

#### Использование базового сервиса

```python
from logic.services.base_service import BaseService
from logic.model import Problem

class ProblemService(BaseService):
    def __init__(self):
        super().__init__(Problem)

service = ProblemService()
problem = service.get_by_id(1)
all_problems = service.get_all(limit=50)
```

### Frontend (JavaScript)

#### API клиент

```javascript
// GET запрос
const problems = await API.get('/problems', { limit: 10, category: 1 });

// POST запрос
const result = await API.post('/problem', {
    name: 'Название',
    describe: 'Описание'
});

// FormData
const formData = new FormData();
formData.append('name', 'Название');
const result = await API.postFormData('/problem', formData);
```

#### DOM утилиты

```javascript
// Создание элемента
const button = DOM.createElement('button', {
    className: 'btn btn-primary',
    text: 'Нажми меня',
    attributes: { 'data-id': '123' }
});

// Уведомления
DOM.showNotification('Успешно сохранено!', 'success');
DOM.showNotification('Ошибка!', 'error');

// Индикатор загрузки
const loader = DOM.showLoader('#container', 'Загрузка данных...');
// ... async operation
DOM.hideLoader(loader);
```

#### Валидация форм

```javascript
// Валидация формы
const result = Validation.validateForm(form, {
    username: {
        required: true,
        minLength: 3,
        maxLength: 30
    },
    email: {
        required: true,
        email: true
    },
    password: {
        required: true,
        custom: (value) => Validation.isValidPassword(value, {
            minLength: 6,
            requireUppercase: true
        })
    }
});

if (!result.valid) {
    console.log('Ошибки:', result.errors);
}
```

#### Вспомогательные функции

```javascript
// Форматирование даты
Helpers.formatDate(new Date(), 'short'); // "17.01.2026"
Helpers.timeAgo('2026-01-16T10:00:00'); // "7 часов назад"

// Форматирование чисел
Helpers.formatPrice(1000); // "1 000 ₽"
Helpers.formatNumber(1234567); // "1 234 567"

// Работа с localStorage
Helpers.saveToStorage('user', { id: 1, name: 'User' });
const user = Helpers.getFromStorage('user');

// URL параметры
Helpers.setUrlParams({ page: 2, category: 'tech' });
const page = Helpers.getUrlParam('page');
```

## API Документация

Полная документация API доступна в файле [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Основные endpoints:

- `POST /api/login` - Авторизация
- `POST /api/registration` - Регистрация
- `GET /api/problems` - Список проблем
- `POST /api/problem` - Создание проблемы
- `GET /api/solutions` - Список решений
- `POST /api/solution` - Создание решения
- `GET /api/categories` - Категории
- `GET /api/hashtags` - Хештеги
- `GET /api/favourites` - Избранное
- `GET /api/cart` - Корзина

## Система рекомендаций

Подробнее о ML-рекомендациях: [RECOMMENDATIONS_README.md](RECOMMENDATIONS_README.md)

### Генерация эмбеддингов

```bash
python generate_embeddings.py
```

## Рефакторинг

Проект был полностью рефакторизирован. Подробности: [REFACTORING_GUIDE.md](REFACTORING_GUIDE.md)

### Основные улучшения:

- ✅ Модульная структура БД инициализации
- ✅ Централизованное логгирование
- ✅ Константы вынесены в отдельный файл
- ✅ Базовые сервисы для CRUD операций
- ✅ Безопасность: секреты в .env
- ✅ JS утилиты для API, DOM, валидации
- ✅ Улучшенная обработка ошибок
- ✅ Application Factory Pattern

## Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=logic --cov-report=html

# Конкретный тест
pytest tests/test_auth.py
```

## Безопасность

### Важные моменты:

1. **JWT Secret**: Используйте сильный случайный ключ (минимум 32 символа)
2. **Пароли БД**: Никогда не коммитьте пароли в git
3. **CORS**: Ограничьте список разрешенных origin'ов
4. **HTTPS**: Используйте HTTPS в production
5. **SSL БД**: Включите SSL для подключения к БД в production

### Генерация секретов:

```bash
# JWT Secret
python -c "import secrets; print(secrets.token_hex(32))"

# Случайный пароль
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Логи

Логи сохраняются в папке `logs/`:

- `app.log` - Все логи приложения
- `errors.log` - Только ошибки

```bash
# Просмотр логов в реальном времени
tail -f logs/app.log

# Последние ошибки
tail -n 100 logs/errors.log
```

## Production

### Запуск с Gunicorn

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Запуск с systemd

Создайте файл `/etc/systemd/system/vseprost.service`:

```ini
[Unit]
Description=VseProst Web Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/VseProst
Environment="FLASK_ENV=production"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable vseprost
sudo systemctl start vseprost
```

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/VseProst/;
    }
}
```

## Разработка

### Добавление нового endpoint

1. Создайте blueprint в `logic/`:

```python
from flask import Blueprint, jsonify
from logic.middleware import token_required

my_bp = Blueprint('my_feature', __name__, url_prefix='/api')

@my_bp.route('/my-endpoint', methods=['GET'])
@token_required
def my_endpoint():
    return jsonify({'message': 'Hello!'})
```

2. Зарегистрируйте в `app.py`:

```python
from logic.my_feature import my_bp
app.register_blueprint(my_bp)
```

### Добавление нового сервиса

```python
from logic.services.base_service import BaseService
from logic.model import MyModel

class MyService(BaseService):
    def __init__(self):
        super().__init__(MyModel)

    def custom_method(self):
        # Ваша логика
        pass
```

## Troubleshooting

### Проблема: Ошибка подключения к БД

**Решение**: Проверьте настройки в `.env` и доступность MySQL сервера

### Проблема: 401 ошибки после входа

**Решение**: Проверьте настройки JWT_SECRET и cookies в браузере

### Проблема: ML рекомендации не работают

**Решение**: Установите `sentence-transformers` и запустите `generate_embeddings.py`

## Лицензия

MIT License

## Контакты

При возникновении вопросов создавайте issue в репозитории.

---

**Создано с ❤️ с использованием Flask и Vanilla JavaScript**
