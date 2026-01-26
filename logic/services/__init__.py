"""
Service layer - бизнес-логика приложения

Services содержат всю бизнес-логику и отделены от HTTP endpoints.
Это позволяет переиспользовать бизнес-логику и упрощает тестирование.
"""

from logic.services.problem_service import ProblemService
from logic.services.solution_service import SolutionService

__all__ = ['ProblemService', 'SolutionService']
