"""
Скрипт для создания backup базы данных MySQL
"""
import os
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def create_backup_with_mysqldump():
    """Создает backup используя mysqldump"""
    
    # Получаем параметры подключения из .env
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'vseprost')
    
    # Создаем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{db_name}_{timestamp}.sql'
    
    print(f"Создание backup базы данных '{db_name}'...")
    print(f"Файл: {backup_filename}")
    
    # Команда mysqldump
    # Используем переменную окружения для пароля (безопаснее)
    env = os.environ.copy()
    env['MYSQL_PWD'] = db_password
    
    cmd = [
        'mysqldump',
        f'--host={db_host}',
        f'--port={db_port}',
        f'--user={db_user}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--events',
        '--add-drop-database',
        '--add-drop-table',
        '--default-character-set=utf8mb4',
        db_name
    ]
    
    try:
        # Выполняем команду и сохраняем вывод в файл
        with open(backup_filename, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                env=env
            )
        
        if result.returncode == 0:
            file_size = os.path.getsize(backup_filename)
            print(f"[OK] Backup успешно создан!")
            print(f"Файл: {backup_filename}")
            print(f"Размер: {file_size / 1024 / 1024:.2f} MB")
            return backup_filename
        else:
            print(f"[ERROR] Ошибка при создании backup:")
            print(result.stderr)
            return None
            
    except FileNotFoundError:
        print("[ERROR] mysqldump не найден в PATH")
        print("Попытка использовать альтернативный метод...")
        return None
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        return None


def create_backup_with_python():
    """Создает backup используя Python библиотеки"""
    try:
        import pymysql
    except ImportError:
        print("[ERROR] Библиотека pymysql не установлена")
        print("Установите: pip install pymysql")
        return None
    
    # Получаем параметры подключения из .env
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '3306'))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'vseprost')
    
    # Создаем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{db_name}_{timestamp}.sql'
    
    print(f"Создание backup базы данных '{db_name}' через Python...")
    print(f"Файл: {backup_filename}")
    
    try:
        # Подключаемся к базе данных
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            with open(backup_filename, 'w', encoding='utf-8') as f:
                # Записываем заголовок
                f.write(f"-- MySQL Backup\n")
                f.write(f"-- Database: {db_name}\n")
                f.write(f"-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- Host: {db_host}:{db_port}\n")
                f.write(f"\n")
                f.write(f"SET NAMES utf8mb4;\n")
                f.write(f"SET FOREIGN_KEY_CHECKS=0;\n")
                f.write(f"\n")
                f.write(f"DROP DATABASE IF EXISTS `{db_name}`;\n")
                f.write(f"CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n")
                f.write(f"USE `{db_name}`;\n")
                f.write(f"\n")
                
                # Получаем список таблиц
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    print(f"  Экспорт таблицы: {table}")
                    
                    # Получаем структуру таблицы
                    cursor.execute(f"SHOW CREATE TABLE `{table}`")
                    create_table = cursor.fetchone()[1]
                    f.write(f"\n-- Структура таблицы `{table}`\n")
                    f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                    f.write(f"{create_table};\n")
                    f.write(f"\n")
                    
                    # Получаем данные таблицы
                    cursor.execute(f"SELECT * FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    if rows:
                        # Получаем названия колонок
                        cursor.execute(f"DESCRIBE `{table}`")
                        columns = [col[0] for col in cursor.fetchall()]
                        
                        f.write(f"-- Данные таблицы `{table}`\n")
                        f.write(f"LOCK TABLES `{table}` WRITE;\n")
                        
                        for row in rows:
                            values = []
                            for value in row:
                                if value is None:
                                    values.append('NULL')
                                elif isinstance(value, (int, float)):
                                    values.append(str(value))
                                else:
                                    # Экранируем специальные символы
                                    escaped = str(value).replace('\\', '\\\\').replace("'", "\\'")
                                    values.append(f"'{escaped}'")
                            
                            f.write(f"INSERT INTO `{table}` (`{'`, `'.join(columns)}`) VALUES ({', '.join(values)});\n")
                        
                        f.write(f"UNLOCK TABLES;\n")
                        f.write(f"\n")
                
                f.write(f"SET FOREIGN_KEY_CHECKS=1;\n")
        
        connection.close()
        
        file_size = os.path.getsize(backup_filename)
        print(f"[OK] Backup успешно создан!")
        print(f"Файл: {backup_filename}")
        print(f"Размер: {file_size / 1024 / 1024:.2f} MB")
        return backup_filename
        
    except Exception as e:
        print(f"[ERROR] Ошибка при создании backup: {e}")
        return None


def create_backup():
    """Создает backup базы данных"""
    # Сначала пробуем mysqldump
    result = create_backup_with_mysqldump()
    if result:
        return result
    
    # Если mysqldump не доступен, используем Python
    print("\nИспользование альтернативного метода через Python...")
    return create_backup_with_python()


if __name__ == '__main__':
    # Устанавливаем кодировку для вывода
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    create_backup()
