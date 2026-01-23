"""Database initialization and table creation logic"""
import os
import logging
from sqlalchemy import text, inspect

logger = logging.getLogger(__name__)


def create_directories():
    """Создает необходимые директории для приложения"""
    directories = ['uploads']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def init_database(db, app):
    """
    Инициализация базы данных

    Args:
        db: SQLAlchemy database instance
        app: Flask application instance
    """
    try:
        # Проверяем соединение с БД
        db.session.execute(text('SELECT 1'))
        logger.info("✅ Успешное подключение к базе данных")

        db_info = app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1].split('?')[0]
        logger.info(f"📊 MySQL: {db_info}")

        # Проверяем существующие таблицы
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        logger.info(f"📋 Найдено таблиц в БД: {len(table_names)}")

        # Создаем недостающие таблицы
        _create_missing_tables(db, table_names)

    except Exception as e:
        logger.error(f"⚠️ Ошибка при подключении к базе данных: {e}", exc_info=True)
        logger.warning("⚠️ Сервер будет запущен, но некоторые функции могут не работать")


def _create_missing_tables(db, existing_tables):
    """
    Создает недостающие таблицы в БД

    Args:
        db: SQLAlchemy database instance
        existing_tables: List of existing table names
    """
    # Определяем правильные имена таблиц
    table_name_mapping = _get_table_name_mapping(existing_tables)

    # Проверяем и создаем основные таблицы
    _check_and_create_problem_table(db, existing_tables, table_name_mapping)
    _check_and_create_comment_solution_table(db, existing_tables, table_name_mapping)
    _check_and_create_cart_table(db, existing_tables, table_name_mapping)
    _check_and_create_association_tables(db, existing_tables, table_name_mapping)
    _check_and_create_recommendation_tables(db, existing_tables, table_name_mapping)
    _check_and_create_password_reset_table(db, existing_tables, table_name_mapping)


def _get_table_name_mapping(existing_tables):
    """Определяет правильные имена таблиц для внешних ключей"""
    return {
        'problem': 'Problem' if 'Problem' in existing_tables else 'problem',
        'user': 'User' if 'User' in existing_tables else 'user',
        'category': 'Category' if 'Category' in existing_tables else 'category',
        'topic': 'Topic' if 'Topic' in existing_tables else 'topic',
        'hashtag': 'Hashtag' if 'Hashtag' in existing_tables else 'hashtag',
        'solution': 'Solution' if 'Solution' in existing_tables else 'solution'
    }


def _check_and_create_problem_table(db, existing_tables, table_mapping):
    """Проверяет и создает таблицу problem"""
    problem_exists = 'problem' in existing_tables or 'Problem' in existing_tables

    if problem_exists:
        actual_name = 'Problem' if 'Problem' in existing_tables else 'problem'
        try:
            count = db.session.execute(text(f"SELECT COUNT(*) FROM `{actual_name}`")).scalar()
            logger.info(f"📊 Таблица '{actual_name}' содержит {count} записей")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при подсчете записей в '{actual_name}': {e}")
        return

    logger.info("⚠️ Таблица 'problem' не найдена. Создаю таблицу...")

    create_sql = f"""
        CREATE TABLE IF NOT EXISTS `problem` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `category` INT NOT NULL,
            `describe` TEXT,
            `favourite` INT DEFAULT 0,
            `fromauthor` BOOLEAN DEFAULT FALSE,
            `isnew` BOOLEAN DEFAULT TRUE,
            `creator` INT NOT NULL,
            `modified_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `created_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `image` TEXT NOT NULL DEFAULT '../images/default.png',
            `name` TEXT NOT NULL,
            `reply` INT,
            `show` INT,
            `topic` INT,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`category`) REFERENCES `{table_mapping['category']}`(`id`),
            FOREIGN KEY (`creator`) REFERENCES `{table_mapping['user']}`(`id`),
            FOREIGN KEY (`topic`) REFERENCES `{table_mapping['topic']}`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    _execute_sql(db, create_sql, "Таблица 'problem' успешно создана")


def _check_and_create_comment_solution_table(db, existing_tables, table_mapping):
    """Проверяет и создает таблицу comment_solution"""
    comment_exists = 'CommentSolution' in existing_tables or 'comment_solution' in existing_tables

    if comment_exists:
        logger.info(f"✅ Таблица 'comment_solution' существует")
        return

    logger.info("⚠️ Таблица 'comment_solution' не найдена. Создаю таблицу...")

    create_sql = f"""
        CREATE TABLE IF NOT EXISTS `comment_solution` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `isnew` BOOLEAN DEFAULT TRUE,
            `likecount` INT DEFAULT 0,
            `notlikecount` INT DEFAULT 0,
            `solution_id` INT NOT NULL,
            `text` TEXT NOT NULL,
            `creator` INT NOT NULL,
            `modified_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `created_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`solution_id`) REFERENCES `{table_mapping['solution']}`(`id`),
            FOREIGN KEY (`creator`) REFERENCES `{table_mapping['user']}`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    _execute_sql(db, create_sql, "Таблица 'comment_solution' успешно создана")


def _check_and_create_cart_table(db, existing_tables, table_mapping):
    """Проверяет и создает таблицу UserCartSolution"""
    cart_table_names = [name.lower() for name in existing_tables]
    cart_exists = any(name in cart_table_names for name in ['usercartsolution', 'user_cart_solution'])

    if cart_exists:
        logger.info("✅ Таблица 'UserCartSolution' существует")
        return

    logger.info("⚠️ Таблица 'UserCartSolution' не найдена. Создаю таблицу...")

    create_sql = f"""
        CREATE TABLE IF NOT EXISTS `UserCartSolution` (
            `id` INT NOT NULL AUTO_INCREMENT,
            `is_bought` BOOLEAN DEFAULT FALSE,
            `solution` INT NOT NULL,
            `user` INT NOT NULL,
            `creator` INT NOT NULL,
            `modified_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `created_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`id`),
            FOREIGN KEY (`solution`) REFERENCES `{table_mapping['solution']}`(`id`),
            FOREIGN KEY (`user`) REFERENCES `{table_mapping['user']}`(`id`),
            FOREIGN KEY (`creator`) REFERENCES `{table_mapping['user']}`(`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    _execute_sql(db, create_sql, "Таблица 'UserCartSolution' успешно создана")


def _check_and_create_association_tables(db, existing_tables, table_mapping):
    """Проверяет и создает ассоциативные таблицы"""
    association_tables = [
        {
            'name': 'favourite_problem',
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `favourite_problem` (
                    `problem_id` INT NOT NULL,
                    `user_id` INT NOT NULL,
                    PRIMARY KEY (`problem_id`, `user_id`),
                    FOREIGN KEY (`problem_id`) REFERENCES `{table_mapping['problem']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`user_id`) REFERENCES `{table_mapping['user']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        },
        {
            'name': 'favourite_solution',
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `favourite_solution` (
                    `solution_id` INT NOT NULL,
                    `user_id` INT NOT NULL,
                    PRIMARY KEY (`solution_id`, `user_id`),
                    FOREIGN KEY (`solution_id`) REFERENCES `{table_mapping['solution']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`user_id`) REFERENCES `{table_mapping['user']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        },
        {
            'name': 'hashtag_problem',
            'alt_names': ['hashtag_problems'],
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `hashtag_problem` (
                    `problem_id` INT NOT NULL,
                    `hashtag_id` INT NOT NULL,
                    PRIMARY KEY (`problem_id`, `hashtag_id`),
                    FOREIGN KEY (`problem_id`) REFERENCES `{table_mapping['problem']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`hashtag_id`) REFERENCES `{table_mapping['hashtag']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        },
        {
            'name': 'problem_link_problem',
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `problem_link_problem` (
                    `problem_id` INT NOT NULL,
                    `problem_link_id` INT NOT NULL,
                    PRIMARY KEY (`problem_id`, `problem_link_id`),
                    FOREIGN KEY (`problem_id`) REFERENCES `{table_mapping['problem']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`problem_link_id`) REFERENCES `{table_mapping['problem']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        },
        {
            'name': 'solution_problems',
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `solution_problems` (
                    `problem_id` INT NOT NULL,
                    `solution_id` INT NOT NULL,
                    PRIMARY KEY (`problem_id`, `solution_id`),
                    FOREIGN KEY (`problem_id`) REFERENCES `{table_mapping['problem']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`solution_id`) REFERENCES `{table_mapping['solution']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        },
        {
            'name': 'solution_link_solution',
            'sql': f"""
                CREATE TABLE IF NOT EXISTS `solution_link_solution` (
                    `solution_id` INT NOT NULL,
                    `solution_link_id` INT NOT NULL,
                    PRIMARY KEY (`solution_id`, `solution_link_id`),
                    FOREIGN KEY (`solution_id`) REFERENCES `{table_mapping['solution']}`(`id`) ON DELETE CASCADE,
                    FOREIGN KEY (`solution_link_id`) REFERENCES `{table_mapping['solution']}`(`id`) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }
    ]

    for table_info in association_tables:
        table_name = table_info['name']
        alt_names = table_info.get('alt_names', [])
        table_exists = table_name in existing_tables or any(alt_name in existing_tables for alt_name in alt_names)

        if not table_exists:
            logger.info(f"⚠️ Таблица '{table_name}' не найдена. Создаю таблицу...")
            _execute_sql(db, table_info['sql'], f"Таблица '{table_name}' успешно создана")
        else:
            logger.info(f"✅ Таблица '{table_name}' существует")


def _check_and_create_recommendation_tables(db, existing_tables, table_mapping):
    """Проверяет и создает таблицы для системы рекомендаций"""
    # Таблица user_activity
    if 'user_activity' not in existing_tables:
        logger.info("⚠️ Таблица 'user_activity' не найдена. Создаю таблицу...")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS `user_activity` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `activity_type` VARCHAR(50) NOT NULL,
                `entity_type` VARCHAR(20) NOT NULL,
                `entity_id` INT NULL,
                `search_query` TEXT NULL,
                `created_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                INDEX `idx_user_activity` (`user_id`, `entity_type`, `created_date`),
                FOREIGN KEY (`user_id`) REFERENCES `{table_mapping['user']}`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        _execute_sql(db, create_sql, "Таблица 'user_activity' успешно создана")
    else:
        logger.info("✅ Таблица 'user_activity' существует")

    # Таблица embedding
    if 'embedding' not in existing_tables:
        logger.info("⚠️ Таблица 'embedding' не найдена. Создаю таблицу...")

        create_sql = """
            CREATE TABLE IF NOT EXISTS `embedding` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `entity_type` VARCHAR(20) NOT NULL,
                `entity_id` INT NOT NULL,
                `embedding_vector` JSON NOT NULL,
                `text_content` TEXT NOT NULL,
                `model_name` VARCHAR(100) NOT NULL DEFAULT 'paraphrase-multilingual-MiniLM-L12-v2',
                `created_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `modified_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`),
                UNIQUE KEY `unique_entity_embedding` (`entity_type`, `entity_id`),
                INDEX `idx_entity` (`entity_type`, `entity_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        _execute_sql(db, create_sql, "Таблица 'embedding' успешно создана")
    else:
        logger.info("✅ Таблица 'embedding' существует")


def _check_and_create_password_reset_table(db, existing_tables, table_mapping):
    """Проверяет и создает таблицу password_reset_token"""
    if 'password_reset_token' not in existing_tables:
        logger.info("⚠️ Таблица 'password_reset_token' не найдена. Создаю таблицу...")

        create_sql = f"""
            CREATE TABLE IF NOT EXISTS `password_reset_token` (
                `id` INT NOT NULL AUTO_INCREMENT,
                `user_id` INT NOT NULL,
                `token` VARCHAR(255) NOT NULL UNIQUE,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                `expires_at` TIMESTAMP NOT NULL,
                `used` BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (`id`),
                INDEX `idx_token` (`token`),
                INDEX `idx_user_id` (`user_id`),
                FOREIGN KEY (`user_id`) REFERENCES `{table_mapping['user']}`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        _execute_sql(db, create_sql, "Таблица 'password_reset_token' успешно создана")
    else:
        logger.info("✅ Таблица 'password_reset_token' существует")


def _execute_sql(db, sql, success_message):
    """
    Выполняет SQL запрос с обработкой ошибок

    Args:
        db: SQLAlchemy database instance
        sql: SQL query string
        success_message: Message to log on success
    """
    try:
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        db.session.execute(text(sql))
        db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
        db.session.commit()
        logger.info(f"✅ {success_message}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Ошибка при создании таблицы: {e}", exc_info=True)
