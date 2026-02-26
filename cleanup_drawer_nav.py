#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаления блока drawer-nav из всех HTML файлов проекта VseProst
"""

import os
import re
from pathlib import Path

# Путь к директории с HTML файлами
HTML_DIR = Path(__file__).parent / "html"

def remove_drawer_nav(content):
    """Удаляет блок drawer-nav из HTML контента"""
    # Паттерн для поиска блока drawer-nav
    # Ищем от <nav class="drawer-nav"> до </nav> и следующий </div> если есть
    pattern = r'<nav class="drawer-nav">.*?</nav>\s*(?:</div>)?'

    # Удаляем блок
    content = re.sub(pattern, '', content, flags=re.DOTALL)

    return content

def process_html_file(file_path):
    """Обрабатывает один HTML файл"""
    print(f"Processing: {file_path.name}")

    try:
        # Читаем файл
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Сохраняем оригинал для сравнения
        original_content = content

        # Проверяем наличие drawer-nav
        if 'drawer-nav' not in content:
            print(f"  [-] No drawer-nav found: {file_path.name}")
            return False

        # Удаляем drawer-nav
        content = remove_drawer_nav(content)

        # Записываем обратно только если были изменения
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [+] Updated: {file_path.name}")
            return True
        else:
            print(f"  [-] No changes: {file_path.name}")
            return False

    except Exception as e:
        print(f"  [!] Error processing {file_path.name}: {e}")
        return False

def main():
    """Главная функция"""
    print("=" * 60)
    print("Cleaning up drawer-nav from HTML files")
    print("=" * 60)

    if not HTML_DIR.exists():
        print(f"Error: Directory {HTML_DIR} not found!")
        return

    # Получаем все HTML файлы
    html_files = list(HTML_DIR.glob("*.html"))

    print(f"\nFound files to process: {len(html_files)}")
    print()

    # Обрабатываем каждый файл
    updated_count = 0
    for html_file in sorted(html_files):
        if process_html_file(html_file):
            updated_count += 1

    print()
    print("=" * 60)
    print(f"Processing complete!")
    print(f"Total files: {len(html_files)}")
    print(f"Updated: {updated_count}")
    print(f"No changes: {len(html_files) - updated_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
