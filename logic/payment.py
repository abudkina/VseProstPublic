"""API платежей через ЮKassa (пополнение баланса, тариф 999 руб/мес)."""
import uuid
import logging
import time
from yookassa import Payment, Configuration
from flask import Blueprint, current_app, g, jsonify, request
from logic.model import db
from logic.middleware import token_required

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')
logger = logging.getLogger(__name__)

# Простой кэш баланса (ключ -> (значение, expiry))
_balance_cache = {}
_BALANCE_CACHE_TTL = 30


def _get_db_connection():
    """Возвращает raw connection для запросов с cursor."""
    return db.engine.raw_connection()


def _get_cursor(conn, dictionary=False):
    if dictionary:
        from pymysql.cursors import DictCursor
        return conn.cursor(DictCursor)
    return conn.cursor()


class YooKassaPayment:
    def __init__(self):
        try:
            Configuration.account_id = current_app.config.get('YOOKASSA_SHOP_ID', '')
            Configuration.secret_key = current_app.config.get('YOOKASSA_SECRET_KEY', '')
            self.return_url = current_app.config.get('YOOKASSA_RETURN_URL', '')
            if not Configuration.account_id or not Configuration.secret_key:
                logger.warning("YooKassa configuration is missing or empty")
        except RuntimeError:
            from config import get_config
            config = get_config()
            Configuration.account_id = config.YOOKASSA_SHOP_ID
            Configuration.secret_key = config.YOOKASSA_SECRET_KEY
            self.return_url = config.YOOKASSA_RETURN_URL

    def create_payment(self, amount, description, user_id):
        if amount < 50:
            raise ValueError("Минимальная сумма пополнения 50 рублей")
        idempotence_key = str(uuid.uuid4())
        user_email = ''
        try:
            conn = _get_db_connection()
            try:
                cur = _get_cursor(conn, dictionary=True)
                cur.execute("SELECT email FROM user WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if row:
                    user_email = row.get('email', '')
                cur.close()
            finally:
                conn.close()
        except Exception as e:
            logger.warning(f"Не удалось получить email: {e}")

        payment = Payment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": self.return_url},
            "capture": True,
            "description": description[:128],
            "metadata": {"user_id": user_id, "purpose": "balance_deposit"},
            "receipt": {
                "customer": {"email": user_email},
                "items": [{
                    "description": description[:128],
                    "quantity": "1",
                    "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                    "vat_code": 1,
                    "payment_mode": "full_payment",
                    "payment_subject": "service"
                }]
            }
        }, idempotence_key)

        self._save_transaction_to_db(
            user_id=user_id, yookassa_payment_id=payment.id, amount=amount,
            type='deposit', description=description, status=payment.status
        )
        return {
            "id": payment.id,
            "status": payment.status,
            "confirmation_url": payment.confirmation.confirmation_url,
            "amount": amount
        }

    def _save_transaction_to_db(self, user_id, yookassa_payment_id, amount, type, description, status):
        conn = _get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO transactions
                (user_id, yookassa_payment_id, service_type, calculation_category,
                 amount, type, description, status, created_at, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                        CURRENT_TIMESTAMP, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 30 DAY))
            """, (user_id, yookassa_payment_id, 'balance_deposit', 'payment', amount, type, description, status))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving transaction: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_payment_info_directly(self, payment_id):
        try:
            payment = Payment.find_one(payment_id)
            return {
                'id': payment.id, 'status': payment.status, 'paid': payment.paid,
                'amount': payment.amount.value if payment.amount else None,
                'description': payment.description,
                'created_at': payment.created_at,
                'cancellation_details': getattr(payment, 'cancellation_details', None),
                'expires_at': getattr(payment, 'expires_at', None), 'test': getattr(payment, 'test', None)
            }
        except Exception as e:
            current_app.logger.error(f"Error getting payment info for {payment_id}: {e}")
            return None

    def check_payment_status(self, payment_id):
        try:
            payment = Payment.find_one(payment_id)
            amount_value = float(payment.amount.value) if payment.amount and payment.amount.value else None
            return {
                'id': payment.id, 'status': payment.status, 'paid': payment.paid,
                'amount': amount_value, 'description': payment.description
            }
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            return None

    def capture_payment(self, payment_id):
        try:
            payment = Payment.capture(payment_id, str(uuid.uuid4()))
            return payment.status == 'succeeded'
        except Exception as e:
            logger.error(f"Error capturing payment {payment_id}: {e}")
            return False

    def update_transaction_status(self, payment_id, status):
        conn = _get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT id, user_id, amount, status FROM transactions WHERE yookassa_payment_id = %s
            """, (payment_id,))
            transaction = cur.fetchone()
            if not transaction:
                return False
            trans_id, user_id, amount, current_status = transaction
            should_topup = False
            if current_status == 'succeeded':
                return True
            if current_status == 'canceled':
                return True
            if current_status in ('waiting_for_capture', 'pending') and status == 'succeeded':
                should_topup = True

            cur.execute("""
                UPDATE transactions SET status = %s, updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE WHEN %s IN ('succeeded', 'waiting_for_capture') THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE yookassa_payment_id = %s
            """, (status, status, payment_id))

            if status == 'succeeded' and current_status != 'succeeded':
                should_topup = True

            if status == 'waiting_for_capture':
                try:
                    payment_info = Payment.find_one(payment_id)
                    if payment_info:
                        captured = Payment.capture(payment_id, str(uuid.uuid4()))
                        if captured and captured.status == 'succeeded':
                            cur.execute("""
                                UPDATE transactions SET status = 'succeeded', completed_at = CURRENT_TIMESTAMP
                                WHERE yookassa_payment_id = %s
                            """, (payment_id,))
                            status = 'succeeded'
                except Exception as e:
                    logger.warning(f"Capture failed: {e}")

            if status == 'succeeded' and should_topup:
                try:
                    from logic.services.subscription_service import add_subscription_payment
                    add_subscription_payment(user_id, float(amount))
                except Exception:
                    pass
                cur.execute("SELECT id, balance FROM user_balance WHERE user_id = %s", (user_id,))
                balance_result = cur.fetchone()
                if balance_result:
                    cur.execute("""
                        UPDATE user_balance SET balance = balance + %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s
                    """, (amount, user_id))
                else:
                    cur.execute("INSERT INTO user_balance (user_id, balance, reserved_balance) VALUES (%s, %s, 0)", (user_id, amount))
                self._invalidate_balance_cache(user_id)
                cur.execute("""
                    UPDATE transactions SET description = CONCAT(COALESCE(description, ''), ' (баланс пополнен)')
                    WHERE yookassa_payment_id = %s
                """, (payment_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error update_transaction_status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_user_balance(self, user_id):
        cache_key = f"balance_{user_id}"
        now = time.time()
        if cache_key in _balance_cache:
            val, expiry = _balance_cache[cache_key]
            if now < expiry:
                return float(val)
        conn = _get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(balance, 0) FROM user_balance WHERE user_id = %s", (user_id,))
            result = cur.fetchone()
            balance = float(result[0]) if result else 0.00
            _balance_cache[cache_key] = (balance, now + _BALANCE_CACHE_TTL)
            return balance
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.00
        finally:
            conn.close()

    def _invalidate_balance_cache(self, user_id):
        _balance_cache.pop(f"balance_{user_id}", None)

    def get_transaction_history(self, user_id, limit=10, offset=0):
        conn = _get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT t.id, t.amount, t.type, t.description, t.status, t.created_at,
                       t.yookassa_payment_id, t.service_type, t.calculation_category, t.chart_id
                FROM transactions t WHERE t.user_id = %s ORDER BY t.created_at DESC LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            rows = cur.fetchall()
            transactions = []
            for row in rows:
                transactions.append({
                    'id': row[0], 'amount': float(row[1]), 'type': row[2], 'description': row[3],
                    'status': row[4], 'created_at': row[5].isoformat() if row[5] else None,
                    'yookassa_payment_id': row[6], 'service_type': row[7], 'calculation_category': row[8],
                    'chart_id': row[9], 'data_exists': False
                })
            return transactions
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
        finally:
            conn.close()


@payment_bp.route("/create", methods=["POST"])
@token_required
def create_payment():
    try:
        data = request.json or {}
        amount = float(data.get("amount", 0))
        if amount < 50:
            return jsonify({"status": "error", "message": "Минимальная сумма пополнения 50 рублей"}), 400
        if amount > 100000:
            return jsonify({"status": "error", "message": "Максимальная сумма пополнения 100 000 рублей"}), 400
        user_id = g.user_id
        yookassa_payment = YooKassaPayment()
        payment_result = yookassa_payment.create_payment(
            amount=amount,
            description=f"Пополнение баланса на {amount:.2f} руб.",
            user_id=user_id
        )
        return jsonify({"status": "success", "payment": payment_result})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating payment: {e}")
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500


@payment_bp.route("/webhook", methods=["POST"])
def payment_webhook():
    try:
        event_json = request.json or {}
        event_type = event_json.get("event")
        payment_data = event_json.get("object", {})
        payment_id = payment_data.get("id")
        payment_status = payment_data.get("status")
        if event_type not in ["payment.succeeded", "payment.waiting_for_capture", "payment.canceled"]:
            return jsonify({"status": "ok"})
        if not payment_status:
            return jsonify({"status": "error"}), 400
        yookassa_payment = YooKassaPayment()
        status_map = {'succeeded': 'succeeded', 'pending': 'pending',
                      'waiting_for_capture': 'waiting_for_capture', 'canceled': 'canceled'}
        db_status = status_map.get(payment_status, payment_status)
        yookassa_payment.update_transaction_status(payment_id, db_status)
        if db_status == 'waiting_for_capture':
            if yookassa_payment.capture_payment(payment_id):
                yookassa_payment.update_transaction_status(payment_id, 'succeeded')
        return jsonify({"status": "ok"})
    except Exception as e:
        current_app.logger.error(f"Webhook error: {e}")
        return jsonify({"status": "ok"})  # 200 чтобы ЮKassa не слала повторно


@payment_bp.route("/check_balance")
@token_required
def check_balance():
    try:
        yookassa_payment = YooKassaPayment()
        balance = yookassa_payment.get_user_balance(g.user_id)
        transactions = yookassa_payment.get_transaction_history(g.user_id, limit=20, offset=0)
        subscription = {"balance_rub": 0, "period_end": None, "can_profile_plan": False, "can_ai_plan": False, "tariff_name": "manual"}
        try:
            from logic.services.subscription_service import get_subscription
            subscription = get_subscription(g.user_id)
        except Exception:
            pass
        return jsonify({
            "status": "success",
            "balance": balance,
            "transactions": transactions,
            "subscription_balance": subscription.get("balance_rub", 0),
            "subscription_period_end": subscription.get("period_end"),
            "can_profile_plan": subscription.get("can_profile_plan", False),
            "can_ai_plan": subscription.get("can_ai_plan", False),
            "tariff_name": subscription.get("tariff_name", "manual"),
        })
    except Exception as e:
        current_app.logger.error(f"Error check_balance: {e}")
        return jsonify({"status": "error", "message": "Ошибка при получении баланса"}), 500


@payment_bp.route("/get_transactions", methods=["POST"])
@token_required
def get_transactions():
    try:
        data = request.get_json() or {}
        offset = int(data.get('offset', 0))
        limit = int(data.get('limit', 20))
        yookassa_payment = YooKassaPayment()
        transactions = yookassa_payment.get_transaction_history(g.user_id, limit=limit, offset=offset)
        return jsonify({"status": "success", "transactions": transactions, "has_more": len(transactions) == limit})
    except Exception as e:
        current_app.logger.error(f"Error get_transactions: {e}")
        return jsonify({"status": "error", "message": "Ошибка при получении транзакций"}), 500
