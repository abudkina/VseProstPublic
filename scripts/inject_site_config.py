#!/usr/bin/env python3
"""Добавляет site-config.js в <head> всех HTML-страниц."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = '    <script src="/js/site-config.js"></script>\n    <script src="/js/static-api.js"></script>\n    <script src="/js/paths.js"></script>\n'
MARKER = '/js/static-api.js'


def inject(content: str) -> str:
    if MARKER in content:
        return content
    return re.sub(r'(<head[^>]*>\s*)', r'\1' + SNIPPET, content, count=1)


def main():
    for path in (ROOT / 'html').glob('*.html'):
        text = path.read_text(encoding='utf-8')
        updated = inject(text)
        if updated != text:
            path.write_text(updated, encoding='utf-8')
            print('updated', path.name)

    src = (ROOT / 'html' / 'index.html').read_text(encoding='utf-8')
    (ROOT / 'index.html').write_text(inject(src), encoding='utf-8')
    print('created index.html')


if __name__ == '__main__':
    main()
