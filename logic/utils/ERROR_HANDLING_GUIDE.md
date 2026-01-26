"""
Документация по единой системе обработки ошибок

=============================================================================
СТРУКТУРА ПРОЕКТА
=============================================================================

Новые модули в logic/utils/:
- error_handler.py: Основные классы ошибок (AppError и подклассы)
- error_decorators.py: Декораторы для endpoints

=============================================================================
ИСПОЛЬЗОВАНИЕ
=============================================================================

1. БАЗОВЫЕ КЛАССЫ ОШИБОК (в logic/utils/error_handler.py):

   - AppError: Базовый класс для всех ошибок приложения
   - ValidationError: Ошибки валидации (400)
   - AuthenticationError: Ошибки аутентификации (401)
   - AuthorizationError: Ошибки авторизации (403)
   - ResourceNotFoundError: Ресурс не найден (404)
   - ConflictError: Конфликты данных (409)
   - RateLimitError: Превышение лимита запросов (429)
   - DatabaseError: Ошибки БД (500)

2. ИСПОЛЬЗОВАНИЕ В ENDPOINTS:

   СТАРЫЙ КОД:
   -----------
   @problem_bp.route('/problems', methods=['GET'])
   def get_problems():
       try:
           problems = Problem.query.all()
           if not problems:
               return jsonify({'error': 'Проблемы не найдены'}), 404
           return jsonify([...]), 200
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   НОВЫЙ КОД:
   ----------
   from logic.utils.error_handler import ResourceNotFoundError, DatabaseError
   from logic.utils.error_decorators import handle_errors

   @problem_bp.route('/problems', methods=['GET'])
   @handle_errors()  # Автоматическая обработка ошибок
   def get_problems():
       problems = Problem.query.all()
       if not problems:
           raise ResourceNotFoundError('Problem')  # Автоматически вернет 404
       return {'data': problems}, 200


3. ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ОШИБОК:

   # Валидация входных данных
   from logic.utils.error_handler import ValidationError
   
   @handle_errors()
   def create_problem():
       title = request.json.get('title')
       if not title or len(title) < 3:
           raise ValidationError(
               "Название слишком короткое",
               details={'min_length': 3, 'provided_length': len(title or '')}
           )
       
       # Ваш код...


   # Ошибка авторизации
   from logic.utils.error_handler import AuthorizationError
   
   @handle_errors()
   def delete_problem(problem_id):
       problem = Problem.query.get(problem_id)
       if problem.creator_id != current_user_id:
           raise AuthorizationError("Только автор может удалить проблему")
       
       # Ваш код...


   # Ошибка конфликта
   from logic.utils.error_handler import ConflictError
   
   @handle_errors()
   def create_category():
       category = Category.query.filter_by(name=request.json['name']).first()
       if category:
           raise ConflictError("Категория с таким названием уже существует")
       
       # Ваш код...


4. СТРУКТУРА ОТВЕТА:

   При успехе (без использования handle_errors):
   {
       "success": true,
       "data": {...},
       "message": "Успешно",
       "status": 200
   }

   При ошибке:
   {
       "success": false,
       "error": {
           "code": "INVALID_INPUT",
           "message": "Название слишком короткое",
           "details": {  // Только если include_details=True
               "min_length": 3
           }
       }
   }

=============================================================================
МИГРАЦИЯ СТАРОГО КОДА
=============================================================================

Этапы:
1. Обновить общие обработчики ошибок в app.py для использования новых классов
2. Миграция blueprint'ов:
   - problem.py (1426 строк) - Приоритет 1
   - solution.py (1265 строк) - Приоритет 1
   - authorization.py - Приоритет 2
   - user.py - Приоритет 2
   - ... остальные - По мере возможности

3. Для каждого blueprint:
   - Добавить импорт: from logic.utils.error_decorators import handle_errors
   - Добавить @handle_errors() к endpoints
   - Заменить try-except на raise ошибок
   - Обновить return statements для единообразия

=============================================================================
РАСШИРЕНИЕ СИСТЕМЫ
=============================================================================

Если нужны новые типы ошибок, добавьте в ErrorCode enum и создайте подкласс AppError:

   class CustomError(AppError):
       def __init__(self, message: str):
           super().__init__(
               message=message,
               error_code=ErrorCode.CUSTOM_ERROR,
               status_code=400  # или другой
           )

=============================================================================
"""
