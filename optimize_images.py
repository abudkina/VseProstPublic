#!/usr/bin/env python
"""
Image Optimization Script
Сжимает и оптимизирует все изображения в проекте

Usage:
    python optimize_images.py
"""

import os
from pathlib import Path
from PIL import Image
import sys

# Расширения изображений для обработки
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

# Параметры оптимизации
OPTIMIZATION_SETTINGS = {
    'quality': 85,              # JPEG качество (0-95)
    'optimize': True,           # Использовать PIL оптимизацию
    'max_width': 2000,          # Максимальная ширина
    'max_height': 2000,         # Максимальная высота
}

class ImageOptimizer:
    """Класс для оптимизации изображений"""
    
    def __init__(self, source_dir='assets/images'):
        self.source_dir = Path(source_dir)
        self.stats = {
            'total_files': 0,
            'optimized_files': 0,
            'original_size': 0,
            'optimized_size': 0,
            'errors': []
        }
    
    def get_file_size(self, filepath):
        """Получить размер файла в КБ"""
        return os.path.getsize(filepath) / 1024
    
    def optimize_image(self, image_path):
        """Оптимизировать одно изображение"""
        try:
            original_size = self.get_file_size(image_path)
            
            # Открываем изображение
            img = Image.open(image_path)
            
            # Конвертируем RGBA в RGB если необходимо
            if img.mode in ('RGBA', 'LA', 'P'):
                # Создаем белый фон
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Уменьшаем размер если превышен
            if img.width > OPTIMIZATION_SETTINGS['max_width'] or \
               img.height > OPTIMIZATION_SETTINGS['max_height']:
                img.thumbnail(
                    (OPTIMIZATION_SETTINGS['max_width'], 
                     OPTIMIZATION_SETTINGS['max_height']),
                    Image.Resampling.LANCZOS
                )
            
            # Сохраняем оптимизированное изображение
            if image_path.suffix.lower() == '.png':
                img.save(image_path, 'PNG', optimize=True)
            else:
                img.save(
                    image_path,
                    'JPEG',
                    quality=OPTIMIZATION_SETTINGS['quality'],
                    optimize=True
                )
            
            optimized_size = self.get_file_size(image_path)
            compression_ratio = ((original_size - optimized_size) / original_size) * 100
            
            return {
                'success': True,
                'original_size': original_size,
                'optimized_size': optimized_size,
                'compression_ratio': compression_ratio
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_directory(self):
        """Оптимизировать все изображения в директории"""
        
        if not self.source_dir.exists():
            print(f"❌ Директория {self.source_dir} не найдена!")
            return
        
        print(f"🖼️  Оптимизация изображений в {self.source_dir}...")
        print("-" * 60)
        
        image_files = [
            f for f in self.source_dir.glob('**/*')
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        if not image_files:
            print("ℹ️  Изображения не найдены!")
            return
        
        self.stats['total_files'] = len(image_files)
        
        for image_path in image_files:
            result = self.optimize_image(image_path)
            
            if result['success']:
                self.stats['optimized_files'] += 1
                self.stats['original_size'] += result['original_size']
                self.stats['optimized_size'] += result['optimized_size']
                
                print(
                    f"✅ {image_path.name:<40} "
                    f"{result['original_size']:.1f}KB → {result['optimized_size']:.1f}KB "
                    f"({result['compression_ratio']:.1f}%)"
                )
            else:
                self.stats['errors'].append((image_path.name, result['error']))
                print(f"❌ {image_path.name:<40} Ошибка: {result['error']}")
        
        self._print_summary()
    
    def _print_summary(self):
        """Вывести итоговый отчет"""
        print("-" * 60)
        print("\n📊 ИТОГОВЫЙ ОТЧЕТ:")
        print(f"  📁 Всего файлов: {self.stats['total_files']}")
        print(f"  ✅ Оптимизировано: {self.stats['optimized_files']}")
        print(f"  ❌ Ошибок: {len(self.stats['errors'])}")
        
        if self.stats['original_size'] > 0:
            total_ratio = (
                (self.stats['original_size'] - self.stats['optimized_size']) /
                self.stats['original_size']
            ) * 100
            
            print(f"\n  💾 Исходный размер: {self.stats['original_size']:.1f}MB")
            print(f"  📦 Оптимизированный: {self.stats['optimized_size']:.1f}MB")
            print(f"  🎯 Сжатие: {total_ratio:.1f}%")
            print(f"  ⬇️  Сэкономлено: {self.stats['original_size'] - self.stats['optimized_size']:.1f}MB")
        
        if self.stats['errors']:
            print(f"\n❌ Ошибки при обработке:")
            for filename, error in self.stats['errors']:
                print(f"  - {filename}: {error}")
        
        print("\n✅ Оптимизация завершена!")


def main():
    """Главная функция"""
    
    # Проверяем наличие PIL
    try:
        from PIL import Image
    except ImportError:
        print("❌ Pillow не установлен!")
        print("Установите с помощью: pip install Pillow")
        sys.exit(1)
    
    # Получаем путь директории с изображениями
    images_dir = 'assets/images'
    if len(sys.argv) > 1:
        images_dir = sys.argv[1]
    
    # Запускаем оптимизацию
    optimizer = ImageOptimizer(images_dir)
    optimizer.optimize_directory()


if __name__ == '__main__':
    main()
