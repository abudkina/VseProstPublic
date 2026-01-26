"""
Unit тесты для SolutionService

Тестирует бизнес-логику работы с решениями без зависимости от Flask endpoints.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from logic.services.solution_service import SolutionService
from logic.utils.error_handler import (
    ValidationError, ResourceNotFoundError, AuthorizationError
)
from logic.model import Solution, Problem, Hashtag, User


class TestSolutionService:
    """Тесты для SolutionService"""
    
    def test_get_all_solutions_empty(self):
        """Тест получения пустого списка решений"""
        with patch('logic.services.solution_service.Solution') as mock_solution:
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = []
            mock_query.count.return_value = 0
            
            mock_solution.query = MagicMock()
            mock_solution.query.options.return_value = mock_query
            
            solutions, total = SolutionService.get_all_solutions()
            
            assert solutions == []
            assert total == 0
    
    def test_get_all_solutions_with_filters(self):
        """Тест получения решений с фильтрами"""
        with patch('logic.services.solution_service.Solution') as mock_solution:
            mock_solution_obj = Mock()
            mock_solution_obj.id = 1
            mock_solution_obj.name = "Test Solution"
            mock_solution_obj.describe = "Test Description"
            mock_solution_obj.problem_id = 1
            mock_solution_obj.creator_id = 1
            mock_solution_obj.created_date = datetime.utcnow()
            mock_solution_obj.modified_date = None
            mock_solution_obj.show = True
            mock_solution_obj.hashtags = []
            mock_solution_obj.creator = None
            
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.options.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = [mock_solution_obj]
            mock_query.count.return_value = 1
            
            mock_solution.query = MagicMock()
            mock_solution.query.options.return_value = mock_query
            
            solutions, total = SolutionService.get_all_solutions(
                problem_id=1,
                search="Test",
                limit=10,
                offset=0
            )
            
            assert len(solutions) == 1
            assert total == 1
            assert solutions[0]['ID'] == 1
            assert solutions[0]['Name'] == "Test Solution"
    
    def test_get_solution_by_id_not_found(self):
        """Тест получения несуществующего решения"""
        with patch('logic.services.solution_service.Solution') as mock_solution:
            mock_query = MagicMock()
            mock_query.options.return_value = mock_query
            mock_query.get.return_value = None
            
            mock_solution.query = MagicMock()
            mock_solution.query.options.return_value = mock_query
            
            with pytest.raises(ResourceNotFoundError) as exc_info:
                SolutionService.get_solution_by_id(999)
            
            assert "не найден" in str(exc_info.value.message)
    
    def test_create_solution_validation_error_empty_name(self):
        """Тест создания решения с пустым названием"""
        with pytest.raises(ValidationError) as exc_info:
            SolutionService.create_solution(
                user_id=1,
                data={'name': '', 'describe': 'Test'}
            )
        
        assert "обязательно" in str(exc_info.value.message)
    
    def test_create_solution_validation_error_long_name(self):
        """Тест создания решения с слишком длинным названием"""
        long_name = 'a' * (SolutionService.MAX_TITLE_LENGTH + 1)
        
        with pytest.raises(ValidationError) as exc_info:
            SolutionService.create_solution(
                user_id=1,
                data={'name': long_name, 'describe': 'Test'}
            )
        
        assert "слишком длинное" in str(exc_info.value.message)
    
    def test_create_solution_validation_error_invalid_problem(self):
        """Тест создания решения с несуществующей проблемой"""
        with patch('logic.services.solution_service.Problem') as mock_problem:
            mock_problem.query.get.return_value = None
            
            with pytest.raises(ValidationError) as exc_info:
                SolutionService.create_solution(
                    user_id=1,
                    data={'name': 'Test', 'problem_id': 999}
                )
            
            assert "Проблема не найдена" in str(exc_info.value.message)
    
    def test_update_solution_not_found(self):
        """Тест обновления несуществующего решения"""
        with patch('logic.services.solution_service.Solution') as mock_solution:
            mock_solution.query.get.return_value = None
            
            with pytest.raises(ResourceNotFoundError):
                SolutionService.update_solution(999, 1, {'name': 'New Name'})
    
    def test_update_solution_unauthorized(self):
        """Тест обновления решения не автором"""
        mock_solution = Mock()
        mock_solution.creator_id = 1  # Другой пользователь
        
        with patch('logic.services.solution_service.Solution') as mock_solution_class:
            mock_solution_class.query.get.return_value = mock_solution
            
            with pytest.raises(AuthorizationError) as exc_info:
                SolutionService.update_solution(1, 2, {'name': 'New Name'})
            
            assert "создатель" in str(exc_info.value.message)
    
    def test_delete_solution_not_found(self):
        """Тест удаления несуществующего решения"""
        with patch('logic.services.solution_service.Solution') as mock_solution:
            mock_solution.query.get.return_value = None
            
            with pytest.raises(ResourceNotFoundError):
                SolutionService.delete_solution(999, 1)
    
    def test_delete_solution_unauthorized(self):
        """Тест удаления решения не автором"""
        mock_solution = Mock()
        mock_solution.creator_id = 1  # Другой пользователь
        
        with patch('logic.services.solution_service.Solution') as mock_solution_class:
            mock_solution_class.query.get.return_value = mock_solution
            
            with pytest.raises(AuthorizationError):
                SolutionService.delete_solution(1, 2)
    
    def test_format_solution_response(self):
        """Тест форматирования ответа решения"""
        mock_solution = Mock()
        mock_solution.id = 1
        mock_solution.name = "Test"
        mock_solution.describe = "Description"
        mock_solution.problem_id = 1
        mock_solution.creator_id = 1
        mock_solution.created_date = datetime.utcnow()
        mock_solution.modified_date = None
        mock_solution.show = True
        mock_solution.hashtags = []
        mock_solution.creator = None
        
        result = SolutionService._format_solution_response(mock_solution, user_id=None)
        
        assert result['ID'] == 1
        assert result['Name'] == "Test"
        assert result['Describe'] == "Description"
        assert result['ProblemID'] == 1
        assert result['IsFavourite'] is False
        assert result['Show'] is True
