"""
Модуль для рекомендаций на основе ML/LMM моделей
Использует sentence-transformers для векторизации текстов и поиска похожих элементов
"""
import os
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from flask import current_app
from logic.model import db, UserActivity, Embedding, Problem, Solution, User
from logic.utils.logger import get_logger

logger = get_logger(__name__)

# Попытка импортировать sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers не установлен. Рекомендации будут работать в упрощенном режиме.")

# Глобальная переменная для модели (загружается один раз)
_model = None
# Используем более легкую модель для быстрой загрузки (поддерживает русский)
_model_name = 'paraphrase-multilingual-MiniLM-L12-v2'  # 384 размерность, ~420MB
# Альтернатива (еще легче, но меньше размерность): 'paraphrase-multilingual-mpnet-base-v2'

def get_model():
    """Получить или загрузить модель sentence-transformers"""
    global _model
    if _model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            logger.info(f"Загрузка модели {_model_name}...")
            _model = SentenceTransformer(_model_name)
            logger.info(f"Модель {_model_name} загружена успешно")
        except Exception as e:
            logger.warning(f"Ошибка загрузки модели: {e}")
            logger.info("Рекомендации будут работать в упрощенном режиме (на основе текстового поиска)")
    return _model

def track_user_activity(user_id: int, activity_type: str, entity_type: str, 
                       entity_id: Optional[int] = None, search_query: Optional[str] = None):
    """
    Отслеживание активности пользователя
    
    Args:
        user_id: ID пользователя
        activity_type: 'create', 'search', 'favorite', 'view'
        entity_type: 'problem' or 'solution'
        entity_id: ID проблемы или решения (опционально)
        search_query: Поисковый запрос (для типа 'search')
    """
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            search_query=search_query,
            created_date=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
        
        # Запускаем обновление персональных знаний (асинхронно, не блокируя основной процесс)
        try:
            from logic.user_knowledge import trigger_knowledge_update
            trigger_knowledge_update(user_id)
        except Exception as e:
            # Не критично, если не удалось обновить знания
            logger.warning(f"Не удалось обновить персональные знания: {e}")
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Ошибка отслеживания активности: {e}")

def get_text_for_embedding(entity_type: str, entity_id: int) -> Optional[str]:
    """Получить текст для векторизации из проблемы или решения"""
    try:
        if entity_type == 'problem':
            problem = Problem.query.get(entity_id)
            if problem:
                # Объединяем название, описание и хэштеги
                text_parts = []
                if problem.name:
                    text_parts.append(problem.name)
                if problem.describe:
                    text_parts.append(problem.describe)
                # Добавляем хэштеги
                if hasattr(problem, 'hashtags') and problem.hashtags:
                    hashtag_names = [h.name for h in problem.hashtags]
                    text_parts.extend(hashtag_names)
                return ' '.join(text_parts)
        elif entity_type == 'solution':
            solution = Solution.query.get(entity_id)
            if solution:
                # Объединяем название и описание
                text_parts = []
                if solution.name:
                    text_parts.append(solution.name)
                if solution.describe:
                    text_parts.append(solution.describe)
                return ' '.join(text_parts)
    except Exception as e:
        logger.warning(f"Ошибка получения текста для векторизации: {e}")
    return None

def create_embedding(entity_type: str, entity_id: int, force_update: bool = False) -> Optional[List[float]]:
    """
    Создать или получить векторное представление для проблемы/решения
    
    Args:
        entity_type: 'problem' or 'solution'
        entity_id: ID проблемы или решения
        force_update: Принудительно обновить вектор
    
    Returns:
        Вектор (список чисел) или None
    """
    try:
        # Проверяем, есть ли уже вектор
        if not force_update:
            existing = Embedding.query.filter_by(
                entity_type=entity_type,
                entity_id=entity_id
            ).first()
            if existing:
                return existing.embedding_vector
        
        # Получаем текст для векторизации
        text = get_text_for_embedding(entity_type, entity_id)
        if not text or len(text.strip()) == 0:
            return None
        
        # Векторизуем с помощью модели
        model = get_model()
        if model:
            # Используем sentence-transformers
            vector = model.encode(text, convert_to_numpy=True).tolist()
        else:
            # Упрощенный режим: используем простой TF-IDF или просто возвращаем None
            # В реальном приложении можно использовать sklearn TfidfVectorizer
            logger.debug("Модель не загружена, пропускаем векторизацию")
            return None
        
        # Сохраняем вектор в БД
        if force_update:
            existing = Embedding.query.filter_by(
                entity_type=entity_type,
                entity_id=entity_id
            ).first()
            if existing:
                existing.embedding_vector = vector
                existing.text_content = text
                existing.modified_date = datetime.utcnow()
            else:
                embedding = Embedding(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    embedding_vector=vector,
                    text_content=text,
                    model_name=_model_name
                )
                db.session.add(embedding)
        else:
            embedding = Embedding(
                entity_type=entity_type,
                entity_id=entity_id,
                embedding_vector=vector,
                text_content=text,
                model_name=_model_name
            )
            db.session.add(embedding)
        
        db.session.commit()
        return vector
    
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Ошибка создания вектора: {e}")
        import traceback
        traceback.print_exc()
        return None

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Вычислить косинусное сходство между двумя векторами"""
    try:
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        logger.warning(f"Ошибка вычисления косинусного сходства: {e}")
        return 0.0

def find_similar_entities(entity_type: str, entity_id: int, limit: int = 10, 
                         exclude_ids: Optional[List[int]] = None) -> List[Tuple[int, float]]:
    """
    Найти похожие проблемы/решения на основе векторного сходства
    
    Args:
        entity_type: 'problem' or 'solution'
        entity_id: ID проблемы или решения
        limit: Максимальное количество результатов
        exclude_ids: ID для исключения из результатов
    
    Returns:
        Список кортежей (entity_id, similarity_score)
    """
    try:
        # Получаем вектор для текущей сущности
        current_embedding = Embedding.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).first()
        
        if not current_embedding:
            # Пытаемся создать вектор
            vector = create_embedding(entity_type, entity_id)
            if not vector:
                return []
            current_embedding = Embedding.query.filter_by(
                entity_type=entity_type,
                entity_id=entity_id
            ).first()
            if not current_embedding:
                return []
        
        current_vector = current_embedding.embedding_vector
        
        # Получаем все векторы того же типа
        all_embeddings = Embedding.query.filter_by(
            entity_type=entity_type
        ).all()
        
        # Вычисляем сходство
        similarities = []
        exclude_ids = exclude_ids or []
        
        for embedding in all_embeddings:
            if embedding.entity_id == entity_id or embedding.entity_id in exclude_ids:
                continue
            
            similarity = cosine_similarity(current_vector, embedding.embedding_vector)
            similarities.append((embedding.entity_id, similarity))
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ результатов
        return similarities[:limit]
    
    except Exception as e:
        logger.warning(f"Ошибка поиска похожих сущностей: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_user_recommendations(user_id: int, entity_type: str, limit: int = 20) -> List[int]:
    """
    Получить рекомендации для пользователя на основе его активности
    
    Args:
        user_id: ID пользователя
        entity_type: 'problem' or 'solution'
        limit: Максимальное количество рекомендаций
    
    Returns:
        Список ID рекомендованных проблем/решений
    """
    try:
        # Получаем последнюю активность пользователя (за последние 30 дней)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.entity_type == entity_type,
            UserActivity.created_date >= cutoff_date
        ).order_by(UserActivity.created_date.desc()).limit(50).all()
        
        if not activities:
            return []
        
        # Собираем ID сущностей, с которыми взаимодействовал пользователь
        interacted_ids = set()
        search_queries = []
        
        for activity in activities:
            if activity.entity_id:
                interacted_ids.add(activity.entity_id)
            if activity.activity_type == 'search' and activity.search_query:
                search_queries.append(activity.search_query)
        
        if not interacted_ids and not search_queries:
            return []
        
        # Находим похожие сущности на основе взаимодействий
        recommended_ids = set()
        
        # Для каждой взаимодействованной сущности находим похожие
        for entity_id in list(interacted_ids)[:10]:  # Ограничиваем для производительности
            similar = find_similar_entities(entity_type, entity_id, limit=5, exclude_ids=list(interacted_ids))
            for similar_id, score in similar:
                if score > 0.3:  # Минимальный порог сходства
                    recommended_ids.add(similar_id)
        
        # Если есть поисковые запросы, находим похожие на основе запросов
        if search_queries and SENTENCE_TRANSFORMERS_AVAILABLE:
            model = get_model()
            if model:
                # Векторизуем последний поисковый запрос
                last_query = search_queries[0]
                query_vector = model.encode(last_query, convert_to_numpy=True).tolist()
                
                # Ищем похожие сущности по векторам
                all_embeddings = Embedding.query.filter_by(entity_type=entity_type).all()
                for embedding in all_embeddings:
                    if embedding.entity_id in interacted_ids:
                        continue
                    similarity = cosine_similarity(query_vector, embedding.embedding_vector)
                    if similarity > 0.3:
                        recommended_ids.add(embedding.entity_id)
        
        # Преобразуем в список и ограничиваем
        recommended_list = list(recommended_ids)[:limit]
        
        return recommended_list
    
    except Exception as e:
        logger.warning(f"Ошибка получения рекомендаций: {e}")
        import traceback
        traceback.print_exc()
        return []

def batch_create_embeddings(entity_type: str, entity_ids: Optional[List[int]] = None, 
                           batch_size: int = 10):
    """
    Создать векторы для множества проблем/решений (для первоначальной настройки)
    
    Args:
        entity_type: 'problem' or 'solution'
        entity_ids: Список ID для обработки (если None, обрабатываются все)
        batch_size: Размер батча для обработки
    """
    try:
        if entity_type == 'problem':
            if entity_ids:
                entities = Problem.query.filter(Problem.id.in_(entity_ids)).all()
            else:
                entities = Problem.query.all()
        elif entity_type == 'solution':
            if entity_ids:
                entities = Solution.query.filter(Solution.id.in_(entity_ids)).all()
            else:
                entities = Solution.query.all()
        else:
            return
        
        total = len(entities)
        processed = 0
        
        logger.info(f"Создание векторов для {total} {entity_type}...")
        
        for i in range(0, total, batch_size):
            batch = entities[i:i+batch_size]
            for entity in batch:
                try:
                    create_embedding(entity_type, entity.id, force_update=False)
                    processed += 1
                    if processed % 10 == 0:
                        logger.info(f"Обработано: {processed}/{total}")
                except Exception as e:
                    logger.warning(f"Ошибка обработки {entity_type} {entity.id}: {e}")
                    continue
        
        logger.info(f"Создано векторов: {processed}/{total}")
    
    except Exception as e:
        logger.error(f"Ошибка batch создания векторов: {e}")
        import traceback
        traceback.print_exc()
