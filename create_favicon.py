#!/usr/bin/env python3
"""
Скрипт для создания favicon.ico из существующего логотипа
"""
import os
from PIL import Image

def create_favicon():
    """Создает favicon.ico из существующего логотипа"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Пути к возможным источникам логотипа
    source_candidates = [
        os.path.join(project_root, 'assets', 'images', 'logo1-Photoroom1.png'),
        os.path.join(project_root, 'assets', 'images', 'logo1-Photoroom.png'),
        os.path.join(project_root, 'assets', 'images', 'Screenshot_4-ww78noDj9-transformed.png'),
        os.path.join(project_root, 'assets', 'images', 'logo1.jpg'),
    ]
    
    # Ищем существующий файл
    source_path = None
    for candidate in source_candidates:
        if os.path.exists(candidate):
            source_path = candidate
            print(f"Найден источник: {candidate}")
            break
    
    if not source_path:
        print("Ошибка: не найден файл логотипа для создания favicon")
        return False
    
    # Путь для сохранения favicon.ico
    favicon_path = os.path.join(project_root, 'favicon.ico')
    
    try:
        img = Image.open(source_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        sizes = [(16, 16), (32, 32), (48, 48)]
        icons = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icons.append(resized)

        icons[0].save(
            favicon_path,
            format='ICO',
            sizes=[(s.width, s.height) for s in icons]
        )

        png48_path = os.path.join(project_root, 'favicon-48x48.png')
        icons[2].save(png48_path, format='PNG')
        print(f"Favicon 48x48 PNG: {png48_path}")

        apple_path = os.path.join(project_root, 'apple-touch-icon.png')
        img_orig = Image.open(source_path)
        if img_orig.mode == 'P':
            img_orig = img_orig.convert('RGBA')
        elif img_orig.mode != 'RGBA':
            img_orig = img_orig.convert('RGBA')
        img_180 = img_orig.resize((180, 180), Image.Resampling.LANCZOS)
        img_180.save(apple_path, format='PNG')
        print(f"Apple Touch Icon: {apple_path}")
        
        print(f"Favicon успешно создан: {favicon_path}")
        return True
        
    except Exception as e:
        print(f"Ошибка при создании favicon: {e}")
        return False

if __name__ == '__main__':
    create_favicon()
