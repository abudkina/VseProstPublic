# Автотесты для VseProst

Этот каталог содержит автоматические тесты для приложения VseProst.

## Структура тестов

```
tests/
├── conftest.py           # Конфигурация pytest и фикстуры
├── helpers.py            # Вспомогательные утилиты для тестов
├── test_auth.py          # Тесты авторизации
├── test_category.py      # Тесты категорий
├── test_middleware.py    # Тесты middleware и JWT
├── test_problem.py       # Тесты проблем
├── test_registration.py  # Тесты регистрации
├── test_solution.py      # Тесты решений
└── test_user.py          # Тесты пользователей
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск тестов

### Запуск всех тестов

```bash
pytest
```

### Запуск конкретного файла тестов

```bash
pytest tests/test_auth.py
```

### Запуск конкретного теста

```bash
pytest tests/test_auth.py::TestLogin::test_login_success
```

### Запуск с покрытием кода

```bash
pytest --cov=logic --cov=app --cov-report=html
```

Это создаст отчет о покрытии в формате HTML в папке `htmlcov/`.

### Запуск с подробным выводом

```bash
pytest -v
```

### Запуск с выводом print-ов

```bash
pytest -s
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

## Ключевые улучшения после рефакторинга

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

