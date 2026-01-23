// solutions.js
// Вместо дублированного кода auth
import { initAuthHandlers } from './common.js';
import { initTagsScroll } from './tagsScroll.js';
import { addToCart, checkInCart } from './cartFunctions.js';
import {
    loadCategories,
    initHashtagsTomSelect,
    initFilterHandlers,
    initTagClickHandler
} from './problemListCommon.js';

// Инициализация обработчиков авторизации
initAuthHandlers();

let choicesInstance;

let currentFilters = {
  search: '',
  hashtags: [],
  category: null,
  limit: 50,
  offset: 0
};

async function loadCards(search = '', category = null, hashtags = [], offset = 0) {
  const container = document.querySelector('.cards-container');
  container.innerHTML = 'Загрузка...';

  const params = new URLSearchParams();
  if (currentFilters.search) params.append('search', currentFilters.search);
  if (currentFilters.hashtags.length)
    params.append('hashtags', currentFilters.hashtags.join(','));
  if (currentFilters.category != null)
    params.append('category', currentFilters.category);
  params.append('limit', currentFilters.limit);
  params.append('offset', currentFilters.offset);

  try {
    const response = await fetch(`/api/solutions?${params.toString()}`);
    if (!response.ok) throw new Error('Ошибка HTTP: ' + response.status);
    const data = await response.json();

    sortAndRender(data);

  } catch (error) {
    container.innerHTML = `<p style="color:red; text-align:center">Ошибка загрузки данных: ${error.message}</p>`;
  }
}

// Функция loadCategories теперь импортируется из problemListCommon.js

function sortAndRender(data) {
  const sortValue = document.getElementById('sort').value;

  switch (sortValue) {
    case 'popularity':
      data.sort((a, b) => (b.Favourite || 0) - (a.Favourite || 0));
      break;
    case 'show':
      data.sort((a, b) => (b.Show || 0) - (a.Show || 0));
      break;
    case 'date':
      data.sort((a, b) => new Date(b.Modified_date) - new Date(a.Modified_date));
      break;
    default:
      break;
  }

  renderCards(data);
}

// Теперь используем градиентный фон вместо внешних изображений

function renderCards(data) {
  const container = document.querySelector('.cards-container');
  container.innerHTML = '';

  const templateElement = document.getElementById('card-template');
  if (!templateElement) {
    console.error("Шаблон не найден!");
    return;
  }
  const template = templateElement.content;

  if (data.length === 0) {
    container.innerHTML = '<p style="text-align:center;">Ничего не найдено</p>';
    return;
  }

  data.forEach(item => {
    const card = template.cloneNode(true);

    const link = card.querySelector('.card-title-link');
    link.href = `/html/solution.html?solutionId=${encodeURIComponent(item.ID)}`;

    const cardImg = card.querySelector('.card-image');
    const cardImageWrapper = card.querySelector('.card-image-wrapper');
    
    // Функция для генерации SVG изображения с градиентом и названием
    function getImageFromInternet(solutionName) {
      if (!solutionName || solutionName.trim() === '') {
        return null;
      }
      
      // Создаем хеш от названия для получения стабильного изображения
      let hash = 0;
      for (let i = 0; i < solutionName.length; i++) {
        const char = solutionName.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }
      
      const imageId = Math.abs(hash) % 1000;
      
      // Цвета для градиента на основе хеша
      const colors = [
        ['#667eea', '#764ba2'], // Фиолетовый
        ['#f093fb', '#f5576c'], // Розовый
        ['#4facfe', '#00f2fe'], // Синий
        ['#43e97b', '#38f9d7'], // Зеленый
        ['#fa709a', '#fee140'], // Желто-розовый
        ['#30cfd0', '#330867'], // Бирюзовый
        ['#a8edea', '#fed6e3'], // Пастель
        ['#d299c2', '#fef9d7'], // Лаванда
        ['#ff9a9e', '#fecfef'], // Нежно-розовый
        ['#ffecd2', '#fcb69f'], // Персиковый
      ];
      
      const colorPair = colors[imageId % colors.length];
      
      // Очищаем название для текста
      const displayText = solutionName.trim()
        .replace(/[<>]/g, '')
        .substring(0, 30);
      
      // Создаем SVG изображение с градиентом и текстом
      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
          <defs>
            <linearGradient id="grad${imageId}" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:${colorPair[0]};stop-opacity:1" />
              <stop offset="100%" style="stop-color:${colorPair[1]};stop-opacity:1" />
            </linearGradient>
          </defs>
          <rect width="400" height="300" fill="url(#grad${imageId})"/>
          <text x="50%" y="50%" text-anchor="middle" fill="white" font-family="Arial, sans-serif" 
                font-size="24" font-weight="bold" dy=".3em">
            ${displayText}
          </text>
        </svg>
      `;
      
      // Кодируем SVG в data URL
      return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }
    
    // Используем изображение из базы данных, но если это внешний URL или нет изображения, генерируем SVG
    if (item.Image && item.Image.trim() !== '') {
      // Если это внешний URL (не локальный файл), генерируем SVG изображение
      if (item.Image.startsWith('http://') || item.Image.startsWith('https://')) {
        const generatedImage = getImageFromInternet(item.Name);
        if (generatedImage) {
          cardImg.src = generatedImage;
          cardImg.alt = item.Name || 'Решение';
          cardImg.style.display = 'block';
          if (cardImageWrapper) {
            cardImageWrapper.style.background = 'none';
          }
        } else {
          // Не удалось сгенерировать - используем градиент
          cardImg.style.display = 'none';
          if (cardImageWrapper) {
            cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
          }
        }
      } else {
        // Локальный файл - пытаемся загрузить
        cardImg.src = item.Image;
        cardImg.alt = item.Name || 'Решение';
        cardImg.style.display = 'block';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'none';
        }
        
        // Обработка ошибки загрузки локального изображения
        cardImg.onerror = function() {
          // При ошибке локального файла генерируем SVG изображение
          const generatedImage = getImageFromInternet(item.Name);
          if (generatedImage) {
            this.src = generatedImage;
            this.style.display = 'block';
            if (cardImageWrapper) {
              cardImageWrapper.style.background = 'none';
            }
          } else {
            this.style.display = 'none';
            if (cardImageWrapper) {
              cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
          }
        };
      }
    } else {
      // Нет изображения - генерируем SVG изображение
      const generatedImage = getImageFromInternet(item.Name);
      if (generatedImage) {
        cardImg.src = generatedImage;
        cardImg.alt = item.Name || 'Решение';
        cardImg.style.display = 'block';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'none';
        }
      } else {
        // Не удалось сгенерировать - используем градиентный фон
        cardImg.style.display = 'none';
        if (cardImageWrapper) {
          cardImageWrapper.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        }
      }
    }

    const cardTitleText = card.querySelector('.card-title-text');
    cardTitleText.href = `/html/solution.html?solutionId=${encodeURIComponent(item.ID)}`;
    cardTitleText.textContent = item.Name;

    const favoriteCount = card.querySelector('.card-favorites .favorite-count');
    favoriteCount.textContent = item.Favourite || 0;

    // Общий рейтинг
    const ratingNumber = card.querySelector('.rating-number');
    if (ratingNumber) {
      ratingNumber.textContent = item.Rating || 0;
    }

    // Обработчик избранного для решений
    const favoriteIcon = card.querySelector('.favorite-icon');
    if (favoriteIcon) {
      favoriteIcon.style.cursor = 'pointer';
      
      // Проверяем статус избранного и меняем иконку
      if (item.IsFavourite === true) {
        favoriteIcon.src = '/assets/icons/love_6787061.png';
        favoriteIcon.classList.add('favorited');
      } else {
        favoriteIcon.src = '/assets/icons/love_9318199.png';
        favoriteIcon.classList.remove('favorited');
      }
      
      favoriteIcon.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await toggleSolutionFavorite(item.ID, favoriteIcon);
      });
    }

    // Отображаем темы из связанных проблем
    const topicElement = card.querySelector('.problem-topic');
    if (topicElement) {
      topicElement.innerHTML = '';
      // Собираем уникальные темы из всех связанных проблем
      const topicsMap = new Map();
      if (item.Problems && Array.isArray(item.Problems)) {
        item.Problems.forEach(problem => {
          if (problem.TopicInfo && problem.TopicInfo.Name) {
            const topicId = problem.TopicInfo.ID;
            if (!topicsMap.has(topicId)) {
              topicsMap.set(topicId, problem.TopicInfo);
            }
          }
        });
      }
      
      // Отображаем темы (берем первую, как в карточках проблем)
      if (topicsMap.size > 0) {
        const firstTopic = Array.from(topicsMap.values())[0];
        const topicLink = document.createElement('a');
        topicLink.className = 'topic-link';
        topicLink.href = '/';
        topicLink.textContent = firstTopic.Name;
        topicLink.setAttribute('data-topic-id', firstTopic.ID);
        topicLink.style.cursor = 'pointer';
        topicLink.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          window.location.href = `/?topic=${firstTopic.ID}`;
        });
        topicElement.appendChild(topicLink);
        topicElement.style.display = 'block';
      } else {
        topicElement.style.display = 'none';
      }
    }

    const tagsColumn = card.querySelector('.tags-column');
    tagsColumn.innerHTML = '';
    if (item.Problems && Array.isArray(item.Problems)) {
      item.Problems.forEach(problem => {
        if (problem.Hashtags && Array.isArray(problem.Hashtags)) {
          problem.Hashtags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';
            tagElement.textContent = tag.Name;
            tagElement.setAttribute('data-id', tag.ID);
            tagElement.style.cursor = 'pointer';
            tagsColumn.appendChild(tagElement);
          });
        }
      });
    }
    card.querySelector('.stat-item.views .stat-value').textContent = item.Show || 0;
    card.querySelector('.stat-item.comments .stat-value').textContent = item.CommentSolutions.length || 0;
    card.querySelector('.stat-item.shares .stat-value').textContent = item.Reply || 0;
    
    // Количество линков (связанных решений)
    const linksValue = item.LinkedSolutionsCount || item.LinkedSolutions?.length || 0;
    const linksElem = card.querySelector('.stat-item.links .stat-value');
    if (linksElem) linksElem.textContent = linksValue;

    // Кнопка добавления в корзину
    const cartBtn = card.querySelector('.card-cart-btn');
    if (cartBtn) {
      const cartImg = cartBtn.querySelector('img');
      
      cartBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        await handleAddToCart(item.ID, cartBtn, cartImg);
      });
      
      // Проверяем, есть ли уже в корзине
      checkInCart(item.ID).then(inCart => {
        if (inCart) {
          cartBtn.classList.add('in-cart');
          cartBtn.title = 'Уже в корзине';
          // Меняем иконку на shopping-bag_4505309 (зеленая заливка)
          if (cartImg && cartImg.src.includes('shopping-bag_7945129')) {
            cartImg.src = cartImg.src.replace('shopping-bag_7945129.png', 'shopping-bag_4505309.png');
          }
        } else {
          // Убеждаемся, что иконка shopping-bag_7945129 (зеленый ободок)
          if (cartImg && cartImg.src.includes('shopping-bag_4505309')) {
            cartImg.src = cartImg.src.replace('shopping-bag_4505309.png', 'shopping-bag_7945129.png');
          }
        }
      });
    }

    container.appendChild(card);
  });
  
  // Инициализируем прокрутку тегов после рендеринга
  setTimeout(() => {
    initTagsScroll();
  }, 100);
}

// Обработчик клика по тегам теперь используется через initTagClickHandler

// Функция initTomSelect заменена на использование initHashtagsTomSelect из problemListCommon.js

// Обработчики фильтров теперь инициализируются через initFilterHandlers

// Обработчик добавления в корзину
async function handleAddToCart(solutionId, button, img) {
  const result = await addToCart(solutionId);
  
  if (result.success) {
    button.classList.add('in-cart');
    button.title = 'Уже в корзине';
    // Меняем иконку на shopping-bag_4505309 (зеленая заливка)
    if (img && img.src.includes('shopping-bag_7945129')) {
      img.src = img.src.replace('shopping-bag_7945129.png', 'shopping-bag_4505309.png');
    }
    alert(result.message || 'Решение добавлено в корзину');
  } else {
    alert(result.error || 'Не удалось добавить в корзину');
  }
}

// Переключение избранного для решений
async function toggleSolutionFavorite(solutionId, iconElement) {
  try {
    const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
    const response = await fetch(`/api/solutions/${solutionId}/toggle-favourite`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.status === 401) {
      // Пробуем обновить токен
      const refreshResponse = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
      
      if (refreshResponse.ok) {
        // Повторяем запрос
        const retryResponse = await fetch(`/api/solutions/${solutionId}/toggle-favourite`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (retryResponse.ok) {
          const data = await retryResponse.json();
          const countElement = iconElement.closest('.card-favorites')?.querySelector('.favorite-count');
          if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
          }
          iconElement.classList.toggle('liked', data.is_favourite);
        }
      }
    } else if (response.ok) {
      const data = await response.json();
      const countElement = iconElement.closest('.card-favorites')?.querySelector('.favorite-count');
      if (countElement) {
        const currentCount = parseInt(countElement.textContent) || 0;
        countElement.textContent = data.is_favourite ? currentCount + 1 : Math.max(0, currentCount - 1);
      }
      // Переключаем иконку и класс favorited
      if (data.is_favourite) {
        iconElement.src = '/assets/icons/love_6787061.png';
        iconElement.classList.add('favorited');
      } else {
        iconElement.src = '/assets/icons/love_9318199.png';
        iconElement.classList.remove('favorited');
      }
    }
  } catch (error) {
    console.error('Ошибка добавления решения в избранное:', error);
  }
}

// Функция для перезагрузки карточек
function reloadCards() {
  loadCards();
}

// Инициализация
document.addEventListener('DOMContentLoaded', async () => {
  // Загружаем категории
  await loadCategories('category', false);
  
  // Инициализируем TomSelect для хэштегов
  choicesInstance = initHashtagsTomSelect('hashtags', (instance) => {
    currentFilters.hashtags = instance.getValue().map(v => parseInt(v, 10));
    currentFilters.offset = 0;
    reloadCards();
    document.querySelector('.ts-control')?.classList.add('has-items');
  });
  
  // Обработчик удаления хэштегов
  if (choicesInstance) {
    choicesInstance.control.addEventListener('click', function (event) {
      const tag = event.target.closest('.item');
      if (tag) {
        const value = tag.getAttribute('data-value');
        if (value !== null) {
          choicesInstance.removeItem(value);
          currentFilters.hashtags = choicesInstance.getValue().map(v => parseInt(v, 10));
          currentFilters.offset = 0;
          
          // Очищаем опции и закрываем выпадающий список при удалении
          choicesInstance.clearOptions();
          choicesInstance.close();
          choicesInstance.control_input.value = '';
          
          reloadCards();
          if (choicesInstance.items.length == 0) {
            const tsControl = document.querySelector('.ts-control');
            if (tsControl) {
              tsControl.classList.remove('has-items');
              // Убеждаемся, что плейсхолдер виден
              const input = tsControl.querySelector('input[type="text"]');
              if (input && !input.value) {
                input.placeholder = 'Выберите хэштеги';
              }
            }
          }
        }
      }
    });
    
    // Инициализация обработчиков фильтров
    initFilterHandlers(currentFilters, choicesInstance, reloadCards);
    initTagClickHandler(choicesInstance, currentFilters, reloadCards);
  }
  
  // Сортировка
  const sortSelect = document.getElementById('sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      currentFilters.offset = 0;
      reloadCards();
    });
  }
  
  // Загружаем карточки
  reloadCards();
});
