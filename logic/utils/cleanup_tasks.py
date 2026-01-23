"""
Cleanup Tasks for Database Maintenance
Периодические задачи для очистки устаревших данных
"""
from datetime import datetime, timedelta
from sqlalchemy import and_
from logic.model import db, RefreshToken, PasswordResetToken
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_refresh_tokens():
    """
    Удаляет истекшие refresh токены из базы данных

    Returns:
        int: Количество удаленных токенов
    """
    try:
        # Удаляем токены, срок которых истек
        expired_tokens = RefreshToken.query.filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).all()

        count = len(expired_tokens)

        if count > 0:
            for token in expired_tokens:
                db.session.delete(token)
            db.session.commit()
            logger.info(f"Удалено {count} истекших refresh токенов")
        else:
            logger.debug("Истекших refresh токенов не найдено")

        return count

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при очистке refresh токенов: {e}", exc_info=True)
        return 0


def cleanup_expired_password_reset_tokens():
    """
    Удаляет истекшие и использованные токены сброса пароля

    Returns:
        int: Количество удаленных токенов
    """
    try:
        # Удаляем токены, которые истекли или использованы более 24 часов назад
        cutoff_date = datetime.utcnow() - timedelta(hours=24)

        expired_tokens = PasswordResetToken.query.filter(
            and_(
                PasswordResetToken.expires_at < datetime.utcnow(),
                PasswordResetToken.used == True
            ) | (
                PasswordResetToken.created_at < cutoff_date
            )
        ).all()

        count = len(expired_tokens)

        if count > 0:
            for token in expired_tokens:
                db.session.delete(token)
            db.session.commit()
            logger.info(f"Удалено {count} истекших токенов сброса пароля")
        else:
            logger.debug("Истекших токенов сброса пароля не найдено")

        return count

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при очистке токенов сброса пароля: {e}", exc_info=True)
        return 0


def cleanup_old_user_activity(days=90):
    """
    Удаляет старые записи активности пользователей для экономии места в БД

    Args:
        days: Количество дней для хранения (по умолчанию 90)

    Returns:
        int: Количество удаленных записей
    """
    try:
        from logic.model import UserActivity

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_activities = UserActivity.query.filter(
            UserActivity.created_date < cutoff_date
        ).all()

        count = len(old_activities)

        if count > 0:
            for activity in old_activities:
                db.session.delete(activity)
            db.session.commit()
            logger.info(f"Удалено {count} старых записей активности пользователей")
        else:
            logger.debug("Старых записей активности не найдено")

        return count

    except ImportError:
        logger.debug("Модель UserActivity не найдена, пропускаем очистку")
        return 0
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при очистке активности пользователей: {e}", exc_info=True)
        return 0


def run_all_cleanup_tasks():
    """
    Запускает все задачи по очистке

    Returns:
        dict: Статистика выполнения задач
    """
    logger.info("Запуск задач очистки базы данных")

    stats = {
        'refresh_tokens_deleted': cleanup_expired_refresh_tokens(),
        'password_reset_tokens_deleted': cleanup_expired_password_reset_tokens(),
        'user_activities_deleted': cleanup_old_user_activity(days=90)
    }

    total_deleted = sum(stats.values())
    logger.info(f"Задачи очистки завершены. Всего удалено: {total_deleted} записей")

    return stats


# Для использования с cron или планировщиком задач
if __name__ == '__main__':
    # Этот блок используется при запуске скрипта напрямую
    from flask import Flask
    from config import get_config

    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)

    db.init_app(app)

    with app.app_context():
        stats = run_all_cleanup_tasks()
        print(f"Cleanup completed: {stats}")
