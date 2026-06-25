#!/usr/bin/env python3
"""Экспорт данных из MySQL в JSON для GitHub Pages (статический режим)."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv

load_dotenv()

OUTPUT = ROOT / 'data'
ASSETS_BASE = 'assets/images/Screenshot_4-ww78noDj9-transformed.png'
DEFAULT_IMAGE = f'/{ASSETS_BASE}'


def _is_yandex(url: str) -> bool:
    return bool(url) and url.startswith('http') and 'storage.yandexcloud.net' in url


def normalize_image(raw, static_base_url: str) -> str:
    if not raw or not str(raw).strip():
        return f'{static_base_url}{DEFAULT_IMAGE}'
    url = str(raw).strip().replace('\\', '/')
    if _is_yandex(url):
        return url
    if url.startswith('http'):
        return url
    if url.startswith('../images/'):
        return f'{static_base_url}/assets/images/{url.split("/")[-1]}'
    if url.startswith('../assets/'):
        return f'{static_base_url}/assets/{url[11:]}'
    if url.startswith('/'):
        return f'{static_base_url}{url}'
    if url.startswith('uploads/'):
        return f'{static_base_url}/{url}'
    return f'{static_base_url}/{url.lstrip("/")}'


def export():
    from app import create_app
    from logic.model import db, Problem, Solution, Category, Topic, Hashtag
    from sqlalchemy.orm import joinedload

    app = create_app()
    static_base = os.getenv('STATIC_BASE_URL', '').rstrip('/') or 'https://abudkina.github.io/VseProstPublic'

    with app.app_context():
        OUTPUT.mkdir(parents=True, exist_ok=True)

        categories = [
            {'ID': c.id, 'Name': c.name}
            for c in Category.query.order_by(Category.name).all()
        ]

        topics = [
            {'ID': t.id, 'Name': t.name}
            for t in Topic.query.order_by(Topic.name).all()
        ]

        hashtags = [
            {'ID': h.id, 'Name': h.name}
            for h in Hashtag.query.order_by(Hashtag.name).all()
        ]

        topics_map = {t['ID']: t for t in topics}

        problems = Problem.query.options(
            joinedload(Problem.hashtags),
            joinedload(Problem.solutions),
            joinedload(Problem.linked_problems),
        ).order_by(Problem.id).all()

        problems_list = []
        problems_detail = {}

        for p in problems:
            item = {
                'ID': p.id,
                'Name': p.name,
                'Describe': p.describe or '',
                'Image': normalize_image(p.image, static_base),
                'Favourite': p.favourite or 0,
                'IsFavourite': False,
                'Show': p.show or 0,
                'Reply': p.reply or 0,
                'Confirmations': len(p.solutions) if p.solutions else 0,
                'Shares': p.reply or 0,
                'Category': p.category,
                'Topic': p.topic,
                'TopicInfo': topics_map.get(p.topic),
                'Hashtags': [{'ID': h.id, 'Name': h.name} for h in (p.hashtags or [])],
                'Solutions': [{
                    'ID': s.id,
                    'Name': s.name,
                    'Describe': ((s.describe[:100] + '...') if s.describe and len(s.describe) > 100 else (s.describe or '')),
                    'Image': normalize_image(s.image, static_base),
                } for s in (p.solutions or [])],
                'LinkedProblems': [{
                    'ID': lp.id,
                    'Name': lp.name,
                    'Image': normalize_image(lp.image, static_base),
                    'TopicInfo': topics_map.get(lp.topic),
                } for lp in (p.linked_problems or [])],
            }
            problems_list.append(item)

            detail = dict(item)
            detail['Solutions'] = []
            for s in (p.solutions or []):
                sol = Solution.query.options(
                    joinedload(Solution.comments),
                    joinedload(Solution.problems).joinedload(Problem.hashtags),
                    joinedload(Solution.linked_solutions),
                ).get(s.id)
                if not sol:
                    continue
                sd = {
                    'ID': sol.id,
                    'Name': sol.name,
                    'Describe': sol.describe or '',
                    'Image': normalize_image(sol.image, static_base),
                    'Favourite': sol.favourite or 0,
                    'Rating': sol.rating or 0,
                    'Show': sol.show or 0,
                    'Reply': sol.reply or 0,
                    'Price': float(sol.price) if sol.price else 0,
                    'Efficiency': sol.efficiency or 0,
                    'Complexity': sol.complexity or 0,
                    'Time': sol.time or 0,
                    'IsBought': bool(getattr(sol, 'isbought', False)),
                    'IsRating': bool(getattr(sol, 'israting', False)),
                    'Comments': [{
                        'ID': c.id,
                        'Text': c.text,
                        'CreatedDate': c.created_date.isoformat() if c.created_date else '',
                        'Creator': c.creator,
                        'LikeCount': c.likecount or 0,
                        'NotLikeCount': c.notlikecount or 0,
                    } for c in (sol.comments or [])],
                    'Problems': [{
                        'ID': pr.id,
                        'Name': pr.name,
                        'Image': normalize_image(pr.image, static_base),
                        'Hashtags': [{'ID': h.id, 'Name': h.name} for h in (pr.hashtags or [])],
                        'TopicInfo': topics_map.get(pr.topic),
                    } for pr in (sol.problems or [])],
                }
                detail['Solutions'].append(sd)
            problems_detail[str(p.id)] = {'problem': detail}

        solutions = Solution.query.options(
            joinedload(Solution.problems),
        ).order_by(Solution.id).all()

        solutions_list = []
        solutions_detail = {}

        for s in solutions:
            item = {
                'ID': s.id,
                'Name': s.name,
                'Describe': s.describe or '',
                'Image': normalize_image(s.image, static_base),
                'Favourite': s.favourite or 0,
                'IsFavourite': False,
                'Show': s.show or 0,
                'Reply': s.reply or 0,
                'Rating': s.rating or 0,
                'Price': float(s.price) if s.price else 0,
                'Efficiency': s.efficiency or 0,
                'Complexity': s.complexity or 0,
                'Time': s.time or 0,
                'Problems': [{'ID': p.id, 'Name': p.name} for p in (s.problems or [])],
                'Hashtags': [],
            }
            solutions_list.append(item)

            full = Solution.query.options(
                joinedload(Solution.comments),
                joinedload(Solution.problems),
                joinedload(Solution.linked_solutions),
            ).get(s.id)
            sd = {
                'ID': full.id,
                'Name': full.name,
                'Describe': full.describe or '',
                'Image': normalize_image(full.image, static_base),
                'Show': full.show or 0,
                'Favourite': full.favourite or 0,
                'IsFavourite': False,
                'Reply': full.reply or 0,
                'Price': float(full.price) if full.price else 0,
                'Efficiency': full.efficiency or 0,
                'Complexity': full.complexity or 0,
                'Time': full.time or 0,
                'Rating': full.rating or 0,
                'IsBought': bool(getattr(full, 'isbought', False)),
                'IsRating': bool(getattr(full, 'israting', False)),
                'IsNew': bool(getattr(full, 'isnew', True)),
                'Problems': [{'ID': p.id, 'Name': p.name} for p in (full.problems or [])],
                'Comments': [{
                    'ID': c.id,
                    'Text': c.text,
                    'CreatedDate': c.created_date.isoformat() if c.created_date else '',
                    'Creator': {'User': getattr(getattr(c, 'creator_user', None), 'username', None) or 'Аноним'},
                    'LikeCount': c.likecount or 0,
                    'NotLikeCount': c.notlikecount or 0,
                } for c in (full.comments or [])],
                'LinkedSolutions': [{
                    'ID': ls.id,
                    'Name': ls.name,
                    'Image': normalize_image(ls.image, static_base),
                    'Rating': ls.rating or 0,
                } for ls in (full.linked_solutions or [])],
            }
            solutions_detail[str(s.id)] = {'solution': sd}

        payload = {
            'categories': categories,
            'topics': topics,
            'hashtags': hashtags,
            'problems': problems_list,
            'problems_detail': problems_detail,
            'solutions': solutions_list,
            'solutions_detail': solutions_detail,
            'meta': {
                'static_base_url': static_base,
                'exported_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            },
        }

        out = OUTPUT / 'site.json'
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Exported {len(problems_list)} problems, {len(solutions_list)} solutions -> {out}')


if __name__ == '__main__':
    export()
