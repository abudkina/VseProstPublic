# Автотесты для VseProst

Этот каталог содержит полный набор автоматических тестов для приложения VseProst. 
**Всего: 156 тестов** покрывающих все основные модули приложения.

## Структура тестов

```
tests/
├── conftest.py                          # Конфигурация pytest и фикстуры
├── helpers.py                           # Вспомогательные утилиты для тестов
│
├── test_auth.py                         # Авторизация (9 тестов)
├── test_registration.py                 # Регистрация (6 тестов)
├── test_user.py                         # Пользователи (8 тестов)
├── test_middleware.py                   # Middleware & JWT (10 тестов)
│
├── test_problem.py                      # Проблемы (10 тестов)
├── test_solution.py                     # Решения (10 тестов)
├── test_category.py                     # Категории (7 тестов)
├── test_hashtag.py                      # Хэштеги (8 тестов) ✨ НОВОЕ
├── test_topic.py                        # Темы (9 тестов) ✨ НОВОЕ
│
├── test_cart.py                         # Корзина (8 тестов) ✨ НОВОЕ
├── test_comment_solution.py             # Комментарии (10 тестов) ✨ НОВОЕ
├── test_notification.py                 # Уведомления (10 тестов) ✨ НОВОЕ
│
├── test_temporary_link_problem.py       # Временные ссылки проблем (5 тестов) ✨ НОВОЕ
├── test_temporary_link_solution.py      # Временные ссылки решений (5 тестов) ✨ НОВОЕ
├── test_temporary_problem_solution.py   # Связи проблем-решений (6 тестов) ✨ НОВОЕ
│
├── test_password_reset.py               # Сброс пароля (11 тестов) ✨ НОВОЕ
├── test_image_generation.py             # Генерация изображений (7 тестов) ✨ НОВОЕ
├── test_image_proxy.py                  # Прокси изображений (5 тестов) ✨ НОВОЕ
├── test_recommendations.py              # Рекомендации (9 тестов) ✨ НОВОЕ
└── README.md                            # Этот файл
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Статистика

| Модуль | Тестов | Статус |
|--------|--------|--------|
| Авторизация & Регистрация | 15 | ✅ |
| Пользователи | 8 | ✅ |
| Проблемы | 10 | ✅ |
| Решения | 10 | ✅ |
| Категории | 7 | ✅ |
| Middleware & JWT | 10 | ✅ |
| Хэштеги | 8 | ✨ |
| Темы | 9 | ✨ |
| Корзина | 8 | ✨ |
| Комментарии | 10 | ✨ |
| Уведомления | 10 | ✨ |
| Временные ссылки | 10 | ✨ |
| Связи проблем-решений | 6 | ✨ |
| Сброс пароля | 11 | ✨ |
| Генерация изображений | 7 | ✨ |
| Прокси изображений | 5 | ✨ |
| Рекомендации | 9 | ✨ |
| **ВСЕГО** | **156** | **✅** |

## Запуск тестов

### Запуск всех тестов

```bash
pytest tests/ -v
```

### Запуск конкретного файла тестов

```bash
pytest tests/test_auth.py -v
pytest tests/test_hashtag.py -v
pytest tests/test_cart.py -v
```

### Запуск конкретного класса тестов

```bash
pytest tests/test_auth.py::TestLogin -v
pytest tests/test_cart.py::TestGetCart -v
```

### Запуск конкретного теста

```bash
pytest tests/test_auth.py::TestLogin::test_login_success -v
pytest tests/test_hashtag.py::TestAddHashtag::test_add_hashtag_success -v
```

### Запуск только новых тестов

```bash
pytest tests/test_hashtag.py tests/test_topic.py tests/test_cart.py \
        tests/test_comment_solution.py tests/test_notification.py \
        tests/test_temporary_link_problem.py tests/test_temporary_link_solution.py \
        tests/test_temporary_problem_solution.py tests/test_password_reset.py \
        tests/test_image_generation.py tests/test_image_proxy.py \
        tests/test_recommendations.py -v
```

### Запуск с покрытием кода

```bash
pytest tests/ --cov=logic --cov=app --cov-report=html
```

Это создаст отчет о покрытии в формате HTML в папке `htmlcov/`.

### Запуск с подробным выводом

```bash
pytest tests/ -v
```

### Запуск с выводом print-ов

```bash
pytest tests/ -s
```

### Запуск с быстрым выводом

```bash
pytest tests/ -q
```

### Запуск с остановкой на первой ошибке

```bash
pytest tests/ -x
```

### Запуск только не пройденных тестов

```bash
pytest tests/ --lf
```

## Настройка тестового окружения

Тесты используют конфигурацию `TestingConfig` из `config.py`, которая использует SQLite в памяти для изоляции тестов.

Переменные окружения для тестов:
- `FLASK_ENV=testing` - устанавливается автоматически
- `JWT_SECRET=test-secret-key-for-testing-only` - устанавливается автоматически

## Фикстуры

### Основные фикстуры

- `test_app` - Тестовое приложение Flask
- `client` - Тестовый клиент Flask
- `db_session` - Сессия базы данных
- `test_user` - Тестовый пользователь
- `admin_user` - Тестовый администратор
- `auth_token` - JWT токен для обычного пользователя
- `admin_token` - JWT токен для администратора
- `auth_headers` - Заголовки с токеном авторизации
- `admin_headers` - Заголовки с токеном администратора

### Фикстуры для данных

- `test_category` - Тестовая категория
- `test_topic` - Тестовая тема
- `test_problem` - Тестовая проблема
- `test_solution` - Тестовое решение

## Ключевые улучшения

### 1. Вспомогательные утилиты (helpers.py)

**ResponseHelper** - упрощает проверку ответов:
```python
# До рефакторинга
assert response.status_code == 200
data = json.loads(response.data)
assert 'message' in data

# После рефакторинга
data = ResponseHelper.assert_success(response)
ResponseHelper.assert_has_fields(data, ['message'])
```

**TestDataFactory** - создание тестовых данных:
```python
# До рефакторинга
user_data = {
    'username': 'testuser',
    'email': 'test@example.com',
    'password': 'password123'
}

# После рефакторинга
user_data = TestDataFactory.create_user_data(
    username='testuser',
    email='test@example.com'
)
```

### 2. Централизованные константы

Все тестовые константы вынесены в `conftest.py`:
- `TEST_JWT_SECRET`
- `TEST_USERNAME`, `TEST_EMAIL`, `TEST_PASSWORD`
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`

### 3. Устранение дублирования

- Вспомогательная функция `_create_jwt_token()` вместо дублирования кода
- Функция `_create_refresh_token()` в test_auth.py
- Переиспользуемые валидаторы: `assert_valid_id_response()`, `assert_valid_list_response()`

## Написание новых тестов

### Используйте ResponseHelper

```python
def test_example(self, client, auth_headers):
    response = client.get('/api/endpoint', headers=auth_headers)

    # Проверка успеха
    data = ResponseHelper.assert_success(response)

    # Проверка ошибки
    ResponseHelper.assert_error(response, 400)

    # Проверка unauthorized
    ResponseHelper.assert_unauthorized(response)
```

### Используйте TestDataFactory

```python
def test_create_problem(self, client, auth_headers, test_category):
    problem_data = TestDataFactory.create_problem_data(
        name='New Problem',
        category=test_category.id
    )
    response = client.post('/api/problems', json=problem_data, headers=auth_headers)
    data = ResponseHelper.assert_success(response)
```

### Группируйте тесты по классам

```python
class TestUserProfile:
    """Тесты профиля пользователя"""

    def test_get_profile_success(self, client, auth_headers):
        # ...

    def test_get_profile_unauthorized(self, client):
        # ...
```

## Покрытие кода

Цель - достичь покрытия кода не менее 80% для критичных модулей.

Проверить текущее покрытие:
```bash
pytest --cov=logic --cov=app --cov-report=term-missing
```

## CI/CD

Тесты можно интегрировать в CI/CD пайплайн. Пример для GitHub Actions:

```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=logic --cov=app
```

## Отчеты

После запуска тестов с покрытием, отчеты доступны в:
- Консольный вывод
- HTML отчет: `htmlcov/index.html`
- XML отчет: `coverage.xml` (для CI/CD)

## Модули покрытия

### ✅ Полностью протестированы

1. **Аутентификация и авторизация**
   - Authorization (авторизация)
   - Registration (регистрация)
   - Middleware (JWT валидация)

2. **Управление контентом**
   - Problem (проблемы)
   - Solution (решения)
   - Category (категории)
   - Hashtag (хэштеги)
   - Topic (темы)

3. **Пользовательский контент**
   - User (профили пользователей)
   - CommentSolution (комментарии)
   - Cart (корзина)
   - Notification (уведомления)

4. **Дополнительные функции**
   - TemporaryLinkProblem (временные ссылки на проблемы)
   - TemporaryLinkSolution (временные ссылки на решения)
   - TemporaryProblemSolution (связи проблем-решений)
   - PasswordReset (сброс пароля)
   - ImageGeneration (генерация изображений)
   - ImageProxy (прокси изображений)
   - Recommendations (рекомендации)

## Подсказки и лучшие практики

1. **Используйте параметризованные тесты** для проверки множества вариантов:
   ```python
   @pytest.mark.parametrize("status_code", [400, 401, 403])
   def test_error_responses(self, client, status_code):
       # ...
   ```

2. **Используйте fixtures для подготовки данных**:
   ```python
   @pytest.fixture
   def prepared_data(db_session, test_user):
       # Подготовка данных
       return data
   ```

3. **Тестируйте граничные случаи**:
   - Пустые значения
   - Очень длинные значения
   - Специальные символы
   - Null/None значения

4. **Группируйте связанные тесты**:
   - По функциональности
   - По эндпоинтам
   - По типам ошибок

5. **Используйте понятные имена для тестов**:
   ```python
   def test_add_to_cart_should_fail_without_authorization(self):
       # Понятно, что тестируется и какой результат ожидается
   ```

