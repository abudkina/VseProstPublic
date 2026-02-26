# ai_routes.py — API создания проблемы с решениями по ИИ (тариф 999 руб/мес)
from flask import Blueprint, jsonify, request, g
from logic.middleware import token_required
from logic.services.subscription_service import get_subscription
from logic.ai_problem_service import create_problem_with_solutions_from_query

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/create-problem-from-query", methods=["POST"])
@token_required
def create_problem_from_query():
    """Создать проблему и 10 решений по текстовому запросу. Доступно при подключённом тарифе ИИ (999 руб/мес)."""
    try:
        user_id = getattr(g, "user_id", None)
        if not user_id:
            return jsonify({"status": "error", "message": "Требуется авторизация"}), 401
        subscription = get_subscription(user_id)
        if not subscription.get("can_ai_plan"):
            return jsonify({
                "status": "error",
                "message": "Подключите тариф ИИ (999 руб/мес) для создания проблемы с помощью ИИ",
                "ai_plan_price_rub": 999,
            }), 403
        data = request.get_json() or {}
        query = (data.get("query") or data.get("text") or "").strip()
        if not query:
            return jsonify({"status": "error", "message": "Укажите запрос (query)"}), 400
        result = create_problem_with_solutions_from_query(user_id, query)
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
        return jsonify({"status": "success", "problem": result["problem"], "solutions": result["solutions"]}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": "Внутренняя ошибка сервера"}), 500
