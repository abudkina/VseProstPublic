# Развёртывание VseProst на хостинге Beget

## Подготовка

### 1. Создание сайта в панели Beget

1. Войдите в панель управления Beget
2. Перейдите в раздел **"Сайты"**
3. Создайте новый сайт (например: `vseprost`)
4. Прикрепите к нему домен

### 2. Создание базы данных MySQL

1. Перейдите в раздел **"MySQL"**
2. Создайте новую базу данных
3. Запомните:
   - Имя базы данных (например: `login_vseprost`)
   - Имя пользователя
   - Пароль
   - Хост (обычно `localhost`)

---

## Установка проекта

### Шаг 1: Подключение по SSH

```bash
# Подключаемся к серверу
ssh ВАШ_ЛОГИН@ВАШ_ЛОГИН.beget.tech

# Переходим в Docker-контейнер
ssh localhost -p222
```

### Шаг 2: Переход в директорию сайта

```bash
cd ~/ИМЯ_САЙТА/
# Например: cd ~/vseprost.beget.tech/
```

### Шаг 3: Загрузка файлов проекта

**Вариант A: Через Git (рекомендуется)**
```bash
git clone https://github.com/ВАШ_РЕПОЗИТОРИЙ/VseProst.git .
```

**Вариант B: Через FTP/SFTP**
- Используйте FileZilla или другой FTP-клиент
- Загрузите все файлы в директорию сайта

### Шаг 4: Создание виртуального окружения

```bash
# Создаём виртуальное окружение с Python 3.10
python3.10 -m venv venv

# Или если Python 3.10 недоступен:
python3 -m venv venv

# Активируем окружение
source venv/bin/activate

# Проверяем версию Python
python --version
```

### Шаг 5: Установка зависимостей

```bash
# Устанавливаем зависимости (используем файл для Beget)
pip install -r requirements_beget.txt --user --ignore-installed
```

### Шаг 6: Создание .env файла

```bash
# Копируем шаблон
cp .env.example .env

# Редактируем файл
nano .env
```

**Минимальные настройки .env:**
```ini
# Режим работы
FLASK_ENV=production

# ОБЯЗАТЕЛЬНО: Сгенерируйте уникальный ключ!
# Команда для генерации: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=ВАШ_УНИКАЛЬНЫЙ_КЛЮЧ_МИНИМУМ_32_СИМВОЛА

# База данных Beget
DB_HOST=localhost
DB_PORT=3306
DB_USER=ВАШ_ЛОГИН_BEGET_ИМЯ_БД
DB_PASSWORD=ПАРОЛЬ_ОТ_БД
DB_NAME=ВАШ_ЛОГИН_BEGET_ИМЯ_БД
DB_USE_SSL=false

# CORS - укажите ваш домен
CORS_ORIGINS=https://ваш-домен.ru,https://www.ваш-домен.ru

# URL фронтенда для писем восстановления пароля
FRONTEND_URL=https://ваш-домен.ru

# Email (опционально, для восстановления пароля)
MAIL_SERVER=smtp.yandex.ru
MAIL_PORT=465
MAIL_USE_SSL=true
MAIL_USERNAME=ваш-email@yandex.ru
MAIL_PASSWORD=пароль-приложения
MAIL_DEFAULT_SENDER=ваш-email@yandex.ru
```

### Шаг 7: Настройка passenger_wsgi.py

Отредактируйте файл `passenger_wsgi.py` и укажите правильные пути:

```bash
nano passenger_wsgi.py
```

Замените пути на ваши:
```python
# Формат: /home/ПЕРВАЯ_БУКВА_ЛОГИНА/ЛОГИН/ИМЯ_САЙТА
PROJECT_DIR = '/home/v/vseprost/vseprost.beget.tech'
VENV_PACKAGES = '/home/v/vseprost/vseprost.beget.tech/venv/lib/python3.10/site-packages'
```

**Как узнать правильный путь:**
```bash
pwd
# Выведет что-то вроде: /home/v/vseprost/vseprost.beget.tech
```

### Шаг 8: Настройка .htaccess

Отредактируйте файл `.htaccess`:

```bash
nano .htaccess
```

Замените путь к Python:
```apache
PassengerPython /home/v/vseprost/vseprost.beget.tech/venv/bin/python
```

### Шаг 9: Создание необходимых директорий

```bash
# Создаём директории
mkdir -p tmp uploads logs

# Создаём файл restart.txt
touch tmp/restart.txt

# Создаём симлинк для статики
ln -s public_html public
```

### Шаг 10: Импорт базы данных

**Вариант A: Через phpMyAdmin**
1. Откройте phpMyAdmin в панели Beget
2. Выберите вашу базу данных
3. Импортируйте файл `VseProst.sql`

**Вариант B: Через командную строку**
```bash
mysql -u ВАШ_ПОЛЬЗОВАТЕЛЬ -p ИМЯ_БД < VseProst.sql
```

### Шаг 11: Настройка прав доступа

В панели Beget через **Файловый менеджер**:

1. Найдите папку `.local` в корне аккаунта
2. Нажмите **"Инструменты"** → **"Настроить общий доступ к текущей директории"**
3. Установите **"Чтение и запись"** и **"Включая вложенные папки"**
4. Нажмите **"Открыть доступ"**

То же самое сделайте для папки `venv` в директории сайта.

### Шаг 12: Перезапуск приложения

```bash
touch tmp/restart.txt
```

---

## Проверка работоспособности

1. Откройте ваш сайт в браузере
2. Проверьте главную страницу
3. Проверьте API: `https://ваш-домен.ru/api/categories`

### Отладка ошибок

Если сайт не работает:

1. **Проверьте логи ошибок** в панели Beget
2. **Включите отладку** временно в `passenger_wsgi.py`:
   ```python
   from werkzeug.debug import DebuggedApplication
   application.wsgi_app = DebuggedApplication(application.wsgi_app, True)
   application.debug = True
   ```
3. **Проверьте права доступа** на папки

---

## Структура файлов на сервере

```
~/ваш-сайт.beget.tech/
├── .env                    # Конфигурация (создать из .env.example)
├── .htaccess              # Настройки Apache/Passenger
├── passenger_wsgi.py      # Точка входа WSGI
├── app.py                 # Flask приложение
├── config.py              # Конфигурация Flask
├── requirements_beget.txt # Зависимости для Beget
├── venv/                  # Виртуальное окружение
├── tmp/
│   └── restart.txt        # Файл для перезапуска
├── uploads/               # Загруженные файлы
├── logs/                  # Логи приложения
├── public -> public_html  # Симлинк для статики
├── public_html/           # Публичная директория
├── html/                  # HTML шаблоны
├── css/                   # Стили
├── js/                    # JavaScript
├── assets/                # Ресурсы (изображения, иконки)
└── logic/                 # Бэкенд логика
```

---

## Важные замечания

### 1. ML-рекомендации отключены

Система рекомендаций на основе ML (sentence-transformers) **не будет работать** на shared-хостинге из-за ограничений памяти. Если нужны рекомендации - используйте VPS.

### 2. Redis недоступен

На shared-хостинге Beget Redis обычно недоступен. Rate limiter будет использовать memory storage.

### 3. SSL/HTTPS

Beget предоставляет бесплатный SSL-сертификат. Включите его в панели управления.

### 4. Обновление приложения

После изменений в коде:
```bash
touch tmp/restart.txt
```

### 5. Резервные копии

Регулярно делайте бэкапы:
- База данных через phpMyAdmin
- Файлы через FTP

---

## Часто встречающиеся проблемы

### Ошибка 500

1. Проверьте `.env` файл - все ли переменные заполнены
2. Проверьте пути в `passenger_wsgi.py`
3. Проверьте права доступа на `venv`

### Ошибка импорта модулей

```bash
# Проверьте установлены ли зависимости
source venv/bin/activate
pip list
```

### База данных не подключается

1. Проверьте данные в `.env`
2. Убедитесь что база данных создана
3. Проверьте права пользователя БД

### Статика не отображается

1. Проверьте симлинк `public`
2. Проверьте пути в `.htaccess`

---

## Контакты поддержки Beget

- Тикет-система в панели управления
- [Telegram-сообщество](https://t.me/beaborned)
