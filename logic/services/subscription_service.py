"""Подписка: тариф ИИ 999 руб/мес (can_ai_plan)."""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

AI_PLAN_PRICE_RUB = 999
PLAN_TYPE_AI = 'ai_monthly'


def get_subscription(user_id):
    """Возвращает данные подписки: balance_rub, period_end, can_profile_plan, can_ai_plan, tariff_name."""
    try:
        from logic.model import db
        from sqlalchemy import text
        conn = db.engine.raw_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT plan_type, period_end FROM subscription
                WHERE user_id = %s AND period_end > NOW()
            """, (user_id,))
            rows = cur.fetchall()
            cur.close()
            can_ai_plan = any(r[0] == PLAN_TYPE_AI for r in rows)
            period_end = None
            for r in rows:
                if r[0] == PLAN_TYPE_AI and r[1]:
                    period_end = r[1]
                    break
            return {
                "balance_rub": AI_PLAN_PRICE_RUB if can_ai_plan else 0,
                "period_end": period_end.isoformat() if period_end else None,
                "can_profile_plan": False,
                "can_ai_plan": can_ai_plan,
                "tariff_name": "ai_monthly" if can_ai_plan else "manual",
            }
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"get_subscription error: {e}")
        return {
            "balance_rub": 0,
            "period_end": None,
            "can_profile_plan": False,
            "can_ai_plan": False,
            "tariff_name": "manual",
        }


def add_subscription_payment(user_id, amount):
    """При успешной оплате 999 руб продлевает ИИ-тариф на 30 дней."""
    if amount < AI_PLAN_PRICE_RUB:
        return
    try:
        from logic.model import db
        from sqlalchemy import text
        conn = db.engine.raw_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO subscription (user_id, plan_type, period_end, updated_at)
                VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 30 DAY), NOW())
                ON DUPLICATE KEY UPDATE
                    period_end = GREATEST(COALESCE(period_end, NOW()), NOW()) + INTERVAL 30 DAY,
                    updated_at = NOW()
            """, (user_id, PLAN_TYPE_AI))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"add_subscription_payment error: {e}")
