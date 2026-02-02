"""
Модуль для управления персональными знаниями пользователя
Анализирует активность пользователя (поиски, просмотры) и создает персональный профиль знаний
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter
from flask import current_app
from logic.model import db, UserKnowledge, UserActivity, Problem, Solution, Category, Hashtag, Topic, User


def update_user_knowledge(user_id: int, force_update: bool = False) -> Optional[UserKnowledge]:
    """
    Обновить персональные знания пользователя на основе его активности
    
    Args:
        user_id: ID пользователя
        force_update: Принудительно обновить даже если недавно обновлялось
    
    Returns:
        Объект UserKnowledge или None
    """
    try:
        # Проверяем, нужно ли обновлять (обновляем не чаще раза в час, если не force_update)
        knowledge = UserKnowledge.query.filter_by(user_id=user_id).first()
        
        if knowledge and not force_update:
            # Проверяем, когда последний раз обновлялось
            time_since_update = datetime.utcnow() - knowledge.last_updated
            if time_since_update < timedelta(hours=1):
                # Недавно обновлялось, возвращаем существующее
                return knowledge
        
        # Получаем активность пользователя за последние 90 дней
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.created_date >= cutoff_date
        ).order_by(UserActivity.created_date.desc()).all()
        
        if not activities and not knowledge:
            # Нет активности и нет знаний - создаем пустой профиль
            knowledge = UserKnowledge(
                user_id=user_id,
                top_categories=[],
                top_hashtags=[],
                top_topics=[],
                search_keywords=[],
                viewed_problems=0,
                viewed_solutions=0,
                favorite_problems=0,
                favorite_solutions=0
            )
            db.session.add(knowledge)
            db.session.commit()
            return knowledge
        
        # Анализируем активность
        categories_counter = Counter()
        hashtags_counter = Counter()
        topics_counter = Counter()
        search_keywords_counter = Counter()
        viewed_problems_count = 0
        viewed_solutions_count = 0
        favorite_problems_count = 0
        favorite_solutions_count = 0
        
        # Обрабатываем каждую активность
        for activity in activities:
            if activity.activity_type == 'view':
                if activity.entity_type == 'problem':
                    viewed_problems_count += 1
                    # Получаем категорию, хэштеги и топик проблемы
                    problem = Problem.query.get(activity.entity_id)
                    if problem:
                        if problem.category:
                            categories_counter[problem.category] += 1
                        if problem.topic:
                            topics_counter[problem.topic] += 1
                        if hasattr(problem, 'hashtags') and problem.hashtags:
                            for hashtag in problem.hashtags:
                                hashtags_counter[hashtag.id] += 1
                elif activity.entity_type == 'solution':
                    viewed_solutions_count += 1
                    # Получаем категорию, хэштеги и топик решения через связанные проблемы
                    solution = Solution.query.get(activity.entity_id)
                    if solution:
                        # Solution связан с Problem через solution_problems
                        # Получаем категории и топики из связанных проблем
                        if hasattr(solution, 'problems') and solution.problems:
                            for problem in solution.problems:
                                if problem.category:
                                    categories_counter[problem.category] += 1
                                if problem.topic:
                                    topics_counter[problem.topic] += 1
                                if hasattr(problem, 'hashtags') and problem.hashtags:
                                    for hashtag in problem.hashtags:
                                        hashtags_counter[hashtag.id] += 1
                        # Также проверяем хэштеги решения напрямую (если они есть)
                        if hasattr(solution, 'hashtags') and solution.hashtags:
                            for hashtag in solution.hashtags:
                                hashtags_counter[hashtag.id] += 1
            
            elif activity.activity_type == 'favorite':
                if activity.entity_type == 'problem':
                    favorite_problems_count += 1
                elif activity.entity_type == 'solution':
                    favorite_solutions_count += 1
            
            elif activity.activity_type == 'search' and activity.search_query:
                # Анализируем поисковые запросы
                query = activity.search_query.strip().lower()
                if query:
                    # Разбиваем запрос на ключевые слова (простая токенизация)
                    keywords = query.split()
                    for keyword in keywords:
                        if len(keyword) > 2:  # Игнорируем слишком короткие слова
                            search_keywords_counter[keyword] += 1
        
        # Получаем топ категорий
        top_categories = []
        for category_id, count in categories_counter.most_common(10):
            category = Category.query.get(category_id)
            if category:
                top_categories.append({
                    'category_id': category_id,
                    'count': count,
                    'name': category.name if hasattr(category, 'name') else f'Category {category_id}'
                })
        
        # Получаем топ хэштегов
        top_hashtags = []
        for hashtag_id, count in hashtags_counter.most_common(15):
            hashtag = Hashtag.query.get(hashtag_id)
            if hashtag:
                top_hashtags.append({
                    'hashtag_id': hashtag_id,
                    'count': count,
                    'name': hashtag.name if hasattr(hashtag, 'name') else f'Hashtag {hashtag_id}'
                })
        
        # Получаем топ топиков
        top_topics = []
        for topic_id, count in topics_counter.most_common(10):
            topic = Topic.query.get(topic_id)
            if topic:
                top_topics.append({
                    'topic_id': topic_id,
                    'count': count,
                    'name': topic.name if hasattr(topic, 'name') else f'Topic {topic_id}'
                })
        
        # Получаем топ поисковых ключевых слов
        top_keywords = []
        for keyword, count in search_keywords_counter.most_common(20):
            top_keywords.append({
                'keyword': keyword,
                'count': count
            })
        
        # Создаем или обновляем знания
        if knowledge:
            knowledge.top_categories = top_categories
            knowledge.top_hashtags = top_hashtags
            knowledge.top_topics = top_topics
            knowledge.search_keywords = top_keywords
            knowledge.viewed_problems = viewed_problems_count
            knowledge.viewed_solutions = viewed_solutions_count
            knowledge.favorite_problems = favorite_problems_count
            knowledge.favorite_solutions = favorite_solutions_count
            knowledge.last_updated = datetime.utcnow()
        else:
            knowledge = UserKnowledge(
                user_id=user_id,
                top_categories=top_categories,
                top_hashtags=top_hashtags,
                top_topics=top_topics,
                search_keywords=top_keywords,
                viewed_problems=viewed_problems_count,
                viewed_solutions=viewed_solutions_count,
                favorite_problems=favorite_problems_count,
                favorite_solutions=favorite_solutions_count
            )
            db.session.add(knowledge)
        
        db.session.commit()
        return knowledge
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ошибка обновления персональных знаний для пользователя {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_user_knowledge(user_id: int, auto_update: bool = True) -> Optional[Dict[str, Any]]:
    """
    Получить персональные знания пользователя
    
    Args:
        user_id: ID пользователя
        auto_update: Автоматически обновить знания, если их нет или они устарели
    
    Returns:
        Словарь с персональными знаниями или None
    """
    try:
        knowledge = UserKnowledge.query.filter_by(user_id=user_id).first()
        
        if not knowledge:
            if auto_update:
                # Пытаемся создать знания на основе активности
                knowledge = update_user_knowledge(user_id, force_update=True)
            else:
                return None
        
        if knowledge:
            return knowledge.to_dict()
        
        return None
    
    except Exception as e:
        current_app.logger.error(f"Ошибка получения персональных знаний для пользователя {user_id}: {e}")
        return None


def get_user_interests_summary(user_id: int) -> Dict[str, Any]:
    """
    Получить краткую сводку интересов пользователя
    
    Args:
        user_id: ID пользователя
    
    Returns:
        Словарь с краткой сводкой интересов
    """
    try:
        knowledge = get_user_knowledge(user_id, auto_update=True)
        
        if not knowledge:
            return {
                'has_interests': False,
                'message': 'Недостаточно данных для анализа интересов'
            }
        
        # Формируем сводку
        top_categories = knowledge.get('top_categories', [])[:5]
        top_hashtags = knowledge.get('top_hashtags', [])[:10]
        top_topics = knowledge.get('top_topics', [])[:5]
        top_keywords = knowledge.get('search_keywords', [])[:10]
        
        has_interests = bool(top_categories or top_hashtags or top_topics or top_keywords)
        
        return {
            'has_interests': has_interests,
            'top_categories': top_categories,
            'top_hashtags': top_hashtags,
            'top_topics': top_topics,
            'top_keywords': top_keywords,
            'statistics': {
                'viewed_problems': knowledge.get('viewed_problems', 0),
                'viewed_solutions': knowledge.get('viewed_solutions', 0),
                'favorite_problems': knowledge.get('favorite_problems', 0),
                'favorite_solutions': knowledge.get('favorite_solutions', 0)
            }
        }
    
    except Exception as e:
        current_app.logger.error(f"Ошибка получения сводки интересов для пользователя {user_id}: {e}")
        return {
            'has_interests': False,
            'error': 'Ошибка получения данных'
        }


def trigger_knowledge_update(user_id: int):
    """
    Запустить обновление знаний в фоне (для асинхронной обработки)
    В текущей реализации просто вызывает синхронное обновление
    
    Args:
        user_id: ID пользователя
    """
    try:
        # В будущем здесь можно добавить очередь задач (Celery, RQ и т.д.)
        update_user_knowledge(user_id, force_update=False)
    except Exception as e:
        current_app.logger.error(f"Ошибка триггера обновления знаний для пользователя {user_id}: {e}")
