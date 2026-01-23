// Универсальный модуль для управления прокруткой тегов с кнопками-стрелками

// Флаг для отслеживания инициализации глобальных обработчиков
let globalKeyboardHandlersInitialized = false;

// Инициализация глобальных обработчиков клавиатуры (один раз)
function initGlobalKeyboardHandlers() {
  if (globalKeyboardHandlersInitialized) return;
  globalKeyboardHandlersInitialized = true;
  
  // Глобальный обработчик для стрелок при наведении на хэштеги
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      // Проверяем хэштеги
      const hoveredWrapper = document.querySelector('.tags-wrapper[data-hovered="true"]');
      if (hoveredWrapper) {
        const hoveredTagsColumn = hoveredWrapper.querySelector('.tags-column');
        if (hoveredTagsColumn) {
          e.preventDefault();
          const scrollAmount = 150;
          hoveredTagsColumn.scrollBy({
            left: e.key === 'ArrowLeft' ? -scrollAmount : scrollAmount,
            behavior: 'smooth'
          });
          return;
        }
      }
      
      // Проверяем темы
      const hoveredTopic = document.querySelector('.problem-topic[data-hovered="true"]');
      if (hoveredTopic) {
        e.preventDefault();
        const scrollAmount = 150;
        hoveredTopic.scrollBy({
          left: e.key === 'ArrowLeft' ? -scrollAmount : scrollAmount,
          behavior: 'smooth'
        });
      }
    }
  });
}

function initTagsScroll() {
  // Инициализируем глобальные обработчики один раз
  initGlobalKeyboardHandlers();
  
  // Находим все контейнеры с тегами
  const tagsColumns = document.querySelectorAll('.tags-column');
  
  tagsColumns.forEach(tagsColumn => {
    // Проверяем, не инициализирован ли уже этот контейнер
    if (tagsColumn.parentElement.classList.contains('tags-wrapper')) {
      return;
    }
    
    // Создаем обертку
    const wrapper = document.createElement('div');
    wrapper.className = 'tags-wrapper';
    
    // Вставляем обертку перед tags-column
    tagsColumn.parentNode.insertBefore(wrapper, tagsColumn);
    
    // Перемещаем tags-column внутрь обертки
    wrapper.appendChild(tagsColumn);
    
    // Создаем кнопки
    const leftBtn = document.createElement('button');
    leftBtn.className = 'tags-scroll-btn left';
    leftBtn.innerHTML = '‹';
    leftBtn.setAttribute('aria-label', 'Прокрутить влево');
    
    const rightBtn = document.createElement('button');
    rightBtn.className = 'tags-scroll-btn right';
    rightBtn.innerHTML = '›';
    rightBtn.setAttribute('aria-label', 'Прокрутить вправо');
    
    // Добавляем кнопки в обертку
    wrapper.appendChild(leftBtn);
    wrapper.appendChild(rightBtn);
    
    // Функция для обновления видимости кнопок
    const updateButtons = () => {
      const canScrollLeft = tagsColumn.scrollLeft > 0;
      const canScrollRight = 
        tagsColumn.scrollLeft < tagsColumn.scrollWidth - tagsColumn.clientWidth - 1;
      
      leftBtn.classList.toggle('hidden', !canScrollLeft);
      rightBtn.classList.toggle('hidden', !canScrollRight);
    };
    
    // Обработчики для кнопок
    leftBtn.addEventListener('click', () => {
      tagsColumn.scrollBy({
        left: -150,
        behavior: 'smooth'
      });
    });
    
    rightBtn.addEventListener('click', () => {
      tagsColumn.scrollBy({
        left: 150,
        behavior: 'smooth'
      });
    });
    
    // Обработчик клавиатуры для стрелок (локальный)
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const isFocused = wrapper.contains(document.activeElement) || 
                         document.activeElement === tagsColumn;
        
        if (isFocused) {
          e.preventDefault();
          const scrollAmount = 150;
          tagsColumn.scrollBy({
            left: e.key === 'ArrowLeft' ? -scrollAmount : scrollAmount,
            behavior: 'smooth'
          });
        }
      }
    };
    
    // Добавляем обработчик клавиатуры на контейнер и обертку
    tagsColumn.setAttribute('tabindex', '0');
    tagsColumn.addEventListener('keydown', handleKeyDown);
    wrapper.addEventListener('keydown', handleKeyDown);
    
    // Обработчики наведения мыши
    wrapper.addEventListener('mouseenter', () => {
      wrapper.setAttribute('data-hovered', 'true');
    });
    
    wrapper.addEventListener('mouseleave', () => {
      wrapper.removeAttribute('data-hovered');
    });
    
    // Обновляем видимость кнопок при прокрутке
    tagsColumn.addEventListener('scroll', updateButtons);
    
    // Обновляем видимость кнопок при изменении размера
    const resizeObserver = new ResizeObserver(updateButtons);
    resizeObserver.observe(tagsColumn);
    
    // Первоначальная проверка
    setTimeout(updateButtons, 100);
  });
  
  // Инициализируем скролл для тем
  initTopicsScroll();
}

// Функция для инициализации скролла тем
function initTopicsScroll() {
  const topicElements = document.querySelectorAll('.problem-topic:not([data-scroll-initialized])');
  
  topicElements.forEach(topicElement => {
    // Помечаем элемент как инициализированный
    topicElement.setAttribute('data-scroll-initialized', 'true');
    
    // Убеждаемся, что контейнер может скроллиться
    if (topicElement.style.display !== 'none') {
      topicElement.style.overflowX = 'auto';
      topicElement.style.overflowY = 'hidden';
      topicElement.style.scrollBehavior = 'smooth';
      topicElement.style.maxWidth = '100%';
      
      // Если внутри есть несколько элементов, используем flex
      const topicLinks = topicElement.querySelectorAll('.topic-link');
      if (topicLinks.length > 1) {
        topicElement.style.display = 'inline-flex';
        topicElement.style.flexWrap = 'nowrap';
        topicElement.style.gap = '6px';
      }
    }
    
    // Добавляем tabindex для возможности фокуса
    topicElement.setAttribute('tabindex', '0');
    
    // Обработчик клавиатуры для стрелок (локальный)
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const isFocused = document.activeElement === topicElement;
        
        if (isFocused) {
          e.preventDefault();
          const scrollAmount = 150;
          topicElement.scrollBy({
            left: e.key === 'ArrowLeft' ? -scrollAmount : scrollAmount,
            behavior: 'smooth'
          });
        }
      }
    };
    
    topicElement.addEventListener('keydown', handleKeyDown);
    
    // Обработчики наведения мыши
    topicElement.addEventListener('mouseenter', () => {
      topicElement.setAttribute('data-hovered', 'true');
    });
    
    topicElement.addEventListener('mouseleave', () => {
      topicElement.removeAttribute('data-hovered');
    });
  });
}

// Инициализация при загрузке DOM
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTagsScroll);
} else {
  initTagsScroll();
}

// Экспортируем функцию для ручной инициализации
export { initTagsScroll };

