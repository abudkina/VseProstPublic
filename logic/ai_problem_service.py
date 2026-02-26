# ai_problem_service.py — создание проблемы и 10 решений по запросу пользователя (DeepSeek + изображение)
import json
import re
import logging
from typing import Optional, List, Dict, Any

from openai import OpenAI
from logic.model import (
    db, Problem, Solution, Topic, Category, Hashtag,
    SolutionRating, solution_problems, hashtag_problem, hashtag_solution,
)
from logic.utils.image_search import generate_image_with_openai
from logic.utils.normalizers import (
    normalize_category_name,
    normalize_category_display_name,
    normalize_topic_name,
    normalize_hashtag_name,
    capitalize_title,
    capitalize_first,
)
from logic.recommendations import create_embedding

logger = logging.getLogger(__name__)

DEEPSEEK_MODEL = "deepseek/deepseek-chat-v3.1"
SOLUTIONS_COUNT = 10
RATING_TYPES = ["price", "efficiency", "complexity", "time"]


def _deepseek_client():
    from config import Config
    key = getattr(Config, "OPENAI_API_KEY", None)
    base = getattr(Config, "OPENAI_API_URL2", None)
    if not key or not base:
        raise ValueError("OPENAI_API_KEY и OPENAI_API_URL2 должны быть заданы")
    return OpenAI(api_key=key, base_url=base)


def _chat_json(system: str, user: str, model: str = DEEPSEEK_MODEL) -> Optional[Dict]:
    client = _deepseek_client()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
        )
        text = (r.choices[0].message.content or "").strip()
        # Вырезаем возможный markdown code block
        if "```json" in text:
            text = re.sub(r"^.*?```json\s*", "", text)
        if "```" in text:
            text = text.split("```")[0]
        return json.loads(text)
    except Exception as e:
        logger.exception(f"DeepSeek chat error: {e}")
        return None


def _get_catalog_for_prompt(user_id: int) -> Dict[str, List[Dict]]:
    topics = Topic.query.filter(Topic.creator == user_id).order_by(Topic.name).limit(100).all()
    categories = Category.query.filter(Category.creator == user_id).order_by(Category.name).limit(100).all()
    hashtags = Hashtag.query.filter(Hashtag.creator == user_id).order_by(Hashtag.name).limit(200).all()
    problems = Problem.query.filter(Problem.creator == user_id).order_by(Problem.created_date.desc()).limit(50).all()
    return {
        "topics": [{"id": t.id, "name": t.name} for t in topics],
        "categories": [{"id": c.id, "name": c.name} for c in categories],
        "hashtags": [{"id": h.id, "name": h.name} for h in hashtags],
        "problems": [{"id": p.id, "name": p.name} for p in problems],
    }


def _resolve_topic(name: str, user_id: int, create: bool) -> Optional[int]:
    if not name or not name.strip():
        return None
    stripped = name.strip()
    t = Topic.query.filter(Topic.creator == user_id, Topic.name.ilike(stripped)).first()
    if t:
        return t.id
    if not create:
        return None
    topic = Topic(name=normalize_topic_name(stripped), creator=user_id, is_new=True)
    db.session.add(topic)
    db.session.flush()
    return topic.id


def _resolve_category(name: str, user_id: int, create: bool) -> Optional[int]:
    if not name or not name.strip():
        return None
    norm = normalize_category_name(name.strip())
    for c in Category.query.filter(Category.creator == user_id).all():
        if normalize_category_name(c.name) == norm:
            return c.id
    if not create:
        return None
    cat = Category(name=normalize_category_display_name(name.strip()), creator=user_id, isnew=True)
    db.session.add(cat)
    db.session.flush()
    return cat.id


def _resolve_hashtags(names: List[str], user_id: int, create: bool) -> List[int]:
    ids = []
    for name in (names or [])[:20]:
        if not name or not str(name).strip():
            continue
        raw = str(name).strip()
        norm_tag = normalize_hashtag_name(raw)
        h = Hashtag.query.filter(Hashtag.creator == user_id, Hashtag.name.ilike(norm_tag)).first()
        if h:
            ids.append(h.id)
        elif create:
            tag = Hashtag(name=norm_tag, creator=user_id, isnew=True, show=0)
            db.session.add(tag)
            db.session.flush()
            ids.append(tag.id)
    return ids


def generate_problem_from_query(user_id: int, query: str) -> Optional[Dict]:
    """По запросу пользователя возвращает JSON: topic_name, problem_name, problem_describe, category_name, hashtag_names (массив)."""
    catalog = _get_catalog_for_prompt(user_id)
    system = """Ты помощник. По запросу пользователя сформируй структуру проблемы в JSON.
Ответь ТОЛЬКО одним валидным JSON-объектом без markdown и пояснений, с ключами:
- topic_name: строка, подходящая тема (можно взять из списка или предложить новую).
- problem_name: краткое название проблемы (одна строка).
- problem_describe: описание 2-3 предложения.
- category_name: подходящая категория (из списка или новая).
- hashtag_names: массив из не менее 5 строк — хэштеги (из списка или новые).
Используй существующие темы/категории/хэштеги из каталога где уместно."""
    user_text = f"Каталог пользователя:\nТемы: {catalog['topics']}\nКатегории: {catalog['categories']}\nХэштеги: {catalog['hashtags']}\n\nЗапрос пользователя: {query}"
    data = _chat_json(system, user_text)
    if not data:
        return None
    return {
        "topic_name": data.get("topic_name") or "",
        "problem_name": data.get("problem_name") or "",
        "problem_describe": data.get("problem_describe") or "",
        "category_name": data.get("category_name") or "",
        "hashtag_names": data.get("hashtag_names") if isinstance(data.get("hashtag_names"), list) else [],
    }


def generate_solutions_for_problem(
    user_id: int,
    problem_name: str,
    problem_describe: str,
    existing_problem_ids: List[int],
    extra_problems: Optional[List[Dict]] = None,
) -> List[Dict]:
    """Генерирует 10 решений в виде списка словарей с полями для БД и рейтингов."""
    catalog = _get_catalog_for_prompt(user_id)
    problems_info = [p for p in catalog["problems"] if p["id"] in existing_problem_ids]
    if extra_problems:
        problems_info = list(extra_problems) + problems_info
    if not problems_info:
        problems_info = catalog["problems"][:20]
    system = """Ты помощник. Для заданной проблемы сгенерируй ровно 10 решений.
Ответь ТОЛЬКО одним JSON-объектом с ключом "solutions" — массив из 10 элементов.
Каждый элемент — объект с ключами:
- name: краткое название решения.
- describe: описание 2-3 предложения.
- linked_problem_ids: массив id проблем из списка существующих (0-3 id), релевантных этому решению (если список пуст — пустой массив).
- isbought: true если решение можно купить (товар/услуга), иначе false.
- israting: true если решение можно оценить по категориям цена/эффективность/сложность/время.
- price, efficiency, complexity, time: числа 1-5 (оценки), только если israting true, иначе можно не указывать.
Список существующих проблем для linked_problem_ids: """ + json.dumps(problems_info)
    user_text = f"Проблема: {problem_name}\nОписание: {problem_describe}"
    data = _chat_json(system, user_text)
    if not data or not isinstance(data.get("solutions"), list):
        return []
    out = []
    for i, s in enumerate(data["solutions"][:SOLUTIONS_COUNT]):
        if not isinstance(s, dict):
            continue
        linked = s.get("linked_problem_ids") or []
        if not isinstance(linked, list):
            linked = []
        linked = [int(x) for x in linked if isinstance(x, (int, float)) and x in existing_problem_ids]
        out.append({
            "name": str(s.get("name") or f"Решение {i+1}").strip()[:500],
            "describe": str(s.get("describe") or "").strip()[:2000],
            "linked_problem_ids": linked,
            "isbought": bool(s.get("isbought")),
            "israting": bool(s.get("israting")),
            "price": max(1, min(5, int(s.get("price") or 3))),
            "efficiency": max(1, min(5, int(s.get("efficiency") or 3))),
            "complexity": max(1, min(5, int(s.get("complexity") or 3))),
            "time": max(1, min(5, int(s.get("time") or 3))),
        })
    return out


def create_problem_with_solutions_from_query(user_id: int, query: str) -> Dict[str, Any]:
    """
    Создаёт проблему и 10 решений по запросу пользователя.
    Возвращает {"problem": {...}, "solutions": [...]} или {"error": "..."}.
    """
    if not query or not str(query).strip():
        return {"error": "Пустой запрос"}
    query = str(query).strip()[:2000]

    # 1) Генерация структуры проблемы
    problem_spec = generate_problem_from_query(user_id, query)
    if not problem_spec or not problem_spec.get("problem_name"):
        return {"error": "Не удалось сформировать проблему по запросу"}

    topic_id = _resolve_topic(problem_spec.get("topic_name") or "", user_id, create=True)
    category_id = _resolve_category(problem_spec.get("category_name") or "", user_id, create=True)
    if not category_id:
        return {"error": "Не удалось определить категорию"}
    hashtag_ids = _resolve_hashtags(problem_spec.get("hashtag_names") or [], user_id, create=True)
    if len(hashtag_ids) < 5:
        more = ["общее", "помощь", "совет", "решение", "вопрос"]
        for name in more:
            if len(hashtag_ids) >= 5:
                break
            add = _resolve_hashtags([name], user_id, create=True)
            for id in add:
                if id not in hashtag_ids:
                    hashtag_ids.append(id)

    # 2) Изображение проблемы (gpt-image-1, low, 1024x1024)
    image_url = generate_image_with_openai(
        problem_spec["problem_name"],
        problem_spec.get("problem_describe"),
        model="gpt-image-1",
        size="1024x1024",
        response_format="b64_json",
    )
    if not image_url:
        image_url = generate_image_with_openai(problem_spec["problem_name"], problem_spec.get("problem_describe"))

    problem = Problem(
        name=capitalize_title(problem_spec["problem_name"]),
        describe=capitalize_first(problem_spec.get("problem_describe") or ""),
        category=category_id,
        topic=topic_id,
        image=image_url or "../images/default.png",
        creator=user_id,
        isnew=True,
        show=1,
        favourite=0,
        fromauthor=False,
        reply=0,
    )
    db.session.add(problem)
    db.session.flush()
    problem_id = problem.id

    for hid in hashtag_ids:
        db.session.execute(hashtag_problem.insert().values(problem_id=problem_id, hashtag_id=hid))
    db.session.flush()

    existing_problem_ids = [p["id"] for p in _get_catalog_for_prompt(user_id)["problems"]]
    if problem_id not in existing_problem_ids:
        existing_problem_ids.insert(0, problem_id)
    extra_problems = [{"id": problem_id, "name": problem_spec["problem_name"]}]

    solutions_specs = generate_solutions_for_problem(
        user_id,
        problem_spec["problem_name"],
        problem_spec.get("problem_describe") or "",
        existing_problem_ids,
        extra_problems=extra_problems,
    )

    created_solutions = []
    for spec in solutions_specs:
        sol_image = generate_image_with_openai(spec["name"], spec["describe"])
        solution = Solution(
            name=capitalize_title(spec["name"]),
            describe=capitalize_first(spec["describe"]),
            image=sol_image or "../images/default.png",
            creator=user_id,
            isnew=True,
            show=1,
            favourite=0,
            fromauthor=False,
            reply=0,
            isbought=spec["isbought"],
            israting=spec["israting"],
            price=None,
            efficiency=spec["efficiency"] if spec["israting"] else None,
            complexity=spec["complexity"] if spec["israting"] else None,
            time=spec["time"] if spec["israting"] else None,
        )
        db.session.add(solution)
        db.session.flush()
        db.session.execute(solution_problems.insert().values(problem_id=problem_id, solution_id=solution.id))
        for pid in spec.get("linked_problem_ids") or []:
            if pid != problem_id:
                try:
                    db.session.execute(solution_problems.insert().values(problem_id=pid, solution_id=solution.id))
                except Exception:
                    pass
        if spec["israting"]:
            for rtype in RATING_TYPES:
                val = spec.get(rtype, 3)
                r = SolutionRating(
                    solution_id=solution.id,
                    user_id=user_id,
                    rating_type=rtype,
                    rating_value=max(1, min(5, val)),
                )
                db.session.add(r)
        created_solutions.append({"id": solution.id, "name": solution.name})

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception(f"AI create problem commit error: {e}")
        return {"error": "Ошибка сохранения в БД"}

    try:
        create_embedding("problem", problem_id)
    except Exception as e:
        logger.warning(f"create_embedding problem {problem_id}: {e}")

    from logic.utils.file_utils import normalize_image_url
    hashtags = Hashtag.query.filter(Hashtag.id.in_(hashtag_ids)).all()
    hashtag_dict = {h.id: h.name for h in hashtags}
    return {
        "problem": {
            "ID": problem.id,
            "Name": problem.name,
            "Describe": problem.describe,
            "Image": normalize_image_url(problem.image) or "../images/default.png",
            "category": problem.category,
            "topic": problem.topic,
            "Hashtags": [{"ID": hid, "Name": hashtag_dict.get(hid, "")} for hid in hashtag_ids],
        },
        "solutions": created_solutions,
    }
