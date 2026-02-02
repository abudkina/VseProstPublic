"""
RAG (Retrieval-Augmented Generation) модуль для семантического поиска
Использует векторные представления (embeddings) для поиска релевантного контента
"""
import os
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from flask import current_app
from logic.model import db, Embedding, Problem, Solution
from logic.recommendations import get_model, cosine_similarity, create_embedding
from logic.utils.logger import get_logger

logger = get_logger(__name__)

# Попытка импортировать CLIP для мультимодального поиска
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logger.warning("⚠️ CLIP не установлен. Мультимодальный поиск будет недоступен.")

# Глобальные переменные для моделей
_clip_model = None
_clip_processor = None
_clip_model_name = 'openai/clip-vit-base-patch32'  # Легкая модель CLIP


def get_clip_model():
    """Получить или загрузить CLIP модель для мультимодального поиска"""
    global _clip_model, _clip_processor
    
    if not CLIP_AVAILABLE:
        return None, None
    
    if _clip_model is None:
        try:
            logger.info(f"🔄 Загрузка CLIP модели {_clip_model_name}...")
            _clip_model = CLIPModel.from_pretrained(_clip_model_name)
            _clip_processor = CLIPProcessor.from_pretrained(_clip_model_name)
            
            # Переводим в режим оценки (не обучения)
            _clip_model.eval()
            
            # Используем CPU по умолчанию (можно переключить на GPU если доступно)
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _clip_model = _clip_model.to(device)
            
            logger.info(f"✅ CLIP модель {_clip_model_name} загружена на {device}")
        except Exception as e:
            logger.error(f"⚠️ Ошибка загрузки CLIP модели: {e}")
            _clip_model = None
            _clip_processor = None
    
    return _clip_model, _clip_processor


def semantic_search(
    query: str,
    entity_type: str = 'problem',
    limit: int = 20,
    min_similarity: float = 0.3,
    exclude_ids: Optional[List[int]] = None
) -> List[Tuple[int, float]]:
    """
    Семантический поиск на основе векторных представлений (RAG)
    
    Args:
        query: Поисковый запрос
        entity_type: 'problem' or 'solution'
        limit: Максимальное количество результатов
        min_similarity: Минимальный порог сходства (0-1)
        exclude_ids: ID для исключения из результатов
    
    Returns:
        Список кортежей (entity_id, similarity_score) отсортированных по релевантности
    """
    try:
        if not query or len(query.strip()) == 0:
            return []
        
        # Получаем модель для векторизации запроса
        model = get_model()
        if not model:
            logger.warning("⚠️ Модель sentence-transformers не загружена, используем текстовый поиск")
            return []
        
        # Векторизуем поисковый запрос
        query_vector = model.encode(query, convert_to_numpy=True).tolist()
        
        # Получаем все embeddings для указанного типа сущности
        all_embeddings = Embedding.query.filter_by(
            entity_type=entity_type
        ).all()
        
        if not all_embeddings:
            logger.debug(f"Нет embeddings для типа {entity_type}")
            return []
        
        # Вычисляем сходство между запросом и каждым embedding
        similarities = []
        exclude_ids = exclude_ids or []
        
        for embedding in all_embeddings:
            if embedding.entity_id in exclude_ids:
                continue
            
            # Проверяем, что сущность существует и видима
            if entity_type == 'problem':
                entity = Problem.query.get(embedding.entity_id)
                if not entity or entity.show is None:
                    continue
            elif entity_type == 'solution':
                entity = Solution.query.get(embedding.entity_id)
                if not entity or entity.show is None:
                    continue
            else:
                continue
            
            # Вычисляем косинусное сходство
            similarity = cosine_similarity(query_vector, embedding.embedding_vector)
            
            if similarity >= min_similarity:
                similarities.append((embedding.entity_id, similarity))
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ результатов
        return similarities[:limit]
    
    except Exception as e:
        logger.error(f"⚠️ Ошибка семантического поиска: {e}")
        import traceback
        traceback.print_exc()
        return []


def hybrid_search(
    query: str,
    entity_type: str = 'problem',
    limit: int = 20,
    text_weight: float = 0.3,
    semantic_weight: float = 0.7,
    exclude_ids: Optional[List[int]] = None
) -> List[Tuple[int, float]]:
    """
    Гибридный поиск: комбинация текстового (LIKE) и семантического (RAG) поиска
    
    Args:
        query: Поисковый запрос
        entity_type: 'problem' or 'solution'
        limit: Максимальное количество результатов
        text_weight: Вес текстового поиска (0-1)
        semantic_weight: Вес семантического поиска (0-1)
        exclude_ids: ID для исключения из результатов
    
    Returns:
        Список кортежей (entity_id, combined_score) отсортированных по релевантности
    """
    try:
        if not query or len(query.strip()) == 0:
            return []
        
        # Нормализуем веса
        total_weight = text_weight + semantic_weight
        if total_weight > 0:
            text_weight = text_weight / total_weight
            semantic_weight = semantic_weight / total_weight
        
        # 1. Текстовый поиск (LIKE)
        text_results = {}
        try:
            if entity_type == 'problem':
                from sqlalchemy import func
                text_matches = Problem.query.filter(
                    db.or_(
                        func.lower(Problem.name).like(f"%{query.lower()}%"),
                        func.lower(Problem.describe).like(f"%{query.lower()}%")
                    ),
                    Problem.show.isnot(None)
                ).all()
            else:  # solution
                from sqlalchemy import func
                text_matches = Solution.query.filter(
                    db.or_(
                        func.lower(Solution.name).like(f"%{query.lower()}%"),
                        func.lower(Solution.describe).like(f"%{query.lower()}%")
                    ),
                    Solution.show.isnot(None)
                ).all()
            
            # Нормализуем результаты текстового поиска (1.0 для точного совпадения, меньше для частичного)
            for entity in text_matches:
                if entity.id in (exclude_ids or []):
                    continue
                
                # Вычисляем релевантность на основе количества совпадений
                name_match = query.lower() in (entity.name or '').lower()
                desc_match = query.lower() in (entity.describe or '').lower()
                
                score = 0.0
                if name_match:
                    score += 0.7  # Название важнее
                if desc_match:
                    score += 0.3
                
                text_results[entity.id] = min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Ошибка текстового поиска: {e}")
            text_results = {}
        
        # 2. Семантический поиск (RAG)
        semantic_results = {}
        try:
            semantic_matches = semantic_search(
                query=query,
                entity_type=entity_type,
                limit=limit * 2,  # Берем больше для лучшего объединения
                min_similarity=0.2,
                exclude_ids=exclude_ids
            )
            
            for entity_id, similarity in semantic_matches:
                semantic_results[entity_id] = similarity
        
        except Exception as e:
            logger.warning(f"Ошибка семантического поиска: {e}")
            semantic_results = {}
        
        # 3. Объединяем результаты
        combined_scores = {}
        all_ids = set(text_results.keys()) | set(semantic_results.keys())
        
        for entity_id in all_ids:
            text_score = text_results.get(entity_id, 0.0)
            semantic_score = semantic_results.get(entity_id, 0.0)
            
            # Взвешенная комбинация
            combined_score = (text_score * text_weight) + (semantic_score * semantic_weight)
            
            if combined_score > 0:
                combined_scores[entity_id] = combined_score
        
        # Сортируем по убыванию комбинированного счета
        sorted_results = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Возвращаем топ результатов
        return sorted_results[:limit]
    
    except Exception as e:
        logger.error(f"⚠️ Ошибка гибридного поиска: {e}")
        import traceback
        traceback.print_exc()
        return []


def multimodal_search(
    query: Union[str, bytes],
    entity_type: str = 'problem',
    limit: int = 20,
    min_similarity: float = 0.2,
    exclude_ids: Optional[List[int]] = None,
    is_image: bool = False
) -> List[Tuple[int, float]]:
    """
    Мультимодальный поиск с использованием LMM (CLIP)
    Поддерживает поиск по тексту или изображению
    
    Args:
        query: Текстовый запрос или путь к изображению/байты изображения
        entity_type: 'problem' or 'solution'
        limit: Максимальное количество результатов
        min_similarity: Минимальный порог сходства
        exclude_ids: ID для исключения из результатов
        is_image: True если query - это изображение
    
    Returns:
        Список кортежей (entity_id, similarity_score)
    """
    try:
        clip_model, clip_processor = get_clip_model()
        
        if not clip_model or not clip_processor:
            logger.warning("⚠️ CLIP модель не доступна, используем обычный семантический поиск")
            if isinstance(query, str) and not is_image:
                return semantic_search(query, entity_type, limit, min_similarity, exclude_ids)
            return []
        
        # Получаем все сущности с изображениями
        if entity_type == 'problem':
            entities = Problem.query.filter(
                Problem.show.isnot(None),
                Problem.image.isnot(None),
                Problem.image != '',
                Problem.image != '../images/default.png'
            ).all()
        else:  # solution
            entities = Solution.query.filter(
                Solution.show.isnot(None),
                Solution.image.isnot(None),
                Solution.image != '',
                Solution.image != '../images/default.png'
            ).all()
        
        if not entities:
            logger.debug(f"Нет сущностей с изображениями для типа {entity_type}")
            # Fallback на семантический поиск если запрос текстовый
            if isinstance(query, str) and not is_image:
                return semantic_search(query, entity_type, limit, min_similarity, exclude_ids)
            return []
        
        # Подготавливаем запрос для CLIP
        device = next(clip_model.parameters()).device
        
        if is_image:
            # Если запрос - изображение
            from PIL import Image
            import io
            
            if isinstance(query, bytes):
                image = Image.open(io.BytesIO(query))
            else:
                # Предполагаем, что это путь к файлу
                if not os.path.exists(query):
                    logger.warning(f"Изображение не найдено: {query}")
                    return []
                image = Image.open(query)
            
            inputs = clip_processor(images=image, return_tensors="pt", padding=True).to(device)
            query_features = clip_model.get_image_features(**inputs)
        else:
            # Если запрос - текст
            inputs = clip_processor(text=[query], return_tensors="pt", padding=True).to(device)
            query_features = clip_model.get_text_features(**inputs)
        
        # Нормализуем вектор запроса
        query_features = query_features / query_features.norm(dim=-1, keepdim=True)
        
        # Вычисляем сходство с изображениями сущностей
        similarities = []
        exclude_ids = exclude_ids or []
        
        for entity in entities:
            if entity.id in exclude_ids:
                continue
            
            try:
                # Загружаем изображение сущности
                image_path = entity.image
                if not image_path or not os.path.exists(image_path):
                    # Пробуем относительный путь
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    image_path = os.path.join(project_root, image_path.lstrip('/'))
                
                if not os.path.exists(image_path):
                    continue
                
                from PIL import Image
                entity_image = Image.open(image_path)
                
                # Получаем features изображения
                image_inputs = clip_processor(images=entity_image, return_tensors="pt", padding=True).to(device)
                image_features = clip_model.get_image_features(**image_inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # Вычисляем косинусное сходство
                similarity = float(torch.cosine_similarity(query_features, image_features).item())
                
                if similarity >= min_similarity:
                    similarities.append((entity.id, similarity))
            
            except Exception as e:
                logger.debug(f"Ошибка обработки изображения для {entity_type} {entity.id}: {e}")
                continue
        
        # Сортируем по убыванию сходства
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ результатов
        return similarities[:limit]
    
    except Exception as e:
        logger.error(f"⚠️ Ошибка мультимодального поиска: {e}")
        import traceback
        traceback.print_exc()
        # Fallback на семантический поиск
        if isinstance(query, str) and not is_image:
            return semantic_search(query, entity_type, limit, min_similarity, exclude_ids)
        return []


def search_with_rag(
    query: str,
    entity_type: str = 'problem',
    search_mode: str = 'hybrid',
    limit: int = 20,
    exclude_ids: Optional[List[int]] = None
) -> List[Tuple[int, float]]:
    """
    Универсальная функция поиска с поддержкой RAG, ML и LMM
    
    Args:
        query: Поисковый запрос
        entity_type: 'problem' or 'solution'
        search_mode: 'text', 'semantic', 'hybrid', 'multimodal'
        limit: Максимальное количество результатов
        exclude_ids: ID для исключения из результатов
    
    Returns:
        Список кортежей (entity_id, score)
    """
    try:
        if not query or len(query.strip()) == 0:
            return []
        
        if search_mode == 'text':
            # Только текстовый поиск (LIKE)
            from sqlalchemy import func
            if entity_type == 'problem':
                entities = Problem.query.filter(
                    db.or_(
                        func.lower(Problem.name).like(f"%{query.lower()}%"),
                        func.lower(Problem.describe).like(f"%{query.lower()}%")
                    ),
                    Problem.show.isnot(None)
                ).limit(limit).all()
            else:
                entities = Solution.query.filter(
                    db.or_(
                        func.lower(Solution.name).like(f"%{query.lower()}%"),
                        func.lower(Solution.describe).like(f"%{query.lower()}%")
                    ),
                    Solution.show.isnot(None)
                ).limit(limit).all()
            
            return [(e.id, 1.0) for e in entities if e.id not in (exclude_ids or [])]
        
        elif search_mode == 'semantic':
            # Только семантический поиск (RAG)
            return semantic_search(query, entity_type, limit, exclude_ids=exclude_ids)
        
        elif search_mode == 'hybrid':
            # Гибридный поиск (текст + семантика)
            return hybrid_search(query, entity_type, limit, exclude_ids=exclude_ids)
        
        elif search_mode == 'multimodal':
            # Мультимодальный поиск (LMM)
            return multimodal_search(query, entity_type, limit, exclude_ids=exclude_ids, is_image=False)
        
        else:
            # По умолчанию используем гибридный поиск
            return hybrid_search(query, entity_type, limit, exclude_ids=exclude_ids)
    
    except Exception as e:
        logger.error(f"⚠️ Ошибка поиска с RAG: {e}")
        import traceback
        traceback.print_exc()
        return []
