#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления всех HTML файлов проекта VseProst
Подключает mobile-menu.css и mobile-menu.js для улучшения мобильного меню
"""

import os
import re
from pathlib import Path

# Путь к директории с HTML файлами
HTML_DIR = Path(__file__).parent / "html"

def add_mobile_menu_css(content):
    """Добавляет ссылку на mobile-menu.css, если её ещё нет"""
    if '/css/mobile-menu.css' in content:
        return content  # Уже добавлена

    # Ищем строку с header.css и добавляем после неё
    pattern = r'(<link\s+rel="stylesheet"\s+href="/css/header\.css"\s*/?>)'
    replacement = r'\1\n    <link rel="stylesheet" href="/css/mobile-menu.css" />'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
    else:
        # Если header.css не найден, добавляем перед font-awesome
        pattern = r'(<link\s+rel="stylesheet"\s+href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome)'
        replacement = r'    <link rel="stylesheet" href="/css/mobile-menu.css" />\n    \1'
        content = re.sub(pattern, replacement, content)

    return content

def add_mobile_menu_js(content):
    """Добавляет скрипт mobile-menu.js перед закрывающим </body>, если его ещё нет"""
    if '/js/mobile-menu.js' in content:
        return content  # Уже добавлен

    # Ищем </body> и добавляем перед ним
    pattern = r'(</body>)'
    replacement = '<script src="/js/mobile-menu.js"></script>\n\\1'

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)

    return content

def remove_hamburger_and_drawer(content):
    """Удаляет гамбургер-кнопку, drawer и overlay, если они были добавлены ранее"""
    # Удаляем гамбургер-кнопку
    content = re.sub(
        r'<!-- Гамбургер-кнопка.*?</button>\s*',
        '',
        content,
        flags=re.DOTALL
    )

    # Удаляем mobile drawer
    content = re.sub(
        r'<!-- Выдвижное мобильное меню -->.*?</div>\s*',
        '',
        content,
        flags=re.DOTALL
    )

    # Удаляем overlay
    content = re.sub(
        r'<!-- Оверлей для затемнения фона -->.*?</div>\s*',
        '',
        content,
        flags=re.DOTALL
    )

    return content

def ensure_mobile_menu_exists(content):
    """Проверяет наличие mobile-menu в header, если нет - добавляет"""
    # Проверяем, есть ли mobile-menu
    if 'class="nav-menu mobile-menu"' in content or 'class="mobile-menu' in content:
        return content  # Уже есть

    # Ищем desktop-menu и дублируем его как mobile-menu
    desktop_menu_pattern = r'(<ul\s+class="nav-menu desktop-menu">.*?</ul>)'
    match = re.search(desktop_menu_pattern, content, re.DOTALL)

    if match:
        desktop_menu = match.group(0)
        # Создаём mobile-menu на основе desktop-menu
        mobile_menu = desktop_menu.replace('desktop-menu', 'mobile-menu')

        # Вставляем mobile-menu после desktop-menu
        pattern = r'(</ul>\s*)(</header>)'
        replacement = f'\\1\n    {mobile_menu}\n\\2'
        content = re.sub(pattern, replacement, content)

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

        # Применяем все трансформации
        content = remove_hamburger_and_drawer(content)  # Сначала удаляем старое
        content = add_mobile_menu_css(content)
        content = add_mobile_menu_js(content)
        content = ensure_mobile_menu_exists(content)

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
    print("Updating HTML files for mobile menu (top navigation)")
    print("=" * 60)

    if not HTML_DIR.exists():
        print(f"Error: Directory {HTML_DIR} not found!")
        return

    # Получаем все HTML файлы, кроме index.html (обновим его вручную)
    html_files = list(HTML_DIR.glob("*.html"))
    # Включаем index.html тоже
    # html_files = [f for f in html_files if f.name != 'index.html']

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
