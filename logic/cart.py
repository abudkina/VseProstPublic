from flask import Blueprint, jsonify, request, g
from datetime import datetime
from logic.model import UserCartSolution, Solution, User, Problem, db
from logic.middleware import token_required
from logic.utils.logger import get_logger
from logic.utils.file_utils import normalize_image_url, image_url_for_display

logger = get_logger(__name__)

cart_bp = Blueprint('cart', __name__, url_prefix='/api')

@cart_bp.route('/cart', methods=['GET'])
@token_required
def get_cart():
    """Получение списка решений в корзине пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Получаем все решения в корзине пользователя
        cart_items = UserCartSolution.query.filter_by(
            user=user_id,
            is_bought=False
        ).all()
        
        base_url = request.url_root.rstrip('/')
        solutions_list = []
        for item in cart_items:
            solution = Solution.query.get(item.solution)
            if solution:
                # Получаем информацию о проблеме, к которой относится решение
                problem_info = None
                if hasattr(solution, 'problems') and solution.problems:
                    # Берем первую проблему из списка
                    first_problem = solution.problems[0]
                    problem_info = {
                        'ID': first_problem.id,
                        'Name': first_problem.name
                    }
                
                solution_data = {
                    'ID': solution.id,
                    'Name': solution.name,
                    'Describe': solution.describe or '',
                    'Image': image_url_for_display(solution.image, base_url, '/assets/images/default.png'),
                    'Price': float(solution.price) if solution.price else 0,
                    'Efficiency': solution.efficiency or 0,
                    'Complexity': solution.complexity or 0,
                    'Time': solution.time or 0,
                    'Favourite': solution.favourite or 0,
                    'Show': solution.show or 0,
                    'Reply': solution.reply or 0,
                    'CartItemId': item.id,
                    'IsBought': item.is_bought,  # Статус покупки из корзины
                    'Problem': problem_info,  # Информация о проблеме
                    'CreatedDate': solution.created_date.isoformat() if solution.created_date else '',
                    'ModifiedDate': solution.modified_date.isoformat() if solution.modified_date else ''
                }
                solutions_list.append(solution_data)
        
        return jsonify(solutions_list), 200
        
    except Exception as e:
        logger.exception(f"Ошибка получения корзины: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Ошибка базы данных', 'details': str(e)}), 500

@cart_bp.route('/cart/<int:solution_id>', methods=['POST'])
@token_required
def add_to_cart(solution_id):
    """Добавление решения в корзину"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Проверяем, существует ли решение
        solution = Solution.query.get(solution_id)
        if not solution:
            return jsonify({'error': 'Решение не найдено'}), 404
        
        # Проверяем, не добавлено ли уже в корзину
        existing_item = UserCartSolution.query.filter_by(
            user=user_id,
            solution=solution_id,
            is_bought=False
        ).first()
        
        if existing_item:
            return jsonify({
                'message': 'Решение уже в корзине',
                'in_cart': True
            }), 200
        
        # Создаем новую запись в корзине
        cart_item = UserCartSolution(
            user=user_id,
            solution=solution_id,
            creator=user_id,
            is_bought=False,
            created_date=datetime.utcnow(),
            modified_date=datetime.utcnow()
        )
        
        try:
            db.session.add(cart_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Ошибка добавления в корзину: {e}")
            return jsonify({'error': 'Ошибка добавления в корзину'}), 500
        
        return jsonify({
            'message': 'Решение добавлено в корзину',
            'in_cart': True,
            'cart_item_id': cart_item.id
        }), 201
        
    except Exception as e:
        logger.exception(f"Ошибка добавления в корзину: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@cart_bp.route('/cart/<int:solution_id>', methods=['DELETE'])
@token_required
def remove_from_cart(solution_id):
    """Удаление решения из корзины"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Находим запись в корзине
        cart_item = UserCartSolution.query.filter_by(
            user=user_id,
            solution=solution_id,
            is_bought=False
        ).first()
        
        if not cart_item:
            return jsonify({'error': 'Решение не найдено в корзине'}), 404
        
        try:
            db.session.delete(cart_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Ошибка удаления из корзины: {e}")
            return jsonify({'error': 'Ошибка удаления из корзины'}), 500
        
        return jsonify({
            'message': 'Решение удалено из корзины',
            'in_cart': False
        }), 200
        
    except Exception as e:
        logger.exception(f"Ошибка удаления из корзины: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@cart_bp.route('/cart/item/<int:cart_item_id>', methods=['DELETE'])
@token_required
def remove_cart_item(cart_item_id):
    """Удаление элемента корзины по ID"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        # Находим запись в корзине
        cart_item = UserCartSolution.query.get(cart_item_id)
        
        if not cart_item:
            return jsonify({'error': 'Элемент корзины не найден'}), 404
        
        # Проверяем, что это корзина текущего пользователя
        if cart_item.user != user_id:
            return jsonify({'error': 'Нет прав на удаление'}), 403
        
        try:
            db.session.delete(cart_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Ошибка удаления из корзины: {e}")
            return jsonify({'error': 'Ошибка удаления из корзины'}), 500
        
        return jsonify({
            'message': 'Решение удалено из корзины'
        }), 200
        
    except Exception as e:
        logger.exception(f"Ошибка удаления из корзины: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@cart_bp.route('/cart/check/<int:solution_id>', methods=['GET'])
@token_required
def check_in_cart(solution_id):
    """Проверка, находится ли решение в корзине пользователя"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        cart_item = UserCartSolution.query.filter_by(
            user=user_id,
            solution=solution_id,
            is_bought=False
        ).first()
        
        return jsonify({
            'in_cart': cart_item is not None,
            'cart_item_id': cart_item.id if cart_item else None
        }), 200
        
    except Exception as e:
        logger.exception(f"Ошибка проверки корзины: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера', 'details': str(e)}), 500

@cart_bp.route('/cart/count', methods=['GET'])
@token_required
def get_cart_count():
    """Получение количества решений в корзине"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'error': 'userID не найден'}), 401
        
        count = UserCartSolution.query.filter_by(
            user=user_id,
            is_bought=False
        ).count()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        logger.exception(f"Ошибка подсчета корзины: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Внутренняя ошибка сервера', 'details': str(e)}), 500

